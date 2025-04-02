############################################################################
#
# resources.py - Rev 1.0
# Copyright (C) 2021-5 by Joseph B. Attili, joe DOT aa2il AT gmail DOT com
#
# Routine to locate various resources.
#
############################################################################
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
############################################################################

import sys
import os
import numpy as np
import time

from subprocess import check_output, CalledProcessError
import platform
import socket

import serial.tools.list_ports as lp
from pprint import pprint
import platform

############################################################################

VERBOSITY=0

#DEVICE_IDs={'nanoIO'   : '1A86' ,
#DEVICE_IDs={'nanoIO'   : 'USB2.0-Ser' ,
DEVICE_IDs={'nanoIO'   : '1A86:7523' ,
            'nanoIO32' : '10C4:EA60' ,
            'FTdx3000' : 'SER=AH046H3M120067',
            'FT991a'   : 'SER=00A50791',
            'IC9700'   : '10C4:EA60'}

#            'IC9700'   : 'SER=IC-9700 12007709 A',
#            'IC9700B'   : 'SER=IC-9700 12007709 B'}

#            'FTdx3000' : '10C4:EA70'}
#            'FT991a'   : '10C4:EA70'}
#            'IC9700'   : '10C4:EA60'}

############################################################################

# Function to locate a file
def find_resource_file(f,VERBOSITY=1):

    PATH=os.path.realpath(sys.executable)
    if VERBOSITY>0:
        print('FIND_RESOURCE_FILE: PATH=',PATH)
        
    if '/usr/bin/python' in PATH or 'python.exe' in PATH:
        # Python script on linux or Windoz
        if VERBOSITY>0:
            print('FIND_RESOURCE_FILE: _file_=',__file__)
        dname = os.path.dirname(__file__)
    elif platform.system()=='Linux':
        dname = os.path.dirname(PATH)
    elif platform.system()=='Windows':
        dname = os.path.dirname(PATH)
    else:
        print("FIND RESOURCE FILE: I don't know what I'm doing here!")
        return None

    if VERBOSITY>0:
        #print('FIND_FILE: argv=',sys.argv)
        print('FIND_RESOURCE_FILE: dname=',dname)
    fname = dname+'/'+f
    #print('FIND_FILE: fname=',fname)
    if not os.path.isfile(fname):
        fname = os.path.expanduser('~/Python/data/'+f)
    #print('FIND_FILE: fname=',fname)
    if not os.path.isfile(fname):
        fname=f
    #print('FIND_FILE: fname=',fname)

    return fname

############################################################################

# Function to list all of the serial devices
def list_all_serial_devices(USB_ONLY=False):
    ports = lp.comports()
    print('LIST ALL SERIAL DEVICES: USB_ONLY=',USB_ONLY)   #  ports=',ports,'\n')
    
    for port in ports:
        if not USB_ONLY or ('USB' in str(port)):
            print('\nport=',port,':')
            pprint(vars(port))
            #print("\nport={}: desc={} hwid=[{}]".format(port.device, port.description, port.hwid))

    return ports

# Function to find a particular serial device via vender id and product id
def find_serial_device(device_name,device_number,PORT=None,VERBOSITY=0):

    if VERBOSITY>0:
        print('\nFIND SERIAL DEVICE: Looking for device name=',device_name,
              '\tdevice number=',device_number,'...')

    if PORT!=None:
        print('\nFIND SERIAL DEVICE: Looking for port',PORT)
        desc=PORT
    elif device_name=='':
        print('\nFIND SERIAL DEVICE: Fatal Error - Bad device name=',device_name)
        return None,None
        #sys.exit(0)
    elif device_name in DEVICE_IDs.keys():
        desc=DEVICE_IDs[device_name]
    else:
        desc=device_name
    if VERBOSITY>0:
        print('\tdescriptor=',desc)
    ports = lp.grep(desc)            # name, description and hwid are searched
    if VERBOSITY>0:
        print('ports=',ports)
    
    """
    except Exception as e: 
        if VERBOSITY>0:
            print('\nFIND SERIAL DEVICE: *** ERROR *** No such device -',device_name)
            print(e)
            ports = lp.comports()
            print('ports=',ports,'\n')

            for port in ports:
                pprint(vars(port))
                #print("port={}: desc={} hwid=[{}]".format(port.device, port.description, port.hwid))
            sys.exit(0)
        return None,None
    """
    
    nports=0
    device=None
    vid_pid=None
    best=None
    for port in ports:
        nports+=1
        if VERBOSITY>0:
            print(nports,'\tport=',port)

        try:
            loc=int(port.location[-1])         # @@@@@@@
        except:
            print("\tCan't locate port",port,"- skipping ...")
            continue
            
        if best==None or (device_number==0 and loc<best)  or (device_number==1 and loc>best):
            device=port.device
            best=loc
            hwid=port.hwid
            idx=hwid.find('VID:PID=')
            vid_pid=hwid[(idx+8):(idx+17)]
        if VERBOSITY>0:
            print('port=')
            pprint(vars(port))
            print('\nFIND SERIAL DEVICE: hwid=',hwid,'\tvid_pid=',vid_pid,len(vid_pid),'\tdevice=',device,'\tloc=',loc)

    if VERBOSITY>0:
        if nports==0:
            print('\nFIND SERIAL DEVICE: Unable to locate serial device',desc)
            print('\nMake sure MY_KEYER_DEVICE_ID is set in ~/.keyerrc')
            cmd='python3 -m serial.tools.list_ports -v'
            print('\nTo find a valid descriptor, use\n\n\t',cmd,'\n')
            os.system(cmd)
            print('\nFIND SERIAL DEVICE: Unable to locate serial device',desc)
            print('*** Giving up ***')
            sys.exit(0)
        elif nports>1:
            print('FIND SERIAL DEVICE: Multiple devices found!',desc,nports)
            print('\tReturning device with location ending in',best)
            print(device)

    return device,vid_pid


# Function to find a particular serial device via /dev/serial/by-id 
def find_serial_device_by_serial_id(device_id,device_number,VERBOSITY=0):

    if VERBOSITY>0:
        print('\nFIND SERIAL DEVICE BY SERIAL ID: Looking for device id=',device_id,'...')
              
    DEV_PATH='/dev/serial/by-id'
    try:
        files = os.listdir(DEV_PATH)
    except:
        files=[]

    print('\nUSB ports found:')
    device=None
    VID_PID=None
    for f in files:
        print(f)
        port=os.path.realpath(DEV_PATH+'/'+f)
        print(port)

        if device_id in f and "-if0"+str(device_number) in f:
            print('... There it is on port',port,' ...\n')
            device=port

    return device,VID_PID
        
################################################################################

# Function to display hostname and IP address
def get_Host_Name_IP():
    try:
        host_name = socket.gethostname()+'.local'
        host_ip = socket.gethostbyname(host_name)
        #print("\nHostname :  ", host_name)
        #print("IP : ", host_ip)
    except:
        host_name = None
        host_ip = None
        print("Unable to get Hostname and IP")

    return host_name,host_ip

# Test ability to ping a host
# Note - On windoz, use -n instead of -c 
def ping_test(host):
    response = os.system("ping -c 1 " + host)
    return response == 0

def check_internet():

    print('\nChecking internet connection ...')
    host_name,host_ip=get_Host_Name_IP()
    print("\tHostname :  ",host_name)
    print("\tIP : ",host_ip,'\n')
    if host_ip=='127.0.0.1':
        INTERNET=False
        print('No internet connection :-(')
        #sys.exit(0)
    else:
        print('\tLocal Internet connection appears to be alive ...')
        
        # Next try pinging something outside LAN
        INTERNET=ping_test('8.8.8.8')
        if INTERNET:
            print('\n... Outside Internet Connection appears to be alive also!  :-)')
        else:
            print('\n... No internet connection :-(')
            #sys.exit(0)

    return INTERNET,host_name,host_ip

############################################################################

# Routine to get PID of a process by name
def get_PIDs(name):
    if platform.system()=='Linux':
        try:
            cmd=['pidof','-x',name]
            pidlist = list(map(int, check_output(cmd).split()))
        except CalledProcessError:
            pidlist = []
    elif platform.system()=='Windows':
        #name='chrome'
        name=name+'.exe'
        #print('GET_PIDs: Windoz')
        cmd='tasklist /fi "imagename eq '+name
        #print('GET_PIDs: cmd=',cmd)
        result = check_output(cmd).decode()
        #print('GET_PIDs: result=',result)
        result2=result.strip().split('\r\n')
        #print('GET_PIDs: result2=',result2)
        #print(len(result2))
        pidlist = []
        for line in result2:
            if name in line:
                #print(line)
                a=line.split()
                #print(a)
                pidlist.append(int(a[1]))
        #sys.exit(0)
    else:
        print('GET_PIDs: Unknown OS',platform.system())
        sys.exit(0)

    #print('GET_PISD: List of PIDs = ',pidlist)
    #sys.exit(0)
    return pidlist

"""
 In windoz, use wmic:
 C:\>wmic process where "name='chrome.exe'" get ProcessID, ExecutablePath

 In Linux, can also use    pgrep flrig

def process_exists(process_name):
    call="TASKLIST", '/FI', 'imagename eq %s' % process_name
    # use buildin check_output right away
    output = subprocess.check_output(call).decode()
    # check in last line for process name
    last_line = output.strip().split('\r\n')[-1]
    # because Fail message could be translated
    return last_line.lower().startswith(process_name.lower())

>>> import platform
>>> platform.system()
'Linux'
'Windows' or
'Darwin'   (Mac)

"""


