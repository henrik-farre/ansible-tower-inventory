# ansible-tower-inventory
Generates inventory that Ansible can understand by making API request to Ansible Tower / AWX.

Usage: 

* Set the following environment variables:
 - TOWER_URL (https://url.to.tower)
 - TOWER_USERNAME
 - TOWER_PASSWORD

* List available tower inventories
 tower-inventory.py --list-inventories

* Set the TOWER_INVENTORY_ID environment variable with the id of the inventory you would like to use

* List available tower inventories: `tower-inventory.py --list-inventories`

* Set the TOWER_INVENTORY_ID environment variable with the id of the inventory you would like to use

* Make sure `tower_inventory.py` is executeable and use it as an inventory file. E.g.: `ansible all -i tower_inventory.py -m ping`
