from _thread import *
from os import sep
import socket
from sys import _clear_type_cache
import time
import datetime
import json

with open('ip.json') as f:
    ip = json.load(f)

with open('port.json') as fp:
    port = json.load(fp)

GFD_ip = ip['GFD']
GFD_port = port['GFD']

LFD1_ip = ip['S1']
LFD2_ip = ip['S2']
LFD3_ip = ip['S3']
LFD1_port = port['LFD1']
LFD2_port = port['LFD2']
LFD3_port = port['LFD3']

RM_ip = ip['RM']
RM_port = port['RM']

version = 1
membership = []
membership_changed = False
status = ['died', 'died', 'died']

def update_status_from_membership():
    global status
    global membership
    status[0] = 'alive' if 'S1' in membership else 'died'
    status[1] = 'alive' if 'S2' in membership else 'died'
    status[2] = 'alive' if 'S3' in membership else 'died'


def init_server():
    # Create a TCP/IP socket
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    # Bind the socket to the port
    server_address = (GFD_ip, GFD_port)
    print("Starting up on {} port {}".format(server_address[0], server_address[1]))
    server.bind(server_address)

    # Listen for incoming connections
    server.listen(5)
    print("Waiting for connection!")
    return server

def init_socket():
    # Create a TCP/IP socket
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    return server

# GFD as server talks to clients
def GFD_client_connection(connection):
    while True:
        # receive and print message from GFD
        current_time = datetime.datetime.now()
        request_message = connection.recv(1024).decode()
        print("[{}] Received <C, GFD, {}, request>".format(str(current_time), request_message))

        # disconnect to GFD using 'exit'
        #if request_message == "exit":
        #    break

        #if request_message == 'membership':
        # send and print receipt message to GFD
        current_time = datetime.datetime.now()
        reply_message = str(membership)
        connection.send(reply_message.encode())
        print("[{}] Sending: <GFD, C, {}, reply>".format(str(current_time), request_message))

    # close the connection and print on server console
    print("Connection to GFD closed!\n")
    connection.close()

def request_to_RM(RM_conn):
    try:
        global status

        RM_conn.connect((RM_ip, RM_port))
        current_time = datetime.datetime.now()
        
        request_message = ' '.join(status)
        print("here" + request_message)
        RM_conn.send(request_message.encode())
        print("[{}] Sent: <GFD, RM, {}, request>".format(str(current_time), request_message))
        
        current_time = datetime.datetime.now()
        response = RM_conn.recv(1024).decode()
        print("[{}] Received: <GFD, RM, {}, request>".format(str(current_time), response))
        
        RM_conn.close()

    except:
        print("Connection between GFD and RM fails")
    


def receive_from_LFD(LFD_conn, LFD_ip, LFD_port, LFD_num, RM_conn):
    server_name = "S{}".format(LFD_num)
    LFD_name = "LFD{}".format(LFD_num)
    try: 
        LFD_conn.connect((LFD_ip, LFD_port))

        # receive status of replica
        state_message = LFD_conn.recv(1024).decode()
        global membership
        global membership_changed
        #global status
        #status[int(RM_conn)-1] = state_message 
        #print("line 110")
        if (state_message == 'alive') and (server_name not in membership):
            membership.append(server_name)
            membership_changed = True
        elif (state_message == 'died') and (server_name in membership):
            membership.remove(server_name)
            membership_changed = True
        else:
            membership_changed = False

        # Send heartbeat message to server
        heartbeat_message = ("Are you alive?")
        LFD_conn.send(heartbeat_message.encode())

        # Print heartbeat message to LFD console
        current_time = datetime.datetime.now()
        print("[{}] Sent: <GFD, {}, {}, request>".format(str(current_time), LFD_name, heartbeat_message))

        # Get reply from server
        reply_message = LFD_conn.recv(1024).decode()

        # Print reply message to LFD console
        current_time = datetime.datetime.now()
        print("[{}] Received: <GFD, {}, {}, reply>".format(str(current_time), LFD_name, reply_message))

        # prevent error
        time.sleep(1)

        # close connection to LFD1
        LFD_conn.close()
    except:
        print("Not Start {} yet or {} dies".format(LFD_name, LFD_name))


# GFD as client talks to LFDs
def GFD_LFD_connection():
    # Run socket
    while True:
        # Initialize a socket
        server1 = init_socket()
        server2 = init_socket()
        server3 = init_socket()
        RM_conn = init_socket()

        receive_from_LFD(server1, LFD1_ip, LFD1_port, 1, RM_conn)
        receive_from_LFD(server2, LFD2_ip, LFD2_port, 2, RM_conn)
        receive_from_LFD(server3, LFD3_ip, LFD3_port, 3, RM_conn)

        global membership
        global membership_changed
        global version
        if membership_changed:
            version += 1
        
        update_status_from_membership()
        request_to_RM(RM_conn)

        # print membership info
        print("GFD Membership Version {}: {}".format(version, len(membership)) + " Member:",end='')
        print(*membership,sep=',')
        print()
        # set heart beaat frequency
        time.sleep(10)


# Main method
server = init_server()

start_new_thread(GFD_LFD_connection, ())

# Run multithreaded socket
while True:
    connection, address = server.accept()
    start_new_thread(GFD_client_connection, (connection,))
