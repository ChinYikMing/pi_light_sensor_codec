import time, sys, math
from grove.adc import ADC
import socket
import signal
import os
__all__ = ["GroveLightSensor"]

st = 1#sleep time

HOST = 'localhost'
PORT = 8081


class GroveLightSensor(object):
    '''
    Grove Light Sensor class

    Args:
        pin(int): number of analog pin/channel the sensor connected.
    '''
    def __init__(self, channel):
        self.channel = channel
        self.adc = ADC()

    @property
    def light(self):
        '''
        Get the light strength value, maximum value is 100.0%

        Returns:
            (int): ratio, 0(0.0%) - 1000(100.0%)
        '''
        value = self.adc.read(self.channel)
        return value
    
    

Grove = GroveLightSensor


def detect_one_byte(sensor):
    byte_msg = ""
    #print('Detecting light...')
    for _ in range(0,8) :
        
        if sensor.light >= 50:
            byte_msg += '1'
        else :
            byte_msg += '0'
        
        print('Light value: {0}'.format(sensor.light))
        time.sleep(st)
    
    return byte_decode(byte_msg)
        
        
        
    


def byte_decode(byte_msg):
    
    #ord(A) == 65
    #chr(65) == 'A'
    # add bin format to string ex : 0b01000001 
    byte_msg = '0b' + byte_msg 
    c = int(byte_msg,2) # change string for binary  to int decimal
    return chr(c)
    
    
    
    

def detect_preamable(sensor):
    
    byte_msg = ""
    #print('Detecting light...')
    for _ in range(0,16) :
        
        if sensor.light >= 50:
            byte_msg += '1'
        else :
            byte_msg += '0'
        
        
        print('Light value: {0}'.format(sensor.light))
        time.sleep(st)
    
    
    if(byte_msg == '1010101010101010'):
        return True
    else:
        return False
    




def main():
    from grove.helper import SlotHelper
    
    # setup socket
    sock = socket.socket()
    try:
        sock.connect((HOST, PORT))
        print("Connected to socket server!")
    except:
        print("Connection failed.")
        return 0
    sock.setblocking(0)
    
    sh = SlotHelper(SlotHelper.ADC)
    pin = sh.argv2pin()
    
    retransmission = False
    with open('./gpio_pid.txt', 'r') as file:
        gpio_pid = int(file.read())
        
    while True:
        num =''
        msg = ''
        sensor = GroveLightSensor(pin)
        while sensor.light < 100:
            continue
        
        print('Ready')
        
        while not detect_preamable(sensor):
            
            os.kill(gpio_pid, signal.SIGUSR1)
            print('Not preamable. Send signal to sender!!!!!!')
            continue
            if not retransmission:
                print("retransmit")
                sock.send('ARQ'.encode())
                retransmission = True
        
        
        for _ in range(0,2):
            b =detect_one_byte(sensor)
            print(b)
            num += (b)
            
        for _ in range(0,int(num)):
            msg += (detect_one_byte(sensor))
        
        print('Your msg is: ' + msg)
        sock.send('ACK'.encode())
        

if __name__ == '__main__':
    main()
