############################################################################################
#
# Icom Rig IO - Rev 1.0
# Copyright (C) 2021 by Joseph B. Attili, aa2il AT arrl DOT net
#
# Functions to support communicating with Icom 706 & 9700 rigs
#
# Some notes on the 706:
#   - Press LOCK while powering on to set the following CI-V menu items:
#        25 CI-V Address = 0x4E  - This is the default for the 706 MKII
#        26 CI-V Baud    = 19200
#        27 CI-V TRN     = Off   - When on. the rig sends out packets when something changes (e.g. freq).
#                                  My software is not (yet?) robust enough to handle this so disable it.
#        28 CI-V 731     = ?     - ??? - Probably should be off
#   - Steve's radio only has the FL-223 optional filter installed which has BW = 1.9 KHz - very tough for CW!
#
############################################################################################
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
# Notes:
# To test hamlib:
#   echo f | nc -w 1 localhost 4532
#
############################################################################################

import sys
import numpy as np

############################################################################################

# Function to convert a list of BCD hex values to an integer
def bcd2int(x,ireverse=0):

    mult= 1
    val = 0
    if ireverse:
        #x.reverse()
        x=x[::-1];
    for xx in x:
        xxx = xx.replace('0x','')
        val  += mult*int(xxx)
        mult *= 100

    return val


# Function to convert an integer to a list of BCD hex values
def int2bcd(x,n,ireverse=0):

    y=str(int(x)).zfill(2*n)
    if ireverse==0:
        #y.reverse()
        y=y[::-1];
    bcd=[]
    for i in range(n):
        i2 = 2*i
        yy = y[i2:(i2+2)]
        bcd.append(int(yy,16))

    return bcd


# Function to return hex values of a list of bytes
def show_hex(x):
    #print('SHOW_HEX: x=',x,type(x))
    if isinstance(x, str):
        return [hex(ord(c)) for c in x]
    else:
        return [hex(c) for c in x]            


############################################################################################
    
# Object for usb communications with ICOM rigs
class icom_civ:
    def __init__(self,rig_type2):

        self.rig_type2=rig_type2
        if rig_type2=='IC9700':
            ICOM_RIG_ID    = 0xA2
        else:
            ICOM_RIG_ID    = 0x4E
            
        self.ICOM_PREAMBLE1 = [0xFE, 0xFE, ICOM_RIG_ID, 0xE0]         # Computer to rig
        self.ICOM_PREAMBLE2 = [0xFE, 0xFE, 0xE0, ICOM_RIG_ID]         # Rig to computer
        self.ICOM_EOM       = [0xFD]
        self.ICOM_OK        = self.ICOM_PREAMBLE2 + [0xFB] + self.ICOM_EOM
        self.ICOM_NG        = self.ICOM_PREAMBLE2 + [0xFA] + self.ICOM_EOM

    # Function to form entire command from computer to rig
    def icom_form_command(self,cmd):
        if np.isscalar(cmd):
            cmd = [cmd]
        #print cmd
        return self.ICOM_PREAMBLE1 + cmd + self.ICOM_EOM

    # Function to strip out the important part of the rig's response to a command
    def icom_response(self,cmd,x):
        x=list(x)                      # Python 3
        if False:
            print('ICOM_RESPONSE: x=',x,x[-2]==0xfa )

        # Check for an unsupported command or NO GOOD response from rig
        if False and x[-2]==0xfa :
            print('ICOM_RESPONSE: Command not supported by this rig')
            print('\tcmd      =',show_hex(cmd))
            print('\tresponse =',show_hex(x))
            return 'NG'

        # Commands on the 706 are echoed so make sure we got the echo
        if self.rig_type2=='IC706':
            N=len(cmd)
            cmd2 = ''.join(chr(i) for i in cmd)
            echo = x[:N]
            valid = echo==cmd2
            if not valid:
                print('Echo is ok:\t',valid)
        else:
            valid = True
            N=0

        # Check for OK and NG messages from rig
        #resp = [ord(c) for c in x[N:]]             #Python2
        resp = x[N:]
        N2 = N+len(self.ICOM_PREAMBLE2)
        if resp==self.ICOM_NG:
            print('ICOM_RESPONSE: Command NO GOOD')
            print('\tcmd      =',show_hex(cmd))
            print('\tresponse =',show_hex(x))
            print('\tresp     =',show_hex(resp))
            return 'NG'

        elif resp==self.ICOM_OK:
            #print 'ICOM_RESPONSE: OK message received from rig',valid
            return 'OK'

        else:
            # Check also that the correct preamble and EOM were obtained
            #preamble = [ord(c) for c in x[N:N2] ]       #Python2
            preamble = x[N:N2]
            eom = [cmd[-1]]
            valid = valid and (preamble==self.ICOM_PREAMBLE2) and (eom==self.ICOM_EOM)
            if not valid:
                print('Preamble and EOM ok:\t',valid,(preamble==self.ICOM_PREAMBLE2),(eom==self.ICOM_EOM))
                print('preamble  =',preamble)
                print('preamble2 =', self.ICOM_PREAMBLE2)
            
            # Check that this is the reponse to the proper command
            #print('cmd4=',cmd[4])
            #print('xN2 =',x[N2])
            #valid = valid and cmd[4]==ord(x[N2])       # Python2
            valid = valid and cmd[4]==x[N2]
            if not valid:
                print('Proper command:\t',valid)

        # Extract the response
        if valid:
            N2+=1
            #response = [hex(ord(c)) for c in x[N2:-1] ]      # Python2
            response = [hex(c) for c in x[N2:-1] ]
        else:
            print('ICOM_RESPONSE: Invalid message')
            print('\tcmd      =',show_hex(cmd))
            print('\tresponse =',show_hex(x))
            response=''

        #print 'response=',response
        return response


    
