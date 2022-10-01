from jinja2 import Environment, FileSystemLoader
from jdiff import extract_data_from_json
from jdiff.utils.diff_helpers import fix_deepdiff_key_names
from deepdiff import DeepDiff, Delta
from collections import defaultdict
from netmiko import ConnectHandler
from jdiff import CheckType
from pprint import pprint
from ttp import ttp
import json_delta
import schedule
import time
import json

def strip_lines(text):
  return "\n".join([s for s in text.splitlines() if s.strip()])

def get_from_dict(pathstring, data):
   # pathstring = root[0]['dhcp']['dhcp-pools']['OFFICE']['default-gateway']
   # data = [ {'dhcp': {...
   temp = data
   path = pathstring[4:].replace('[','').replace(']','/').replace('\'','')[:-1]
   for key in path.split('/'):
     if key.isnumeric():
       key = int(key)
     temp = temp[key]
   return temp

def make_patch(incoming, reference):
  diff_result = DeepDiff(incoming, reference)
  result = diff_result.get('values_changed', {})
  print('get result')
  for k, v in result.items():
    result[k] = v.get('new_value','')
  print(result)
  if diff_result.get("dictionary_item_added"):
    result.update({k: get_from_dict(k, reference) for k in diff_result["dictionary_item_added"]})

  removed = {}
  if diff_result.get("dictionary_item_removed"):
    removed.update({k: get_from_dict(k, incoming) for k in diff_result["dictionary_item_removed"]})

  return fix_deepdiff_key_names(result), fix_deepdiff_key_names(removed)

def main():
  env = Environment(loader=FileSystemLoader('templates'))
  template = env.get_template('ip_dhcp_pool.j2')
  
  f = open('ref/R1.json','r')
  reference = json.load(f)
  
  R1 = {
    "device_type": "cisco_ios",
    "host":     "192.168.122.2",
    "username": "cisco",
    "password": "cisco",
    "secret"  : "cisco"
  }

  with ConnectHandler(**R1) as net_connect:
    net_connect.enable()
    config = net_connect.send_command('show running-config | section ip dhcp')
    parser = ttp(data=config, template='parsers/ios_show_run_dhcp.ttp')
    parser.parse()
    results = parser.result(format='json')[0]
    incoming = json.loads(results)
    #print("Incoming config <<<<")
    #print(results)
  
  #print("Reference value >>>>")
  #print(json.dumps(reference, indent=4))
  
  check = CheckType.create(check_type='exact_match')
  diff  = check.evaluate(reference, incoming)
  if diff[1] == False:
    print("Diff ====")
    print(json.dumps(diff, indent=4))
  
    patch, removals = make_patch(incoming,reference)
    print("Changes to Apply:")
    config = strip_lines(template.render(data=patch, template='templates/ip_dhcp_pool.j2'))
    print(config)
    if config != '':
      with ConnectHandler(**R1) as net_connect:
        configlines = config.splitlines()
        net_connect.enable()
        output = net_connect.send_config_set(configlines)
        output += net_connect.save_config()
        print(output)
  else:
    print("Configuration is compliant.")

if __name__ == '__main__':
  print("Setting up scheduler...")
  schedule.every().minute.do(main)
  while True:
    schedule.run_pending()
    time.sleep(1)
