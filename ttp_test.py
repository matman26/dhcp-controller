#!/usr/bin/python3
from ttp import ttp
from pprint import pprint

data = """
no ip dhcp use vrf connected
ip dhcp pool SITE1
   network 10.20.30.0 255.255.255.0
   subnet prefix-length 24
   domain-name TEST
   default-router 192.168.1.1
   lease 22
ip dhcp pool TOTO
   lease infinite
ip dhcp pool SITE
"""

ttp_template = """
<doc>
Reads the output from 'show running-config | section ip dhcp'

IN ---
ip dhcp pool SITE1
   network 10.20.30.0 255.255.255.0
   subnet prefix-length 24
   domain-name TEST
   default-router 192.168.1.1
   lease 22
ip dhcp pool TOTO
   lease infinite
ip dhcp pool SITE


OUT ---
{
  'dhcp': {
    'dhcp-pool': {
      'SITE1': {
        'network': {
	  'address': '10.20.30.0',
	  'mask': '255.255.255.0'
	},
	'subnet': {
	  'prefix-length': 24
	},
	'domain-name': 'TEST',
	'default-gateway': '192.168.1.1',
	'lease': 22
      },
      'TOTO': {
	'lease': 'infinite'
      }
      'SITE': {
      }
    }
  }
}
</doc>
<macro>
def string_or_int(data):
  return int(data) if data.isnumeric() else data
</macro>
<group name="dhcp">
 <group name="dhcp-pool">
  <group name="{{pool-name}}">
ip dhcp pool {{ pool-name }}
   <group name="network">
   network {{ address | IP }} {{ mask | IP }}
   </group>
   <group name="subnet">
   subnet prefix-length {{ prefix-length | to_int }}
   </group>
   domain-name {{ domain-name }}
   default-router {{ default-gateway | IP }}
   lease {{ lease-time | macro('string_or_int') }}
  </group>
 </group>
</group>
"""

parser = ttp(data=data,template=ttp_template)
parser.parse()
results = parser.result(format='json')[0]
print(results)
