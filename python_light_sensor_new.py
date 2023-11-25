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

# detect unicode
one_byte_mask   = 0b00000000
two_byte_mask   = 0b11000000
three_byte_mask = 0b11100000
four_byte_mask  = 0b11110000

def used_four_byte(bin_byte):
    return (bin_byte & four_byte_mask) == four_byte_mask

def used_three_byte(bin_byte):
    return (bin_byte & three_byte_mask) == three_byte_mask

def used_two_byte(bin_byte):
    return (bin_byte & two_byte_mask) == two_byte_mask

def used_one_byte(bin_byte):
    return (bin_byte & one_byte_mask) == one_byte_mask

def detect_bytes_n(sensor, n):
    byte_arr = []
    for _ in range(0, n):
        one_byte = detect_one_byte(sensor)
        if one_byte == 'err':
            return 'err'
        byte_arr.append(int(format(int(one_byte, 2), '08b'), 2))
    return byte_arr

def detect_bytes(sensor):
    byte_msg = ""
    byte_arr = []
    #print('Detecting light...')
    one_byte_str = detect_one_byte(sensor)
    if one_byte_str == 'err':
        return 'err'
    one_byte = int(format(int(one_byte_str, 2), '08b'), 2)
    byte_arr.append(one_byte)

    ret = ''
    if used_four_byte(one_byte):
        ret = detect_bytes_n(sensor, 3)
        if one_byte_str == 'err':
            return 'err'
        byte_arr.extend(ret)
    elif used_three_byte(one_byte):
        ret = detect_bytes_n(sensor, 2)
        if one_byte_str == 'err':
            return 'err'
        byte_arr.extend(ret)
    elif used_two_byte(one_byte):
        ret = detect_bytes_n(sensor, 1)
        if one_byte_str == 'err':
            return 'err'
        byte_arr.extend(ret)
    elif used_one_byte(one_byte):
        pass

    # ascii
    if len(byte_arr) == 1 :
        return byte_decode(one_byte_str)
        # return ''.join(chr(b) for b in byte_arr)
    # unicode
    return bytearray(byte_arr).decode(encoding = 'utf-8')


def detect_one_byte(sensor):
    byte_msg = ""
    #print('Detecting light...')
    for _ in range(0,8) :

        if sensor.light >= 295:
            return 'err'
        elif sensor.light >= 50:
            byte_msg += '1'
        else :
            byte_msg += '0'

        print('Light value: {0}'.format(sensor.light))
        time.sleep(st)

    return byte_msg
    # return byte_decode(byte_msg)



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
    


sock = None
retransmission = False
gpio_pid = None
num =''
msg = ''
sensor = None

def decode_reliable():
    global sock
    global retransmission
    global num
    global msg
    global sensor

    num = ''
    msg = ''
    ret = ''
    retransmission = False

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
        ret = detect_one_byte(sensor)
        if ret == 'err':
            print("interference detected, ARQ!")
            sock.send('ARQ'.encode())
            retransmission = True
            break
        num += (byte_decode(ret))

    if ret != 'err':
        for _ in range(0,int(num)):
            ret = detect_bytes(sensor)
            if ret == 'err':
                print("interference detected, ARQ!")
                sock.send('ARQ'.encode())
                retransmission = True
                break
            msg += (ret)
    
    if ret != 'err':
        print('Your msg is: ' + msg)
        sock.send('ACK'.encode())

def main():
    from grove.helper import SlotHelper

    global sock
    global retransmission
    global gpio_pid
    global num
    global msg
    global sensor
    
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
        sensor = GroveLightSensor(pin)
        decode_reliable()
        

if __name__ == '__main__':
    main()
