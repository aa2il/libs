############################################################################
#
# resources.py - Rev 1.0
# Copyright (C) 2021-4 by Joseph B. Attili, aa2il AT arrl DOT net
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
def find_resource_file(f):

    PATH=os.path.realpath(sys.executable)
    #print('FIND_FILE: PATH=',PATH)
    if '/usr/bin/python' in PATH or 'python.exe' in PATH:
        # Python script on linux or Windoz
        #print('FIND_FILE: _file_=',__file__)
        dname = os.path.dirname(__file__)
    elif platform.system()=='Linux':
        dname = os.path.dirname(PATH)
    elif platform.system()=='Windows':
        dname = os.path.dirname(PATH)
    else:
        print("FIND RESOURCE FILE: I don't know what I'm doing here!")
        return None

    #print('FIND_FILE: argv=',sys.argv)
    #print('FIND_FILE: dname=',dname)
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
def list_all_serial_devices():
    ports = lp.comports()
    print('LIST ALL SERIAL DEVICES: ports=',ports,'\n')
    
    for port in ports:
        print('\n',port,':')
        pprint(vars(port))
        print("\nport={}: desc={} hwid=[{}]".format(port.device, port.description, port.hwid))

# Function to find a particular serial device        
def find_serial_device(device_name,device_number,VERBOSITY=0):

    try:
        VID_PID=DEVICE_IDs[device_name]
        if VERBOSITY>0:
            print('\nFIND SERIAL DEVICE: Looking for device name=',device_name,
                  '\tvid_pid=',VID_PID)
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
        return None
        
    ports = lp.grep(VID_PID)
    nports=0
    device=None
    best=None
    for port in ports:
        nports+=1
        loc=int(port.location[-1])
        if best==None or (device_number==0 and loc<best)  or (device_number==1 and loc>best):
            device=port.device
            best=loc            
        if VERBOSITY>0:
            print('port=')
            pprint(vars(port))
            print('\nFIND SERIAL DEVICE: vid_pid=',VID_PID,'\tdevice=',device)

    if VERBOSITY>0:
        if nports==0:
            print('FIND SERIAL DEVICE: Unable to locate serial device',VID_PID)
        elif nports>1:
            print('FIND SERIAL DEVICE: Multiple devices found!',VID_PID,nports)
            print('\tReturning device with location ending in',best)
            print(device)

    return device

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


