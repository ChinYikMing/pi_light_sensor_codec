import RPi.GPIO as GPIO
import time
import socket
import threading
import errno
from time import sleep
import sys
import signal
import os

HOST = 'localhost'
PORT = 8081


st = 1 # sleep time

retransmission = False
msg = ''

def preamable(pin):
    for _ in range(0,8):
        blink(pin)  # blink 0.5s
        time.sleep(st) #dim 0.5s
    return

def all_one(pin):
    for _ in range(0,8):
        blink(pin)
    return

def decode(msg):
    
    msg_list =  []
    for c in msg:
        a = bin(ord(c)) # change c to ASCII int ord and bin format str
        a =  a.replace('0b','')
        
        while len(a) < 8: # append to 8-bits format
            a = '0' + a
        print(a)
        msg_list.append(a)
    
    
    return msg_list


# blink_msg in byte format
def blink_msg(msg_list,pin):
    
    for msg in msg_list:
        for i in msg :
            if i == '0':
                time.sleep(st)
            else :
                blink(pin)
    return


# blinking one bit signal function
def blink(pin):
    GPIO.output(pin,GPIO.HIGH)
    time.sleep(st) #light 0.1 sec
    GPIO.output(pin,GPIO.LOW)
    #time.sleep(0.01)
    # dim 0.01 sec
    return

def user_feedback():
    try:
        recv = client.recv(1024).decode() # received message 
    except socket.error as e:
        err = e.args[0]
        if err == errno.EAGAIN or err == errno.EWOULDBLOCK:
            sleep(1)
            print('No data available')
            sys.exit(1)
        else:
            # a "real" error occurred
            print(e)
            sys.exit(1)
    # got a message, do something :)
    if recv == 'ACK':
        retransmission = False
    elif recv == 'ARQ':
        retransmission = True
    print("Received from client: ", recv)
    input_msg()

def transmission():
    global msg
    init_GPIO()
    preamable(22)
    print("msg: ", msg)
    if len(bytearray(msg.encode(encoding='utf-8'))) < 10:
        blink_msg(decode( '0' + str(len(bytearray(msg.encode(encoding='utf-8'))))),22)
    else :
        blink_msg(decode(str(len(bytearray(msg.encode(encoding='utf-8'))))),22)

    bytes_arr = bytearray(msg.encode(encoding='utf-8'))
    blink_msg([bin(v)[2:].zfill(8) for v in bytes_arr],22)

    GPIO.cleanup()
    user_feedback()

def input_msg():
    global msg
    msg = input("Type the message: ")
    transmission()

def init_GPIO():
    # setup GPIO
    GPIO.setwarnings(False)
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(22, GPIO.OUT)
    GPIO.output(22, GPIO.LOW)

def signal_handler(sig, _):
    if sig == signal.SIGUSR1:
        print("Received from client: ARQ")
        transmission()

signal.signal(signal.SIGUSR1, signal_handler)

# setup socket
s = socket.socket()
s.bind((HOST, PORT))
s.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR, 1)
s.listen(1)
print("Start listening in {}:{} ...".format(HOST, PORT))

client, addr = s.accept()
client.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR, 1)
print("Client address: ", addr)

def main():
    global msg
    my_pid = os.getpid()
    with open('./gpio_pid.txt', 'w') as file:
        file.write(str(my_pid))
    file.close()
        
    while True:
        input_msg()
        # input_msg()
        # if retransmission:
        #     print("Retransmit msg \"{}\"".format(msg))
        # else:
        
        # transmission()
        
        
            
    
    
if __name__ == '__main__':
    main()
    
