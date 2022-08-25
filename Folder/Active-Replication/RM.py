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
status = ['died', 'died', 'died']
primary_index = -1

def get_membership_from_status():
    global status
    global membership
    global primary_index
    new_membership = []
    if status[0] == 'alive':
        new_membership.append('S1')
    if status[1] == 'alive':
        new_membership.append('S2')
    if status[2] == 'alive':
        new_membership.append('S3')
    membership = new_membership

    if primary_index == -1 or status[primary_index] == 'died':
        # select an alive server to be new primary
        for i in range(3):
            if status[i] == 'alive':
                status[i] = 'primary'
                primary_index = i
                print("New primary selected: S{}.".format(primary_index + 1))
                break

    # no server alive condition: new primary is not selected
    if primary_index == -1 or status[primary_index] == 'died':
        print("All servers are dead, no primary selected.")
    else:
        status[primary_index] = 'primary'






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
    sock_3.send(RM.encode())
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
    if primary_index == 0:
        sock_1 = RM_server1_connection()
        checkpoint_request = 'checkpoint'
        sock_1.send(checkpoint_request.encode())
        checkpoint_reply = sock_1.recv(1024).decode()
        checkpoint_state = 'state {}'.format(checkpoint_reply)
        if status[1] == 'alive':
            sock_2 = RM_server2_connection()
            sock_2.send(checkpoint_state.encode())
            success_message = sock_2.recv(1024).decode()
        if status[2] == 'alive':
            sock_3 = RM_server3_connection()
            sock_3.send(checkpoint_state.encode())
            success_message = sock_3.recv(1024).decode()

    # S2 is primary
    if primary_index == 1:
        sock_2 = RM_server2_connection()
        checkpoint_request = 'checkpoint'
        sock_2.send(checkpoint_request.encode())
        checkpoint_reply = sock_2.recv(1024).decode()
        checkpoint_state = 'state {}'.format(checkpoint_reply)
        if status[0] == 'alive':
            sock_1 = RM_server1_connection()
            sock_1.send(checkpoint_state.encode())
            success_message = sock_1.recv(1024).decode()
        if status[2] == 'alive':
            sock_3 = RM_server3_connection()
            sock_3.send(checkpoint_state.encode())
            success_message = sock_3.recv(1024).decode()

    # S3 is primary
    if primary_index == 2:
        sock_3 = RM_server3_connection()
        checkpoint_request = 'checkpoint'
        sock_3.send(checkpoint_request.encode())
        checkpoint_reply = sock_3.recv(1024).decode()
        checkpoint_state = 'state {}'.format(checkpoint_reply)
        if status[0] == 'alive':
            sock_1 = RM_server1_connection()
            sock_1.send(checkpoint_state.encode())
            success_message = sock_1.recv(1024).decode()
        if status[1] == 'alive':
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
def RM_status_update():
    global membership
    global status
    global relaunch
    global server_alive_before_reluanch
    global relaunched_server
  
    checkpoint_request = 'checkpoint'
    # if membership changes, ask the rest servers to quiescent
    if "S1" in membership:
        sock_1 = RM_server1_connection()
        membership_message = 'status {}'.format(' '.join(status))
        sock_1.send(membership_message.encode())
        success_message_1_2 = sock_1.recv(1024).decode()
        # if (1)relauch and (2) server is alive before reluanch --> send quiecent request and ask for checkpoint
        if ((relaunch == True) and ("S1" in server_alive_before_reluanch)):
            sock_1.send(checkpoint_request.encode())
            checkpoint_reply = sock_1.recv(1024).decode()
            checkpoint_state = 'state {}'.format(checkpoint_reply)

         
    if "S2" in membership:
        sock_2 = RM_server2_connection()
        membership_message = 'status {}'.format(' '.join(status))
        sock_2.send(membership_message.encode())
        success_message_2_2 = sock_1.recv(1024).decode()
         # if (1)relauch and (2) server is alive before reluanch --> send quiecent request and ask for checkpoint
        if ((relaunch == True) and ("S2" in server_alive_before_reluanch)):
            sock_2.send(checkpoint_request.encode())
            checkpoint_reply = sock_1.recv(1024).decode()
            checkpoint_state = 'state {}'.format(checkpoint_reply)
           
       
    if "S3" in membership:
        sock_3 = RM_server3_connection()
        membership_message = 'status {}'.format(' '.join(status))
        sock_3.send(membership_message.encode())
        success_message_3_2 = sock_3.recv(1024).decode()
         # if (1)relauch and (2) server is alive before reluanch --> send quiecent request and ask for checkpoint
        if ((relaunch == True) and ("S3" in server_alive_before_reluanch)):
            sock_3.send(checkpoint_request.encode())
            checkpoint_reply = sock_1.recv(1024).decode()
            checkpoint_state = 'state {}'.format(checkpoint_reply)

    # send checkpoints to the relaunched server
    if (relaunch == True) and (relaunched_server == "S1"):
        sock_1.send(checkpoint_state.encode())
        ready_message = sock_1.recv(1024).decode()
   
    elif (relaunch == True) and (relaunched_server == "S2"):
        sock_2.send(checkpoint_state.encode())
        ready_message = sock_2.recv(1024).decode()
     
    elif (relaunch == True) and (relaunched_server == "S3"):
        sock_3.send(checkpoint_state.encode())
        ready_message = sock_3.recv(1024).decode()
    
    # print ready message from the relaunched server on the RM's console
    print(ready_message)
    
        
    if "S1" in membership:
        sock_1.close()
    if "S2" in membership:
        sock_2.close()
    if "S3" in membership:
        sock_3.close()


# RM as a server talk to GFD
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

    global membership
    global version
    global status
    global membership_change
    global relaunch
    global relaunched_server
    global server_alive_before_reluanch
    # if membership changes(kill any of the server or relaunch any server)
    if new_list != status:
        #if relaunched
        if new_list.count("alive") > status.count("alive"):
            relaunch = True
            server_alive_before_reluanch = membership
        else:
            relauch = False
            
        status = new_list
        print(status)
        version += 1
        get_membership_from_status()
        # find the relaunched server
        for server in membership:
            if server not in server_alive_before_reluanch:
                relaunched_server = server
        # only membership changes call this function
        RM_server_connection()

    print("RM Membership Version {}: {}".format(version, len(membership)) + " Member:",end='')
    print(*membership,sep=',')
    print()


RM = init_as_server(RM_ip, RM_port)

while True:
    connection, address = RM.accept()
    start_new_thread(RM_GFD_connection, (connection,))

