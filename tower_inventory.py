#!/usr/bin/env python

'''
tower_inventory.py

Ansible Tower "external" inventory script
=================================

Generates inventory that Ansible can understand by making API request to
Ansible Tower using the Requests library.

NOTE: This script assumes Ansible is being executed where the environment
variables needed have already been set:
    export TOWER_URL=https://url.to.tower
    export TOWER_USERNAME=username
    export TOWER_PASSWORD=password

    export TOWER_INVENTORY_ID (Run tower_inventory.py --list-inventories
    to list available inventory id's)


'''
__author__ = "Stig Christian Aske"
__email__ = "stigchristian@me.com"
__license__ = "MIT"
__version__ = "1.0.0"

import requests
import json
import argparse
import os

class TowerInventory(object):

    ssl_verify = False
    inventory = dict()

    def __init__(self):
        ''' Main execution path '''

        # Don't display urllib3 warnings (i.e. InsecureRequestWarning)
        if not self.ssl_verify:
            requests.packages.urllib3.disable_warnings()

        data_to_print = json.dumps(self.inventory)

        # Read settings and parse CLI arguments
        self.parse_cli_args()
        self.read_settings()

        if self.args.list_inventories:
            data_to_print = self.list_inventories()

        if self.args.list:
            self.inventory.update(self.list_inventory())
            data_to_print = json.dumps(self.inventory)

        if self.args.host:
            data_to_print = "Not implemented. For more information: http://docs.ansible.com/developing_inventory.html#tuning-the-external-inventory-script"

        print(data_to_print)

    def read_settings(self):
        tower_url = os.environ.get('TOWER_URL')
        tower_username = os.environ.get('TOWER_USERNAME')
        tower_password = os.environ.get('TOWER_PASSWORD')
        tower_inventory_id = os.environ.get('TOWER_INVENTORY_ID')

        if not tower_url:
            print "Plase set the environment variable TOWER_URL"
            exit()

        if not tower_username or not tower_password:
            print "Please set the environment variables TOWER_USERNAME and TOWER_PASSWORD"
            exit()

        if not tower_inventory_id and not self.args.list_inventories:
            print "Please set the environment variable TOWER_INVENTORY_ID or use the argument --list-inventories to list available inventories"
            exit()

        self.tower_url = tower_url
        self.tower_credentials = (tower_username, tower_password)
        self.tower_inventory_id = tower_inventory_id

    def parse_cli_args(self):
        ''' Command line argument processing '''
        parser = argparse.ArgumentParser(description='Produce an Ansible Inventory file based on Ansible Tower')

        group = parser.add_mutually_exclusive_group(required=True)
        group.add_argument('--list', action='store_true', help='List hosts in Ansible Tower Inventory')
        group.add_argument('--host', help='List variables for a host in the Ansible Tower Inventory')
        group.add_argument('--list-inventories', action='store_true', help='List Ansible Tower Inventories')
        self.args = parser.parse_args()

    def list_inventories(self):
        data = []

	r = requests.get(self.tower_url + "/api/v1/inventories/", auth=self.tower_credentials, verify=self.ssl_verify)
	inventories = r.json()

	for inventory in inventories['results']:
	    data.append("[{}] {}".format(inventory['id'], inventory['name']))

	return '\n'.join(data)

    def get_groups(self):
        r = requests.get(self.tower_url + '/api/v1/inventories/' + self.tower_inventory_id + '/groups/', auth=self.tower_credentials, verify=self.ssl_verify)
        return r.json()['results']

    def get_group_vars(self, group):
        r = requests.get(self.tower_url + group['related']['variable_data'], auth=self.tower_credentials, verify=self.ssl_verify)
        return r.json()

    def get_hosts(self, group):
        r = requests.get(self.tower_url + group['related']['all_hosts'], auth=self.tower_credentials, verify=self.ssl_verify)
        return r.json()['results']

    def get_host_vars(self, host):
        r = requests.get(self.tower_url + host['related']['variable_data'], auth=self.tower_credentials, verify=self.ssl_verify)
        if r.content: #Bug in Ansible Tower API, should return empty json ({}) when no data, but returns empty string
            return r.json()
        else:
            return {}

    def list_inventory(self):
        data = dict()
        host_vars = dict()
        self.inventory['_meta'] = dict()
        self.inventory['_meta']['hostvars'] = dict()

        groups = self.get_groups()

        for group in groups:
            group_data = dict()
            host_list = []
            
            hosts = self.get_hosts(group)
            for host in hosts:
                host_list.append(host['name'])
                self.inventory['_meta']['hostvars'][host['name']] = self.get_host_vars(host)

            group_data['hosts'] = host_list
            group_vars = self.get_group_vars(group)
            if group_vars:
                group_data['vars'] = group_vars

            data[group['name']] = group_data

        return data

# Run the script
TowerInventory()
