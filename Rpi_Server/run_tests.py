"""Script for Testing Functionality"""
import subprocess
"""
def check_server():
    address = "http://192.168.1.35"
    res = subprocess.call(['ping', address])
    if res == 0:
        print(f"ping to {address} OK")
    elif res == 2:
        print (f"no response from {address}")
    else:
        print (f"ping to {address} failed!")

check_server()"""
import os
import socket
import sys

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)  # Create a TCP/IP socket
address = "192.168.1.35"
rep = os.system('ping' + 'address')

if rep == 0:
    print (f"Server: {address} is up")
else:
    print (f"Server: {address} is down")
