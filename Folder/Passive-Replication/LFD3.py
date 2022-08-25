import socket
from sys import _clear_type_cache
import time
import datetime
from _thread import *
import json

with open('ip.json') as f:
    ip = json.load(f)

with open('port.json') as fp:
    port = json.load(fp)

LFD_name = 'LFD3'
server_name = 'S3'
LFD_ip = ip[server_name]
LFD_port = port[LFD_name]
server_ip = ip[server_name]
server_port = port[server_name]

server_alive = False

# Initialize hearbeat frequency to be every 10 second
hearbeat_freq = 10
user_input = input("The default heartbeat frequency is set to be every 10 second. Do you want to change the heartbeat frequency? (y/n):")

# User manually change hearbeat frequency
if (user_input == "y"):
    hearbeat_freq = int(input("Enter the heartbeat frequency in second: "))
    print("Set heartbeat frequency to be every {} second.".format(hearbeat_freq))
# Use default hearbeat frequency
else:
    print("Use default heartbeat frequency: every 10 second.")

def init_server(LFD_ip, LFD_port):
    # Create a TCP/IP socket
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    # Bind the socket to the port
    server_address = (LFD_ip, LFD_port)
    print("Starting up on {} port {}".format(server_address[0], server_address[1]))
    server.bind(server_address)

    # Listen for incoming connections
    server.listen(5)
    print("Waiting for connection!")
    return server

# LFD as a server talks to GFD
def LFD_GFD_connection(LFD_name, connection):

    global server_alive
    if server_alive:
        state_message = ('alive')
    else:
        state_message = ('died')
    connection.send(state_message.encode())

    # receive and print message from GFD
    current_time = datetime.datetime.now()
    request_message = connection.recv(1024).decode()
    print("[{}] Received <GFD, {}, {}, request>".format(str(current_time), LFD_name, request_message))

    # send and print receipt message to GFD
    current_time = datetime.datetime.now()
    connection.send(request_message.encode())
    print("[{}] Sending: <GFD, {}, {}, reply>".format(str(current_time), LFD_name, request_message))

    # close the connection and print on server console
    print("Connection to GFD closed!\n")
    connection.close()

def LFD_server_connection(server_ip, server_port, LFD_name):
    while True:
        try:
            # Create a TCP/IP socket
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

            # Connect the socket to the port where the server is listening
            server_address = (server_ip, server_port)
            sock.connect(server_address)

            # send the LFD name to server
            sock.send(LFD_name.encode())

            # receive the successful connection message from server
            success_message = sock.recv(1024).decode()
            print(success_message)

            # Send heartbeat message to server
            heartbeat_message = ("Are you alive?")
            sock.send(heartbeat_message.encode())

            # Print heartbeat message to LFD console
            current_time = datetime.datetime.now()
            print("[{}] Sent: <LFD, S, {}, request>".format(str(current_time), heartbeat_message))

            # Get reply from server
            reply_message = sock.recv(1024).decode()

            global server_alive
            server_alive = True
            
            # Print reply message to LFD console
            current_time = datetime.datetime.now()
            print("[{}] Received: <LFD, S, {}, reply>".format(str(current_time), reply_message))
            
            # prevent error
            time.sleep(1) 

            # send disconnection message to server
            exit_message = ("exit")
            sock.send(exit_message.encode())
            print("Disconnect from S!\n")

            # close LFD
            sock.close()

            # set heart beaat frequency
            time.sleep(hearbeat_freq-1)

        except:
            #Fault detected
            print("Heart beat fail! Error detected from Server S!\n")
            server_alive = False
            # delete_server = True
            time.sleep(hearbeat_freq-1)


# Main method
server = init_server(LFD_ip, LFD_port)
start_new_thread(LFD_server_connection, (server_ip, server_port, LFD_name))

# Run multithreaded socket
while True:
    connection, address = server.accept()
    start_new_thread(LFD_GFD_connection, (LFD_name, connection))
