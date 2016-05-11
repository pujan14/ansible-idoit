#!/usr/bin/python
# Specify right path in variable FACTS
# Execute this script with single parameter, hostname, which should be same in ansible and idoit.
# If name of host is different in ansible and idoit use first argument as ansible name and second argument as name in idoit.
from socket import gethostbyaddr
import jsonrpclib
import os
import sys
import yaml
FACTS = "/tmp/dom"

apikey = "your_api_key"
server = jsonrpclib.Server("http://idoit.cc-0.dom.de/src/jsonrpc.php")
ANSIBLE_HOST = sys.argv[1]
if len(sys.argv) < 3:
    HOST = ANSIBLE_HOST
else:
    HOST = sys.argv[2]
FACTS = os.path.abspath(FACTS)


def hostidfromtitle(host_title):
    try:
        return int(server.cmdb.objects(apikey=apikey, filter={"title": host_title, "limit": "1"}).pop().get('id'))
    except IndexError:
        print "idoit did not find specified host. Please check that host exist in idoit."
        print "If host has different name in idoit pass it (name inside idoit) as second parameter to this script."
        sys.exit(0)
HOST_ID = hostidfromtitle(HOST)


def idfromtitle(search_title, category, objID=HOST_ID):
    for entry in server.cmdb.category.read(apikey=apikey, objID=HOST_ID, category=category):
        if entry["title"] == search_title:
            return int(entry["id"])


def idfromip(search_ip, objID=HOST_ID):
    for entry in server.cmdb.category.read(apikey=apikey, objID=HOST_ID, category="C__CATG__IP"):
        if entry["hostaddress"]["ref_title"] == search_ip:
            return int(entry["id"])

with open(FACTS + "/" + ANSIBLE_HOST, "r") as f:
        facts = yaml.load(f)
for i in range(10):
    if "ansible_eth" + str(i) in facts["ansible_facts"]:
        IFACE = facts["ansible_facts"]["ansible_eth" + str(i)]["device"]
        IFACE_ID = None
        if facts["ansible_facts"]["ansible_virtualization_role"] == "guest":
            IFACE_ID = idfromtitle(IFACE, category="C__CMDB__SUBCAT__NETWORK_INTERFACE_P")
            IFACE_DATA = {
                "title": IFACE,
                "model": "Virtual Ethernetdevice",
                "description": "Autocreated",
            }
            if IFACE_ID is None:
                IFACE_ID = int(server.cmdb.category.create(apikey=apikey, objID=HOST_ID, category="C__CMDB__SUBCAT__NETWORK_INTERFACE_P", data=IFACE_DATA).get('id'))
                print "Created Interface %s" % IFACE
            else:
                IFACE_DATA["id"] = IFACE_ID
                server.cmdb.category.update(apikey=apikey, objID=HOST_ID, category="C__CMDB__SUBCAT__NETWORK_INTERFACE_P", data=IFACE_DATA).get('message')
                print "Updated Interface %s" % IFACE

        PORT_ID = idfromtitle(IFACE, category="C__CMDB__SUBCAT__NETWORK_PORT")
        PORT_DATA = {
            "active": facts["ansible_facts"]["ansible_eth" + str(i)]["active"],
            "default_vlan": "-",
            "description": "Autocreated",
            "duplex": "2",
            "interface": IFACE_ID,
            "layer2_assignment": "-",
            "mac": facts["ansible_facts"]["ansible_eth" + str(i)]["macaddress"],
            "mtu": facts["ansible_facts"]["ansible_eth" + str(i)]["mtu"],
            "negotiation": "1",
            "plug_type": "RJ45",
            "port_mode": "1",
            "port_type": "Ethernet",
            "speed": "1",
            "speed_type": "4",
            "title": "eth" + str(i),
        }
        if PORT_ID is None:
            PORT_ID = int(server.cmdb.category.create(apikey=apikey, objID=HOST_ID, category="C__CMDB__SUBCAT__NETWORK_PORT", data=PORT_DATA).get('id'))
            print "Created Port %s" % IFACE
        else:
            PORT_DATA["id"] = PORT_ID
            server.cmdb.category.update(apikey=apikey, objID=HOST_ID, category="C__CMDB__SUBCAT__NETWORK_PORT", data=PORT_DATA).get('message')
            print "Updated Port %s" % IFACE

        if "ipv4" in facts["ansible_facts"]["ansible_eth" + str(i)]:
            IP = facts["ansible_facts"]["ansible_eth" + str(i)]["ipv4"]["address"]
            IP_ID = idfromip(IP)
            try:
                HOSTNAME = gethostbyaddr(IP)[0]
            except:
                HOSTNAME = None
            IP_DATA = {
                "active": facts["ansible_facts"]["ansible_eth" + str(i)]["active"],
                "assigned_port": PORT_ID,
                "description": "Autocreated",
                "hostaddress": IP,
                "hostname": HOSTNAME,
                "ipv4_address": IP,
                "ipv4_assignment": "2",
                "ipv6_assignment": "1",
                "ipv6_scope": "1",
                "primary": "1",
            }
            if IP_ID is None:
                IP_ID = int(server.cmdb.category.create(apikey=apikey, objID=HOST_ID, category="C__CATG__IP", data=IP_DATA).get('id'))
                print "Created IP %s" % IP
            else:
                IP_DATA["id"] = IP_ID
                server.cmdb.category.update(apikey=apikey, objID=HOST_ID, category="C__CATG__IP", data=IP_DATA).get('message')
                print "Updated IP %s" % IP

        try:
            for IPS in facts["ansible_facts"]["ansible_eth" + str(i)]["ipv4_secondaries"]:
                IP = IPS.get('address')
                IP_ID = idfromip(IP)
                try:
                    HOSTNAME = gethostbyaddr(IP)[0]
                except:
                    HOSTNAME = None
                IP_DATA = {
                    "active": facts["ansible_facts"]["ansible_eth" + str(i)]["active"],
                    "assigned_port": PORT_ID,
                    "description": "Autocreated",
                    "hostaddress": IP,
                    "hostname": HOSTNAME,
                    "ipv4_address": IP,
                    "ipv4_assignment": "2",
                    "ipv6_assignment": "1",
                    "ipv6_scope": "1",
                }
                if IP_ID is None:
                    IP_ID = int(server.cmdb.category.create(apikey=apikey, objID=HOST_ID, category="C__CATG__IP", data=IP_DATA).get('id'))
                    print "Created IP %s" % IP
                else:
                    IP_DATA["id"] = IP_ID
                    server.cmdb.category.update(apikey=apikey, objID=HOST_ID, category="C__CATG__IP", data=IP_DATA).get('message')
                    print "Updated IP %s" % IP
        except:
            print
