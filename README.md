# ansible-tower-inventory
Generates inventory that Ansible can understand by making API request to Ansible Tower.

Usage: 

1. Set the following environment variables:
 - TOWER_URL (https://url.to.tower)
 - TOWER_USERNAME
 - TOWER_PASSWORD

2. List available tower inventories
 tower-inventory.py --list-inventories

3. Set the TOWER_INVENTORY_ID environment variable with the id of the inventory you would like to use

4. Make sure tower_inventoryTOWER_PASSWORD

2. List available tower inventories
 tower-inventory.py --list-inventories

3. Set the TOWER_INVENTORY_ID environment variable with the id of the inventory you would like to use

4. Make sure tower_inventory is executeable and use it as an inventory file. E.g.: ansible all -i tower_inventory.py -m ping
