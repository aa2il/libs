############################################################################################
#
# Socket IO - Rev 1.0
# Copyright (C) 2021-4 by Joseph B. Attili, aa2il AT arrl DOT net
#
# This module contains socket I/O routines related to commanding the radio.
#
# The "BY;" at the beginning of some commands is to make sure the radio responses.
# Otherwise, hamlib takes much too long to respond.
#
# Notes on power control with the FT991a:
#    The command we need is DT GAIN under the F/M-LIST menu.
#    There doesn't appear to be a cat command for this.
#    We can probably control the audio gain via the OS:
#        Use   pacmd list-sinks     to get list of sink device - see pySDR/start_loopback
#        Use pactl -- set-sink-volume 12 90%  to set the volume of device 12 to 90%
#        Use pactl -- set-sink-volume 12 -10%  to decrease the volume of device 12 by 10%
#        etc
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
############################################################################################

import sys
import threading
from .fldigi_io import fldigi_xlmrpc,fllog_xlmrpc
import serial
import socket
from .ft_tables import *
from utilities import get_PIDs
import time
import numpy as np
from pprint import pprint

from .dummy_io import *
from .hamlib_io import *
from .direct_io import *

############################################################################################

# Crude debugging functions
import inspect

def whoami():
    print('SOCKET_IO - INSPECT:',inspect.stack()[2][3],
          '->',inspect.stack()[1][3] )

############################################################################################

VERBOSITY=0
DIGI_MODES=['PKTUSB','PKT-U','RTTY','PSK-U']

############################################################################################

# Routine to check if an app is running
def check_app(app):
    
    pids = get_PIDs(app)
    if len(pids)==0:
        print('*** ',app.upper(),' does not appear to be running ***')
    return pids

# Routine to find port for an fldigi connection
def find_fldigi_port(host,start,end,tag,required=True):
    pids = check_app('fldigi')
    sock=None
    if len(pids)==0:
        if required:
            print('*** Connection to FLDIGI required - exiting ***\n')
            sys,exit(0)
    else:
        print('FIND_FLDIGI_PORT: pids=',pids,' \t ports=',start,'-',end)
        for port in range(start,end+1):
            print('FIND_FLDIGI_PORT: Trying port',port,'...')
            sock1 = fldigi_xlmrpc(host,port,tag,1)
            if sock1.fldigi_active:
                print('FIND_FLDIGI_PORT: Found it on port',port)
                sock=sock1
                break
            else:
                print('...Nope...')
    return sock

# Top-level routine to open the connection
def open_rig_connection(connection,host=0,port=0,baud=0,tag='',
                        required=True,rig=None,force=False,quiet=False):

    if not quiet:
        print('SOCKET_IO: OPEN_RIG_CONNECTION: connection=',connection,'\trig=',rig, \
              '\thost=',host,'\tport=',port,'\ttag=',tag,'...')
        
    if connection=='NONE':
        return no_connect(host,port)

    if rig=='TYT9000d':
        print('HEY TYT!!!')
        sock = tyt9000d_connect()
        return sock

    if connection=='TS850' and force:
        #print('HEY',force)
        sock = direct_connect(850,baud,force)
        return sock

    if connection=='FLRIG' or connection=='ANY':

        ntries=0
        while ntries<5:
            ntries+=1
        
            pid = get_PIDs('flrig')
            if len(pid)==0:
                
                print('\n*** FLRIG does not appear to be running ***')
                print('pids=',pid)
                time.sleep(1)
                
            else:
            
                # Use xlmrpc server in FLRIG
                if port==0:
                    port = 12345;
                sock = fldigi_xlmrpc(host,port,tag)
                if sock.flrig_active:
                    return sock

        # If we get here, we couldn't open the connection
        if connection=='FLRIG':
            print('SOCKET_IO: Unable to activate required FLRIG connection - giving up')
            sys.exit(0)

    if connection=='FLDIGI' or connection=='ANY':
        pids = check_app('fldigi')
        if len(pids)==0:
            if connection=='FLDIGI':
                print('*** Connection to FLDIGI required - exiting ***\n')
                sys,exit(0)
                
        else:
            # Use xlmrpc server in FLDIGI 
            if port==0:
                port = 7362;
            print('Atempting to open FLDIGI',host,port,tag,'...')
            sock = fldigi_xlmrpc(host,port,tag)
            if connection=='FLDIGI' and not sock.fldigi_active and True:
                print('SOCKET_IO: Unable to activate FLDIGI connection - aborting')
                sys.exit(0)
            return sock
            
    if connection=='FLLOG':
        pid = get_PIDs('fllog')
        if len(pid)==0:
            print('\n*** FLLOG does not appear to be running ***')
            return no_connect(host,port)
            #print '*** Connection to FLLOG required - exiting ***\n'
            #sys,exit(0)

        else:
            # Use xlmrpc server in FLLOG
            sock = fllog_xlmrpc(host,port,tag)
            print(connection,sock.fllog_active)
            if connection=='FLLOG' and not sock.fllog_active and True:
                print('SOCKET_IO: Unable to activate FLLOG connection - aborting')
                sys.exit(0)
            return sock

    if connection=='HAMLIB' or connection=='ANY':
        # Hamlib daemon
        if port==0:
            if tag=='ROTOR':
                #port = 4533;
                pass
            else:
                port = 4532;
        sock = hamlib_connect(host,port,baud,tag)
        if sock.active:
            return sock
        elif connection=='HAMLIB' and required:
            print('SOCKET_IO: Unable to activate HAMLIB connection - aborting')
            sys,exit(0)

    if connection=='DIRECT' or connection=='ANY':
        if tag=='ROTOR':
            port=232
        elif rig:
            if rig=='FTdx3000':
                port=3000
            elif rig=='FT991a':
                port=991
            elif rig=='TS850':
                port=850
            elif rig=='IC706':
                port=706
            elif rig=='IC7300':
                port=7300
            elif rig=='IC9700':
                port=9700
            else:
                print('OPEN_RIG_CONNECTION: Unknown rig',rig)
                sys.exit(0)
        else:
            port=0
                
        # Direct connection to rig
        sock = direct_connect(port,baud)
        if sock.active or force:
            if False:
                print(port,baud,sock)
                pprint(vars(sock))
                sys.exit(0)
            
            if tag=='ROTOR':
                sock.send('C2\r')
                print(sock.recv(256))
            else:
                sock.send('FA;')
                print(sock.recv(256))
            return sock
        elif connection=='DIRECT':
            print('SOCKET_IO: Unable to activate DIRECT connection - aborting')
            sys,exit(0)

    print('\n*** Unable to open connection to rig via',connection,' route ***\n')
    return no_connect(host,port)


############################################################################################

# Function to send a command and get response
def get_response_OLD(s,cmd,wait=False):
    print('Sending CMD ... ',cmd)
    s.send(cmd)
    print('Waiting for response ...')
    buf = s.recv(1024).rstrip()
    print('...Got it',buf)

    return buf

############################################################################################

# Routine to set keyer speed of radio
def set_speed_old(sock,wpm):

    if VERBOSITY>0:
        print('Setting keyer speed ...',sock.rig_type,sock.rig_type2,wpm)
        
    if sock.active:
    
        if sock.rig_type=='Hamlib':
            cmd='L KEYSPD '+str(wpm)
            reply = sock.get_response(cmd)
            #print 'reply=',reply
            
        elif sock.rig_type=='Yaesu':
            cmd='KS'+str(wpm).zfill(3)+';'
            sock.send(cmd)

        else:
            print('*** SET_SPEED not yet implemented for rig type',sock.rig_type,sock.rig_type2)

            
    
############################################################################################

# Function to read radio status
def read_radio_status(sock,verbosity=0):

    if verbosity+VERBOSITY>0:
        print('Reading radio status...',sock.rig_type,sock.rig_type2)
        
    if sock.rig_type=='Kenwood':
        buf = sock.get_response("IF;",True)
        buf = strip_garbage(buf,'IF')
        #print 'IF: buf=',buf  
        #sock.freq = int( buf[2:13] )*1e-3
        sock.freq = int( buf[2:13] )
        sock.mode = Decode_Mode(buf[29])
        # Keyer speed is not available in Kenwood command set
        #filts = sock.get_filters()
        #sock.filt1 = filts[0]
        #sock.filt2 = filts[1]
        
    else:
        sock.freq = sock.get_freq()
        sock.mode = sock.get_mode()
        sock.pl_tone = sock.get_PLtone()
        if sock.rig_type=='Yaesu':
            wpm = sock.read_speed()
            if wpm>0:
                sock.wpm=wpm

    sock.filt = sock.get_filters()
    #sock.band = str( sock.get_band(sock.freq * 1e-6) ) + 'm'
    #print('frq=',sock.freq*1e-6)
    b=sock.get_band(sock.freq * 1e-6)
    if isinstance(b, str):
        sock.band = b
    else:
        sock.band = str( b ) + 'm'

    
# Legacy Function to read radio status
def get_status(self):

    s=self.sock
    print("\n++++++++++++++++++ Reading status ... ",s.connection,s.rig_type,s.rig_type1,s.rig_type2)

    if s.rig_type=='Hamlib' or s.rig_type=='FLDIGI' or s.rig_type=='FLRIG':

        frq  = s.get_freq() * 1e-3
        mode = s.get_mode()
        ant  = s.get_ant()
        read_mic_gain(self)
        print(("GAIN: %d" % self.gain))
        try:
            self.slider1.set(self.gain)
        except:
            pass
        print('Get Status:',frq,mode,ant)
        
    elif s.rig_type1=='Kenwood':
        # The Kenwood command set is similar to Yaesu's but not as flush
        buf=self.sock.get_response("IF;",True)
        buf = strip_garbage(buf,'IF')
        #print 'IF: buf=',buf  
        frq = int( buf[2:13] )*1e-3
        mode = Decode_Mode(buf[29])
        ant = 1

    elif s.rig_type1=='Icom':
        # Icom's commands are quite different
        #print 'ICOM;;;;;;;;;'
        frq  = s.get_freq() * 1e-3
        mode = s.get_mode()
        ant  = 1
        
    else:
        # Assume Yaesu command set - Get freq
        if True:
            # This works - need to get get_freq working on all connections (fldigi?)
            buf=self.sock.get_response("FA;")
            if VERBOSITY>0 or True:
                print('GET_STATUS: buf=',buf,buf[2:-1]) 
            frq = int( buf[2:-1] )*1e-3
            #print 'frq=',frq
        else:
            # So does this but requires more functions in class defs
            frq = s.get_freq() * 1e-3
            print('frq=',frq)

        # Get mode
        if True:
            # This works - need to get get_freq working on all connections
            buf=self.sock.get_response("MD0;")
            m=buf[3]
            if VERBOSITY>0:
                print('buf=',buf,m)
            mode = Decode_Mode(m)
        else:
            # So does this but requires more functions in class defs
            mode=s.get_mode()

        # Decode antenna
        ant=s.get_ant()

            
    print("Mode,frq=",mode,frq)
    if mode=='USB' or mode=='LSB':
        mode='SSB'
    elif mode in DIGI_MODES:
        mode='RTTY'

    # Save these
    #x=str(frq)+' KHz  '+str(mode)
    x = format(frq,',.3f')+' KHz  '+str(mode)

    # Decode which band
    if frq>=1200000 and frq<=1400000:
        b='23cm'
    elif frq>=900000 and frq<=930000:
        b='33cm'
    elif frq>=420000 and frq<=450000:
        b='70cm'
    elif frq>=220000 and frq<230000:
        b='1.25m'
    elif frq>=140000 and frq<150000:
        b='2m'
    elif frq>49900 and frq<54500:
        b='6m'
    elif frq>27800 and frq<30000:
        b='10m'
    elif frq>24000 and frq<25000:
        b='12m'
    elif frq>20900 and frq<22000:
        b='15m'
    elif frq>17000 and frq<19000:
        b='17m'
    elif frq>13900 and frq<15000:
        b='20m'
    elif frq>9800  and frq<11000:
        b='30m'
    elif frq>6500 and frq<8000:
        b='40m'
    elif frq>3300 and frq<5000:
        b='80m'
    elif frq>1700 and frq<2100:
        b='160m'
    else:
        b='0'

    try:

        # Legacy
        print('Legacy BAND.SET ... b=',b)
        self.band.set(b)
        if frq>1600 or frq<500:
            self.station.set(0)
        self.status.set(x)
        self.frequency=frq
        self.mode.set(mode)
        self.ant.set(ant)

    except:
        print('Legacy failed BAND.SET ... b=',b)
        self.band=b
        self.freq=frq
        self.mode=mode
        
    print('++++++++++++++++ Get Status - Done.\n')

############################################################################################

# Function to manipulate VFOs
# Attempting t use flrig commands but so far no very stable
def SetVFO(self,cmd):
    s=self.sock
    print('SOCKET IO->SetVFO: cmd=',cmd,'\t',s.rig_type,'\t',s.rig_type1)

    if cmd=='A':
        if s.rig_type1=='Icom':
            print('SetVFO - Select A - Not implemented on ICOM rigs yet')
        else:
            self.sock.get_response("BY;FR0;FT2;")
    
    elif cmd=='B':
        if s.rig_type1=='Icom':
            print('SetVFO - Select A - Not implemented on ICOM rigs yet')
        else:
            self.sock.get_response("BY;FR4;FT3;")
    
    elif cmd in ['A','B']:
        for itry in range(5):
            s.set_vfo(cmd)
            time.sleep(DELAY)
            s.split_mode(0)
            time.sleep(DELAY)
            vfo = s.get_vfo()
            time.sleep(DELAY)
            print('SOCKET IO->SetVFO: cmd=',cmd,'\titry=',itry,'\tvfo=',vfo)
            if vfo==cmd:
                break
        ClarReset(self,True)
        time.sleep(DELAY)
            
    #elif cmd in ['SPLIT']:
    #    s.set_vfo(rx='A',tx='B')
    #elif cmd in ['A->B','A<->B']:
    #    s.set_vfo(op=cmd)
    
    elif cmd=='A->B':
        if s.rig_type1=='Icom':
            print('SetVFO - Select A->B - Not implemented on ICOM rigs yet')
        else:
            self.sock.get_response("BY;AB;")
    elif cmd=='B->A':
        if s.rig_type1=='Icom':
            print('SetVFO - Select B->A - Not implemented on ICOM rigs yet')
        else:
            self.sock.get_response("BY;BA;")
    elif cmd=='A<->B':
        if s.rig_type1=='Icom':
            print('SetVFO - Select A<->B - Not implemented on ICOM rigs yet')
        else:
            self.sock.get_response("BY;SV;")
    elif cmd=='SPLIT':
        if s.rig_type1=='Icom':
            print('SetVFO - Select SPLIT - Not implemented on ICOM rigs yet')
        else:
            self.sock.get_response("BY;FT3;")
    elif cmd=='TXW':
        if s.rig_type1=='Icom':
            print('SetVFO - TXW - Not implemented on ICOM rigs yet')
        else:
            txw=self.sock.get_response("TS;")
            print('TXW=',txw)
            if txw=='TS0;':
                self.sock.get_response("BY;TS1;")
            else:
                self.sock.get_response("BY;TS0;")
    else:
        print('SetVFO: Invalid command - ',cmd)

# Function to reset clarifier
def ClarReset(self,RXClarOn=False):
    VERBOSITY=1
    if VERBOSITY>0:
        print('Clarifier reset ...',RXClarOn)
    if self.sock.rig_type1=='Kenwood' or self.sock.rig_type1=='Icom':
        print('CLARIFIER RESET not available in',self.sock.rig_type,'command set')
        return
    if self.sock.rig_type=='Hamlib' and True:
        # These arent working quite right in latest hamlib - patched
        print('\n**** WARNING **** CLARIFIER RESET is flaky in hamlib - needs some attention! ***\n')
        if RXClarOn:
            self.sock.get_response('U RIT 1')
        else:
            self.sock.get_response('U RIT 0')
        self.sock.get_response('U XIT 0')
        self.sock.get_response("J 0")
        self.sock.get_response("Z 0")
        self.sock.get_response("J 0")             # This is the problem child and needs to be repeated for some reason
    else:
        # Yaesu rigs
        if RXClarOn:
            cmd="BY;RC;RT1;XT0;"
        else:
            cmd="BY;RC;RT0;XT0;"
        self.sock.get_response(cmd)
        #self.sock.set_sub_dial('CLAR')
        time.sleep(DELAY)
        SetSubDial(self)
    if VERBOSITY>0:
        print('Clarifier reset done.')

# Function to set sub=dial on FTdx3000
def SetSubDial(self,opt='CLAR'):
    VERBOSITY=1
    if VERBOSITY>0:
        print('Setting Sub-dial ...',opt)
    self.sock.set_sub_dial(opt)

        
# Function to set TX split
def SetTXSplit(self,df_kHz,onoff=True):
    max_df=9999
    df=max( min(max_df, int( df_kHz*1000 ) ) , -max_df)
    if self.sock.rig_type=='Hamlib' and True:
        
        if onoff:
            print('Set TX CLARIFIER SPLIT: *ON* df=',df)
            self.sock.get_response('U RIT 1')
            self.sock.get_response("Z "+str(df))
        else:
            print('Set TX CLARIFIER SPLIT: *OFF* df=',0)
            self.sock.get_response('U RIT 0')
            self.sock.get_response("Z 0")
            
    else:
        
        if onoff:
            cmd = 'BY;RC;RT0;XT1;RU'+str(df).zfill(4)+';'
        else:
            cmd = 'BY;RC;RT0;XT0;'
            
        print('Set TX CLARIFIER SPLIT: df=',df,'\tcmd=',cmd)
        self.sock.get_response(cmd)

# Function to get split settings (clarifier)
#def GetSplit(self,df_kHz):
#    df=int( df_kHz*1000 )
#    cmd = 'BY;RC;RT0;XT1;RU'+str(df).zfill(4)+';'
#    print('CLARSPLIT:',df,cmd)
#    self.sock.get_response(cmd)

# Function to get rig info
def GetInfo(self):
    if VERBOSITY>0:
        print('GetInfo ...')

    if self.sock.rig_type1=='Kenwood' or self.sock.rig_type1=='Icom' or \
       self.sock.rig_type=='Hamlib' or self.sock.rig_type=='FLDIGI' or \
       self.sock.rig_type=='FLRIG':
        #print('GET INFO not (yet) fully implemented for rig type', \
        #    self.sock.rig_type)
        try:
            frx = 1e-3*self.sock.get_freq()
        except:
            whoami()
            print('******* SOCKET_IO - GetInfo - Unxcepted error')
            frx=0
        return (frx,frx)

    # Yaesu - Query rig
    frx=0
    ftx=0
    buf=self.sock.get_response('IF;')

    # Strip off any leading garbage (e.g. ?;)
    idx = buf.find('IF')
    #print 'GetInfo: buf=',buf,idx,len(buf)
    
    if idx>=0:
        #buf=IF12707023955+333201340000;
        buf=buf[idx:]
        #P1=buf[2:5]         # Mem chan
        P2=buf[5:13]         # VFO A
        P3=buf[13:18]        # Clarifier dir & offset
        P4=buf[18]           # RX Clar off/on
        P5=buf[19]           # TX Clar off/on
        P6=buf[20]           # Mode
        #P7=buf[21]          # Other stuff - see manual
        #P8=buf[22]
        #P9=buf[23:25]
        #P10=buf[25]
        
        MODES=[None,'LSB','USB','CW','FM','AM','FSK (RTTY-LSB)','CW-R', \
               'PKT-L','FSK-R (RTTY-USB)','PKT-FM','FM-N','PKT-U']

        # Compute RX & TX freqs including clarifier offset
        frx = .001*( float(P2) + int(P4)*float(P3) )
        ftx = .001*( float(P2) + int(P5)*float(P3) )

        if False:
            print('GetInfo: IF=',buf)
            print('VFO A     =',P2,'Hz =',float(P2)/1000.,'KHz')
            print('Clarifier =',P3,'Hz =',float(P3),'Hz')
            print('RX/TX clar on/off:',P4,P5)
            print('Mode=',P6,'=',MODES[int(P6)])
            print(' ')
    
    return (frx,ftx)

# Function to reset rx attenuator
def AttenReset(self):
    self.sock.get_response("BY;RA00;")

############################################################################################

# Callback to select antenna
def SelectAnt(self,a=None):
    #print 'SelectAnt:',a
    s = self.sock
    if not a:
        a  = self.ant.get()
    print("\n%%%%%%%%%% Select Antenna: Setting Antenna =",a,"%%%%%%%%")
    #buf=self.sock.get_response('BY;AN0'+str(a)+';')
    buf=self.sock.set_ant(a)

############################################################################################

# Callback to select operating band
def SelectBand(self,b=None,m=None,df=0):
    s = self.sock
    print('\nSelectBand b0',b,self.band)
    if not b:
        try:
            b = self.band.get()
            print('SelectBand b1',b)
        except:
            b = s.band
            print('SelectBand b2',b)

    code = bands[b]["Code"]
    #print code
    gain = bands[b]["MicGain"]

    if not m:
        try:
            m = self.mode.get()
        except:
            m = s.mode
            
        if m=='':
            m = s.get_mode()

    print("%%%%%%%%%% Select band: Setting band ... b=",b,"  m=",m,"  df=",df,"%%%%%%%%",s.rig_type)
    
    if s.rig_type1=='Kenwood' or s.rig_type1=='Icom' or s.rig_type=='Hamlib':
        # The TS850 command set does not have a band select so we fake it by setting a freq
        # Likewise, our implementation of hamlib is limited.
        if True:
            if m=='LSB' or m=='USB' or m=='FM':
                m='SSB'
            frq = bands[b][m+'1']+df
            print('Setting freq to',frq)
            s.set_freq(frq,'A')

            # There can be a delay before freq change is actually accomplished
            if s.rig_type=='Hamlib' and False:
                frq2=0
                while np.abs(frq2-frq)>10:
                    frq2 = s.get_freq()*1e-3
                    print('Readback frq=',frq,frq2,frq-frq2)
        else:
            frq = int( (bands[b][m+'1']+df) * 1000 )
            #print s.rig_type,frq
            cmd = 'FA'+str(frq).zfill(11)+';'           # Tune to lower sub-band edge
            buf = s.get_response(cmd)
            
        get_status(self)
        #self.band = b
        #self.freq = frq
        #self.mode = m
        
        return
    
    else:

        # Yaesu
        cmd1 = 'BY;BS'+str(code).zfill(2)+';'          # Band select
        cmd2 = 'BY;MS3;'                               # Set meter to SWR
        if s.rig_type2=='FT991a':
            cmd3 = 'BY;MG'+str(gain).zfill(3)+';'      # Set input audio level for digital modes??
        else:
            cmd3 = 'BY;EX076'+str(gain).zfill(4)+';'   # Set input audio level for digital modes
        
    print(("SELECT BAND: Setting Band cmd1=-%s- ..." % cmd1))
    buf=s.get_response(cmd1)
    print('buf=',buf)
    s.band = b

    # Do it on the other VFO also
    #if self.sock.connection=='DIRECT' and s.rig_type2!='FT991a':
    if self.sock.connection=='DIRECT':
        time.sleep(DELAY)
        vfo = self.sock.get_vfo()
        print(("SELECT BAND:", vfo))
        if vfo[0]=='A':
            self.sock.set_vfo('B')
        else:
            self.sock.set_vfo('A')
        buf=self.sock.get_response(cmd1)
        self.sock.set_vfo(vfo[0])

    print('\nReseting Clarifier...')
    ClarReset(self)                         # Reset clarifier
    print('\nReseting Attenuator...')
    AttenReset(self)                        # Reset attenuator
    
    print(("\nSetting meter -%s- ..." % cmd2))
    buf=self.sock.get_response(cmd2)        # Set meter to SWR
    print("\nSetting Roofing Filter ...")
    if m=='':
        m = s.get_mode()
    SetFilter(self,b,m)                         # Set roofing filter
    
    print(("\nSetting audio level -%s- ..." % cmd3))
    buf=self.sock.get_response(cmd3)
    try:
        self.slider1.set(gain)
        self.station.set(0)
        self.mode.set('')
        get_status(self)
    except:
        pass
    
    print("%%%%%%%%%%%%%%%% Select Band - Done. %%%%%%%%%%%%%%%%%%%%%%%%%%")

############################################################################################

# Callback to select operating mode
def SelectMode(self,b=None,m=None):
    s=self.sock
    #print('SelectMode',self.mode)  # ,self.TxT
    if not m:
        m = self.mode.get()
    elif m=='':
        m = s.get_mode()

    if self.sock.rig_type=='Hamlib' or self.sock.rig_type1=='Icom':
        split=self.sock.split_mode(-1)
        print("\n=-=-=- Select Mode:",b,m,self.sock.connection,'\tSplit=',split)
        if split:
            self.sock.set_mode(m,VFO='A')
            self.sock.set_mode(m,VFO='B')
        else:
            self.sock.set_mode(m)
        
        get_status(self)
        return
        
    c = modes[m]["Code"]

    try:
        frq = self.frequency
    except:
        frq = 1e-3*s.get_freq()
        
    print("\n=== Select Mode:",b,m,c,frq,self.sock.connection)
    if m=='SSB':
        if s.rig_type!='Kenwood' and  self.sock.rig_type!='Hamlib' and self.rig_type2!='FT991a':
            buf=self.sock.get_response('BY;EX1030;');            # Audio from MIC (front)
        if frq<10000:
            c='01'
            print('LSB')
        else:
            print('USB')

    if s.rig_type1=='Kenwood':
        cmd  = 'MD'+c[1]+';'
    else:
        cmd  = 'BY;MD'+c+';'
    buf=self.sock.get_response(cmd)
    print(("Setting Mode cmd=-%s- : buf=-%s-" % (cmd,buf) ))
    self.sock.set_mode(m)

    # Do it on the other VFO also
    if self.sock.connection=='DIRECT':
        vfo = self.sock.get_vfo()
        if vfo=='A':
            self.sock.set_mode(m,'B')
        else:
            self.sock.set_mode(m,'A')
        self.sock.set_vfo(vfo)
    
    SetFilter(self,b,m)                            # Set roofing filter
    SetPower(self,b,m)                             # Set max tx power
    if m=='RTTY':
        buf=self.sock.get_response('BY;GT03;');    # Slow AGC for digi modes
    elif m=='PSK':
        b = self.band.get()
        buf=self.sock.get_response('BY;GT03;');    # Slow AGC for digi modes
        frq = bands[b]['PSK']
        s.set_freq(frq)
    elif m=='WSJT':
        # Slow AGC for digi modes & Audio from USB port
        if rig_type2=='FT991a':
            buf=self.sock.get_response('BY;GT03;');
        else:
            buf=self.sock.get_response('BY;GT03;EX1032;');   
    else:
        buf=self.sock.get_response('BY;GT02;');                # Mid AGC is a good choice for other modes

    try:
        get_status(self)
        m2 = self.mode.get()
        print("m =",m)
        print("m2=",m2)
        if m=='PSK' and m2=='RTTY':
            self.mode.set(m)
    except:
        pass

    print("=== SELECT MODE Done ===")

############################################################################################

# Function to select one of the push button radio stations
def SelectStation(self):
    s=self.sock
    frq=self.station.get()
    print("SELECT STATION: Setting Station frq=",frq)
    s.set_freq(frq)
    s.set_mode('AM')
    get_status(self)

############################################################################################

# Function to set filter bandwith
def SetFilter(self,b=None,m=None):
    s = self.sock
    if not b:
        try:
            b = self.band.get()
        except:
            b = s.get_band()
    if not m:
        try:
            m = self.mode.get()
        except:
            m = s.get_mode()
    print("\nSetFilter: band=",b,'\tmode=',m)
    
    if self.ContestMode:
        filt = modes[m]["Filter2"]
        buf=self.sock.get_response("BY;NA01;")
    else:
        filt = modes[m]["Filter1"]
        buf=self.sock.get_response("BY;NA00;")  
    if m!="AM" and self.sock.rig_type2=='FTdx3000':
        buf=self.sock.get_response("BY;RF"+filt+";")             # Roofing filter
        if m=='CW':
            buf2=self.sock.get_response("BY;SH004;")              # Bandwidth
        print("SetFilter:",self.ContestMode,filt)

############################################################################################

# Function to set output power
def SetPower(self,b=None,m=None):
    s=self.sock
    if not b:
        b = self.band.get()
    if not m:
        m = self.mode.get()
    print("\nSetPower:",b,m)

    if m=='WSJT':
        set_tx_pwr(self,5)
    else:
        set_tx_pwr(self,99)

    return

    if rig_type2=='FT991a':
        cmd='EX137'
    else:
        cmd='EX177'
        
    if m=='WSJT':
        buf=self.sock.get_response('BY;'+cmd+'005;');              # Set max power to 5W
    else:
        buf=self.sock.get_response('BY;'+cmd+'099;');              # Set max power to 99W

############################################################################################

# Functions related to reading and setting microphone gain
def set_tx_pwr(self,tx_pwr=None):
    s = self.sock
    if not tx_pwr:
        tx_pwr = self.tx_pwr
    print(("SET_TX_PWR: Setting TX Power %s " % tx_pwr))

    if s.rig_type1=='Kenwood' or s.rig_type1=='Icom':
        print('SET_TX_POWER not available in',s.rig_type,s.rig_type2,'command set')
        return
    
    elif s.rig_type=='Hamlib':
        # Hamlib had a goofy mapping for which .388 seems to correspond to 99W so go with it
        # cmd  = 'L RFPOWER ' + str(0.388*float(tx_pwr)*0.01)
        # not any more, just looks like 0 to 1
        cmd  = 'L RFPOWER ' + str(float(tx_pwr)*0.01)
        buf=self.sock.get_response(cmd)
        print('cmd=',cmd)
        print('reply=',buf)

    else:
        cmd  = 'BY;PC'+str(tx_pwr).zfill(3)+';' 
        buf=self.sock.get_response(cmd)
        
    print('TX Power set.')

    
def set_mic_gain(self,gain=None):
    s = self.sock
    if s.rig_type1=='Kenwood' or s.rig_type1=='Icom' or \
       (s.rig_type=='Hamlib' and s.rig_type2!='FTdx3000' and s.rig_type2!='FT991a'):
        print('SET_MIC_GAIN not available in',s.rig_type,s.rig_type2,'command set')
        return
    
    if not gain:
        gain = self.gain

    mode=s.get_mode()
    print("SET_MIC_GAIN: Setting Mic Gain to",gain,mode)
    if mode=='CW':
        # There's no mic gain to set in CW!
        return
    
    elif mode in DIGI_MODES:
        if s.rig_type2=='FT991a':
            cmd = 'BY;'                                # No-op since what we really need isn't available
            #cmd = 'BY;EX073'+str(gain).zfill(3)+';'   # Set input audio level for digital modes - nope
            #cmd = 'BY;EX049'+str(gain).zfill(3)+';'   # Set input audio level for digital modes - nope
            # What we really want is to control the "DT GAIN" under F-LIST but there doesn't seem to be any
            # CAT command for this - ugh!  See comments at top for how to proceed
        else:
            cmd = 'BY;EX076'+str(gain).zfill(4)+';'   # Set input audio level for digital modes
    else:
        cmd = 'BY;MG'+str(gain).zfill(3)+';'       # Set input audio level for voice modes
        
    print('cmd=',cmd)
    buf = s.get_response(cmd)
    print('Mic Gain set - buf=',buf)


    
def set_mon_level(self,gain=None):
    s = self.sock
    if s.rig_type1=='Kenwood' or s.rig_type1=='Icom':
        print('SET_MON_LEVEL not available in',s.rig_type,s.rig_type2,'command set')
        return
    if not gain:
        gain = self.mon_level
    print(("SET_MON_LEVEL: Setting Monitor Level Gain %s " % gain))


    self.sock.set_monitor_gain(gain)
    #print('-------------------------------------- Mon Level=',self.mon_level)
    return 

    # Old obsolete code
    #cmd  = 'BY;EX035'+str(gain).zfill(3)+';' 
    cmd  = 'BY;ML1'+str(gain).zfill(3)+';' 
    buf=self.sock.get_response(cmd)
    print('Monitor level set.')

    
def read_monitor_level(self):
    s = self.sock
    self.mon_level=0
    if s.rig_type1=='Kenwood' or s.rig_type1=='Icom':
        print('READ_MONITOR_LEVEL not available in',s.rig_type,s.rig_type2,'command set')
        return self.mon_level

    self.mon_level = self.sock.get_monitor_gain()
    #print('-------------------------------------- Mon Level=',self.mon_level)
    return  self.mon_level

    # Old obsolete code
    print("Reading Monitor level ...")
    Done=False
    itries=0
    while not Done:
        if True:
            buf=self.sock.get_response('ML1;')
            print("buf=",buf)
            try:
                self.mon_level = int(buf[3:6])
                Done = True
            except:
                itries+=1
                Done = itries>5
        else:
            buf=self.sock.get_response('EX035;')
            print("buf=",buf)
            try:
                self.mon_level = int(buf[5:8])
                Done = True
            except:
                itries+=1
                Done = itries>5
    print(("... Read Monitor Level = -%d-" % self.mon_level))
    return self.mon_level


def read_tx_pwr(self):
    self.tx_pwr = 0
    s = self.sock
    if s.rig_type2=='TS850' or s.rig_type1=='Icom':
        print('SOCKET_IO: READ_TX_PWR not available in',s.rig_type1,s.rig_type2,
              'command set')
        return self.tx_pwr

    print("&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&& Reading TX Power ...")
    if s.rig_type=='Hamlib':
        buf=self.sock.get_response('l RFPOWER')
        print("SOCKET_IO: READ_TX_PWR: buf=",buf)
        # Hamlib had a goofy mapping for which .388 seems to correspond to 99W so go with it
        # self.tx_pwr = min( 99, int(100.*float(buf)/.388235) )
        # Now, it looks like scale is from 0 to 1:
        self.tx_pwr = min( 99, int(100.*float(buf)) )
        return self.tx_pwr
        
    else:
        Done=False
        itries=0
        while not Done:
            buf=self.sock.get_response('PC;')
            print("buf=",buf)
            try:
                self.tx_pwr = int(buf[2:5])
                Done = True
            except:
                itries+=1
                Done = itries>5
                
    print(("... Read TX Power = -%d-" % self.tx_pwr))
    return self.tx_pwr


def read_mic_gain(self):
    s = self.sock
    self.gain=0
    if s.rig_type1=='Kenwood' or s.rig_type1=='Icom' or \
       (s.rig_type=='Hamlib' and s.rig_type2!='FTdx3000' and s.rig_type2!='FT991a'):
        print('READ_MIC_GAIN not available in',s.rig_type,s.rig_type2,'command set')
        return self.gain

    mode=s.get_mode()
    print("SOCKET_IO: READ_MIC_GAIN - Reading Mic Gain ...",mode)
    if mode=='CW':
        # There's no mic gain to set in CW!
        return 0
    
    elif mode in DIGI_MODES:
        if s.rig_type2=='FT991a':
            #cmd = 'BY;EX073;'   # Get input audio level for digital modes - nope
            cmd = 'EX073;'   # Get input audio level for digital modes - nope
        elif s.rig_type2=='FTdx3000':
            #cmd = 'BY;EX076;'   # Get input audio level for digital modes
            cmd = 'EX076;'   # Get input audio level for digital modes
        else:
            print('\n******* SOCKET_IO READ_MIC_GAIN: Unknown rig type - giving up',s.rig_type2,'\n')
            sys.exit(0)
    else:
        cmd = 'MG;'       # Get input audio level for SSB
    
    Done=False
    itries=0
    while not Done:
        buf=self.sock.get_response(cmd)
        print("cmd=",cmd,"\t\tbuf=",buf)
        try:
            if cmd=='MG;':
                self.gain = int(buf[2:5])
            elif cmd=='EX073':
                self.gain = int(buf[5:8])
            else:
                self.gain = int(buf[5:9])
            Done = True
        except:
            itries+=1
            Done = itries>5
                
    print(("... Read Mic Gain = -%d-" % self.gain))
    return self.gain


def Read_Meter(self,i):
    print('SOCKET_IO: Read Meter:',i,METERS[i]," ...")
    s = self.sock
    Done=False
    itries=0
    while not Done:
        buf=self.sock.get_response('RM'+str(i)+';')
        print("buf=",buf)
        try:
            val=int(buf[3:6])
            Done = True
        except:
            itries+=1
            Done = itries>5
    print(("... Read Mic Gain = -%d-" % val))
    return val

############################################################################################

# Functions related to setting sub-band freqs (arrows on gui)
def SetSubBand(self,iopt):
    print('\nSET SUB-BAND: iopt=',iopt)
    s=self.sock

    try:
        b = self.band.get()
        m = self.mode.get()
        print('1: b=',b)
        print('1: m=',m)
    except:
        #b = str( s.get_band() ) + 'm'
        #m = s.get_mode()
        b = self.band
        m = self.mode
        print('2: b=',b)
        print('2: m=',m)

    if b[-1]!='m':
        b+='m'
        
    if iopt==1:
        frq = bands[b][m+'1'] 
    elif iopt==2:
        frq1 = bands[b][m+'1']
        frq2 = bands[b][m+'2']
        frq  = (frq1+frq2)/2.
    elif iopt==3:
        frq = bands[b][m+'2'] 
    print("\nSET SUBBAND: Setting subband:",b,m,frq)

    s.set_freq(frq,'A')
    s.set_freq(frq,'B')
    #print("Shifting to low end -%s- :" % cmd)
    #buf=self.sock.get_response(cmd)

    try:
        get_status(self)
    except:
        pass
    print("Done. ")




# Adjust mic gain level
def Auto_Adjust_Mic_Gain(self,sock=None):
    print('\nSOCKET_IO -> AUTO_ADJUST_MIC_GAIN ...')
    if not sock:
        s=self.sock
    else:
        s=sock

    # Some apps have multiple sockets, e.g. for SO2V
    try:
        s1=self.sock1
    except:
        s1=None

    print("SOCKET_IO: Auto adjusting mic gain ...",s.connection,s1)
            
    # Try to key the radio
    NTRYS=10
    for ntry in range(NTRYS):

        # Key the tx
        if s.connection=='FLDIGI':
            s.tune(True)
        elif s1:
            s1.tune(True)
        else:
            print('*** PTT ON ...')
            s.ptt(True)
        time.sleep(.1)

        # Check if in tune mode by reading power meter
        pwr = Read_Meter(self,5)
        print("POWER=",pwr)
        if pwr==0:
            print("*** TUNE command did not appear to work ***",ntry)
        else:
            break
        
    else:     

        # Never got a valid power reading - give up
        print("*** Need to press TUNE button ***\n")
        if s.connection=='FLDIGI':
            s.tune(False)
        elif s1:
            s1.tune(False)
        else:
            print('*** PTT OFF ...')
            s.ptt(False)

        print('*** Giving up ***')
        return

    swr = Read_Meter(self,6)
    print("SWR=",swr)
    alc = Read_Meter(self,4)
    print("ALC=",alc)
    read_mic_gain(self)

    # Increase gain until ALC starts to kick in
    ALC_THRESH=10
    while alc<=ALC_THRESH:
        self.gain=self.gain+1
        print(("GAIN: %d" % self.gain))
        set_mic_gain(self)

        time.sleep(DELAY)
        alc = Read_Meter(self,4)
        print("ALC=",alc)
        #                self.slider.set(self.gain)
        
    # Back off until ALC doesn't kick in
    while alc>ALC_THRESH:
        self.gain=self.gain-1
        print(("GAIN: %d" % self.gain))
        set_mic_gain(self)
        
        time.sleep(DELAY)
        alc = Read_Meter(self,4)
        print("ALC=",alc)
        #                self.slider.set(self.gain)

    pwr = Read_Meter(self,5)
    print("POWER=",pwr)

    try:
        self.slider1.set(self.gain)
    except:
        self.mic_slider.setValue(self.gain)
        
    # Unkey TX
    time.sleep(DELAY)
    if s.connection=='FLDIGI':
        s.tune(False)
    elif s1:
        s1.tune(False)
    else:
        s.ptt(False)
        
    print("Done.")



