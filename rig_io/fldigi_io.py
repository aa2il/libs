############################################################################################
#
# Fldigi IO - Rev 1.0
# Copyright (C) 2021-5 by Joseph B. Attili, joe DOT aa2il AT gmail DOT com
#
# Functions to control rig through FLDIGI or FLRIG from python.
# See methods.txt for list of methods for these two protocols
#
# To Do:
#
#    This was originally developed for use with fldigi. Flrig was added as
#    an after thought but has become the main pathway I use now.
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
from .dummy_io import no_connect
import threading
import time
import socket
from .ft_tables import DELAY, Decode_Mode, modes
from utilities import error_trap,show_ascii
import re
from .icom_io import icom_civ, show_hex

################################################################################################

VERBOSITY=0

################################################################################################

"""
def full_stack():
    import traceback, sys
    exc = sys.exc_info()[0]
    stack = traceback.extract_stack()[:-1]  # last one would be full_stack()
    if exc is not None:  # i.e. an exception is present
        del stack[-1]       # remove call of full_stack, the printed exception
                            # will contain the caught exception caller instead
    trc = 'Traceback (most recent call last):\n'
    stackstr = trc + ''.join(traceback.format_list(stack))
    if exc is not None:
         stackstr += '  ' + traceback.format_exc().lstrip(trc)
    return stackstr

print full_stac()
"""


class fldigi_xlmrpc(direct_connect):
#class fldigi_xlmrpc(no_connect):
    def __init__(self,host,port,tag='',MAX_TRYS=10):

        if host==0:
            # HOST = 'localhost'
            host = '127.0.0.1'

        self.host       = host
        self.port       = port
        self.tag        = tag
        self.connection = ''
        self.lock       = threading.Lock()             # Avoid collisions between various threads
        self.lock2      = threading.Lock()             # Avoid collisions between various threads
        self.tx_evt     = threading.Event()            # Allow rig quires only when receiving
        self.ntimeouts  = 0

        self.wpm        = 0
        self.freq       = 0
        self.band       = ''
        self.mode       = ''
        self.dead       = False
        self.wpm        = 0
        self.sub_dial_func=None
        self.nrx        = 0

        self.rig_type  = 'UNKNOWN'
        self.rig_type1 = 'UNKNOWN'
        self.rig_type2 = 'UNKNOWN'
        
        # Try to open connection
        for i in range(max(MAX_TRYS,1)):
            if i>0:
                time.sleep(5)
                print('Try Try Try again ...')
            self.open(host,port,tag)
            if self.fldigi_active or self.flrig_active:
                self.active=True
                break
            elif self.dead:
                break
        else:
            self.active=False
            print('Too many tries - giving up')

    # Function to determine rig type
    def get_rig_type(self):
        
        info = self.s.rig.get_info()
        a=info.split()
        print('GET RIG TYPE: info=',a)
        if len(a)==0:
            print('FLDIGI_IO - OPEN: Unknown rig type')
            sys.exit(0)

        self.available_modes = self.s.rig.get_modes()
        print('Available modes=',self.available_modes)
            
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
            if self.rig_type2 == "IC-7300":
                self.rig_type2 = "IC7300"
            self.civ = icom_civ(self.rig_type2)            
        elif self.rig_type2[:2]=='TS':
            self.rig_type1 = 'Kenwood'
        else:
            print('Unknown rig type')
            sys.exit(0)
            
            
    # Function to open connection to FLDIGI/FLRIG
    def open(self,host,port,tag):

        # Open xlmrpc server 
        addr= "http://"+host+":"+str(port)
        print("\nFLDIGI_IO->OPEN tag=",tag,": Opening XMLRPC connection to FLDIGI/FLRIG on ",addr)
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

            # Probe FLRIG interface
            self.fldigi_probe()
            if self.fldigi_active:
                print("\nConnected to FLDIGI")
            
        except:

            try:
                # Look for flrig
                print('... no FLDIG - Looking for FLRIG ...')
                self.get_rig_type()

                self.version = 'flrig'
                self.flrig_active=True
                self.connection = 'FLRIG'
                self.rig_type   = 'FLRIG'
                if tag=='PROBE':
                    return

                # Probe FLRIG interface
                self.flrig_probe()
                if self.flrig_active:
                    print("\nConnected to FLRIG")
            except: 
                error_trap('FLDIGI IO->OPEN: tag='+tag+' Unable to open FLDIGI/FLRIG')

        # Determine which rig is on the other end
        self.active = self.fldigi_active or self.flrig_active
        if not self.active:
            self.s=None
            self.rig_type  = 'UNKNOWN'
            self.rig_type1 = 'UNKNOWN'
            self.rig_type2 = 'UNKNOWN'

        if False:
            # This doesn't work for the FT991a
            buf = self.get_response('FA;')
            print('buf=',buf,len(buf))
            if len(buf)>11:
                self.rig_type1 = 'Kenwood'
            else:
                self.rig_type1 = 'Yaesu'

        if self.flrig_active :
            self.get_rig_type()
            
            # Probing around ...
            """
            info = self.s.rig.get_info()
            print('Rig info=',info)
            update = self.s.rig.get_update()
            print('Rig update=',update)
            self.available_modes = self.s.rig.get_modes()
            print('Avail modes=',self.available_modes)
            bws = self.s.rig.get_bws()
            print('Avail bandwidths=',bws)
            bw = self.s.rig.get_bw()
            print('Current bandwidth=',bw)
            """
            
        if self.fldigi_active:
            
            # Looking for something that distinguishes the rigs ...
            name = self.s.rig.get_name()
            print('\tRig name=',name)
            modes = self.s.rig.get_modes()
            print('\tAvail modes=',modes)
            bws = self.s.rig.get_bandwidths()
            print('\tAvail bandwidths=',bws)
            bw = self.s.rig.get_bandwidth()
            print('\tCurrent bandwidth=',bw)

            if name in ['KCAT','KC505','505DSP']:

                print('Rig appears to be KCAT - assuming KC505 for now ???')
                self.rig_type1 = 'KCAT'
                self.rig_type2 = 'KC505'
                
            elif 'NONE' in modes:

                # FLDIGI attached to FTdx3000 via HAMLIB
                #Avail modes= ['NONE', 'AM', 'CW', 'USB', 'LSB', 'RTTY', 'FM', 'WFM', 'CWR', 'RTTYR', 'AMS', 'PKTLSB', 'PKTUSB', 'PKTFM', 'SAM', 'SAL', 'SAH']
                print('Rig appears to be HAMLIB - assuming FTdx3000 for now ???')
                buf = self.get_response('f')
                print('buf=',buf)
                self.rig_type1 = 'Hamlib'
                self.rig_type2 = 'Hamlib'
                #self.rig_type1 = 'Yaesu'
                #self.s.rig.set_name("FTDX-3000")
                #self.s.rig.set_name("FTdx3000")
                #self.rig_type2 = 'FTdx3000'
                #sys.exit(0)
            
            elif 'DATA-FM' in modes:
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
                buf = self.get_response('FA;')
                if len(buf)>11:
                    # YAESU & KENWOOD rigs have a ID command which might be used instead
                    print('Rig appears to be TS850')
                    self.rig_type1 = 'Kenwood'
                    self.s.rig.set_name("TS-850")
                    self.rig_type2 = 'TS850'
                elif len(buf)==11:
                    print('Rig appears to be FTdx3000')
                    self.rig_type1 = 'Yaesu'
                    #self.s.rig.set_name("FTDX-3000")
                    self.s.rig.set_name("FTdx3000")
                    self.rig_type2 = 'FTdx3000'
                else:
                    print('buf=-',buf,'-\t',len(buf))
                    print('*** Need some more code to figure out what rig we are attached to ***')

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

    # Test function to probe FLRIG interface
    def fldigi_probe(self):
        print("\nProbing FLDIGI interface:")
        print(self.s)
            
        print('\nProgram name    =',self.s.fldigi.name_version() )
        print('Config Dir      =',self.s.fldigi.config_dir() )
                
        print('\nFLDIGI Methods:')
        methods = self.s.fldigi.list()
        for m in methods:
            print(m['name'],'\t',m)

    # Test function to probe FLRIG interface
    def flrig_probe(self):
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

        # JBA - looking for some indicator of whether ths rig is really runing
        # Best I found was to issue a direct cat command
        info = self.s.rig.get_info().split()
        print('info=',info)

        if info[0] in ['R:FTdx3000']:
            self.rig_type1='Yaesu'            
        print('rig_type1=',self.rig_type1)
        if  self.rig_type1 in ['Yaesu','Kenwood']:
            cat = self.s.rig.cat_string('FA;')
            print('cat=',cat)
        else:
            cat=''
            print('FLRIG PROBE - Need a little more code for this rig')

        # JBA - Is the radio really attached or is this just a left over version of flrig
        if cat[:11]=='No response' and True:
            print('Looks like a dead connection')
            self.fldigi_active = False
            self.flrig_active  = False
            self.active        = False
            self.dead          = True
        
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
                acq=self.lock.acquire(timeout=1.0)
                if acq:
                    try:
                        x=self.s.main.get_frequency()
                    except:
                        error_trap('FLDIGI IO->GET_FREQ - Lock acquired but Cant read freq',1)
                    self.lock.release()
                else:
                    print('FLDIGI GET FREQ: Failed to acquire lock')
                    x=0
            else:
                buf = self.get_response('F'+VFO+';')
                try:
                    x = float(buf[2:-1])
                except:
                    error_trap('FLDIGI IO->GET_FREQ ????????',1)
                    print('\tbuf=',buf,'\tlen=',len(buf))
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
            except: 
                error_trap('FLDIGI IO->GET FREQ - Unexpected error')
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
                acq=self.lock.acquire(timeout=1.0)
                if acq:
                    self.s.main.set_frequency(f)
                    self.lock.release()
                else:
                    print('FLDIGI SET FREQ: Failed to acquire lock')
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
            elif VFO=='S':
                self.s.rig.set_AB('B')
                time.sleep(DELAY)
                self.s.rig.set_vfoB(f)
            else:
                print('FLDIGI_IO GET_FREQ - Invalid VFO:',VFO)
                x=0
            self.lock.release()
            time.sleep(DELAY)
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
            acq=self.lock.acquire(timeout=1.0)
            if acq:
                self.set_freq(frq*1000)
                self.lock.release()
            else:
                print('FLDIGI SET BAND: Failed to acquire lock')

    # Function to read rig mode 
    def get_mode(self,VFO='A'):
        VERBOSITY=0
        if VERBOSITY>0:
            print('FLDIGI_IO GET_MODE: vfo=',VFO,'...')
            
        acq=self.lock.acquire(timeout=1.0)
        if acq:
            try:
                if self.fldigi_active:
                    #print('Hey1')
                    #m=self.s.rig.get_mode()    # Rig mode - not really helpful
                    m=self.s.modem.get_mode()   # Modem mode - what we really want
                    #print('Hey2',m)
                else:
                    if VFO=='A':
                        m=self.s.rig.get_modeA()
                    else:
                        m=self.s.rig.get_modeB()
            except: 
                error_trap('FLDIGI IO->GET_MODE - Problem getting vfo')
                m=''
            self.lock.release()
        else:
            print('FLDIGI GET_MODE: Failed to acquire lock')
            m=''
            
        if VERBOSITY>0:
            print('FLDIGI_IO GET_MODE: ... mode=',m)
        return m

    # Function to read fldigi mode 
    def get_fldigi_mode(self):

        acq=self.lock.acquire(timeout=1.0)
        if acq:
            if self.fldigi_active:
                m=self.s.modem.get_name()
            else:
                if not self.flrig_active:
                    print('*** FLDIGI_IO: *** WARNING *** Unable to read modem name ***')
            m=self.s.rig.get_mode()
            self.lock.release()
        else:
            print('FLDIGI GET FLDIGI FREQ: Failed to acquire lock')
            m=''
            
        return m

    def get_vfo(self):
        #VERBOSITY=1
        if VERBOSITY>0:
            print('FLDIGI_IO - GET_VFO:')
            
        if self.flrig_active:
            try:
                vfo=self.s.rig.get_AB()
                if VERBOSITY>0:
                    print('FLDIGI_IO: GET_VFO ',vfo)
                return vfo
            except: 
                error_trap('FLDIGI IO->GET_VFO - Problem getting vfo')
                return 'AA'
        else:
            # Dummied up for now
            print('FLDIGI_IO: GET_VFO not available yet for FLDIGI - assumes A')
            return 'AA'
    
    def set_vfo(self,rx=None,tx=None,op=None):
        #VERBOSITY=1
        if VERBOSITY>0:
            print('FLDIGI_IO - SET_VFO: rx=',rx,'\ttx=',tx,'\top=',op)
            try:
                AB=self.s.rig.get_AB()
                time.sleep(DELAY)
                SP=self.s.rig.get_split()
                time.sleep(DELAY)
                print('\tAB=',AB,'\tSPLIT=',SP)
            except: 
                error_trap('FLDIGI IO->SET_VFO - Problem getting vfo status')

        # Acquire lock
        acq=self.lock2.acquire(timeout=1.0)
        if not acq:
            print('FLDIGI SET VFO: Failed to acquire lock2')
            return
            
        if self.flrig_active:

            if self.rig_type2=='FT991a':
                rx='A'
            
            if rx:
                try:
                    self.s.rig.set_AB(rx)
                    #self.s.rig.set_verify_AB('A')           # These verify commands don't seem to work at all!
                    time.sleep(DELAY)
                except: 
                    error_trap('FLDIGI IO->SET_VFO - Problem setting RX vfo:')
                    print('\trx/tx=',rx,tx)
                    self.lock2.release()
                    return
            else:
                try:
                    rx=self.s.rig.get_AB()
                    time.sleep(DELAY)
                except: 
                    error_trap('FLDIGI IO->SET_VFO - Problem reading RX vfo:')
                    print('\trx/tx=',rx,tx)
                    self.lock2.release()
                    return
                
            if tx:
                if rx==tx:
                    opt=0
                else:
                    opt=1
            else:
                tx=rx
                opt=0
            try:
                self.s.rig.set_split(opt)
                #self.s.rig.set_verify_split(opt)
                time.sleep(DELAY)
            except: 
                error_trap('FLDIGI IO->SET_VFO - Problem setting split:')
                print('\trx=',rx,'\ttx=',tx,'\topt=',opt)
                self.lock2.release()
                return

            if True:
                ###################################################################################
                # FLRIG doesn't quite handle this correctly so fudge it for now.
                # Buttons on FLRIG work fine but not XML commands.  Need to 
                # dig through source sometime...
                ###################################################################################

                if self.rig_type1 == 'Yaesu':
                    time.sleep(2*DELAY)
                    self.set_vfo_direct(rx,tx)
                    """
                    if rx in ['A','M']:
                        cmd='BY;FR0;'
                    else:
                        cmd='BY;FR4;'
                    if tx in ['A','M']:
                        cmd=cmd+'FT2;'
                    else:
                        cmd=cmd+'FT3;'
                    time.sleep(2*DELAY)
                    buf = self.get_response(cmd)
                    print('cmd=',cmd,'\tbuf=',buf)
                    time.sleep(DELAY)
                    #buf = self.get_response(cmd)
                    #print('cmd=',cmd,'\tbuf=',buf)
                    #time.sleep(DELAY)
                    """

            if op:
                if op=='A->B':
                    #cmd='BY;AB;' 
                    print('FLDIGI_IO->SET VFO: A -> B')
                    try:
                        self.s.rig.vfoA2B()
                    except: 
                        error_trap('FLDIGI IO->SET_VFO - Problem copying A to B')
                        self.lock2.release()
                        return
                elif op=='B->A':
                    #cmd='BY;BA;'
                    print('FLDIGI_IO->SET VFO - HELP!!!!')
                elif op=='A<->B':
                    #cmd='BY;SV;'
                    print('FLDIGI_IO->SET VFO: Swap')
                    try:
                        self.s.rig.swap()
                        time.sleep(DELAY)
                    except: 
                        error_trap('FLDIGI IO->SET_VFO - Problem swapping')
                        self.lock2.release()
                        return

        else:
            
            # Dummied up for now
            print('SET_VFO not available yet for FLDIGI - assumes A')
            
        if VERBOSITY>0:
            AB=self.s.rig.get_AB()
            SP=self.s.rig.get_split()
            print('\tAB=',AB,'\tSPLIT=',SP)

        self.lock2.release()
        return


    # Function to set rig mode - return old mode
    def set_mode(self,mode,VFO='A',Filter=None):
        VERBOSITY=1
        if VERBOSITY>0:
            print("FLDIGI_IO - SET_MODE: mode=",mode,'\tVFO=',VFO,self.v4,'\tFilter=',Filter)
        mode2=mode       # Fldigi mode needs to match rig mode

        # Translate rig mode into something rig understands
        if mode==None or mode=='IQ':
            return
        
        elif mode=='SSB':
            frq = self.get_freq()
            if freq<10e6:
                mode='LSB'
            else:
                mode='USB'
                
        elif mode in ['PKTUSB','RTTY','DIGITA','DIGITAL','FT8','FT4'] or mode.find('PSK')>=0 or mode.find('JT')>=0:

            # There are some issues with the various versions of flrig
            # Need to add some code to get all available modes & select the right one?!
            """
            if not self.v4 or self.flrig_active:
            #if not (self.v4 or self.flrig_active):
                mode='PSK-U'           # For some reason, this was changed in version 4
            else:
                mode='PKT-U'           # Another inconsistency vs version???
            """
            if self.flrig_active:
                if 'PSK-U' in self.available_modes:
                    mode='PSK-U' 
                else:
                    mode='PKT-U'    
            else:
                mode='PKT-U'           # Another inconsistency vs version???
                
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

        # Translate fldigi mode into something fldigi understands
        if mode2 in ['DIGITAL','DIGITA','FT8','FT4'] or mode2.find('JT')>=0:
            mode2='RTTY'
        elif mode2=='USB' or mode2=='LSB' or mode2=='AM':
            mode2='SSB'
        elif mode2=='PSK':
            mode2='BPSK31'
        if VERBOSITY>0:
            print('FLDIGI_IO - SET_MODE: mode=',mode,'\tmode2=',mode2,'\tVersion 4=',self.v4)

        if VFO=='A' or self.flrig_active:
            #print('FLDIGI_IO - SET_MODE: Using xlmrpc mode=',mode)
        
            acq=self.lock.acquire(timeout=1.0)
            if not acq:
                print('FLDIGI SET MODE: Failed to acquire lock')
                return ' '
                
            if self.fldigi_active:
                
                ntries=0
                while ntries<5:
                    ntries+=1
                    try:
                        self.s.rig.set_mode(mode)  
                        time.sleep(DELAY)
                        mold=self.s.modem.set_by_name(mode2)
                        print('mold=',mold)
                        time.sleep(DELAY)
                        mout=self.s.modem.get_name()
                        time.sleep(DELAY)
                        break
                    except:
                        time.sleep(DELAY)
                    else:
                        print('\tSET_MODE: *** ERROR *** Failed to set mode after 5 tries!!!!!\n')
                        
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
                print('*** FLDIGI_IO: *** WARNING *** Unable to read modem name ***')
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


        if Filter=='Auto':
            if VERBOSITY>0:
                print("FLDIGI_IO: SET MODE - Setting filter ...\n")
            self.set_filter(Filter,mode=mout)

        if VERBOSITY>0:
            print("FLDIGI_IO: SET MODE Done.\n")
            
        return mout

    
    # Function to set call 
    def set_call(self,call):
        if self.fldigi_active:
            print("SET CALL:",call)
            acq=self.lock.acquire(timeout=1.0)
            if acq:
                x=self.s.log.set_call(call)
                self.lock.release()
            else:
                x=''
            return x

    # Function to set log fields
    def set_log_fields(self,fields):
        if self.fldigi_active:
            #print('SET_LOG_FIELDS: Fields:',fields)
            acq=self.lock.acquire(timeout=1.0)
            if acq:
                
                for key in list(fields.keys()):
                    if key=='Call':
                        self.s.log.set_call(fields['Call'])
                        print('FLDIGI_IO-SET LOG FIELDS: call=',fields['Call'])
                    elif key=='Name':
                        self.s.log.set_name(fields['Name'])
                        print('FLDIGI_IO-SET LOG FIELDS: name=',fields['Name'])
                    elif key=='QTH':
                        self.s.log.set_qth(fields['QTH'])
                        self.s.log.set_locator(fields['QTH'])
                        print('FLDIGI_IO-SET LOG FIELDS: qth=',fields['QTH'])
                    elif key=='RST_out':
                        self.s.log.set_rst_out(fields['RST_out'])
                        print('FLDIGI_IO-SET LOG FIELDS: rst=',fields['RST_out'])
                    elif key=='Exchange':
                        self.s.log.set_exchange(fields['Exchange'])
                        print('FLDIGI_IO-SET LOG FIELDS: xchange=',fields['Exchange'])
                    else:
                        print('SET_LOG_FIELD: %%% Unknwon log field %%%%%%%%%% ',key)
                        
                self.lock.release()
            print('SET_LOG_FIELDS: Done.')

    # Function to get log fields
    def get_log_fields(self,CALL_ONLY=False):
        if self.fldigi_active:
            #print('GET_LOG_FIELDS:')
            self.lock.acquire()
            call    = self.s.log.get_call()
            if CALL_ONLY:
                self.lock.release()
                return {'Call':call}
            name    = self.s.log.get_name()
            qth     = self.s.log.get_qth()
            if qth=='':
                qth     = self.s.log.get_locator()
            rst_in  = self.s.log.get_rst_in()
            rst_out = self.s.log.get_rst_out()
            ser_in  = self.s.log.get_serial_number()
            ser_out = self.s.log.get_serial_number_sent()
            exch    = self.s.log.get_exchange()
            self.lock.release()
        else:
            call    = ''
            if CALL_ONLY:
                self.lock.release()
                return {'Call':call}
            name    = ''
            qth     = ''
            rst_in  = ''
            rst_out = ''
            ser_in  = ''
            ser_out = ''
            exch    = ''

        cat=''
        prec=''
        check=''

        return {'Call':call,'Serial_In':ser_in,'Serial_Out':ser_out,\
                'Name':name,'QTH':qth,'Exchange':exch,\
                'Category':cat,'Prec':prec,'Check':check,
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
        #VERBOSITY=1
        if VERBOSITY>0:
            print('FLDIGI SEND: Waiting for LOCK...')
        self.lock.acquire()
        if VERBOSITY>0:
            print('FLDIGI SEND: ... Got LOCK...')
        if self.fldigi_active:
            #print "FLDIGI SEND:",cmd
            self.reply = self.s.rig.send_command(cmd,100)
            #print 'SEND: REPLY=',self.reply
        elif self.flrig_active:
            try:
                reply=None
                if self.rig_type1 == "Icom":
                    cmd2=' '.join( show_hex(cmd) )
                else:
                    cmd2=cmd
                reply = self.s.rig.cat_string(cmd2)
                if VERBOSITY>0:
                    print("FLDIGI SEND: cmd=",cmd2,'\treply=',reply)
                if self.rig_type2 in ['IC9700','IC7300']:
                    self.reply = [int(i,16) for i in reply.split(' ')]
                else:
                    self.reply = reply
                #print('SEND: reply=',self.reply)
            except: 
                error_trap('FLDIGI IO->SEND FAILURE')
                print('\tcmd=',cmd2,'\nreply=',reply)
                #print('reply=',reply,'\n',show_hex(reply) )
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

    def get_response(self,cmd,VERBOSITY=0):
        #VERBOSITY=0
        if VERBOSITY>0:
            print('FLDIGI GET_RESPONSE: Sending CMD ... ',cmd)
            
        #print('Waiting for lock')
        #self.lock.acquire()
        
        if len(cmd)>0:
            self.send(cmd)
        else:
            print('FLDIGI GET_RESPONSE: Unexpected NULL CMD ... ',cmd,len(cmd))
            return ''

        if VERBOSITY>0:
            print('Waiting for response ...')
        if self.rig_type1 == "Icom":
            buf = self.recv(1024)
        else:
            try:
                buf = self.recv(1024).rstrip()
            except: 
                error_trap('FLDIGI IO->GET RESPONSE: Error reading response',1)
                print('\tcmd=',cmd,'\t=len=',len(cmd))
                buf=''

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

    # Function to turn PTT on and off or to query T/R state
    def ptt(self,on_off,VFO='A'):
        VERBOSITY=1
        if VERBOSITY>0:
            print('FLDIGI_IO PTT: on/off=',on_off,'\tVFO=',VFO,'...')
        state=None
            
        if self.flrig_active:

            # Need to test this pathway out but it shows promise
            print('FLDIGI_IO PTT - Using flrig - on/off=',on_off, \
                  '\tvfo=',VFO)
            self.lock.acquire()
            if on_off<0:
                print('FLRIG PTT - Need to add some code to query t/r state')
                return None
            elif on_off:
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
                        print('FLRIG PTT - Houston, we have a problem!',VFO,vfo2,ntries)
                    else:
                        break
                    
                self.tx_evt.set()
                self.s.rig.set_ptt(1)
                
            else:
                
                self.s.rig.set_ptt(0)
                self.tx_evt.clear()
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

            if VERBOSITY>0:
                print('FLDIGI_IO PTT - Using fl - on/off=',on_off,'\tVFO=',VFO)
            
            self.lock.acquire()
            if on_off<0:

                # Query
                print('FLDIGI_IO PTT - Query ... evt set=',self.tx_evt.is_set())
                #buf=self.s.main.get_trx_status()
                buf=self.s.main.get_trx_state()
                print('\tbuf=',buf)
                state= buf in ['tx','TX']
                if state and not self.tx_evt.is_set():
                    self.tx_evt.set()
                if not state and self.tx_evt.is_set():
                    self.tx_evt.clear()
            
            elif on_off:

                # Key down
                self.tx_evt.set()
                if self.fldigi_active:
                    self.s.main.tx()
                else:
                    # Shouldn't get here anymore
                    self.s.rig.set_ptt(1)
                    
            else:
                
                # Key up
                if self.fldigi_active:
                    print('Hey A')
                    time.sleep(DELAY)
                    self.s.main.rx()
                    time.sleep(DELAY)
                    print('Hey B')
                else:
                    # Shouldn't get here anymore
                    self.s.rig.set_ptt(0)
                #self.tx_evt.clear()
            self.lock.release()

        else:

            if VERBOSITY>0:
                print('FLDIGI_IO PTT - Using direct - on/off, vfo=:',on_off,VFO)
            if on_off:
                self.tx_evt.set()
                self.send('FT3;TX1;')
            else:
                self.send('TX0;')
                time.sleep(DELAY)
                self.send('FT2;')
                self.tx_evt.clear()
                
        if VERBOSITY>0:
            print('... FLDIGI/FLRIG PTT Done.')
            
        return state

    # Routine to get/put rig split mode
    def split_mode(self,opt):
        if VERBOSITY>0:
            print('FLDIGI_IO - SPLIT_MODE: opt=',opt)

        if self.fldigi_active:
            print('FLDIGI_IO: SPLIT_MODE not available yet for FLDIGI')
            return

        if opt==-1:
            #print('\nQuerying split ...')
            self.lock.acquire()
            buf=self.s.rig.get_split()
            self.lock.release()
            if VERBOSITY>0:
                print('SPLIT: buf=',buf)
            return buf==1

        elif opt in [0,1]:
            
            self.lock.acquire()
            #buf=self.s.rig.set_split(byte(opt))
            buf=self.s.rig.set_split(opt)
            self.lock.release()
                
        else:
            
            print('FLDIGI_IO - SPLIT_MODE: Invalid opt',opt)
            return -1
            

    # Routine to get/put fldigi squelch mode
    def squelch_mode(self,opt):
        VERBOSITY=1
        if VERBOSITY>0:
            print('FLDIGI_IO - SQUELCH_MODE: opt=',opt)

        if self.flrig_active:
            print('FLDIGI_IO: SQUELCH_MODE not available yet for FLRIG')
            return

        if opt==-1:
            #print('\nQuerying split ...')
            self.lock.acquire()
            buf=self.s.main.get_squelch()
            self.lock.release()
            if VERBOSITY>0:
                print('SQUELCH: buf=',buf)
            return buf==1
            
        elif opt in [0,1]:
                
            self.lock.acquire()
            buf=self.s.main.set_squelch(opt==1)
            self.lock.release()
                
        else:
            
            print('FLDIGI_IO - SQUELCH_MODE: Invalid opt',opt)
            return -1
            

    # Routine to get/put fldigi modem carrier freq
    def modem_carrier(self,frq=None):
        if VERBOSITY>0:
            print('FLDIGI_IO - MODEM_CARRIER: frq=',frq)
            
        if self.flrig_active:
            print('FLDIGI_IO: MODEM_CARRIER not available yet for FLRIG')
            return 0

        if frq==None:
            
            print('\nQuerying modem carrier ...')
            self.lock.acquire()
            buf=self.s.modem.get_carrier()
            self.lock.release()
            if VERBOSITY>0 or True:
                print('CARRIER: buf=',buf,type(buf))
            return int(buf)

        else:
            
            print('\nSetting modem carrier ...',frq)
            self.lock.acquire()
            buf=self.s.modem.set_carrier(int(frq))
            self.lock.release()
            if VERBOSITY>0 or True:
                print('CARRIER: buf=',buf,type(buf))
            return int(buf)


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

            
    def init_keyer(self):
        print('Keyer not yet supported for FLRIG')
        return -1


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


    def cwio_set_wpm(self,wpm):
        VERBOSITY=1
        if VERBOSITY>0:
            print('FLDIGI_IO - CWIO SET WPM wpm=',wpm)
        self.wpm=wpm
        self.s.rig.cwio_set_wpm(wpm)

    def cwio_get_wpm(self):
        VERBOSITY=1
        if VERBOSITY>0:
            print('FLDIGI_IO - CWIO GET WPM wpm=',self.wpm)
        return self.wpm
    
    def cwio_write(self,txt):
        VERBOSITY=1
        if VERBOSITY>0:
            print('FLDIGI_IO - CWIO WRITE txt=',txt)
        self.s.rig.cwio_text(txt)
        #self.s.rig.set_ptt(1)

    def get_rx_buff(self):
        VERBOSITY=1
        if VERBOSITY>0:
            print('GET_RX_BUFF...')
            
        acq=self.lock.acquire(timeout=1.0)
        if acq:
            n = self.s.text.get_rx_length()
            print('\tn=',self.nrx,n)
            if n>self.nrx:
                s = self.s.text.get_rx(self.nrx,n)
            else:
                s=''
            print('\t',s,show_ascii(str(s)))
            self.nrx=n
            self.lock.release()
        else:
            print('FLDIGI GET RX BUFF: Failed to acquire lock')
            s=''
            self.nrx=0

        return str(s)

    def put_tx_buff(self,txt,HALT=False):
        print('PUT_RX_BUFF... txt=',txt)
        self.lock.acquire()
        ntries=0
        while ntries<10:
            try:
                ntries+=1
                if HALT:
                    self.s.text.clear_tx()
                else:
                    self.s.text.add_tx(txt)
                break
            except:
                time.sleep(DELAY)
        else:
            print('\nPUT_RX_BUFF: *** ERROR *** Failed to insert txt after 10 tries!!!!!\n')
        self.lock.release()

        
        

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
        print("\nFLDIGI_IO->OPEN tag=",tag,": Opening XMLRPC connection to FLLOG on ",addr)
        self.s = ServerProxy(addr)

        # Init assuming failure
        self.fllog_active=False
        self.v4 = False
        
        # Look for fllog - need to add error trapping 
        info = self.s.system.listMethods()
        print(info)
        print("\nConnected to FLLOG")
        
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
                error_trap('FLDIGI IO->FLLOG PROBE - No help available for method -'+m)

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
        tags = re.findall(r'<(.*?):(\d+).*?>([^<]+)',rec)
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


        
