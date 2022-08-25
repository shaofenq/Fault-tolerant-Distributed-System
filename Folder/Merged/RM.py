import socket
from _thread import *
from sys import _clear_type_cache
import time
import datetime
import json


with open('ip.json') as f:
    ip = json.load(f)

with open('port.json') as fp:
    port = json.load(fp)

server_ip_1 = ip['S1']
server_ip_2 = ip['S2']
server_ip_3 = ip['S3']
GFD_ip = ip['GFD']
GFD_port = port['GFD']
RM_ip = ip['RM']
RM_port = port['RM']
RM_name = "RM"

version = 1
membership = []
status = ['active', 'died', 'died', 'died']
primary_index = -1

# update membership and include "primary" in status
def get_membership_from_status():
    global status
    global membership
    global primary_index
    new_membership = []
    if status[1] == 'alive':
        new_membership.append('S1')
    if status[2] == 'alive':
        new_membership.append('S2')
    if status[3] == 'alive':
        new_membership.append('S3')
    membership = new_membership

    if primary_index == -1 or status[primary_index] == 'died':
        # select an alive server to be new primary
        for i in range(1, 4):
            if status[i] == 'alive':
                status[i] = 'primary'
                primary_index = i
                print("New primary selected: S{}.".format(primary_index))
                break

    # no server alive condition: new primary is not selected
    if primary_index == -1 or status[primary_index] == 'died':
        print("All servers are dead, no primary selected.")
    else:
        status[primary_index] = 'primary'

    print("Status right now: {}".format(status))


def init_socket():
    # Create a TCP/IP socket
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    return server

def init_as_server(RM_ip, RM_port):
    # Create a TCP/IP socket
    RM = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    # Bind the socket to the port
    RM_address = (RM_ip, RM_port)
    print("Starting up RM.")
    RM.bind(RM_address)

    # Listen for incoming connections
    RM.listen(5)
    print("Waiting for connection from GFD!")
    return RM

def RM_server1_connection():
    sock_1 = init_socket()
    server_address_1 = (server_ip_1, 1111)
    sock_1.connect(server_address_1)
    sock_1.send(RM_name.encode())
    # need a reply from server to avoid message jam
    success_message = sock_1.recv(1024).decode()
    return sock_1

def RM_server2_connection():
    sock_2 = init_socket()
    server_address_2 = (server_ip_2, 2222)
    sock_2.connect(server_address_2)
    sock_2.send(RM_name.encode())
    # need a reply from server to avoid message jam
    success_message = sock_2.recv(1024).decode()
    return sock_2

def RM_server3_connection():
    sock_3 = init_socket()
    server_address_3 = (server_ip_3, 3333)
    sock_3.connect(server_address_3)
    sock_3.send(RM_name.encode())
    # need a reply from server to avoid message jam
    success_message = sock_3.recv(1024).decode()
    return sock_3


# RM as client talk to server
def RM_checkpoint_connection():
    global status
    global membership
    if primary_index == -1 or status[primary_index] == 'died':
        print("Primary is dead, checkpoint connection fail.")
        return
    # S1 is primary
    if primary_index == 1:
        sock_1 = RM_server1_connection()
        checkpoint_request = 'checkpoint'
        sock_1.send(checkpoint_request.encode())
        checkpoint_reply = sock_1.recv(1024).decode()
        checkpoint_state = 'state {}'.format(checkpoint_reply)
        if status[2] == 'alive':
            sock_2 = RM_server2_connection()
            sock_2.send(checkpoint_state.encode())
            success_message = sock_2.recv(1024).decode()
        if status[3] == 'alive':
            sock_3 = RM_server3_connection()
            sock_3.send(checkpoint_state.encode())
            success_message = sock_3.recv(1024).decode()

    # S2 is primary
    if primary_index == 2:
        sock_2 = RM_server2_connection()
        checkpoint_request = 'checkpoint'
        sock_2.send(checkpoint_request.encode())
        checkpoint_reply = sock_2.recv(1024).decode()
        checkpoint_state = 'state {}'.format(checkpoint_reply)
        if status[1] == 'alive':
            sock_1 = RM_server1_connection()
            sock_1.send(checkpoint_state.encode())
            success_message = sock_1.recv(1024).decode()
        if status[3] == 'alive':
            sock_3 = RM_server3_connection()
            sock_3.send(checkpoint_state.encode())
            success_message = sock_3.recv(1024).decode()

    # S3 is primary
    if primary_index == 3:
        sock_3 = RM_server3_connection()
        checkpoint_request = 'checkpoint'
        sock_3.send(checkpoint_request.encode())
        checkpoint_reply = sock_3.recv(1024).decode()
        checkpoint_state = 'state {}'.format(checkpoint_reply)
        if status[1] == 'alive':
            sock_1 = RM_server1_connection()
            sock_1.send(checkpoint_state.encode())
            success_message = sock_1.recv(1024).decode()
        if status[2] == 'alive':
            sock_2 = RM_server2_connection()
            sock_2.send(checkpoint_state.encode())
            success_message = sock_2.recv(1024).decode()

    if "S1" in membership:
        sock_1.close()
    if "S2" in membership:
        sock_2.close()
    if "S3" in membership:
        sock_3.close()


# RM as client talk to server
# send status including primary information to server
def RM_status_update():
    global membership
    global status
    if "S1" in membership:
        sock_1 = RM_server1_connection()
        membership_message = 'status {}'.format(' '.join(status))
        sock_1.send(membership_message.encode())
        success_message = sock_1.recv(1024).decode()

    if "S2" in membership:
        sock_2 = RM_server2_connection()
        membership_message = 'status {}'.format(' '.join(status))
        sock_2.send(membership_message.encode())
        success_message = sock_2.recv(1024).decode()

    if "S3" in membership:
        sock_3 = RM_server3_connection()
        membership_message = 'status {}'.format(' '.join(status))
        sock_3.send(membership_message.encode())
        success_message = sock_3.recv(1024).decode()


    if "S1" in membership:
        sock_1.close()
    if "S2" in membership:
        sock_2.close()
    if "S3" in membership:
        sock_3.close()


# RM as a server talk to GFD
# Switch active/passive pattern according to isAlive.
def RM_GFD_connection(connection):
    current_time = datetime.datetime.now()
    request_message = connection.recv(1024).decode()
    print(request_message)
    print("[{}] Received: <RM, GFD, {}, request>".format(str(current_time), request_message))

    connection.send(request_message.encode())
    current_time = datetime.datetime.now()
    print("[{}] Sent: <RM, GFD, {}, reply>".format(str(current_time), request_message))

    # close the connection and print on server console
    print("Connection to GFD closed!\n")
    connection.close()
    
    new_list = request_message.split(' ')
    print(new_list[0])

    global membership
    global version
    global status

    old_status = status
    old_status[1] = 'alive' if status[1] == 'primary' or status[1] == 'alive' else 'died'
    old_status[2] = 'alive' if status[2] == 'primary' or status[2] == 'alive' else 'died'
    old_status[3] = 'alive' if status[3] == 'primary' or status[3] == 'alive' else 'died'

    print("************************")
    # need to change this method!
    if new_list != old_status:
        status = new_list
        version += 1
        get_membership_from_status()
        #print("Passive")
        RM_status_update()
    RM_checkpoint_connection()
    
    print(status)


    print("RM Membership Version {}: {}".format(version, len(membership)) + " Member:", end='')
    print(*membership, sep=',')
    print()


RM = init_as_server(RM_ip, RM_port)

while True:
    connection, address = RM.accept()
    start_new_thread(RM_GFD_connection, (connection,))

