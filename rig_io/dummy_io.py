############################################################################################
#
# Dummy Rig IO - Rev 1.0
# Copyright (C) 2021 by Joseph B. Attili, aa2il AT arrl DOT net
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

############################################################################################

VERBOSITY=0

############################################################################################

# Setup basic logging
logging.basicConfig(
    format="%(asctime)-15s [%(levelname)s] DUMMY_IO:%(funcName)s:\t%(message)s",
    level=logging.INFO)

# Object with dummy connection
class no_connect:
    def __init__(self,host=0,port=0):
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
        self.rig_type2  = None
        self.tlast      = None

    def get_band(self,frq=None,VFO='A'):
        if VERBOSITY>0:
            logging.info('Ignoring call')
        return 0
        
    def set_band(self,b,VFO='A'):
        if VERBOSITY>0:
            logging.info('Ignoring call')
        return 0
    
    def get_ant(self):
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
            logging.info('Ignoring call')
        return 'CW'
        
    def set_mode(self,mode,VFO='A',Filter=None):
        if VERBOSITY>0:
            logging.info('Ignoring call')
        return '0'
        
    def get_freq(self,VFO='A'):
        if VERBOSITY>0:
            logging.info('Ignoring call')
        return 0

    def set_freq(self,f,VFO='A'):
        if VERBOSITY>0:
            logging.info('Ignoring call')
            #print('Ignoring call to SET_FREQ')
        return 0

    def set_vfo(self,rx=None,tx=None):
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
    
    def get_response(self,cmd):
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

    def split_mode(self,opt):
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
        return 0,0,0
    
    def set_date_time(self,VERBOSITY=0):
        if VERBOSITY>0:
            logging.info('Ignoring call')

    
