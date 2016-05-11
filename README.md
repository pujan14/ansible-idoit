# ansible-idoit
Script to import ansible facts into idoit

Specify your API key in apikey, path to facts and URL to idoit api.

Execute this script with single parameter, hostname, which should be same in ansible and idoit.
If name of host is different in ansible and idoit use first argument as ansible name and second argument as name in idoit.

Example of facts gathered by ansible can be seen [here](http://docs.ansible.com/ansible/playbooks_variables.html#information-discovered-from-systems-facts)

Display facts from all hosts and store them indexed by hostname at /tmp/facts.
ansible all -m setup --tree /tmp/facts
