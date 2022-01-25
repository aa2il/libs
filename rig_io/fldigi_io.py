############################################################################################
#
# Fldigi IO - Rev 1.0
# Copyright (C) 2021 by Joseph B. Attili, aa2il AT arrl DOT net
#
# Functions to control rig through FLDIGI or FLRIG from python.
# See methods.txt for list of methods for these two protocols
#
# To Do:
#    This was originally developed for use with fldigi and flrig was added as an after though.
#    As is turns out, flrig is very good for rig control and is becomeing my main pathway.
#    Should therefore separate capability for flrig into its own module
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
if sys.version_info[0]==3:
    from xmlrpc.client import ServerProxy, Error
else:
    from xmlrpclib import ServerProxy, Error
    
from .direct_io import direct_connect
import threading
import time
from .util import *
import socket
from .ft_tables import DELAY, Decode_Mode, modes
import re
from .icom_io import icom_civ, show_hex

################################################################################################

VERBOSITY=0

################################################################################################

class fldigi_xlmrpc(direct_connect):
    def __init__(self,host,port,tag='',MAX_TRYS=10):

        if host==0:
            # HOST = 'localhost'
            host = '127.0.0.1'

        self.host       = host
        self.port       = port
        self.tag        = tag
        self.connection = ''
        self.lock       = threading.Lock()             # Avoid collisions between various threads

        self.wpm        = 0
        self.freq       = 0
        self.band       = ''
        self.mode       = ''

        self.rig_type  = 'UNKNOWN'
        self.rig_type1 = 'UNKNOWN'
        self.rig_type2 = 'UNKNOWN'
        
        # Try to open connection
        for i in range(max(MAX_TRYS,1)):
            if i>0:
                time.sleep(5)
            self.open(host,port,tag)
            if self.fldigi_active or self.flrig_active:
                self.active=True
                break
        else:
            self.active=False
            print('Too many tries - giving up')

    # Function to open connection to FLDIGI/FLRIG
    def open(self,host,port,tag):

        # Open xlmrpc server 
        addr= "http://"+host+":"+str(port)
        print("\n",tag,": Opening XMLRPC connection to FLDIGI/FLRIG on ",addr)
        self.s = ServerProxy(addr)

        # Init assuming failure
        self.fldigi_active=False
        self.flrig_active=False
        self.v4 = False
        
        # Get version info
        try:
            # Look for fldigi
            print('Looking for FLDIGI ...')
            self.version = self.s.fldigi.version()
            self.v4 = int( self.version.split('.')[0] ) >=4
            print("fldigi version: ",self.version,self.v4)
            self.fldigi_active=True
            self.flrig_active=False
            self.connection = 'FLDIGI'
            self.rig_type   = 'FLDIGI'

            # Kludge
            #socket.setdefaulttimeout(5)           # set the timeout to N seconds
            socket.setdefaulttimeout(None)      # sets the default back

        except:

            try:
                # Look for flrig
                print('Looking for FLRIG ...')
                info = self.s.rig.get_info()
                self.version = 'flrig'
                self.flrig_active=True
                self.connection = 'FLRIG'
                self.rig_type   = 'FLRIG'
                if tag=='PROBE':
                    return

                # Probe FLRIG interface
                self.flrig()
                print("Connected to flrig")
            except Exception as e: 
                print( str(e) )
                print(tag,": Unable to open FLDIGI/FLRIG")

        # Determine which rig is on the other end
        self.active = self.fldigi_active or self.flrig_active

        if False:
            # This doesn't work for the FT991a
            buf = self.get_response('FA;')
            print('buf=',buf,len(buf))
            if len(buf)>11:
                self.rig_type1 = 'Kenwood'
            else:
                self.rig_type1 = 'Yaesu'

        if self.flrig_active :
            info = self.s.rig.get_info()
            a=info.split()
            print('a=',a)
            if len(a)==0:
                print('FLDIGI_IO - OPEN: Unknown rig type')
                sys.exit(0)
            
            print("\nFLRIG active - Rig info: ",info,'\tinfo0=',a[0])
            self.rig_type2 = a[0][2:]
            if self.rig_type2[:2]=='FT':
                self.rig_type1 = 'Yaesu'
                if self.rig_type2 == "FT-991A":
                    self.rig_type2 = "FT991a"
            elif self.rig_type2[:2]=='IC':
                self.rig_type1 = 'Icom'
                if self.rig_type2 == "IC-9700":
                    self.rig_type2 = "IC9700"
                self.civ = icom_civ(self.rig_type2)            
            else:
                print('Unknown rig type')
                sys.exit(0)
            #self.flrig()
            #sys.exit(0)
            
        if self.fldigi_active:
            # Looking for something that distinguishes the rigs ...
            name = self.s.rig.get_name()
            print('Rig name=',name)
            modes = self.s.rig.get_modes()
            print('Avail modes=',modes)
            bws = self.s.rig.get_bandwidths()
            print('Avail bandwidths=',bws)
            bw = self.s.rig.get_bandwidth()
            print('Current bandwidth=',bw)

            if 'DATA-FM' in modes:
                # ['LSB', 'USB', 'CW-USB', 'FM', 'AM', 'RTTY-LSB', 'CW-LSB', 'DATA-LSB', 'RTTY-USB', 'DATA-FM', 'FM-N', 'DATA-USB', 'AM-N']
                print('Rig appears to be FT991a')
                self.s.rig.set_name("FT991a")
                self.rig_type1 = 'Yaesu'
                self.rig_type2 = 'FT991a'
                name = self.s.rig.get_name()
                print('name=',name)

                # FLRIG attached to FTdx3000:
                #Avail modes= ['LSB', 'USB', 'CW', 'FM', 'AM', 'RTTY-L', 'CW-R', 'PSK-L', 'RTTY-U', 'PKT-FM', 'FM-N', 'PSK-U', 'AM-N']
                
            else:
                print('*** Need some more code to figure out what rig we are attached to ***')
                buf = self.get_response('FA;')
                print('buf=-',buf,'-\t',len(buf))
                if len(buf)>11:
                    self.rig_type1 = 'Kenwood'
                    self.s.rig.set_name("TS-850")
                    self.rig_type2 = 'TS850'
                elif len(buf)==11:
                    self.rig_type1 = 'Yaesu'
                    #self.s.rig.set_name("FTDX-3000")
                    self.s.rig.set_name("FTdx3000")
                    self.rig_type2 = 'FTdx3000'

        # Set rig name
        print('FLDIGI_OPEN: rig type=',self.rig_type1,self.rig_type2)
        #if self.rig_type=='Kenwood':
        #        self.s.rig.set_name("TS-850")
        #    else:
        #        self.s.rig.set_name("FTDX-3000")

        # Probe FLDIGI/FLRIG interface
        if self.fldigi_active and False:
            # Test setting counter
            print('Getting counter...')
            c = self.s.main.get_counter()
            print(c)
            print('Setting counter...')
            self.s.main.set_counter(c+101)
            print('Getting counter...')
            c = self.s.main.get_counter()
            print(c)
            sys.exit(0)
            
        if self.fldigi_active and False:
            methods = self.s.fldigi.list()
            for m in methods:
                print(m['name'],'\t',m)
            sys.exit(0)
        elif False:
            self.flrig()

                
    # Test function to probe FLRIG interface
    def flrig(self):
        print("\nProbing FLRIG interface:")
        print(self.s)
        #print dir(self.s)
        #print getattr(self.s)
        #print help(self.s)

        #print self.s.system.listMethods()
        #print('FLRIG Methods:')
        #methods = self.s.system.listMethods()
        #for m in methods:
        #    print(m)

        #print self.s.rig.list_methods()
        print('FLRIG Methods:')
        methods = self.s.rig.list_methods()
        for m in methods:
            print(m['name'],'\t',m)

        print("\nRig info: ",self.s.rig.get_info())
        if self.fldigi_active:
            print("FA:   ",self.s.rig.send_command("FA;"))
            print("FB:   ",self.s.rig.send_command("FB;"))
            print("FB:   ",self.s.rig.send_command("FB14080000;"))
            print("FB:   ",self.s.rig.send_command("FB;"))
            print("RA00: ",self.s.rig.send_command("RA00;"))
            sys.exit(0)

    # Function to read list of available methods
    def get_methods(self,show_list=False):
        methods = self.s.fldigi.list()
        if show_list:
            for m in methods:
                print(m)
        return methods

    # Function to retrieve serial counter
    def get_counter(self):
        #print 'Getting counter...'
        return self.s.main.get_counter()

    # Function to set serial counter
    def set_counter(self,x):
        #print 'Setting counter...',x
        return self.s.main.set_counter(x)


    # Function to read rig freq 
    def get_freq(self,VFO='A'):
        if VERBOSITY>0:
            print('FLDIGI_IO: GET_FREQ vfo=',VFO)
        
        if self.fldigi_active:
            if VFO=='A':
                self.lock.acquire()
                x=self.s.main.get_frequency()
                self.lock.release()
            else:
                buf = self.get_response('F'+VFO+';')
                try:
                    x = float(buf[2:-1])
                except:
                    print('$$$$$$$$$$$$ Problem with FLDIGI GET_FREQ $$$$$$$$$$$$$$$$')
                    print('buf=',buf)
                    x=0
        elif self.flrig_active:
            #print('GET_FREQ:',VFO)
            self.lock.acquire()
            try:
                if VFO=='A':
                    x=float( self.s.rig.get_vfoA() )
                elif VFO=='B':
                    x=float( self.s.rig.get_vfoB() )
                elif VFO=='M':
                    #self.s.rig.set_verify_AB('A')
                    self.set_vfo('A')            # A or M ?
                    x=float( self.s.rig.get_vfoA() )
                    time.sleep(DELAY)
                elif VFO=='S':
                    #self.s.rig.set_verify_AB('B')
                    self.set_vfo('B')            # B or S ?
                    x=float( self.s.rig.get_vfoB() )
                    time.sleep(DELAY)
                else:
                    print('FLDIGI_IO GET_FREQ - Invalid VFO:',VFO)
                    x=0
            except Exception as e: 
                print('FLDIGI_IO GET FREQ - Unexpected error')
                print(e)
                x=0
            self.lock.release()
            #buf = self.get_response('F'+VFO+';')
            #x = float(buf[2:-1])
            #print('GET_FREQ:',x)
        else:
            x=0
        return x

    # Function to set rig freq 
    def set_freq(self,frq_KHz,VFO='A'):
        if VERBOSITY>0:
            print('FLDIGI SET_FREQ:',frq_KHz,VFO)
            
        f=float( 1000*frq_KHz )
        if self.fldigi_active:
            if VFO=='A':
                self.lock.acquire()
                self.s.main.set_frequency(f)
                self.lock.release()
            else:
                cmd='BY;F'+VFO+str(int(f)).zfill(8)+';'
                self.send(cmd)
        elif self.flrig_active:
            self.lock.acquire()
            if VFO=='A':
                self.s.rig.set_vfoA(f)
            elif VFO=='B':
                self.s.rig.set_vfoB(f)
            elif VFO=='M':
                self.s.rig.set_AB('A')
                time.sleep(DELAY)
                self.s.rig.set_vfoA(f)
                time.sleep(DELAY)
            elif VFO=='S':
                self.s.rig.set_AB('B')
                time.sleep(DELAY)
                self.s.rig.set_vfoB(f)
                time.sleep(DELAY)
            else:
                print('FLDIGI_IO GET_FREQ - Invalid VFO:',VFO)
                x=0
            self.lock.release()
            #cmd='F'+VFO+str(int(f)).zfill(8)+';'
            #self.send(cmd)
        else:
            f=0
        return f

    # Function to set rig band - need to be able to issue BS command to get this to work better but for now
    def set_band_fldigi(self,band):

        if band==160:
            frq = 1.8
        elif band==80:
            frq = 3.5
        elif band==60:
            frq = 5
        elif band==40:
            frq = 7
        elif band==30:
            frq = 10
        elif band==20:
            frq = 14
        elif band==17:
            frq = 18.068
        elif band==15:
            frq = 21
        elif band==12:
            frq = 24.89
        elif band==10:
            frq = 28
        elif band==6:
            frq = 50.1
        else:
            print("FLDIGI_IO SET_BAND: Invalid band",band)
            frq = 0

        print("FLDIGI_IO SET BAND ",band,frq)
        if frq>0:
            self.lock.acquire()
            self.set_freq(frq*1000)
            self.lock.release()

    # Function to read rig mode 
    def get_mode(self,VFO='A'):
        if VERBOSITY>0:
            print('FLDIGI_IO: GET_MODE vfo=',VFO)
            
        self.lock.acquire()
        if self.fldigi_active:
            m=self.s.rig.get_mode()
        else:
            if VFO=='A':
                m=self.s.rig.get_modeA()
            else:
                m=self.s.rig.get_modeB()
        self.lock.release()
            
        return m

    # Function to read fldigi mode 
    def get_fldigi_mode(self):
        self.lock.acquire()
        if self.fldigi_active:
            m=self.s.modem.get_name()
        else:
            if not self.flrig_active:
                print('*** FLDIGI_IO: Warning - unable to read modem name ***')
            m=self.s.rig.get_mode()
        self.lock.release()
        return m

    def get_vfo(self):
        if self.flrig_active:
            try:
                vfo=self.s.rig.get_AB()
                print('FLDIGI_IO: GET_VFO ',vfo)
                return vfo
            except Exception as e: 
                print('*** ERROR *** FLDIGI_IO - GET_VFO - Problem getting vfo')
                print(e)
                return 'AA'
        else:
            # Dummied up for now
            print('FLDIGI_IO: GET_VFO not available yet for FLDIGI - assumes A')
            return 'AA'
    
    def set_vfo(self,rx=None,tx=None):
        if VERBOSITY>0:
            print('FLDIGI_IO - SET_VFO:',rx,tx)
            
        if self.flrig_active:
            if rx:
                try:
                    self.s.rig.set_AB(rx)
                    time.sleep(DELAY)
                except Exception as e: 
                    print('***ERROR *** FLDIGI_IO - SET_VFO - Problem setting RX vfo:',rx,tx)
                    print(e)
                    return
            else:
                rx=self.s.rig.get_AB()
            if tx:
                if rx==tx:
                    opt=0
                else:
                    opt=1
                self.s.rig.set_split(opt)
                time.sleep(DELAY)

        else:
            # Dummied up for now
            print('SET_VFO not available yet for FLDIGI - assumes A')
            
        return


    # Function to set rig mode - return old mode
    def set_mode(self,mode,VFO='A',Filter=None):
        #VERBOSITY=1
        if VERBOSITY>0:
            print("FLDIGI_IO - SET_MODE mode=",mode,'\tVFO=',VFO,self.v4)
        mode2=mode       # Fldigi mode needs to match rig mode

        # Translate rig mode into something rig understands
        if mode==None or mode=='IQ':
            return
        if mode in ['PKTUSB','RTTY','DIGITAL','FT8'] or mode.find('PSK')>=0 or mode.find('JT')>=0:
            if not self.v4 or self.flrig_active:
                mode='PSK-U'           # For some reason, this was changed in version 4
            else:
                mode='PKT-U'    
        elif mode in ['CW','CW-U','CWUSB','CW-USB']:
            if self.flrig_active:
                if self.rig_type2 == 'FT991a':
                    mode='CW-U'
                else:
                    mode='CW'
            else:
                mode='CW'
        elif mode in ['CWLSB','CW-LSB','CW-R','CWR','CW-L']:
            if self.flrig_active:
                if self.rig_type2 == 'FT991a':
                    mode='CW-L'
                else:
                    mode='CW-R'
            else:
                mode='CWR'
        if VERBOSITY>0:
            print('FLDIGI_IO - SET_MODE: mode=',mode,self.v4)

        # Translate fldigi mode into something fldigi understands
        if mode2=='DIGITAL' or mode2.find('JT')>=0 or mode2=='FT8':
            mode2='RTTY'
        elif mode2=='USB' or mode2=='LSB' or mode2=='AM':
            mode2='SSB'
        elif mode2=='PSK':
            mode2='BPSK31'
        if VERBOSITY>0:
            print('FLDIGI_IO: mode2=',mode2)

        if VFO=='A' or self.flrig_active:
            #print('FLDIGI_IO - SET_MODE: Using xlmrpc mode=',mode)
        
            self.lock.acquire()
            if self.fldigi_active:
                self.s.rig.set_mode(mode)  
                mold=self.s.modem.set_by_name(mode2)
                print('mold=',mold)
                mout=self.s.modem.get_name()
            elif self.flrig_active:
                #print('FLDIGI_IO - SET_MODE: Using xlmrpc for FLRIG vfo/mode=',VFO,mode)
                if VFO=='A':
                    #print('FLDIGI_IO: Setting VFO A to',mode)
                    self.s.rig.set_modeA(mode)
                elif VFO=='B':
                    #print('FLDIGI_IO: Setting VFO B to',mode)
                    self.s.rig.set_modeB(mode)
                elif VFO=='M':
                    #print('FLDIGI_IO: Setting VFO M (A) to',mode)
                    self.s.rig.set_modeA(mode)
                    time.sleep(DELAY)
                elif VFO=='S':
                    #print('FLDIGI_IO: Setting VFO S (B) to',mode)
                    self.s.rig.set_modeB(mode)
                    time.sleep(DELAY)
                else:
                    print('FLDIGI_IO: SET_MODE - Invalid VFO:',VFO,mode)
                mout=mode
            else:
                print('*** FLDIGI_IO: Warning - unable to read modem name ***')
                mout=self.s.rig.get_mode()
            self.lock.release()
            if VERBOSITY>0:
                print("FLDIGI_IO SET_MODE: mout=",mout)

            if Filter=='Wide':
                if VERBOSITY>0:
                    print("FLDIGI_IO SET_MODE: Setting filter to ",Filter)
                time.sleep(DELAY)
                self.s.rig.set_bandwidth(2000)
                if VERBOSITY>0:
                    print("FLDIGI_IO SET_MODE: Filter Set")                
                    time.sleep(DELAY)
                    print(self.s.rig.get_bw())
                    print(self.s.rig.get_bwA())
                    print(self.s.rig.get_bwB())
                
        else:
            try:
                if VERBOSITY>0:
                    print('FLDIGI_IO - SET_MODE: Trying direct approach',mode)
                c = modes[mode]["Code"]
                self.send('FR4;MD'+c+';')
                time.sleep(DELAY)
                self.send('FR0;')
                mout=mode
            except:
                print('FLDIGI_IO SET_MODE: Unable to set mode =',mode)
                return mode

        if VERBOSITY>0:
            print("FLDIGI_IO: SET MODE Done.\n")
            
        return mout

    # Function to set call 
    def set_call(self,call):
        if self.fldigi_active:
            print("SET CALL:",call)
            self.lock.acquire()
            x=self.s.log.set_call(call)
            self.lock.release()
            return x

    # Function to set log fields
    def set_log_fields(self,fields):
        if self.fldigi_active:
            print('SET_LOG_FIELDS: Fields:',fields)
            self.lock.acquire()
            for key in list(fields.keys()):
                if key=='Call':
                    self.s.log.set_call(fields['Call'])
                elif key=='Name':
                    self.s.log.set_name(fields['Name'])
                elif key=='QTH':
                    self.s.log.set_qth(fields['QTH'])
                elif key=='RST_out':
                    self.s.log.set_rst_out(fields['RST_out'])
                elif key=='Exchange':
                    self.s.log.set_exchange(fields['Exchange'])
                else:
                    print('SET_LOG_FIELD: %%% Unknwon log field %%%%%%%%%% ',key)
            self.lock.release()
            print('SET_LOG_FIELDS: Done.')

    # Function to get log fields
    def get_log_fields(self):
        if self.fldigi_active:
            print('GET_LOG_FIELDS:')
            self.lock.acquire()
            call    = self.s.log.get_call()
            name    = self.s.log.get_name()
            qth     = self.s.log.get_qth()
            rst_in  = self.s.log.get_rst_in()
            rst_out = self.s.log.get_rst_out()
            ser_in  = self.s.log.get_serial_number()
            ser_out = self.s.log.get_serial_number_sent()
            self.lock.release()
        else:
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

    def get_serial_out(self):
        if self.fldigi_active:
            print('GET_SERIAL_OUT:')
            self.lock.acquire()
            x=self.s.log.get_serial_number_sent()
            self.lock.release()
        else:
            x=0
        return x

    def set_serial_out(self,x):
        if self.fldigi_active:
            print('SET_SERIAL_OUT:',x)
            self.lock.acquire()
            #x=self.s.main.set_serial_number_sent()
            self.s.main.set_counter(x)
            self.lock.release()

    # Functions to send a command directly to the rig & get the response
    def send(self,cmd):
        #print 'SEND: Waiting for LOCK...'
        self.lock.acquire()
        #print 'SEND: Got LOCK...'
        if self.fldigi_active:
            #print "FLDIGI SEND:",cmd
            self.reply = self.s.rig.send_command(cmd,100)
            #print 'SEND: REPLY=',self.reply
        elif self.flrig_active:
            try:
                if self.rig_type1 == "Icom":
                    cmd2=' '.join( show_hex(cmd) )
                else:
                    cmd2=cmd
                #print("FLDIGI SEND: cmd=",cmd2)
                reply = self.s.rig.cat_string(cmd2)
                #print('SEND: reply=',reply)
                if self.rig_type2 == "IC9700":
                    self.reply = [int(i,16) for i in reply.split(' ')]
                else:
                    self.reply = reply
                #print('SEND: reply=',self.reply)
            except Exception as e: 
                print("**** FLDIGI SEND FAILURE cmd=",cmd2)
                print(e)
                self.reply = ''
        else:
            self.reply = ''
        #print 'SEND: Releasing LOCK...'
        self.lock.release()
        #print 'SEND: Done.'

    # Function to run a macro
    def run_macro(self,idx):
        if self.fldigi_active:
            self.lock.acquire()
            if idx<0:
                x=self.s.main.get_max_macro_id()
            else:
                x=self.s.main.run_macro(idx)
            self.lock.release()
            return x
            
    def recv(self,n):
        #print "fldigi recv:",self.reply
        return self.reply
        
    def close(self):
        return 0

    def get_response(self,cmd):
        #VERBOSITY=0
        if VERBOSITY>0:
            print('FLDIGI GET_RESPONSE: Sending CMD ... ',cmd)
        #print('Waiting for lock')
        #self.lock.acquire()
        self.send(cmd)
        if VERBOSITY>0:
            print('Waiting for response ...')
        if self.rig_type1 == "Icom":
            buf = self.recv(1024)
        else:
            buf = self.recv(1024).rstrip()
        if VERBOSITY>0:
            print('...Got it',buf)

        #self.lock.release()
        #print('Lock released')
        return buf

    # Function to effect pressing of TUNE button
    def tune(self,on_off):
        self.lock.acquire()
        if on_off:
            self.s.main.tune()
        else:
            self.s.main.abort()
        self.lock.release()

    # Function to turn PTT on and off
    def ptt(self,on_off,VFO='A'):
        #print('FLDIGI_IO PTT:',on_off,VFO)
        if self.flrig_active and True:

            # Need to test this pathway out but it shows promise
            print('FLDIGI_IO PTT - Using flrig - on/off=',on_off, \
                  '\tvfo=',VFO)
            self.lock.acquire()
            if on_off:
                # Need to set both TX&RX VFOs to get ant correct if
                # monitoring different bands
                ntries=0
                while ntries<5:
                    ntries+=1
                    self.s.rig.set_verify_AB(VFO)
                    #self.s.rig.set_split(1)          # Doesn't work
                    time.sleep(DELAY)
                
                    vfo2=self.get_vfo()
                    if vfo2!=VFO:
                        print('FLDIGI PTT - Houston, we have a problem!',VFO,vfo2,ntries)
                    else:
                        break
                    
                self.s.rig.set_ptt(1)
                
            else:
                
                self.s.rig.set_ptt(0)
                time.sleep(DELAY)
                
                ntries=0
                while ntries<5:
                    ntries+=1
                    self.s.rig.set_verify_AB('A')
                    #self.s.rig.set_split(0)
                    time.sleep(DELAY)
                
                    vfo2=self.get_vfo()
                    if vfo2!='A':
                        print('FLDIGI PTT - Houston, we have another problem!','A',vfo2)
                    else:
                        break
                    
            self.lock.release()
            
        elif VFO=='A':

            print('FLDIGI_IO PTT - Using fl - on/off, vfo=:',\
                  on_off,VFO,self.fldigi_active)
            
            self.lock.acquire()
            if on_off:
                if self.fldigi_active:
                    self.s.main.tx()
                else:
                    # Shouldn't get here anymore
                    self.s.rig.set_ptt(1)
            else:
                if self.fldigi_active:
                    self.s.main.rx()
                else:
                    # Shouldn't get here anymore
                    self.s.rig.set_ptt(0)
            self.lock.release()

        else:

            print('FLDIGI_IO PTT - Using direct - on/off, vfo=:',on_off,VFO)
            if on_off:
                self.send('FT3;TX1;')
            else:
                self.send('TX0;')
                time.sleep(DELAY)
                self.send('FT2;')
                
        print('FLDIGI/FLRIG PTT Done.')

    # Routine to put rig into split mode
    def split_mode(self,opt):
        if VERBOSITY>0:
            print('FLDIGI_IO - SPLIT_MODE: opt=',opt)

        if opt==-1:
            #print('\nQuerying split ...')
            self.lock.acquire()
            buf=self.s.rig.get_split()
            self.lock.release()
            if VERBOSITY>0:
                print('SPLIT: buf=',buf)
            return buf==1

        elif opt==0:
            
            self.lock.acquire()
            buf=self.s.rig.set_split(0)
            self.lock.release()
                
        elif opt==1:
            
            self.lock.acquire()
            buf=self.s.rig.set_split(1)
            self.lock.release()
                
        else:
            
            print('FLDIGI_IO - SPLIT_MODE: Invalid opt',opt)
            return -1
            

    def mic_setting(self,m,iopt,src=None,lvl=None,prt=None):
        if VERBOSITY>0:
            print('FLDIGI_IO MIC_SETTING:',iopt,src,lvl,prt)

        if iopt==0:
            # Read
            self.lock.acquire()
            buf=self.s.rig.get_micgain()
            print('buf=',buf)
            src=int(buf)
            self.lock.release()
        else:
            # Set
            if lvl!=None and level:
                self.lock.acquire()
                buf=self.s.rig.set_micgain(lvl)
                self.lock.release()
                
        return [src,lvl,prt]


    def read_meter(self,meter):
        if VERBOSITY>0:
            print('FLDIGI_IO - READ_METER:',meter)

        self.lock.acquire()
        if meter=='S':
            # Flrig processes the raw number read from the rigs
            # It returns the dB above S0. So 0 for S0 and 54 for S9. 
            buf=self.s.rig.get_smeter()
        elif meter=='Power':
            buf=self.s.rig.get_pwrmeter()
        elif meter=='SWR':
            buf=self.s.rig.get_swrmeter()
        else:
            print('FLDIGI_IO - READ_METER: Unknown meter',meter)
            buf=0
        
        #print('buf=',buf)
        self.lock.release()
        return int(buf)
            

################################################################################################
    

class fllog_xlmrpc:
    def __init__(self,host,port=8421,tag='',MAX_TRYS=10):

        if host==0:
            # HOST = 'localhost'
            host = '127.0.0.1'
        if port==0:
            port = 8421;

        self.host       = host
        self.port       = port
        self.tag        = tag
        self.connection = 'FLLOG'
        self.lock       = threading.Lock()             # Avoid collisions between various threads

        self.wpm        = 0
        self.freq       = 0
        self.band       = ''
        self.mode       = ''
        
        # Try to open connection
        for i in range(max(MAX_TRYS,1)):
            if i>0:
                time.sleep(5)
            self.open(host,port,tag)
            if self.fllog_active:
                self.active=True
                break
        else:
            self.active=False
            print('Too many tries - giving up')

    # Function to open connection to FLLOG
    def open(self,host,port,tag):

        # Open xlmrpc server 
        addr= "http://"+host+":"+str(port)
        print("\n",tag,": Opening XMLRPC connection to FLLOG on ",addr)
        self.s = ServerProxy(addr)

        # Init assuming failure
        self.fllog_active=False
        self.v4 = False
        
        # Look for fllog - need to add error trapping 
        info = self.s.system.listMethods()
        print(info)
        print("Connected to FLLOG")
        
        self.fllog_active=True
        #print tag,": Unable to open FLLOG"

        # Probe FLLOG interface
        # self.fllog_probe()

        
    # Test function to probe FLRIG interface
    def fllog_probe(self):
        print("Probing FLLOG interface:")
        print(self.s)

        methods = self.s.system.listMethods()
        for m in methods:
            print('\nmethod=',m)
            try:
                hlp = self.s.system.methodHelp(m)
                print(hlp)
            except:
                print('No help available for method',m)

        print('\nGET RECORD:')
        #rec = self.s.log.get_record('AA2IL')
        rec = self.Get_Last_QSO('AA2IL')
        print(rec)
                
        print('\nCHECK DUPE:')
        #log.check_dup CALL, MODE(0), TIME_SPAN(0), FREQ_KHZ(0), STATE(0), XCHG_IN(0)
        #qso = self.s.log.check_dup('AA2IL','0','0','0','0','0')
        dupe = self.Dupe_Check('AA2IL')
        print(dupe)
        dupe = self.Dupe_Check('AA2IL','CW',60000,7000)
        print(dupe)

        qso={'CALL'         : 'AA2IL'    ,\
             'QSO_DATE_OFF' : '20190130' ,\
             'TIME_OFF'     : '014530'   ,\
             'FREQ'         : '14.0234'  ,\
             'MODE'         : 'RTTY'     ,\
             'NAME'         : 'JOE'      ,\
             'QTH'          : 'CA'       ,\
             'GRID'         : ''
            }
        #rec = adif_record(qso)
        #print rec
        #qso = self.s.log.add_record(rec)
        self.Add_QSO(qso)

        print('FLLOG_PROBE - Exiting...')
        sys.exit(0)
        
        
    def Get_Last_QSO(self,call):
        rec = self.s.log.get_record(call)
        #print rec
        qso = {}
        #tags = re.findall('<(.*?):(\d+).*?>([^<]+)',rec.replace('<RST> <CNTR>','A AA2IL 78 CA'))
        tags = re.findall('<(.*?):(\d+).*?>([^<]+)',rec)
        #print tags
        for tag in tags:
            qso[tag[0].upper()] = tag[2][:int(tag[1])]
        return qso
        
    def Dupe_Check(self,call,mode='0',span='0',frq='0',state='0',xchg='0'):
        #print 'DUPE_CHECK:',call
        #print mode,span,frq,state,xchg
        dupe = self.s.log.check_dup(call,str(mode),str(span),str(frq),state,xchg)
        print('Dupe_Check:',dupe)
        if dupe=='true':
            return True
        else:
            return False
        
    def Add_QSO(self,qso):
        rec = adif_record(qso)
        print(rec)
        self.s.log.add_record(rec)
        

def adif_record(qso):
#    qso['freq'] = str( 1e-3*float( qso['freq'] ) )

    if 'QSO_DATE' not in qso:
        qso['QSO_DATE'] = qso['QSO_DATE_OFF']
    if 'TIME_ON' not in qso:
        qso['TIME_ON'] = qso['TIME_OFF']
    if 'RST_SENT' not in qso:
        qso['RST_SENT']='599'
    if 'RST_RCVD' not in qso:
        qso['RST_RCVD']='599'
    #if not qso.has_key('STATION_CALLSIGN'):
    #    qso['STATION_CALLSIGN']=MY_CALL
    #if not qso.has_key('MY_GRIDSQUARE'):
    #    qso['MY_GRIDSQUARE']=MY_GRID
    #if not qso.has_key('MY_CITY'):
    #    qso['MY_CITY']=MY_CITY

    a=''
    fields = list(qso.keys()) 
    fields.sort()
    for f in fields:
        val = str( qso[f] )
        n = len(val)
        if n>0:
            a = a +'<'+ f +':'+ str(n) +'>'+ val +' '
            
    a = a +'<EOR>\n'
    return a

    
def adif_field(fld,val):
    a = '<'+ fld +':'+ str(len(val)) +'>'+ val +' '
    return a


        
