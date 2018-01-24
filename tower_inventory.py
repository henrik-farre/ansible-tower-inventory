#!/usr/bin/env python2

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

import urllib2
import json
import argparse
import os

class TowerInventory(object):

    inventory = dict()

    def __init__(self):
        ''' Main execution path '''

        data_to_print = json.dumps(self.inventory)

        # Read settings and parse CLI arguments
        self.parse_cli_args()
        self.read_settings()

        req = urllib2.Request(
                url = self.tower_url + '/api/v1/authtoken/',
                headers = {
                    "Content-Type": "application/json"
                    },
                data = json.dumps({
                    "username": self.tower_username,
                    "password": self.tower_password
                    })
                )
        response = urllib2.urlopen(req)
        results = json.loads(response.read())
        self.token = results['token']

        if self.args.list_inventories:
            data_to_print = self.list_inventories()

        if self.args.list:
            self.inventory.update(self.list_inventory())
            data_to_print = json.dumps(self.inventory)

        if self.args.host:
            data_to_print = "Not implemented. For more information: http://docs.ansible.com/developing_inventory.html#tuning-the-external-inventory-script"

        print(data_to_print)

    def read_settings(self):
        self.tower_url = os.environ.get('TOWER_URL')
        self.tower_username = os.environ.get('TOWER_USERNAME')
        self.tower_password = os.environ.get('TOWER_PASSWORD')
        self.tower_inventory_id = os.environ.get('TOWER_INVENTORY_ID')

        if not self.tower_url:
            print "Plase set the environment variable TOWER_URL"
            exit()

        if not self.tower_username or not self.tower_password:
            print "Please set the environment variables TOWER_USERNAME and TOWER_PASSWORD"
            exit()

        if not self.tower_inventory_id and not self.args.list_inventories:
            print "Please set the environment variable TOWER_INVENTORY_ID or use the argument --list-inventories to list available inventories"
            exit()

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

        req = urllib2.Request(
                url = self.tower_url + '/api/v1/inventories/',
                headers = {
                    "Content-Type": "application/json",
                    "Authorization": "Token " + self.token
                    }
                )
        response = urllib2.urlopen(req)
        inventories = json.loads(response.read())

        for inventory in inventories['results']:
            data.append("[{}] {}".format(inventory['id'], inventory['name']))

        return '\n'.join(data)

    def get_groups(self):
        # TODO: replace page_size with pagination support:
        # https://docs.ansible.com/ansible-tower/latest/html/towerapi/pagination.html
        req = urllib2.Request(
                url = self.tower_url + '/api/v1/inventories/' + self.tower_inventory_id + '/groups/?page_size=200',
                headers = {
                    "Content-Type": "application/json",
                    "Authorization": "Token " + self.token
                    }
                )
        response = urllib2.urlopen(req)
        results = json.loads(response.read())

        return results['results']

    def get_group_vars(self, group):
        req = urllib2.Request(
                url = self.tower_url + group['related']['variable_data'],
                headers = {
                    "Content-Type": "application/json",
                    "Authorization": "Token " + self.token
                    }
                )
        response = urllib2.urlopen(req)
        results = json.loads(response.read())

        return results

    def get_hosts(self, group):
        req = urllib2.Request(
                url = self.tower_url + group['related']['all_hosts'] + '?enabled=true',
                headers = {
                    "Content-Type": "application/json",
                    "Authorization": "Token " + self.token
                    }
                )
        response = urllib2.urlopen(req)
        results = json.loads(response.read())

        return results['results']

    def get_host_vars(self, host):
        req = urllib2.Request(
                url = self.tower_url + host['related']['variable_data'],
                headers = {
                    "Content-Type": "application/json",
                    "Authorization": "Token " + self.token
                    }
                )
        response = urllib2.urlopen(req)
        results = json.loads(response.read())

        return results

    def get_inventory_vars(self):
        req = urllib2.Request(
                url = self.tower_url + '/api/v1/inventories/' + self.tower_inventory_id + '/variable_data/',
                headers = {
                    "Content-Type": "application/json",
                    "Authorization": "Token " + self.token
                    }
                )
        response = urllib2.urlopen(req)
        results = json.loads(response.read())

        return results

    def list_inventory(self):
        data = dict()
        host_vars = dict()
        self.inventory['_meta'] = dict()
        self.inventory['_meta']['hostvars'] = dict()

        # Put all hosts for the requested inventory into a "fake" all group named __inventory_all__
        self.inventory['__inventory_all__'] = dict()
        self.inventory['__inventory_all__']['hosts'] = []
        self.inventory['__inventory_all__']['vars'] = self.get_inventory_vars()

        groups = self.get_groups()
        for group in groups:
            group_data = dict()
            host_list = []

            hosts = self.get_hosts(group)
            for host in hosts:
                host_list.append(host['name'])
                self.inventory['_meta']['hostvars'][host['name']] = self.get_host_vars(host)
                self.inventory['__inventory_all__']['hosts'].append(host['name'])

            group_data['hosts'] = host_list
            group_vars = self.get_group_vars(group)
            if group_vars:
                group_data['vars'] = group_vars

            data[group['name']] = group_data

        return data

# Run the script
TowerInventory()
