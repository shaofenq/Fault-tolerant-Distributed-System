import socket
import datetime
import re
import json

with open('ip.json') as f:
    ip = json.load(f)

with open('port.json') as fp:
    port = json.load(fp)

GFD_ip = ip['GFD']
GFD_port = port['GFD']
server_ip_1 = ip['S1']
server_ip_2 = ip['S2']
server_ip_3 = ip['S3']
server1_port = port['S1']
server2_port = port['S2']
server3_port = port['S3']

sock_4 = socket.socket(socket.AF_INET, socket.SOCK_STREAM)# for connection to GFD
server_GFD = (GFD_ip, GFD_port)  # unknow port number from GFD
sock_4.connect(server_GFD)
client_name = "C3"
#isActive = True
change = False

while True:

    # Send request to server
    request_message = input("\nPlease enter the message you want to send to Sever: ")
    if request_message == "change to passive" or request_message == "change to active":
        change = True
    
    reply_message_1 = ''
    reply_message_2 = ''
    reply_message_3 = ''

    # send request for GFD
    request_membership = "change" if change == True else "null"
    sock_4.send(request_membership.encode())

    # receive membership from GFD (a number)
    membership = sock_4.recv(1024).decode()
    print(membership)

    if request_message == "change to passive" or request_message == "change to active":
        continue

    if "S1" in membership:
        sock_1 = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_address_1 = (server_ip_1, server1_port)
        print("Connecting to {} port {}".format(server_address_1[0], server_address_1[1]))
        sock_1.connect(server_address_1)
        sock_1.send(client_name.encode())
        success_message_1 = sock_1.recv(1024).decode()
        print(success_message_1)
    if "S2" in membership:
        sock_2 = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_address_2 = (server_ip_2, server2_port)
        print("Connecting to {} port {}".format(server_address_2[0], server_address_2[1]))
        sock_2.connect(server_address_2)
        sock_2.send(client_name.encode())
        success_message_2 = sock_2.recv(1024).decode()
        print(success_message_2)
    if "S3" in membership:
        sock_3 = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_address_3 = (server_ip_3, server3_port)
        print("Connecting to {} port {}".format(server_address_3[0], server_address_3[1]))
        sock_3.connect(server_address_3)
        sock_3.send(client_name.encode())
        success_message_3 = sock_3.recv(1024).decode()
        print(success_message_3)

    # send request to each server
    if "S1" in membership:
        sock_1.send(request_message.encode())
        current_time = datetime.datetime.now()
        print("[{}] Sent <{}, S1, {}, request>".format(str(current_time), client_name, request_message))
        reply_message_1 = sock_1.recv(1024).decode()
        
    if "S2" in membership:
        sock_2.send(request_message.encode())
        current_time = datetime.datetime.now()
        print("[{}] Sent <{}, S2, {}, request>".format(str(current_time), client_name, request_message))
        reply_message_2 = sock_2.recv(1024).decode()
        
    if "S3" in membership:
        sock_3.send(request_message.encode())
        current_time = datetime.datetime.now()
        print("[{}] Sent <{}, S3, {}, request>".format(str(current_time), client_name, request_message))
        reply_message_3 = sock_3.recv(1024).decode()


    current_time = datetime.datetime.now()
    if reply_message_1:
        print("[{}] Received <{}, {}, {}, reply>".format(str(current_time), client_name, membership, reply_message_1))
        if reply_message_2:
            print("request_num {}: Discard duplicate reply from S2".format(request_message))
        if reply_message_3:
            print("request_num {}: Discard duplicate reply from S3".format(request_message))
    elif reply_message_2:
        print("[{}] Received <{}, {}, {}, reply>".format(str(current_time), client_name, membership, reply_message_2))
        if reply_message_3:
            print("request_num {}: Discard duplicate reply from S3".format(request_message))
    elif reply_message_3:
        print("[{}] Received <{}, {}, {}, reply>".format(str(current_time), client_name, membership, reply_message_3))


    # Print request message on client console

    # disconnect from server using 'exit'
    if request_message == "exit":
        print("Disconnect from S1，S2, S3!")
        break
    
    if "S1" in membership:
        sock_1.close()
    if "S2" in membership:
        sock_2.close()
    if "S3" in membership:
        sock_3.close()

sock_4.close()
