import asyncio
import snapcast.control
import subprocess
import time
import sys

macaddr = subprocess.getoutput("cat /sys/class/net/wlan0/address")
loop = asyncio.get_event_loop()
server = loop.run_until_complete(snapcast.control.create_server(
    loop, 'localhost'))
server_group = ''
list_client_to_add = []

for client in server.clients:
    print('CLIENT : ' + str(client.friendly_name) + "\nID : " + str(client.identifier) + '\nOLD GROUP :' + str(client.group) + "\n")

for client in server.clients:
    if client.identifier == macaddr:
        server_group = client.group
        print("The server is on " + str(client.friendly_name) + " and the group is " + str(server_group))
    else:
        list_client_to_add.append(client.identifier)
        print(str(client.friendly_name) + " needs to be added")

print("List of clients to add: ")
print(list_client_to_add)
print("\n\n\n")

#temp_list_client_to_add = list_client_to_add

for client_to_add in list_client_to_add:
#    print("Currently trying to add " + str(client_to_add) + "\n")
#    print("These are the available groups: ")
#    print(server.client(client_to_add).groups_available())
    for group in server.client(client_to_add).groups_available():
#        print(str(group) + " is available to the client " + str(client_to_add))
#        print("Server Group is: " + str(server_group) + "\nCurrently Testing group is: " + str(group))
        if str(group) == str(server_group):
#            print("Found the server group!")
            loop.run_until_complete(group.add_client(client_to_add))
            print(str(client_to_add) + " was added to " + str(server_group))
            #list_client_to_add.remove(client_to_add)
            #print("Updated clients to add: ")
            #print(list_client_to_add)
#        else:
#            print("Could not find the SERVER GROUP")
#        print("\n")

#print("We need to add: ")
#print(list_client_to_add)
#print("\n")

#TO DELETE
for client in server.clients:
    print('CLIENT : ' + str(client.friendly_name) + "\nID : " + str(client.identifier) + '\nNEW GROUP :' + str(client.group) + "\n")
sys.exit()
