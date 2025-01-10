#######################################################################################
#
# Direct Rig IO - Rev 1.0
# Copyright (C) 2021-5 by Joseph B. Attili, aa2il AT arrl DOT net
#
# Socket I/O routines related to commanding the radio via a
# direct USB connection.
#
# If there are problems with serial module:
# First uninstall serial with
#         sudo pip uninstall serial
# Then, if import serial does not work anymore: use
#         sudo pip install pyserial
# to install the correct serial module.
#
#######################################################################################
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
#######################################################################################

import traceback
import sys
from .ft_tables import *
import socket
import time
import threading
import serial
from .icom_io import *
from datetime import timedelta,datetime
from pytz import timezone
from utilities import find_serial_device,error_trap,show_ascii

#######################################################################################

VERBOSITY=0

#######################################################################################

# Routine to strip off any leading garbage (e.g. ?;)
def strip_garbage(buf,cmd):
    #print(cmd)
    #if cmd[-1]==';':
    #    cmd=cmd[:-1]
    #print(cmd)
    idx = buf.find(cmd)
    if idx>=0:
        buf=buf[idx:]
    return buf


# Routine to try a port and see if anything is connected
def try_port(port,baud,verbosity,ICOM=None):
    if verbosity>=1:
        print('\nDIRECT_IO - TRY_PORT: Trying port %s at %d baud - verb=%d ...' %
              (port,baud,verbosity) )

    try:
        self=blank_struct()
        self.s = serial.Serial(port,baud,timeout=0.1)
        #ICOM = "IC-9700" in port
        if ICOM:
            #print("ICOM 9700!")
            #self.civ = icom_civ('IC9700')            
            self.civ = icom_civ(ICOM)            
            cmd = self.civ.icom_form_command(0x03)            # Get freq
        else:
            cmd='ID;'.encode()
            
        while True:
            if verbosity>=1:
                print('TRY_PORT: Sending command cmd=',cmd)
            self.s.write(cmd)
            if verbosity>=1:
                print('TRY_PORT: Reading response...')
            if ICOM:
                time.sleep(DELAY)
                x = self.s.read(256)
                if verbosity>=1:
                    print('\tx=',x)
                if len(x)>0:
                    if verbosity>=1:
                        buf   = self.civ.icom_response(cmd,x) 
                        print('\tbuf=',buf)

                    if x[-2]==0xfa:
                        # The IC9700 returns NG when its turned off
                        if verbosity>=1:
                            print('TRY_PORT: No Good')
                    else:
                        self.rig_type  = 'Icom'
                        self.rig_type1 = 'Icom'
                        if x[-3]==0x94:
                            self.rig_type2 = 'IC7300'
                        else:
                            self.rig_type2 = 'IC9700'
                        self.lock      = threading.Lock() 
                        if verbosity>=1:
                            print('TRY_PORT: Found IC9700/IC7300')
                        return ['Icom',self.rig_type2,self]
                else:
                    buf=''
            else:
                buf = self.s.read(256).decode("utf-8")
                
            #print('buf=',buf)
            if verbosity>=1:
                print('TRY_PORT: cmd=%s \t response=%s' % (cmd,buf))
                
            if 'ID0460;' in buf:
                self.rig_type  = 'Yaesu'
                self.rig_type1 = 'Yaesu'
                self.rig_type2 = 'FTdx3000'
                self.mode      = ''
                self.lock      = threading.Lock() 
                return ['Yaesu','FTdx3000',self]
            elif buf=='ID0670;':
                self.rig_type  = 'Yaesu'
                self.rig_type1 = 'Yaesu'
                self.rig_type2 = 'FT991a'
                self.mode      = ''
                self.lock      = threading.Lock() 
                return ['Yaesu','FT991a',self]
            elif buf=='ID009;':
                self.rig_type  = 'Kenwood'
                self.rig_type1 = 'Kenwood'
                self.rig_type2 = 'TS850'
                self.mode      = ''
                self.lock      = threading.Lock() 
                return ['Kenwood','TS850',self]
            elif buf=='?;' or  buf=='E;':
                if verbosity>=1:
                    print('DIRECT TRY_PORT: Got a ? response - trying again')
                    print('cmd=%s \t response=%s',(cmd,buf))
            elif len(buf)>0:
                print('\nDIRECT TRY_PORT: Trying port %s at %d baud ...' % (port,baud) )
                print('DIRECT TRY_PORT: Got a response but dont know what to do?!')
                print('cmd=',cmd,'\tresponse=',buf)
                sys.exit(0)
            else:
                break

    #except:
    except Exception as e: 
        if verbosity>=1:
            print('e=',e,'\n')
            traceback.print_exc()
            print('...Nope')
        
    

# Routine to test connection to a particular rig
def try_rig(self,type1,type2,port,baud):
    try:
        if baud==0:
            if type2=='TS850':
                baud = 4800
            elif type2=='GS232b':
                baud = 9600
            else:
                baud = BAUD
        if type2=='GS232b':
            TimeOut=1
        else:
            TimeOut=0.1

        print('\nTRY_RIG: Trying %s %s\nport=%s\nbaud=%d ...' %
              (type1,type2,port,baud) )

        self.s = serial.Serial(port,baud,timeout=TimeOut)
        if not self.s.is_open:
            print("... Can't open port - giving up!")
            return False
        self.rig_type  = type1
        self.rig_type1  = type1
        self.rig_type2 = type2

        if type1=='Icom':
            #print(port)
            self.civ = icom_civ(self.rig_type2)

        if type2=='GS232b':
            print('Hmmm - so far so good ... baud=',baud)
            self.get_position()
            return True
        
        #print('Hey4',self.rig_type)
        freq = self.get_freq()
        print('Freq test=',freq)
        if type2=='IC9700' and False:
            print('Stopping for debug')
            sys.exit(0)
        
        if freq>0:
            self.port=port
            self.baud=baud
            return True
        else:
            print("%s %s doesn't seem to be responding - giving up" % (type1,type2))
            if type1=='Icom':
                print("See comments at top of icom_io.py for necessary settings")

    except Exception as e: 
        print("\n... Can't find %s %s ..." % (type1,type2))
        print('e=',e,'\n')
        traceback.print_exc()
        if self.lock.locked():
            self.lock.release()      # Still might have lock if bombed in get_freq

    if type2=='IC9700' and False:
        #print('Hey5')
        freq = self.get_freq()
        #print('Hey6',freq)
        
    return False
    

# Routine to search known ports & find a rig
def find_direct_rig(self,port_in,baud_in,force=False):

    print('\nFIND_DIRECT_RIG: Looking for any rigs connected to a USB port - port=',port_in,'\tbaud=',baud_in)
    baud=baud_in
    
    # The GS232 rotor
    if port_in==232:
        port=find_serial_device('GS232b',0,VERBOSITY=0)
        if try_rig(self,'Yaesu','GS232b',port,baud):
            return True

    # FTdx3000
    if port_in in [0,3000]:
        port=find_serial_device('FTdx3000',0,VERBOSITY=0)
        if try_rig(self,'Yaesu','FTdx3000',port,baud):
            return True
        
    # FT991a
    if port_in in [0,991]:
        port=find_serial_device('FT991a',0,VERBOSITY=0)
        if try_rig(self,'Yaesu','FT991a',port,baud):
            return True

    # IC-9700
    if port_in in [0,9700]:
        port=find_serial_device('IC9700',0,VERBOSITY=0)
        if try_rig(self,'Icom','IC9700',port,baud):
            return True
    elif port_in in [0,7300]:
        port=find_serial_device('IC7300',0,VERBOSITY=0)
        if try_rig(self,'Icom','IC7300',port,baud):
            return True

    # There are two possible connections to the TS-850
    # The first is via my home-brew interface
    if port_in in [0,850]:
        if try_rig(self,'Kenwood','TS850',SERIAL_PORT5,baud) or force:
            return True
        
    # The other is via the RT-system cable
    if port_in in [0,850]:
        if try_rig(self,'Kenwood','TS850',SERIAL_PORT6,baud):
            return True

    # IC-706
    if port_in in [0,706]:
        if try_rig(self,'Icom','IC706',SERIAL_PORT7,baud):
            return True

    print("\n*** FIND_DIRECT: Can't find any rigs - giving up - PORT =",port_in,'***')
    return False

############################################################################################

# Object for basic direct connection via serial port
class direct_connect:
    def __init__(self,port,baud,force=False):

        self.wpm           = 0
        self.freq          = 0
        self.band          = ''
        self.mode          = ''
        self.lock          = threading.Lock()             # Avoid collisions between various threads
        self.tx_evt        = threading.Event()            # Allow rig quires only when receiving
        self.fldigi_active = False
        self.flrig_active  = False
        self.tlast         = None
        self.pl_tone       = 0
        self.sub_dial_func = None
        self.ntimeouts     = 0

        print('DIRECT_CONNECT: Looking for rig - port=',port,'\tbaud=',baud,'...')
        Found = find_direct_rig(self,port,baud,force)

        if Found:
            self.rig_type1 = self.rig_type
            self.last_frqA  = 0
            self.last_frqB  = 0
            self.last_frqA1 = 0
            self.last_frqB1 = 0
            self.keyed=False
        
            self.s.setDTR(False)           # Make sure DTR is not asserted
            print('DIRECT_CONNECT: Connection to rig via', \
                  self.s.name,'\tport=',port,'\tbaud=',baud)
            print('Rig type=',self.rig_type,self.rig_type2)

            self.connection='DIRECT'
            self.active = True

        else:
            print("\n*** DIRECT_CONNECT: Unable to open DIRECT connection to rig ***")
            self.active=False
            print('\tport=',port,'\tbaud=',baud)
            

        # Test to make sure USB port is still alive
        if self.active:
            if self.rig_type2=='GS232b':
                print('DIRECT INIT - put test here!')
                return

            if self.rig_type1=='Icom':

                # Read freq
                freq = self.get_freq()
                print('\nIcom init - freq =',freq)
                return
            
            self.send('FA;')
            x = self.recv(256)
            print('DIRECT INIT:',x)
            if x[0:2]!='FA':
                print('*** DIRECT INIT - USB port appears to be there but no connection to rig ***')
                self.active=False or force
                return


    def send(self,cmd):
        # TODO - add ability to detect or override if we already have the lock
        self.lock.acquire()
        #print('Sending',cmd)
        cnt=self.s.write(cmd.encode())
        self.s.flush()
        self.lock.release()
        
        return cnt
    
    def recv(self,n=1024):
        # TODO - add ability to detect or override if we already have the lock
        self.lock.acquire()
        x = self.s.read(n).decode("utf-8") 
        self.lock.release()

        return x


    def check_port(self,txt,stop=False):
        #print('CHECK PORT: txt=',txt,'\ts=',self.s,'\topen=',self.s.is_open)
        #print(self.s.in_waiting)

        # We probably want this but let's not upset the apple cart for now
        #if (not self.s.is_open):
        #    print('\n*** CHECK PORT - Port is not open! ***')
        #    #sys,exit(0)
        #    return False
        if self.s.in_waiting:
            buf=self.s.read(1024)
            if len(txt)>0:
                print('DIRECT CHECK_PORT - '+txt+'*** Unexpected serial data waiting ***')
                print('buf=',buf)
                return False
            # Should never stop
            if stop:
                print('STOPPED')
                sys.exit(0)
            else:
                return False
        else:
            return True

    def get_response(self,cmd,wait=False):
        if VERBOSITY>0:
            if self.rig_type1=='Icom':
                print('DIRECT GET RESPONSE cmd=',show_hex(cmd))
            else:
                print('DIRECT GET RESPONSE cmd=',cmd)
        #print('Waiting for lock')
        self.lock.acquire()
        #status=self.lock.acquire(timeout=2)
        #if not status:
        #    print('DIRECT GET_RESPONSE: Unable to acquire lock - aborting')
        #    return
        #print('GET_RESPONSE: cmd=',cmd)
        #print('cmd=',' '.join(show_hex(cmd)))

        if self.rig_type1=='Icom':
            txt=' '.join( show_hex(cmd) )
        else:
            txt=str(cmd)
        ok=self.check_port('GET_RESPONSE:  writing '+txt,True)
        #if not ok:
        #    self.lock.release()
        #    return '?'
        if self.rig_type1=='Icom':
            cnt=self.s.write(cmd)
            self.s.flush()
            x=self.s.read(1024)
            q=b'?'
        else:
            #print('DIRECT GET_RESPONSE: cmd=',cmd)
            cnt=self.s.write(cmd.encode())
            self.s.flush()
            #time.sleep(DELAY)
            x=self.s.read(1024).decode("utf-8")
            #print('DIRECT GET_RESPONSE: x=',x)
            q='?'

        #x=self.recv()   # Can't use this bx lock has already been acquired
        #print('After read:',self.s.available())
        if wait:
            #while len(x)==0:
            #while x.find(';')<0:
            #while x[-1]!=';':
            while len(x)==0 or x[-1]!=';':
                x = x + self.s.read(1024).decode("utf-8") 
                #x = x + self.recv()

        if x.find(q)>0:
            print('DIRECT GET_RESPONSE: Unrecognized command',cmd,\
                  '\n\tresponse=',x)

        self.lock.release()
        #print('Lock released')
        return x

    def set_band(self,b,VFO='A'):
        if VERBOSITY>0:
            print('DIRECT SET_BAND: band=',b)
            
        if self.rig_type1=='Kenwood' or self.rig_type1=='Icom':
            print('DIRECT_IO: SET_BAND not support yet for Kenwood/Icom rigs')
            return 0            
                        
        code = bands[b]["Code"]
        cmd1 = 'BY;BS'+str(code).zfill(2)+';'          # Band select
        buf=self.get_response(cmd1)
        
    def get_band(self,frq=None,VFO='A'):
        if not frq:
            if not self.active:
                return 0
            frq = self.get_freq(VFO=VFO) * 1e-6

        if frq<0:
            band=None
        elif frq<1.7:
            band='MW'
        elif frq<3:
            band=160
        elif frq<5:
            band=80
        elif frq<6:
            band=60
        elif frq<9:
            band=40
        elif frq<12:
            band=30
        elif frq<16:
            band=20
        elif frq<20:
            band=17
        elif frq<23:
            band=15
        elif frq<27:
            band=12
        elif frq<40:
            band=10
        elif frq<60:
            band=6
        elif frq<144:
            band='AIR'
        elif frq<200:
            band=2
        elif frq<300:
            band=125
        elif frq<500:
            band=70
        elif frq<1000:
            band=33
        elif frq<1300:
            band=23
        else:
            band=0
            
        if VERBOSITY>0:
            print("DIRECT: Current rig freq=",frq," MHz --> ",band,"m")

        return band

    def get_ant(self):
        if VERBOSITY>=1:
            print('DIRECT GET_ANT ...')
        if self.rig_type2=='FTdx3000':
            buf = self.get_response('AN0;')
            try:
                ant=int(buf[3])
            except:
                print('DIRECT GET_ANT: Problem reading ant - buf=',buf)
                ant=1
            if VERBOSITY>=1:
                print('DIRECT GET_ANT: buf=',buf,'\tant=',ant)
        else:
            ant=1
        return ant

    def set_if_shift(self,shift):
        if self.rig_type2 in ['FTdx3000','FT991a']:
            cmd='BY;IS0+'+str(shift).zfill(4)+';'
            #print('DIRECT SET IF SHIFT:',shift,'\tcmd=',cmd)
            buf=self.get_response(cmd)
            #print('buf=',buf)

    # Function to select antenna port and manage tuner
    def set_ant(self,a,VFO='A'):

        # This only make sense on the FTdx3000
        if self.rig_type2=='FTdx3000':
            if VFO=='B':
                buf=self.get_response('BY;FR4;AN0'+str(a)+';FR0;')
            else:
                buf=self.get_response('BY;AN0'+str(a)+';')

            # The 40m ant was temporarily hosed
            band=self.get_band()
            if a==1 or a==2:
            #if band!=40 and (a==1 or a==2):
                # Make sure ant tuner is on for ports 1 & 2
                self.tuner(1)
            else:
                # Make sure ant tuner is off for port 3
                self.tuner(0)

    def get_PLtone(self):
        #VERBOSITY=1
        if VERBOSITY>0:
            print('DIRECT Get PL Tone ...')
        if self.rig_type=='Kenwood' or self.rig_type1=='Hamlib':
            print('GET_PLtone: Function not yet implemented for Kenwood or Hamlib  rigs')
            return 0
            
        elif self.rig_type1=='Icom':
            cmd = self.civ.icom_form_command([0x16,0x42])                 # See if tone is on or off
            x   = self.get_response(cmd)
            y   = self.civ.icom_response(cmd,x)                        
            #print('DIRECT GET_PL_TONE: cmd =',show_hex(cmd))
            on_off = int(y[1],16)
            #print('DIRECT GET_PL_TONE: y   =',y,on_off)

            if on_off==0:
                return 0
            else:
                cmd = self.civ.icom_form_command([0x1b,0x0])             # Get tone freq
                x   = self.get_response(cmd)
                y   = self.civ.icom_response(cmd,x)
                #print('DIRECT GET_PL_TONE: cmd =',show_hex(cmd))
                tone = 0.1*bcd2int(y,1)
                #print('DIRECT GET_PL_TONE: y=',y,on_off,tone)
                return tone
            
        else:
            if self.rig_type2=='FTdx3000':
                cmd1='CT0;'
                cmd2='CN0;'
                idx2=5
            elif self.rig_type2=='FT991a':
                cmd1='CT0;'
                cmd2='CN00;'
                idx2=7
            else:
                print('DIRECT GET_PL_TONE: Unknown rig',self.rig_type2)
                return 0                

            try:
                buf = self.get_response(cmd1)
                on_off = int(buf[3])
            except Exception as e: 
                print('DIRECT GET_PL_TONE: Problem reading PL tone - giving up')
                print('e=',e,'\n')
                traceback.print_exc()
                print('buf=',buf)
                return 0
                
            if VERBOSITY>0:
                print('DIRECT GET_PL_TONE: CT buf=',buf,on_off)
            if on_off==0:
                return 0
            else:
                buf = self.get_response(cmd2)
                if VERBOSITY>0:
                    print('DIRECT GET_PL_TONE: CN buf=',buf)
                try:
                    idx = int(buf[4:idx2])
                    tone = PL_TONES[idx]
                except:
                    print('DIRECT GET_PL_TONE: Error reading PL Tone')
                    print('DIRECT GET_PL_TONE: cmd=',cmd2,'\tbuf=',buf)
                    tone=None
                    
                if VERBOSITY>0:
                    print('DIRECT GET_PL_TONE: CN idx=',buf[4:8],idx,tone)
                return tone

    def set_PLtone(self,tone):
        if VERBOSITY>0:
            print('DIRECT Set PL Tone ...')
        if self.rig_type=='Kenwood':
            print('SET_PLtone: Function not yet implemented for Kenwood rigs')
            return 0

        elif self.rig_type1=='Icom':
            if tone==0:
                cmd = self.civ.icom_form_command([0x16,0x42,0x0])         # Turn off tone
                buf = self.get_response(cmd)
                #print('DIRECT SET_PL_TONE: buf=',buf)
            else:
                cmd = self.civ.icom_form_command([0x16,0x42,0x1])         # Turn on tone
                #print('DIRECT SET_PL_TONE: cmd =',show_hex(cmd))
                buf = self.get_response(cmd)
                #print('DIRECT SET_PL_TONE: buf=',show_hex(buf))

                bcd = int2bcd(10*tone,2,1)
                #print('DIRECT SET_PL_TONE: bcd=',show_hex(bcd),tone)
                cmd = self.civ.icom_form_command([0x1b,0x0]+bcd)          # Set tone freq
                #print('DIRECT SET_PL_TONE: cmd =',show_hex(cmd))
                buf = self.get_response(cmd)
                #print('DIRECT SET_PL_TONE: buf=',show_hex(buf))
            
        else:
            if tone==0:
                buf = self.get_response('CT00;')
                #print('DIRECT SET_PL_TONE: CT buf=',buf)
            else:
                p3 = str( np.where(PL_TONES==tone)[0][0] ).zfill(3)
                cmd='CN00'+p3+';CT02;'
                buf = self.get_response(cmd)
                #print('DIRECT SET_PL_TONE: CT buf=',buf)
                
                
    
    def get_freq(self,VFO='A'):
        #VERBOSITY=1
        if VERBOSITY>0:
            print('DIRECT Get Freq - vfo=',VFO,'...')
            
        if self.rig_type1=='Icom':
            #vfo=self.get_vfo()
            #print('vfo=',vfo)
            try:
                self.select_vfo(VFO)          # Not sure why this was here
            except Exception as e: 
                print("\n**** DIRECT IO -> GET_FREQ ERROR ***")
                print('e=',e,'\n')
                traceback.print_exc()
                
            cmd = self.civ.icom_form_command(0x03)            # Get freq
            x   = self.get_response(cmd)
            y   = self.civ.icom_response(cmd,x)                        
            #sys.exit(0)

            if VERBOSITY>0:
                print('cmd=',show_hex(cmd),'\nx=',x,'\ny=',y)
            
            if len(y)==0:
                x=self.get_response(cmd)              # If at first we don't succeed, try again
                y=self.civ.icom_response(cmd,x)
            try:
                frq = bcd2int(y)
            except Exception as e: 
                error_trap("**** DIRECT IO -> GET_FREQ ERROR ***")

                frq=0
                print('DIRECT Icom get freq - problem reading freq')
                #print('\tcmd      =',[hex(c) for c in cmd])
                #print('\tresponse =',[hex(ord(c)) for c in x])
                #print('\ty        =',[hex(ord(c)) for c in y])
                print('\tcmd      =',cmd)
                print('\tresponse =',x)
                print('\ty        =',y)

        else:
            try:
                buf = self.get_response('F'+VFO+';')
                buf = strip_garbage(buf,'F'+VFO)
                if buf[0]=='?':
                    buf = self.get_response('F'+VFO+';')
                    buf = strip_garbage(buf,'F'+VFO)
                frq = float(buf[2:-1])
            except Exception as e: 
                print('DIRECT GET_FREQ: Unable to read freq - buf=',buf)
                print('e=',e,'\n')
                traceback.print_exc()
                frq=0

        self.freq=frq
        return frq

    def set_freq(self,frq_KHz,VFO='A'):
        #VERBOSITY=1
        if VERBOSITY>0:
            print('\nDirect Set Freq:',frq_KHz,VFO,self.rig_type2)

        frq=int(frq_KHz*1000)
        if self.rig_type=='Kenwood':
            cmd = 'FA'+str(frq).zfill(11)+';'           # Tune to lower sub-band edge
        elif self.rig_type1=='Icom':
            self.select_vfo(VFO)
            if self.rig_type2=='IC706':
                y2  = int2bcd(frq,5)
            else:
                y2  = int2bcd(frq,5,1)
                y2  = y2[::-1]
            cmd =  self.civ.icom_form_command([0x00]+y2)   
            #cmd =  self.civ.icom_form_command([0x05]+y2)   
        elif self.rig_type2=='FT991a':
            cmd = 'BY;F'+VFO+str(frq).zfill(9)+';'
        else:
            cmd = 'BY;F'+VFO+str(frq).zfill(8)+';'
            
        buf=self.get_response(cmd)
        
        if VERBOSITY>0:
            print('SET_FREQ: cmd=',cmd)
            print('SET_FREQ: buf=',buf)
            if self.rig_type1=='Icom':
                print('buf=',show_hex(buf))
                y=self.civ.icom_response(cmd,buf)
                print('y=',y)

        if VFO=='A' or VFO=='M':
            self.last_frqA = frq_KHz
        else:
            self.last_frqB = frq_KHz

        return 1000*frq_KHz
    
    def set_mode(self,mode,VFO='A',Filter=None):
        #VERBOSITY=1
        if VERBOSITY>0:
            print('DIRECT SET_MODE:',mode,VFO)

        if mode==None:
            return
        elif mode=='RTTY' or mode=='DIGITAL' or mode=='FT8' or mode.find('PSK')>=0 or mode.find('JT')>=0:
            #mode='RTTY'
            mode='PKT-U'
            mode='PKTUSB'
            mode='RTTY'
        elif mode=='CW-LSB':
            mode='CW-R'
        c = modes[mode]["Code"]
        
        if self.rig_type=='Kenwood':
            self.send('MD'+c[1]+';')
            if VFO!='A':
                print('DIRECT SET_MODE:',mode,VFO,' ********* Only VFO=A is supported for now ********')
        elif self.rig_type1=='Icom':
            #print('DIRECT SET_MODE Icom',VFO)
            self.select_vfo(VFO)
            c = icom_modes[mode]["Code"]
            f = icom_modes[mode]["Filter1"]
            cmd = self.civ.icom_form_command([0x01,c,f])   
            buf = self.get_response(cmd)
        elif self.rig_type2=='FT991a':
            #if VFO!='A':
            #    print('DIRECT SET_MODE:',mode,VFO,' ********* Only VFO=A is supported for now ********'
            if VFO=='A':
                self.send('MD'+c+';')
            else:
                self.send('SV;MD'+c+';SV;')
        elif VFO=='A':
            self.send('FR0;MD'+c+';')
        else:
            self.send('FR4;MD'+c+';')
            time.sleep(DELAY)
            self.send('FR0;')
        #print('SET_MODE:',buf)


    # Function to set active VFO
    def select_vfo(self,VFO):
        #VERBOSITY=1
        if VERBOSITY>0:
            print('DIRECT SELECT_VFO:',VFO,self.rig_type,self.rig_type1)
            
        if self.rig_type1=='Icom':
            if VFO=='A':
                sub=0x00
                sub=0xD0            # Use Main, not VFO A
            elif VFO=='B':
                sub=0x01
                sub=0xD1            # Use Sub, not VFO B
            elif VFO=='M':
                sub=0xD0
            elif VFO=='S':
                sub=0xD1
            elif VFO=='X':
                sub=0xB0          # Exchange
            else:
                print('DIRECT SELECT_VFO - Invalid VFO:',VFO)
                
            cmd = self.civ.icom_form_command([0x07,sub])   
            buf = self.get_response(cmd)
            y=self.civ.icom_response(cmd,buf)
            
            if VERBOSITY>0:
                print('cmd=',cmd)
                print('buf=',show_hex(buf))
                print('y=',y)
                
        else:            
            print('DIRECT SELECT_VFO Command not yet implemented for non-ICOM rigs')

            
    def set_vfo(self,rx=None,tx=None,op=None):
        
        self.set_vfo_direct(rx,tx,op)
        
    def set_vfo_direct(self,rx=None,tx=None,op=None):
        #VERBOSITY=1
        if VERBOSITY>0:
            print('DIRECT SET_VFO:',rx,tx)
        if self.rig_type1=='Icom':
            
            print('DIRECT SET_VFO Command not yet implemented for ICOM rigs')
            return

        if op=='A->B':
            cmd='BY;AB;' 
        elif op=='B->A':
            cmd='BY;BA;'
        elif op=='A<->B':
            cmd='BY;SV;'
        
        else:
            
            if self.rig_type2=='FT991a':
                cmd='BY;'
                if rx!='A':
                    print('DIRECT SET_VFO: *** WARNING *** RX is always on VFO A for the FT991a *** rx,tx=',rx,tx)
            elif rx=='A' or rx=='M':
                cmd='BY;FR0;'
            elif rx=='B' or rx=='S':
                cmd='BY;FR4;'
            else:
                cmd=''
                
            if tx=='A' or tx=='M':
                cmd=cmd+'FT2;'
            elif tx=='B' or tx=='S':
                cmd=cmd+'FT3;'
            
        if VERBOSITY>0:
            print('DIRECT_SET_VFO: cmd=',cmd)
        buf = self.get_response(cmd)
        if VERBOSITY>0:
            print('DIRECT_SET_VFO: buf=',buf)

    def get_info_old(self):
        print('DIRECT GET_INFO...')
        buf = self.get_response('ID;')
        print('DIRECT GET_INFO buf=',buf)
        buf=buf[:6]
        if buf=='ID0460':
            self.rig_type  = 'Yaesu'
            self.rig_type1 = 'Yaesu'
            self.rig_type2 = 'FTdx3000'
        elif buf=='ID0670':
            self.rig_type  = 'Yaesu'
            self.rig_type1 = 'Yaesu'
            self.rig_type2 = 'FT991a'
        elif buf=='ID009;':
            self.rig_type  = 'Kenwood'
            self.rig_type1 = 'Kenwood'
            self.rig_type2 = 'TS850'
        else:
            print('\n*** SOCKET_IO:DIRECT GET_INFO: Unknown rig on the other end ***',x)
            self.rig_type2 = ''
        print('DIRECT GET_INFO rig_type2=', self.rig_type2)
        return buf
        

    def get_vfo(self):
        #VERBOSITY=1
        if VERBOSITY>0:
            print('\nDIRECT GET_VFO...')
            
        if self.rig_type1=='Kenwood':
            print('GET_VFO not available yet for',self.rig_type,self.rig_type2,' - need some more code')
            return 'AA'

        elif self.rig_type1=='Icom':
            print('GET_VFO not available yet for',self.rig_type,self.rig_type2,' - need some more code')
            return 'AA'

            # There doesn't seem to be a way to do this???!!!!
            #cmd = self.civ.icom_form_command([0x07])   
            #cmd = self.civ.icom_form_command([0x07,0xd2,0x0])   
            cmd = self.civ.icom_form_command([0x03])   
            buf = self.get_response(cmd)
            y=self.civ.icom_response(cmd,buf)
            
            if VERBOSITY>0:
                print('cmd=',cmd)
                print('buf=',show_hex(buf))
                print('y=',y)
                
            return 'AA'
 
        elif self.rig_type2=='FT991a':
            rx='A'
        else:
            buf = self.get_response('FR;')
            if buf[2]=='0' or buf[2]=='1':
                rx='A'
            elif buf[2]=='4' or buf[2]=='5':
                rx='B'
            else:
                rx='?'
            
        buf = self.get_response('FT;')
        if buf[2]=='0':
            tx='A'
        elif buf[2]=='1':
            tx='B'
        else:
            tx='?'
        if VERBOSITY>0:
            print('DIRECT GET_VFO:',rx+tx)
        return rx+tx

    def get_filters(self):
        if VERBOSITY>0 or False:
            print('DIRECT GET_FILTERS:')
            
        if self.rig_type1=='Icom' or self.rig_type2 in ['IC9700','IC7300','IC706'] or \
           self.rig_type2=='Dummy':
            print('DIRECT_IO: Get Filters - not yet supported for Icom Rigs')
            return [None,None]
        elif self.rig_type=='Kenwood':
            cmd = 'FL;'
            buf = self.get_response(cmd,True)
            #print('buf=',buf)
            #print('buf=',buf[2:5],buf[5:8])
            filt1 = Decode_Filter_ts850(buf[2:5])
            filt2 = Decode_Filter_ts850(buf[5:8])
        else:
            cmd = 'NA0;'
            buf = self.get_response(cmd)
            #print('DIRECT GET_FILTERS: cmd=',cmd,' - buf=',buf)
            if buf[3]=='0':
                filt1 = 'Wide'
            else:
                filt1 = 'Narrow'
                
            cmd = 'SH0;'
            buf = self.get_response(cmd)
            #print('DIRECT GET_FILTERS: cmd=',cmd,' - buf=',buf)
            filt2 = Decode_Filter_ft991a(self.mode,filt1,buf[3:5])
            
        return [filt1,filt2]


    def set_breakin(self,onoff):
        if self.rig_type1=='Kenwood' or self.rig_type1=='Icom':
            print('DIRECTSET_BREAKIN: Function not yet implemented for Kenwood and Icom rigs')
            return 
        
        cmd='BY;BI'+str(onoff)+';'
        self.get_response(cmd)


    def set_filter(self,filt,mode=None):
        #VERBOSITY=1
        if VERBOSITY>0:
            print('\nDIRECT SET_FILTER: filt=',filt,'\tmode=',mode,mode[0:2])
            
        if filt in ['Auto','Narrow','Wide']:
            if mode in ['USB','SSB','LSB']:
                filt=['Wide','2400']
            elif mode[0:2]=='CW':
                filt=['Narrow','400']           # Was 500
            elif mode in ['RTTY','DATA']:
                filt=['Wide','3000']
            elif filt=='Auto':
                filt=['Wide']
        elif type(filt) in [int,float]:
            if filt<=500:
                filt=['Narrow',filt]
            else:
                filt=['Wide',filt]
                                
        if not type(filt) is list:
            filt=[filt]
        
        if VERBOSITY>0:
            print('\nDIRECT SET_FILTER: filt=',filt,'\tmode=',mode)
            
        if self.rig_type1=='Icom':
            print('DIRECT_IO: SET_POWER not support yet for Icom rigs')
            return False
            
        if self.rig_type=='Kenwood':
            c1 = modes[filt[0]]["Filter3"]
            c2 = modes[filt[1]]["Filter3"]
            cmd='FL'+c1+c2+';'
            #print('cmd=',cmd)
            #self.check_port('SET_FILTER: B4 send',True)
            self.send(cmd)
            time.sleep(DELAY)
            valid = self.check_port('SET_FILTER After send',False)
            if not valid:
                print('DIRECT SET_FILT - Invalid filter combo')
                return False
            else:
                return True
            
        else:
            
            if filt[0]=='Wide':
                cmd='RF03;NA00;'
            else:
                cmd='RF00;NA01;'
            buf = self.get_response('BY;'+cmd)
            if VERBOSITY>0:
                print('DIRECT SET_FILTERS = Setting wide/narrow: cmd=',
                      cmd,' - buf=',buf)

            if mode:
                m=mode
            else:
                if len(self.mode)==0:
                    self.mode=self.get_mode()
                m=self.mode
            if VERBOSITY>0:
                print('DIRECT SET_FILTER: Mode=',m,filt[0])
                
            if m in ['RTTY','PKTUSB','PSK-U','DATA-U','DIGITA','BPSK31']:
                if filt[0]=='Wide':                    
                    filts=FT991A_DATA_FILTERS2
                else:
                    filts=FT991A_DATA_FILTERS1
            elif m in ['USB','LSB']:
                if filt[0]=='Wide':                    
                    filts=FT991A_SSB_FILTERS2
                else:
                    filts=FT991A_SSB_FILTERS1
            elif m in ['CW','CW-R','CWR','CW-U','CW-L']:
                if filt[0]=='Wide':                    
                    filts=FT991A_CW_FILTERS2
                else:
                    filts=FT991A_CW_FILTERS1
            else:
                print('DIRECT SET_FILTER - Unknown mode',m)
                return False

            if len(filt)==1:
                #print('Hey 1')
                if filt[0]=='Wide':
                    filt.append( max(filts) )
                    if self.rig_type2 == 'FTdx3000':
                        if filt[1]>300:
                            filt[1]=2400
                else:
                    #print('Hey 2',self.rig_type,self.rig_type1,self.rig_type2)
                    filt.append( min(filts) )
                    if self.rig_type2 == 'FTdx3000':
                        #print('Hey 3')
                        if filt[1]<200:
                            filt[1]=200
            else:
                print('DIRECT SET_FILTER - filt=',filt,'\tfilt1=',filt[1])
                filt[1]=str(filt[1]).replace(' Hz','')
            if VERBOSITY>0:
                print('DIRECT SET_FILTER: filt1=',filt[1])
                
            if VERBOSITY>0:
                print('DIRECT SET_FILTER: filts=',filts,len(filts))
            idx=filts.index(int(filt[1]))
            cmd='BY;SH'+str(idx).zfill(3)+';'
            buf = self.get_response(cmd)
            if VERBOSITY>0:
                print('DIRECT SET_FILTER: idx=',idx,'\tcmd=',cmd,'\tbuf=',buf)
            
        return False

        
    def get_mode(self,VFO='A'):
        if VERBOSITY>0:
            print('DIRECT GET_MODE:',VFO)
            
        if self.rig_type=='Kenwood':
            cmd = 'IF;'
            idx = 29
        elif self.rig_type1=='Icom':
            cmd = self.civ.icom_form_command(0x04)   
            buf = self.get_response(cmd)
            y   = self.civ.icom_response(cmd,buf)
            #print('y=',y)
            mode = Icom_Decode_Mode( y[0] )
            return mode
        elif self.rig_type2=='FT991a':
            if VFO=='A':
                cmd = 'MD0;'
                idx = 3
            else:
                cmd = 'OI;'
                idx = 21
        elif VFO=='A':
            cmd = 'FR0;MD0;'
            idx = 3
        else:
            #cmd = 'FR4;MD0;'       # This interrupts the rx
            #idx = 3
            cmd = 'OI;'
            idx = 20

        buf = self.get_response(cmd,True)
        if VERBOSITY>0 or len(buf)<3:
            print('DIRECT GET_MODE: VFO=',VFO,'\tcmd=',cmd,'\tbuf=',buf)
        if VFO=='B' and False:
            time.sleep(DELAY)
            self.send('FR0;')
        mode = Decode_Mode( buf[idx] )
        return mode
            
    def get_fldigi_mode(self):
        return self.get_mode()

    def set_mem_chan(self,ch):
        if VERBOSITY>0:
            print('DIRECT SET_MEM_CHAN: mem chan=',ch)
        if self.rig_type=='Kenwood':
            # Haven't figured this out yet
            #cmd1 = 'FR0;MC '+str(ch).zfill(2)+';'     
            cmd1 = 'MC '+str(ch).zfill(2)+';'     
            #cmd1 = 'MR'+str(ch).zfill(4)+';'     
        else:
            cmd1 = 'BY;MC'+str(ch).zfill(3)+';'  
        buf=self.get_response(cmd1)
        if VERBOSITY>0:
            print('cmd=',cmd1)
        print('SET_MEM_CHAN: buf=',buf)
        
    def get_power(self):
        if VERBOSITY>0:
            print('DIRECT GET_POWER:')
        buf=self.get_response('PC;')
        return int(buf[2:5])
        
    def mic_setting(self,m,iopt,src=None,lvl=None,prt=None):
        if VERBOSITY>0:
            print('DIRECT MIC_SETTING:')
        if m=='CW' or m=='RTTY':
            return
        menu_nums=YAESU_MIC_MENU_NUMBERS[self.rig_type2]
        if m=='LSB' or  m=='USB':
            m='SSB'
        source= menu_nums[m][0]
        level = menu_nums[m][1]
        port  = menu_nums[m][2]
        lvl   = 0
        prt   = 0

        cmd1='EX'+str(source).zfill(3)
        cmd2='EX'+str(level ).zfill(3)
        cmd3='EX'+str(port  ).zfill(3)
        if iopt==0:
            # Read
            buf=self.get_response(cmd1+';')
            src=int(buf[-2])
            if level:
                buf=self.get_response(cmd2+';')
                lvl=int(buf[5:8])
            if port:
                buf=self.get_response(cmd3+';')
                prt=int(buf[-2])
            return [src,lvl,prt]
        else:
            # Set
            if src!=None and source:
                if self.rig_type2=='FTdx3000':
                    src*=2
                print('src=',src,cmd1)
                buf=self.get_response('BY;'+cmd1+str(src)+';')
            if lvl!=None and level:
                print('lvl=',lvl,cmd1)
                buf=self.get_response('BY;'+cmd2+str(lvl).zfill(2)+';')
            if prt!=None and port:
                print('prt=',prt,cmd3)
                buf=self.get_response('BY;'+cmd3+str(prt)+';')
        
    def set_power(self,p):
        if VERBOSITY>0:
            print('DIRECT SET_POWER: p=',p)

        if self.rig_type1=='Kenwood' or self.rig_type1 in ['Icom','Hamlib']:
            print('DIRECT_IO: SET_POWER not support yet for Kenwood/Icom/Hamlib rigs')
            return 0            
            
        p=min(max(p,5),100)
        cmd1 = 'BY;PC'+str(p).zfill(3)+';'          # Power select
        buf=self.get_response(cmd1)
        
    def set_log_fields(self,fields):
        if VERBOSITY>0:
            print('*** WARNING *** Ignored call to SET_LOG_FIELDS ***')
        pass

    def get_log_fields(self):
        if VERBOSITY>0:
            print('*** WARNING *** Ignored call to GET_LOG_FIELDS ***')

        call    = ''
        name    = ''
        qth     = ''
        rst_in  = ''
        rst_out = ''
        ser_in  = ''
        ser_out = ''

        return {'Call':call,'Serial_In':ser_in,'Serial_Out':ser_out,\
                'Name':name,'QTH':qth,\
                'RST_in':rst_in,'RST_out':rst_out}

    def set_call(self,call): 
        if VERBOSITY>0:
            print('*** WARNING *** Ignored call to SET_CALL ***')
        
    def get_serial_out(self):
        return 0
    
    def close(self):
        self.s.close()

    # Function to effect pressing of TUNE button
    def tuner(self,opt):
        #VERBOSITY=1
        if VERBOSITY>0:
            print('DIRECT TUNER:',opt)
        if self.rig_type1=='Kenwood' or self.rig_type1=='Icom':
            print('DIRECT_IO: TUNER not support yet for Kenwood/Icom rigs')
            return 0
            
        if opt==-1:
            buf=self.get_response('AC;')
            if VERBOSITY>0:
                print('DIRECT TUNER: buf=',buf)
            return int(buf[4])
        elif opt>=0 and opt<=2:
            buf=self.get_response('BY;AC00'+str(opt)+';')
            if VERBOSITY>0:
                print('DIRECT TUNER: buf=',buf)
        else:
            print('DIRECT TUNER - Invalid option:',opt)

    # Function to turn PTT on and off
    def ptt(self,on_off,VFO='A'):
        if VERBOSITY>0:
            print('\nDIRECT PTT:',on_off,VFO)

        if self.rig_type=='Kenwood':
            if on_off:
                cmd = 'TX;'
            else:
                cmd = 'RX;'
            self.check_port('PTT: B4 Send',True)
            self.send(cmd)
            time.sleep(DELAY)
            valid = self.check_port('PTT After send',False)
            return valid

        # Yaesu
        if on_off:
            self.keyed=True
            if VFO=='A':
                self.last_frqA1 = self.last_frqA
                self.send('FT2;TX1;')
            else:
                self.last_frqB1 = self.last_frqB
                self.send('FT3;TX1;')
        else:
            #self.send('TX0;FT2;')
            self.send('TX0;')
            time.sleep(DELAY)
            self.send('FT2;')

            # Take care of an freq changes that were commanded while PTT was keyed
            print('Last freqs:',self.last_frqA,self.last_frqA1,self.last_frqB,self.last_frqB1)
            if self.last_frqA1 != self.last_frqA:
                print('Setting VFO A to',self.last_frqA)
                time.sleep(DELAY)
                self.set_freq(self.last_frqA,'A')
            if self.last_frqB1 != self.last_frqB:
                print('Setting VFO B to',self.last_frqB)
                time.sleep(DELAY)
                self.set_freq(self.last_frqB,'B')
                
            self.keyed=False
            
        print('DIRECT PTT Done.')

    # Routine to get date & time 
    def get_date_time(self,VERBOSITY=0):
        #VERBOSITY=1
        if self.rig_type2=='FT991a':
            buf=self.get_response('DT0;')
            d=buf[3:-1]
            if VERBOSITY>0:
                print('DIRECT GET_DATE_TIME: Date=',buf,d)

            buf=self.get_response('DT1;')
            t=buf[3:-1]
            if VERBOSITY>0:
                print('DIRECT GET_DATE_TIME: Time=',buf,t)

            buf=self.get_response('DT2;')
            z=buf[3:-1]
            if VERBOSITY>0:
                print('DIRECT GET_DATE_TIME: Zone=',buf,z)

        elif self.rig_type2 in ['IC9700','IC7300']:

            if VERBOSITY>0:
                print('DIRECT GET_DATE_TIME - Icom - Getting UTC offset ...')
            cmd =  self.civ.icom_form_command([0x1a,0x05,0x01,0x84])  
            x=self.get_response(cmd)
            y=self.civ.icom_response(cmd,x)
            # This is probably not quite right since I set the rig to UTC time so z=0.
            # Pg 16 of the IC9700 CIV manual shows how to decode this message.
            z=bcd2int( y[3:] )
            if VERBOSITY>0:
                print('cmd=',show_hex(cmd),'\nx=',x,'\ny=',y,'\nz=',z)

            if VERBOSITY>0:
                print('\nDIRECT GET_DATE_TIME - Icom - Getting Date ...')
            cmd =  self.civ.icom_form_command([0x1a,0x05,0x01,0x79])  
            x=self.get_response(cmd)
            y=self.civ.icom_response(cmd,x)
            d=str( bcd2int( y[3:],1 ) )
            if VERBOSITY>0:
                print('cmd=',show_hex(cmd),'\nx=',x,'\ny=',y,'\nd=',d)
                
            if VERBOSITY>0:
                print('\nDIRECT GET_DATE_TIME - Icom - Getting Time ...')
            cmd =  self.civ.icom_form_command([0x1a,0x05,0x01,0x80])  
            x=self.get_response(cmd)
            y=self.civ.icom_response(cmd,x)
            t=str( bcd2int( y[3:],1 ) ).zfill(4) + '00'
            if VERBOSITY>0:
                print('cmd=',show_hex(cmd),'\nx=',x,'\ny=',y,'\nt=',t,'\n')
            
        else:
            print('DIRECT GET_DATE_TIME - Rig not supported',self.rig_type2)
            d=None
            t=None
            z=None
            
        return d,t,z


    # Routine to set date & time 
    def set_date_time(self,VERBOSITY=0):
        now_utc = datetime.now(timezone('UTC'))
        date = now_utc.strftime("%Y%m%d")
        time = now_utc.strftime("%H%M%S")

        if self.rig_type2=='FT991a':

            if VERBOSITY>0:
                print('\nSetting Date on FT991a to',date,'...')
            cmd='DT0'+date+';'
            self.send(cmd)
            
            if VERBOSITY>0:
                print('\nSetting Time on FT991a to',time,'...')
            cmd='DT1'+time+';'
            self.send(cmd)
            
            if VERBOSITY>0:
                print('Setting UTC offset on FT991a ...')
            cmd='DT2+0000;'
            self.send(cmd)
            
        elif self.rig_type2 in ['IC9700','IC7300']:
        
            if VERBOSITY>0:
                print('Setting UTC offset on IC9700 ...')
            cmd =  self.civ.icom_form_command([0x1a,0x05,0x01,0x84,0x0,0x0,0x0])
            #print('cmd=',show_hex(cmd))
            x=self.get_response(cmd)
            y=self.civ.icom_response(cmd,x)
            if VERBOSITY>1:
                print('cmd=',show_hex(cmd))
                print('y=',y)
    
            if VERBOSITY>0:
                print('\nSetting Date on IC9700 to',date,'...')
            d=int2bcd(int(date),4,1)
            cmd =  self.civ.icom_form_command([0x1a,0x05,0x01,0x79]+d)  
            #print('cmd=',show_hex(cmd))
            x=self.get_response(cmd)
            y=self.civ.icom_response(cmd,x)
            if VERBOSITY>1:
                print('cmd=',show_hex(cmd))
                print('y=',y)

            if VERBOSITY>0:
                d#print('\nSetting Time on IC9700 to',time,'...')
            t=int2bcd(int(time[0:4]),2,1)
            cmd =  self.civ.icom_form_command([0x1a,0x05,0x01,0x80]+t)  
            #print('cmd=',show_hex(cmd))
            x=self.get_response(cmd)
            y=self.civ.icom_response(cmd,x)
            if VERBOSITY>1:
                print('cmd=',show_hex(cmd))
                print('y=',y)

        else:

            print('DIRECT SET_DATE_TIME - Unknown rig',self.rig_type2)
            sys.exit(0)
            

    # Routine to set ICOM settings to values I find most useful
    def icom_defaults(self):
    
        if self.rig_type2 in ['IC9700','IC7300']:

            # Turn off CI-V transceive mode - this is only useful if multiple rigs
            # are connected together and generates a lot of extranious junk
            cmd =  self.civ.icom_form_command([0x1a,0x05,0x01,0x27,0x0])  
            #print('cmd=',show_hex(cmd))
            x=self.get_response(cmd)
            y=self.civ.icom_response(cmd,x)
            #print('y=',y)
            
        
    # Routine to put rig into sat mode
    def sat_mode(self,opt):
        #VERBOSITY=1
        if VERBOSITY>0:
            print('DIRECT - SAT_MODE: opt=',opt,self.rig_type2)

        if self.rig_type2=='IC9700':
        
            if opt==-1:
                
                # Read current sat mode setting
                cmd =  self.civ.icom_form_command([0x16,0x5a])  
                x=self.get_response(cmd)
                y=self.civ.icom_response(cmd,x)
                if VERBOSITY>0:
                    print('\tcmd=',show_hex(cmd))
                    print('\ty=',y)

                return int( y[1],16 )
    
            elif opt<2:
                
                # Turn it on/off
                cmd =  self.civ.icom_form_command([0x16,0x5a,opt])  
                x=self.get_response(cmd)
                y=self.civ.icom_response(cmd,x)
                if VERBOSITY>0:
                    print('\tcmd=',show_hex(cmd))
                    print('\ty=',y)
                
                return opt

            else:

                print('SAT_MODE: Invalid opt',opt)
                return -1
            
        else:

            if VERBOSITY>0:
                print('SAT_MODE: Invalid rig',self.rig_type2)
                return -1
    
    

    # Routine to put rig into dual watch
    def dual_watch(self,opt):
        VERBOSITY=1
        if VERBOSITY>0:
            print('DIRECT - DUAL_WATCH:',opt,'\trig_type2=',self.rig_type2)

        if self.rig_type2=='IC9700':
        
            if opt==-1:
                # Read current sat mode setting
                cmd =  self.civ.icom_form_command([0x16,0x59])  
                if VERBOSITY>0:
                    print('\tcmd=',show_hex(cmd))
                x=self.get_response(cmd)
                if VERBOSITY>0:
                    print('\tx=',show_hex(x))
                y=self.civ.icom_response(cmd,x)
                if VERBOSITY>0:
                    print('\ty=',y)

                return int( y[1],16 )
    
            elif opt<2:
                # Turn it on/off
                cmd =  self.civ.icom_form_command([0x16,0x59,opt])  
                x=self.get_response(cmd)
                y=self.civ.icom_response(cmd,x)
                if VERBOSITY>0:
                    print('\tcmd=',show_hex(cmd))
                    print('\ty=',y)
                
                return opt

            else:

                print('DUAL_WATCH: Invalid opt',opt)
                return 0
            
        else:

            if VERBOSITY>0:
                print('DUAL_WATCH: Invalid rig',self.rig_type2)
            return 0
    

    # Dummy
    def modem_carrier(self,frq=None):
        return 0

    # Routine to put rig into split mode
    def split_mode(self,opt):
        #VERBOSITY=1
        if VERBOSITY>0:
            print('DIRECT - SPLIT_MODE:',opt)

        # The FT991a always uses VFO A for receiver while the FTdx3000
        # can use either VFO.  For now, we assume the RX is on VFO A
        # for both rigs.
        if self.rig_type=='Yaesu':
        
            if opt==-1:
                #print('\nQuerying split ...')
                buf=self.get_response('FT;')
                #print('SPLIT: buf=',buf)
                return buf[2]=='1'

            elif opt<2:

                #print('SPLIT toggle')
                buf=self.get_response('FT'+str(opt+2)+';')
                #print('SPLIT1: buf=',buf)
                return opt==1
                
            else:

                print('SPLIT_MODE: Invalid opt',opt)
                return -1
            
        elif self.rig_type2 in ['IC9700','IC7300']:
        
            if opt==-1:
                # Read current split setting
                cmd =  self.civ.icom_form_command([0x0f])  
                x=self.get_response(cmd)
                y=self.civ.icom_response(cmd,x)

                if VERBOSITY>0:
                    print('cmd=',show_hex(cmd))
                    print('x=',x)
                print('y=',y)

                return int( y[0],16 )
    
            elif opt<2:
                # Turn it on/off
                cmd =  self.civ.icom_form_command([0x0f,opt])  
                x=self.get_response(cmd)
                y=self.civ.icom_response(cmd,x)

                if VERBOSITY>0:
                    print('cmd=',show_hex(cmd))
                    print('x=',x)
                print('y=',y)
                
                return opt

            else:

                print('DIRECT SPLIT_MODE: Invalid opt',opt)
                return -1
            
        else:

            print('DIRECT SPLIT_MODE: Invalid rig',self.rig_type2)
            return -1
    
    
    # Routine to get/put fldigi squelch mode
    def squelch_mode99(self,opt):
        VERBOSITY=1
        if VERBOSITY>0:
            print('DIRECT_IO - SQUELCH_MODE: opt=',opt)

        print('DIRECT_IO: SQUELCH_MODE not available yet for DIRECT')
        return


    def init_keyer(self):
        #VERBOSITY=1
        
        if self.rig_type=='Hamlib':

            print('Keyer not yet supported for hamlib')
            return -1
            
        elif self.rig_type2 in ['IC9700','IC7300']:

            # Turn on full QSK
            cmd =  self.civ.icom_form_command([0x16,0x47,0x02])  
            x=self.get_response(cmd)
            y=self.civ.icom_response(cmd,x)
            if VERBOSITY>0:
                print('DIRECT INIT_KEYER: Full QSK: cmd=',show_hex(cmd))
                print('x=',x)
                print('y=',y)

            # Turn off DTR for SEND
            cmd =  self.civ.icom_form_command([0x1a,0x05,0x01,0x20,0x00])  
            x=self.get_response(cmd)
            y=self.civ.icom_response(cmd,x)
            if VERBOSITY>0:
                print('DIRECT INIT_KEYER: DTR off SEND: cmd=',show_hex(cmd))
                print('x=',x)
                print('y=',y)
            
            # Turn on DTR for CW
            cmd =  self.civ.icom_form_command([0x1a,0x05,0x01,0x21,0x03])  
            x=self.get_response(cmd)
            y=self.civ.icom_response(cmd,x)
            if VERBOSITY>0:
                print('DIRECT INIT_KEYER: DTR on CW: cmd=',show_hex(cmd))
                print('x=',x)
                print('y=',y)

            # Turn off DTR for RTTY
            cmd =  self.civ.icom_form_command([0x1a,0x05,0x01,0x22,0x00])  
            x=self.get_response(cmd)
            y=self.civ.icom_response(cmd,x)
            if VERBOSITY>0:
                print('DIRECT INIT_KEYER: DTR off RTTY: cmd=',show_hex(cmd))
                print('x=',x)
                print('y=',y)            
            
        else:

            print('INIT_KEYER: Invalid rig',self.rig_type2)
            return -1


    def read_speed(self):
        #VERBOSITY=1
        if VERBOSITY>0:
            print('DIRECT READing keyer SPEED ...',self.rig_type,self.rig_type2)

        if self.rig_type=='Yaesu' or self.rig_type1=='Yaesu' or \
           self.rig_type1=='Kenwood':
            
            if self.rig_type2=='TS850':
                print('DIRECT_IO - READ_SPEED - Not supported on TS-850 rig')
                wpm=0            
            
            buf = self.get_response('KS;')
            if buf[0:2]=='KS':
                try:
                    wpm=int(buf[2:5])
                except:
                    wpm=0
            else:
                wpm=0
                
        elif self.rig_type2 in ['IC9700','IC7300']:
            
            if self.rig_type=='FLRIG' and False:
                print('DIRECT READ_SPEED - Not available yet until we get ability to execute direct commands for ICOM under FLRIG')
                return 0
                
            cmd =  self.civ.icom_form_command([0x14,0x0C])  
            x=self.get_response(cmd)
            y=self.civ.icom_response(cmd,x)

            # The 9700 uses a goofy mapping:  0000->6wpm through 0255->48wpm
            try:
                val=bcd2int(y[1:],1)
                wpm=int( (48.-6.)/(255.-0)*val + 6 +0.5 )
            except Exception as e: 
                print('DIRECT READ_SPEED: Problem reading Rig CW Speed')
                print('e=',e,'\n')
                traceback.print_exc()
                wpm=0

                #if VERBOSITY>0:
                print('DIRECT READ SPEED: cmd=',show_hex(cmd))
                print('x=',x)
                print('y=',y)    # ,val,wpm )

        else:
            print('DIRECT READ SPEED - Unknown Rig Type:',self.rig_type)
            wpm=0            
            
        return wpm

    # Set sub-dial function on Yaesu rigs
    def set_sub_dial(self,func='CLAR'):
        VERBOSITY=1
        if VERBOSITY>0:
            print('DIRECT - SET SUB DIAL: func=',func,
                  '\tcurrent=',self.sub_dial_func)

        if self.rig_type1!='Yaesu':
            print('*** WARNING *** DIRECT SET SUB DIAL only available for Yaesu Rigs')
            return 0            
            
        if func=='CLAR':
            cmd='BY;SF5;'
        elif func=='VFO-B':
            cmd='BY;SF4;'
        else:
            self.sub_dial_func=None
            print('DIRECT_IO - SET_SUB_DIAL - Unknown Function',func)
            return
        
        buf = self.get_response(cmd)
        self.sub_dial_func=func
        if VERBOSITY>0:
            print('DIRECT - SET SUB DIAL: cmd=',cmd)
            print('DIRECT - SET SUB DIAL: buf=',buf)
        
        return


    # Function to read the clarifier
    def read_clarifier(self):
        if VERBOSITY>0:
            print('DIRECT_IO: READ_CLARIFIER ...')
        
        if self.rig_type1=='Kenwood' or self.rig_type1=='Icom':
            print('DIRECT_IO: READ_CLARIFIER not support yet for Kenwood/Icom rigs')
            return 0            

        buf = self.get_response('IF;')

        if self.rig_type2=='FT991a':
            p3=buf[15:20]
            p4=buf[20]
            p5=buf[21]
        else:
            p3=buf[13:18]
            p4=buf[18]
            p5=buf[19]

        shift=int(p3)
        rx=int(p4)*shift
        tx=int(p5)*shift
        
        if VERBOSITY>0:
            print('buf=',buf)
            print('p3=',p3)
            print('p4=',p4)
            print('p5=',p5)
            print('rx=',rx,'\ttx=',tx,'\tshift=',shift)
        
        return rx,tx    #,shift
        
    
    def set_speed(self,wpm):
        #VERBOSITY=1
        if VERBOSITY>0:
            print('DIRECT SETting keyer SPEED ...',self.rig_type,self.rig_type2,wpm)

        if self.rig_type=='Yaesu' or self.rig_type1=='Yaesu' or \
           self.rig_type1=='Kenwood':
            
            if self.rig_type2=='TS850':
                print('DIRECT_IO - SET_SPEED - Not supported on TS-850 rig')
                return
            
            cmd='BY;KS'+str(wpm).zfill(3)+';'
            buf = self.get_response(cmd)
                
        elif self.rig_type2 in ['IC9700','IC7300']:
            
            if self.rig_type=='FLRIG' and False:
                print('DIRECT SET_SPEED - Not available yet until we get ability to execute direct commands for ICOM under FLRIG')
                return
                
            # The 9700 uses a goofy mapping:  6wpm->0000  through 48wpm->0255
            z=int( 255./(48.-6.)*(wpm-6.) + 0.5 )
            z=min(255,max(z,0))
            bcd = int2bcd(z,2,1)
            
            cmd =  self.civ.icom_form_command([0x14,0x0C]+bcd)  
            x=self.get_response(cmd)
            y=self.civ.icom_response(cmd,x)
            
            if VERBOSITY>0:
                print('z=',z,'\twpm=',wpm,'\tbcd=',bcd)
                print('cmd=',show_hex(cmd))
                print('x=',x)
            print('y=',y)

        else:
            print('DIRECT SET SPEED - Unknown Rig Type:',self.rig_type)
            

    def read_meter(self,meter):
        #VERBOSITY=1
        if VERBOSITY>0:
            print('DIRECT READ_METER ...',meter)

        idx=3
        if self.rig_type1=='Icom' or  self.rig_type2=='Dummy':
            print('DIRECT_IO: Read meter not support yet for Icom rigs')
            return 0
            
        elif self.rig_type=='Kenwood':
            if meter=='S':
                cmd = 'SM;'
                idx=2
            elif meter=='Power':
                # Doesn't work - Because meter reads power when transmitting?
                #cmd = 'RM0;RM;'
                # Try this?
                cmd = 'SM;'
                idx=2
            elif meter=='SWR':
                #cmd = 'RM1;RM;'
                #buf = self.get_response(cmd,True)
                #print('buf=',buf)
                cmd='RM;'
            elif meter=='Comp':
                cmd = 'RM2;RM;'
            elif meter=='ALC':
                cmd = 'RM3;RM;'
            else:
                print('Unknown meter')
                return 0

            # The TS850 returns values between 0-30 - scale so 0-255 (like Yaesu)
            sc=255./30
            
        else:
            # Yaesu
            if meter=='S':
                cmd = 'RM0;'
            elif meter=='Power':
                cmd = 'RM5;'
            elif meter=='SWR':
                cmd = 'RM6;'
            elif meter=='Comp':
                cmd = 'RM3;'
            elif meter=='ALC':
                cmd = 'RM4;'
            else:
                print('Unknown meter')
                return 0

            sc=1.
                
        if VERBOSITY>0:
            print('DIRECT READ_METER cmd=',cmd,len(cmd))
        buf = self.get_response(cmd,True)
        if VERBOSITY>0:
            print('DIRECT READ_METER buf=',buf)
            #print('buf=',buf[idx:-1])
        meter = sc*int(buf[idx:-1])
        return meter
            

    # Function to control front-end reamp & attenuator
    def frontend(self,opt,pamp=0,atten=0):
        VERBOSITY=1
        if VERBOSITY>0:
            print('DIRECT FRONTEND: opt=',opt,'\tpamp=',pamp,'\tatten=',atten,
                  '\trig1=',self.rig_type1)
            
        if self.rig_type1=='Kenwood':
            
            print('DIRECT FRONTEND: Function not yet implemented for Kenwood rigs')
            return [0,0]

        elif self.rig_type1=='Icom':

            # Icom - assumes IC9700
            if opt==0:
                
                # Read current settings - need to test this
                cmd = self.civ.icom_form_command([0x16,0x02])       # Pre-amp
                x   = self.get_response(cmd)
                y   = self.civ.icom_response(cmd,x)                        
                #print('DIRECT FRONTEND: cmd =',show_hex(cmd))
                on_off1 = int(y[1],16)
                #print('DIRECT FRONTEND: y   =',y,on_off)

                cmd = self.civ.icom_form_command([0x11])            # Attenautor
                x   = self.get_response(cmd)
                y   = self.civ.icom_response(cmd,x)                        
                #print('DIRECT FRONTEND: cmd =',show_hex(cmd))
                on_off2 = int(y[1],16)
                #print('DIRECT FRONTEND: y   =',y,on_off)

                return [on_off1,on_off2]

            elif opt==1:
                
                # Set pre-amp and/or attenator
                if pamp in [0,1]:

                    print('DIRECT FRONT-END: Setting P-AMP on MAIN RX')
                    cmd = self.civ.icom_form_command([0x16,0x02,pamp])            # Pre-amp for main RX
                    x   = self.get_response(cmd)
                    y   = self.civ.icom_response(cmd,x)
                    print('DIRECT FRONTEND: y   =',y)

                    print('DIRECT FRONT-END: Swapping MAIN and SUB RXs')
                    cmd = self.civ.icom_form_command([0x07,0xB0])                 # Swap main & sub RXs
                    x   = self.get_response(cmd)
                    y   = self.civ.icom_response(cmd,x)
                    print('DIRECT FRONTEND: y   =',y)
                    
                    print('DIRECT FRONT-END: Setting P-AMP on SUB RX')
                    cmd = self.civ.icom_form_command([0x16,0x02,pamp])            # Pre-amp for sub RX
                    x   = self.get_response(cmd)
                    y   = self.civ.icom_response(cmd,x)
                    print('DIRECT FRONTEND: y   =',y)

                    print('DIRECT FRONT-END: Swapping MAIN and SUB RXs')
                    cmd = self.civ.icom_form_command([0x07,0xB0])                 # Swap main & sub RXs back
                    x   = self.get_response(cmd)
                    y   = self.civ.icom_response(cmd,x)                        
                    print('DIRECT FRONTEND: y   =',y)
                    
                if atten in [0,1]:         
                    
                    cmd = self.civ.icom_form_command([0x11,atten*0x10])            # Atten
                    x   = self.get_response(cmd)
                    y   = self.civ.icom_response(cmd,x)                        

            else:
                print('DIRECT FRONTEND: Unknown option',opt)
            
        else:

            # Assumes Yaesu
            if opt==0:
                # Read current settings - need to test this
                buf1=self.get_response('PA0;')
                buf2=self.get_response('RA0;')
                return [buf1,buf2]

            elif opt==1:
                # Build command to set pre-amp and/or attenator
                cmd='BY;'
                if pamp in [0,1,2]:
                    cmd = cmd+'PA0'+str(pamp)+';'
                if atten in [0,1,2,3]:         
                    cmd = cmd+'RA0'+str(atten)+';'

                # Do it
                buf=self.get_response(cmd)
                if VERBOSITY>0:
                    print('DIRECT FRONTEND: cmd=',cmd,'\nresponse=',buf)
                
            else:
                print('DIRECT FRONTEND: Unknown option',opt)
            

        
    
    # Function to control RIT
    def rit(self,opt,df=0,VFO='A'):
        #VERBOSITY=1
        if VERBOSITY>0:
            print('DIRECT RIT:',opt,df,VFO)
            
        if self.rig_type1=='Kenwood' or self.rig_type1=='Icom':
            print('SET_PLtone: Function not yet implemented for Kenwood and Icom rigs')
            return 0

        if opt==-1:
            # Read current rit setting - need to test this!
            buf1=self.get_response('RT;')
            buf2='0'
            return [buf1,buf2]
    
        elif opt<2:
            # Turn it on/off & adjust offset
            # For ftdx3000, df seems to offset from current rit, not abosolute shift
            if df>=0:
                #self.sock.send('RT1;RU0050;')
                p4 = str( df ).zfill(4)
                cmd='BY;RT'+str(opt)+';RU'+p4+';'
            else:
                p4 = str( -df ).zfill(4)
                cmd='BY;RT'+str(opt)+';RD'+p4+';'
            buf = self.get_response(cmd)

        else:

            print('DIRECT RIT: Invalid opt',opt)
            return -1



    # Function to get monitor level - see note below on set_mon_gain
    def get_monitor_gain(self):
        if self.rig_type1=='Kenwood' or self.rig_type1=='Icom':
            print('DIRECT - GET MONITOR GAIN: Function not yet implemented for Kenwood and Icom rigs')
            return 0
        
        buf = self.get_response('ML1;')
        if VERBOSITY>0:
            print('DIRECT_IO - GET_MONITOR_GAIN: buf=',buf,'\t',buf[3:6])
        try:
            return int( buf[3:6] )
        except:
            print('DIRECT_IO - Error in GET_MONITOR_GAIN: buf=',buf)
            return 0
    
        
    # Function to set monitor level and turn on the monitor
    # The doc for this isn't clear but it finally seems to work
    # Note - this seems different than menu item 035 which is General Monitor Level
    # We can acces the latter via EX035xxx command
    def set_monitor_gain(self,gain):
        #VERBOSITY=1
        if self.rig_type1=='Kenwood' or self.rig_type1=='Icom':
            print('DIRECT - SET MONITOR GAIN: Function not yet implemented for Kenwood and Icom rigs')
            return 0
        
        if VERBOSITY>0:
            print('DIRECT_IO - SET_MONITOR_GAIN: gain=',gain)
        if False:
            cmd  = 'ML0001;'
            buf=self.get_response(cmd)
            print('buf=',buf)
            time.sleep(0.1)
            cmd  = 'ML1030;'
            buf=self.get_response(cmd)
            print('buf=',buf)
                
        cmd  = 'ML0001;'+'ML1'+str(gain).zfill(3)+';ML1;'
        #cmd  = 'ML1'+str(gain).zfill(3)+';ML1;'
        #cmd  = 'ML1'+str(gain).zfill(3)+';'
        buf=self.get_response(cmd)
        if VERBOSITY>0:
            print('DIRECT_IO - SET_MONITOR_GAIN: cmd=',cmd,'\tbuf=',buf)
    
    # Need to fill this out
    def recorder(self,on_off=None):
        if False:
            print('DIRECT_IO RECORDER: Ignoring call')
        return False

    # Read rotor position - if at first we don't succeed, try try again
    def get_position(self):
        #VERBOSITY=1
        if VERBOSITY>0:
            print('DIRECT_IO Get Position...')
        if True:
            x = self.get_response('C\r')
            print('x=',x)
            x = self.get_response('C\r')
            print('x=',x)
            x = self.get_response('C\r')
            print('x=',x)
        
        ntries=0
        while ntries<3:
            x = self.get_response('C2\r')
            print('x=',x,ntries)
            try:
                pos = [float(x[3:6]),float(x[9:])]                
                if VERBOSITY>0:
                    print('\DIRECT - GET_POSITION:',pos)
                return pos
            except:
                ntries+=1
        else:
            print('\nDIRECT_IO - GET_POSITION - Unable to read rotor position')
            return [None,None]

            
        
# Empty structure
class blank_struct(direct_connect):
    def __init__(self):
        self.junk=None

    
