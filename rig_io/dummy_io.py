############################################################################################
#
# Dummy Rig IO - Rev 1.0
# Copyright (C) 2021-5 by Joseph B. Attili, joe DOT aa2il AT gmail DOT com
#
# Dummied-up socket I/O routines so codes will work if there is not a
# rig connection.
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

import logging               
import threading

############################################################################################

VERBOSITY=0

############################################################################################

# Setup basic logging
logging.basicConfig(
    format="%(asctime)-15s [%(levelname)s] %(pathname)s %(funcName)s:\t%(message)s",
    level=logging.INFO)

# Object with dummy connection
class no_connect:
    def __init__(self,host=0,port=0,RIG_TYPE=None):
        print('DUMMY_IO->NO CONNECT: Init ...')

        self.s          = None
        self.active     = False
        self.connection = 'NONE'
        self.wpm        = 0
        self.freq       = 0
        self.band       = ''
        self.mode       = ''
        self.pl_tone    = 0
        self.fldigi_active=False
        self.flrig_active=False
        self.host=host
        self.port=port
        self.rig_type   = None
        self.rig_type1  = None
        self.rig_type2  = 'None'
        self.tlast      = None
        self.ntimeouts  = 0
        self.tx_evt     = threading.Event()            # Allow rig quires only when receiving

        self.default_mode = 'CW'
        self.default_freq = 0

        if RIG_TYPE=='TYT9000d':
            self.active       = True
            self.rig_type     = 'TYT'
            self.rig_type1    = 'TYT'
            self.rig_type2    = RIG_TYPE
            self.default_mode = 'FM'
            self.default_freq = 223.5e6
            
        
    def get_band(self,frq=None,VFO='A'):
        if frq==None or frq<0:
            if VERBOSITY>0:
                print('Hey DUMMY GET_BAND: frq=',frq,'\tVFO=',VFO)
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
            band=1.25
        else:
            band='70cm'
            
        if VERBOSITY>0:
            print("DUMMY: Current rig freq=",frq," MHz --> ",band,"m")

        return band

    def set_band(self,b,VFO='A'):
        if VERBOSITY>0:
            logging.info('Ignoring call')
        return 0

    def set_breakin(self,onoff):
        if VERBOSITY>0:
            logging.info('Ignoring call')
        return 0
    
    def get_ant(self):
        if VERBOSITY>0:
            logging.info('Ignoring call')
        return 0

    def set_if_shift(self,shift):
        if VERBOSITY>0:
            logging.info('Ignoring call')
        return 0
    
    def set_ant(self,a,VFO='A'):
        if VERBOSITY>0:
            logging.info('Ignoring call')
        return 0
        
    def get_fldigi_mode(self):
        if VERBOSITY>0:
            logging.info('Ignoring call')
        return '0'

    def get_mode(self,VFO='A'):
        if VERBOSITY>0:
            print('Hey DUMMY GET_MODE: VFO=',VFO)
            logging.info('Ignoring call')
        return self.default_mode
        
    def set_mode(self,mode,VFO='A',Filter=None):
        if VERBOSITY>0:
            logging.info('Ignoring call')
        self.default_mode=mode
        return mode
        
    def get_freq(self,VFO='A'):
        if VERBOSITY>0:
            print('Hey DUMMY GET_FREQ: VFO=',VFO)
            logging.info('Ignoring call')
        return self.default_freq

    def set_freq(self,f,VFO='A'):
        if VERBOSITY>0:
            logging.info('Ignoring call')
            #print('Ignoring call to SET_FREQ')
        self.default_freq=f
        return f

    def set_filter(self,filt,mode=None):
        if VERBOSITY>0:
            logging.info('Ignoring call')
        return 0

    def set_vfo(self,rx=None,tx=None,op=None):
        if VERBOSITY>0:
            logging.info('Ignoring call')
        return

    def set_vfo_direct(self,rx=None,tx=None,op=None):
        if VERBOSITY>0:
            logging.info('Ignoring call')
        return
    
    def send(self,cmd):
        if VERBOSITY>0:
            logging.info('Ignoring call')
        return 0

    def set_log_fields(self,fields):
        if VERBOSITY>0:
            logging.info('Ignoring call')
        return 0
        
    def set_call(self,call):
        if VERBOSITY>0:
            logging.info('Ignoring call')
        return 0

    def get_serial_out(self):
        if VERBOSITY>0:
            logging.info('Ignoring call')
        return 0
    
    def get_response(self,cmd,VERBOSITY=0):
        if VERBOSITY>0:
            logging.info('Ignoring call')
        return ''

    def get_info(self):
        if VERBOSITY>0:
            logging.info('Ignoring call')
        return ''
    
    def set_speed(self,wpm):
        if VERBOSITY>0:
            logging.info('Ignoring call')
        return 0

    def get_PLtone(self):
        if VERBOSITY>0:
            logging.info('Ignoring call')
        return 0
    
    def get_filters(self,VFO='A'):
        if VERBOSITY>0:
            logging.info('Ignoring call')
        #return [None,None]
        return ['Wide','500 Hz']

    def tuner(self,opt):
        if VERBOSITY>0:
            logging.info('Ignoring call')
        return 0
    
    def read_meter(self,meter):
        if VERBOSITY>0:
            logging.info('Ignoring call')
        return 0

    def read_speed(self):
        if VERBOSITY>0:
            logging.info('Ignoring call')
        return 0
    
    def get_position(self):
        if VERBOSITY>0:
            logging.info('Ignoring call')
        return [None,None]

    def modem_carrier(self,frq=None):
        if VERBOSITY>0:
            logging.info('Ignoring call')
        return 0

    def split_mode(self,opt):
        if VERBOSITY>0:
            logging.info('Ignoring call')
        return 0

    def squelch_mode99(self,opt):
        if VERBOSITY>0:
            logging.info('Ignoring call')
        return 0
    
    def set_power(self,p):
        if VERBOSITY>0:
            logging.info('Ignoring call')
        return 0
        
    def set_position(self,pos):
        if VERBOSITY>0:
            logging.info('Ignoring call')
        return 0

    def recorder(self,on_off=None):
        if VERBOSITY>0:
            logging.info('Ignoring call')
        return False

    def get_date_time(self,VERBOSITY=0):
        if VERBOSITY>0:
            logging.info('Ignoring call')
        return '20250101','000000','0'
    
    def set_date_time(self,VERBOSITY=0):
        if VERBOSITY>0:
            logging.info('Ignoring call')

    def get_vfo(self):
        if VERBOSITY>0:
            logging.info('Ignoring call')
        return 'A'
    
    def set_sub_dial(self,func='CLAR'):
        if VERBOSITY>0:
            logging.info('Ignoring call')
        return 
    
    def get_monitor_gain(self):
        if VERBOSITY>0:
            logging.info('Ignoring call')
        return 0
    
    def set_monitor_gain(self,gain):
        #print('DUMMY_IO: Set Monitor Level - Ignored')
        if VERBOSITY>0:
            logging.info('Ignoring call')
        return 

    def sat_mode(self,opt):
        if VERBOSITY>0:
            logging.info('Ignoring call')
        return 

    def set_PLtone(self,tone):
        if VERBOSITY>0:
            logging.info('Ignoring call')
        return 

    def frontend(self,opt,pamp=0,atten=0):
        VERBOSITY=1
        if VERBOSITY>0:
            print('DUMMY FRONTEND: opt=',opt,'\tpamp=',pamp,'\tatten=',atten,
                  '\trig1=',self.rig_type1)
        return
    

# Dummy for the TYT9000d 220 FM rig so it will return something useful
# Should be able to eliminate this soon ...
class tyt9000d_connect(no_connect):

    def __init__(self):
        no_connect.__init__(self)
        self.active     = True
        self.rig_type   = 'TYT'
        self.rig_type1  = 'TYT'
        self.rig_type2  = 'TYT9000d'
    
    def get_mode(self,VFO='A'):
        if VERBOSITY>0:
            print('Hey TYT GET_MODE: VFO=',VFO)
            logging.info('TYT9000d GET MODE')
        return 'FM'
        
    def get_freq(self,VFO='A'):
        if VERBOSITY>0:
            print('Hey TYT GET_FREQ: VFO=',VFO)
            logging.info('TYT9000d GET FREQ')
        return 223.5e6

    
