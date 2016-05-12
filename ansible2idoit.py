#!/usr/bin/python
# Specify right path in variable FACTS
# Execute this script with single parameter, hostname, which should be same in ansible and idoit.
# If name of host is different in ansible and idoit use first argument as ansible name and second argument as name in idoit.
from socket import gethostbyaddr
import jsonrpclib
import os
import sys
import yaml

# Modify  following variables for your needs
FACTS = "/home/test/facts"
apikey = "your_api_key"
URL = "http://demo.idoit.de/src/jsonrpc.php"

server = jsonrpclib.Server(URL)
ANSIBLE_HOST = sys.argv[1]
if len(sys.argv) < 3:
    HOST = ANSIBLE_HOST
else:
    HOST = sys.argv[2]
FACTS = os.path.abspath(FACTS)


def hostidfromtitle(host_title):
    try:
        return int(server.cmdb.objects(apikey=apikey, filter={"title": host_title, "limit": "1"}).pop().get("id"))
    except IndexError:
        print "idoit did not find specified host. Please check that host exist in idoit."
        print "If host has different name in idoit pass it (name inside idoit) as second parameter to this script."
        sys.exit(0)
HOST_ID = hostidfromtitle(HOST)


def idfromtitle(search_title, category, objID=HOST_ID):
    for entry in server.cmdb.category.read(apikey=apikey, objID=HOST_ID, category=category):
        if entry["title"] == search_title:
            return int(entry["id"])


def idfromtitle2(search_title, category, objID=HOST_ID):
    for entry in server.cmdb.category.read(apikey=apikey, objID=HOST_ID, category=category):
        if entry["title"]["title"] == search_title:
            return int(entry["id"])


def idfromip(search_ip, objID=HOST_ID):
    for entry in server.cmdb.category.read(apikey=apikey, objID=HOST_ID, category="C__CATG__IP"):
        if entry["hostaddress"]["ref_title"] == search_ip:
            return int(entry["id"])


def send_data(data, category):
    if data["id"] is None:
        server.cmdb.category.create(apikey=apikey, objID=HOST_ID, category=category, data=data)
        sys.stdout.write("Created ")
    else:
        server.cmdb.category.update(apikey=apikey, objID=HOST_ID, category=category, data=data)
        sys.stdout.write("Updated ")

with open(FACTS + "/" + ANSIBLE_HOST, "r") as f:
    facts = yaml.load(f)

for ansible_iface in facts["ansible_facts"]["ansible_interfaces"]:
    if "ansible_" + str(ansible_iface) in facts["ansible_facts"] and ansible_iface != "lo":
        IFACE = facts["ansible_facts"]["ansible_" + str(ansible_iface)]["device"]
        IFACE_ID = None
        if facts["ansible_facts"]["ansible_virtualization_role"] == "guest":
            IFACE_ID = idfromtitle(IFACE, category="C__CMDB__SUBCAT__NETWORK_INTERFACE_P")
            IFACE_DATA = {
                "description": "Autocreated",
                "id": IFACE_ID,
                "model": "Virtual Ethernetdevice",
                "title": IFACE,
            }
            send_data(IFACE_DATA, "C__CMDB__SUBCAT__NETWORK_INTERFACE_P")
            print "Interface %s" % IFACE

        PORT_ID = idfromtitle(IFACE, category="C__CMDB__SUBCAT__NETWORK_PORT")
        PORT_DATA = {
            "active": facts["ansible_facts"]["ansible_" + str(ansible_iface)]["active"],
            "default_vlan": "-",
            "description": "Autocreated",
            "duplex": "2",
            "id": PORT_ID,
            "interface": IFACE_ID,
            "layer2_assignment": "-",
            "mac": facts["ansible_facts"]["ansible_" + str(ansible_iface)]["macaddress"],
            "mtu": facts["ansible_facts"]["ansible_" + str(ansible_iface)]["mtu"],
            "negotiation": "1",
            "plug_type": "RJ45",
            "port_mode": "1",
            "port_type": "Ethernet",
            "speed": "1",
            "speed_type": "4",
            "title": ansible_iface,
        }
        send_data(PORT_DATA, "C__CMDB__SUBCAT__NETWORK_PORT")
        print "Port %s" % IFACE

        if "ipv4" in facts["ansible_facts"]["ansible_" + str(ansible_iface)]:
            IP = facts["ansible_facts"]["ansible_" + str(ansible_iface)]["ipv4"]["address"]
            IP_ID = idfromip(IP)
            try:
                HOSTNAME = gethostbyaddr(IP)[0]
            except:
                HOSTNAME = None
            IP_DATA = {
                "active": facts["ansible_facts"]["ansible_" + str(ansible_iface)]["active"],
                "assigned_port": PORT_ID,
                "description": "Autocreated",
                "hostaddress": IP,
                "hostname": HOSTNAME,
                "id": IP_ID,
                "ipv4_address": IP,
                "ipv4_assignment": "2",
                "ipv6_assignment": "1",
                "ipv6_scope": "1",
                "primary": "1",
            }
            send_data(IP_DATA, "C__CATG__IP")
            print "IP %s" % IP

        if "ipv6" in facts["ansible_facts"]["ansible_" + str(ansible_iface)]:
            for IPS in facts["ansible_facts"]["ansible_" + str(ansible_iface)]["ipv6"]:
                IPv6 = IPS["address"]
                IPv6_ID = idfromip(IPv6)
                try:
                    HOSTNAME = gethostbyaddr(IPv6)[0]
                except:
                    HOSTNAME = None
                if "link" in IPS["scope"]:
                    IPv6_DATA = {
                        "assigned_port": PORT_ID,
                        "description": "Autocreated",
                        "hostaddress": IPv6,
                        "hostname": HOSTNAME,
                        "id": IPv6_ID,
                        "ipv6_address": IPv6,
                        "ipv6_assignment": "3",
                        "ipv6_scope": "Link Local Unicast",
                        "primary": "0",
                        "net": "21",
                        "net_type": "1000",
                    }
                    send_data(IPv6_DATA, "C__CATG__IP")
                    print "IPv6 %s" % IPv6

        try:
            for IPS in facts["ansible_facts"]["ansible_" + str(ansible_iface)]["ipv4_secondaries"]:
                IP = IPS.get("address")
                IP_ID = idfromip(IP)
                try:
                    HOSTNAME = gethostbyaddr(IP)[0]
                except:
                    HOSTNAME = None
                IP_DATA = {
                    "active": facts["ansible_facts"]["ansible_" + str(ansible_iface)]["active"],
                    "assigned_port": PORT_ID,
                    "description": "Autocreated",
                    "hostaddress": IP,
                    "hostname": HOSTNAME,
                    "id": IP_ID,
                    "ipv4_address": IP,
                    "ipv4_assignment": "2",
                    "ipv6_assignment": "1",
                    "ipv6_scope": "1",
                }
                send_data(IP_DATA, "C__CATG__IP")
                print "IP %s" % IP
        except:
            print

if "SSH_CONNECTION" in facts["ansible_facts"]["ansible_env"]:
    IP = facts["ansible_facts"]["ansible_env"]["SSH_CONNECTION"].split()[2]
    try:
        HOSTNAME = gethostbyaddr(IP)[0]
        ACCESS_ID = idfromtitle(HOSTNAME, category="C__CATG__ACCESS")
        ACCESS_DATA = {
            "description": "Autocreated",
            "id": ACCESS_ID,
            "primary": "1",
            "title": HOSTNAME,
            "type": "Remote Access",
            "url": "ssh://" + HOSTNAME,
        }
        send_data(ACCESS_DATA, "C__CATG__ACCESS")
        print "access info %s" % IP
        ACCESS_ID = None
    except:
        None
    ACCESS_ID = idfromtitle(IP, category="C__CATG__ACCESS")
    ACCESS_DATA = {
        "description": "Autocreated",
        "id": ACCESS_ID,
        "primary": "0",
        "title": IP,
        "type": "Remote Access",
        "url": "ssh://" + IP,
    }
    send_data(ACCESS_DATA, "C__CATG__ACCESS")
    print "access info %s" % IP

print
if facts["ansible_facts"]["ansible_virtualization_role"] == "guest":
    if "ansible_memtotal_mb" in facts["ansible_facts"]:
        MEM = facts["ansible_facts"]["ansible_memtotal_mb"] / 1000
        MEM_ID = idfromtitle2("Virtuelles RAM", category="C__CATG__MEMORY")
        MEM_DATA = {
            "capacity": MEM,
            "description": "Autocreated",
            "id": MEM_ID,
            "title": "Virtuelles RAM",
            "unit": "GB",
        }
        send_data(MEM_DATA, "C__CATG__MEMORY")
        print "Memory %sGB" % MEM
