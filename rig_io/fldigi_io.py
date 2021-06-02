############################################################################################
#
# Fldigi IO - Rev 1.0
# Copyright (C) 2021 by Joseph B. Attili, aa2il AT arrl DOT net
#
# Functions to control rig through FLDIGI or FLRIG from python.
# See methods.txt for list of methods for these two protocols
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
    
import threading
import time
from .util import *
import socket
from .ft_tables import DELAY, Decode_Mode, modes
import re

#################################################################################################

VERBOSITY=0

#################################################################################################

class fldigi_xlmrpc:
    def __init__(self,host,port,tag='',MAX_TRYS=10):
        #        parent.title("Rig Control via FLDIGI")
        #        print "Rig Control via FLDIGI"

        if host==0:
            # HOST = 'localhost'
            host = '127.0.0.1'

        self.host       = host
        self.port       = port
        self.tag        = tag
        self.connection = 'FLDIGI'
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
        self.rig_type = 'UNKNOWN'
        
        # Get version info
        try:
            # Look for fldigi
            self.version = self.s.fldigi.version()
            self.v4 = int( self.version.split('.')[0] ) >=4
            print("fldigi version: ",self.version,self.v4)
            self.fldigi_active=True
            self.flrig_active=False

            # Kludge
            #socket.setdefaulttimeout(5)           # set the timeout to N seconds
            socket.setdefaulttimeout(None)      # sets the default back

        except:

            try:
                # Look for flrig
                info = self.s.rig.get_info()
                self.version = 'flrig'
                print("Connected to flrig")
                self.flrig_active=True

                # Probe FLRIG interface
                self.flrig()
            except:
                print(tag,": Unable to open FLDIGI/FLRIG")

        # Determine which rig is on the other end
        self.active = self.fldigi_active or self.flrig_active
        if False:
            # This doesn't work for the FT991a
            buf = self.get_response('FA;')
            print('buf=',buf,len(buf))
            if len(buf)>11:
                self.rig_type = 'Kenwood'
            else:
                self.rig_type = 'Yaesu'

        if self.fldigi_active:
            # Looking for something that distinguishes the rigs ...
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
                self.rig_type = 'Yaesu'
                self.rig_type2 = 'FT991a'
                name = self.s.rig.get_name()
                print('name=',name)
            else:
                print('*** Need some more code to figure out what rig we are attached to ***')
                buf = self.get_response('FA;')
                print('buf=',buf,len(buf))
                if len(buf)>11:
                    self.rig_type = 'Kenwood'
                    self.s.rig.set_name("TS-850")
                    self.rig_type2 = 'TS850'
                else:
                    self.rig_type = 'Yaesu'
                    self.s.rig.set_name("FTDX-3000")
                    self.rig_type2 = 'FTdx3000'

        # Set rig name
        print('FLDIGI_OPEN: rig type=',self.rig_type)
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
            
            if self.fldigi_active:
                methods = self.s.fldigi.list()
                for m in methods:
                    print(m)
                sys.exit(0)
            else:
                self.flrig()

                
    # Test function to probe FLRIG interface
    def flrig(self):
        print("Probing FLRIG interface:")
        print(self.s)
        #print dir(self.s)
        #print getattr(self.s)
        #print help(self.s)

        #print self.s.system.listMethods()
        methods = self.s.system.listMethods()
        for m in methods:
            print(m)

        #print self.s.rig.list_methods()
        methods = self.s.rig.list_methods()
        for m in methods:
            print(m)

        if False:
            print("\nRig info: ",self.s.rig.get_info())
            print("FA:   ",self.s.rig.send_command("FA;"))
            print("FB:   ",self.s.rig.send_command("FB;"))
            print("FB:   ",self.s.rig.send_command("FB14080000;"))
            print("FB:   ",self.s.rig.send_command("FB;"))
            #print "RA00: ",self.s.rig.send_command("RA00;")
            #        sys.exit(0)

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
            #self.lock.acquire()
            #x=float( self.s.rig.get_vfo() )
            #self.lock.release()
            print('GET_FREQ:',VFO)
            buf = self.get_response('F'+VFO+';')
            x = float(buf[2:-1])
            print('GET_FREQ:',x)
        else:
            x=0
        return x

    # Function to set rig freq 
    def set_freq(self,frq_KHz,VFO='A'):
        print('FLDIGI SET_FREQ:',frq_KHz,VFO)
        if self.fldigi_active:
            f=1000*frq_KHz
            if VFO=='A':
                self.lock.acquire()
                self.s.main.set_frequency(float(f))
                self.lock.release()
            else:
                cmd='BY;F'+VFO+str(int(f)).zfill(8)+';'
                self.send(cmd)
        elif self.flrig_active:
            #self.lock.acquire()
            #self.s.rig.set_vfo(float(frq_KHz)*1000.)
            #self.lock.release()
            f=1000*frq_KHz
            cmd='F'+VFO+str(int(f)).zfill(8)+';'
            self.send(cmd)
        else:
            f=0
        return f

    # Function to read rig band - there might be a better way to do this
    def get_band(self):
        if not self.fldigi_active and not self.flrig_active:
            return 0

        # Don't need lock here since get_freq does it
        frq = self.get_freq()
        band = convert_freq2band(frq * 1e-3)
        print('GET BAND out',band)
        return band

    # Function to set rig band - need to be able to issue BS command to get this to work better but for now
    def set_band(self,band):

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
            print("Invalid band",band)
            frq = 0

        print("SET BAND ",band,frq)
        if frq>0:
            self.lock.acquire()
            self.set_freq(frq*1000)
            self.lock.release()

    # Function to read rig mode 
    def get_mode(self,VFO='A'):
        if VFO=='A':
            self.lock.acquire()
            m=self.s.rig.get_mode()
            self.lock.release()
        else:
            cmd = 'FR4;MD0;'
            buf = self.get_response(cmd)
            time.sleep(DELAY)
            self.send('FR0;')
            #print 'GET_MODE:',buf
            m = Decode_Mode( buf[3] )
            
        return m

    # Function to read fldigi mode 
    def get_fldigi_mode(self):
        self.lock.acquire()
        if self.fldigi_active:
            m=self.s.modem.get_name()
        else:
            print('*** FLDIGI_IO: Warning - unable to read modem name ***')
            m=self.s.rig.get_mode()
        self.lock.release()
        return m

    # Dummied up for now
    def get_vfo(self):
        print('GET_VFO not available yet for FLDIGI - assumes A')
        return 'AA'
    
    # Dummied up for now
    def set_vfo(self,vfo):
        print('SET_VFO not available yet for FLDIGI - assumes A')
        return 'AA'
    
    # Function to set rig mode - return old mode
    def set_mode(self,mode,VFO='A'):
        print("SET_MODE=",mode,VFO)
        mode2=mode

        # Translate mode into something rig understands
        if mode=='RTTY' or mode=='DIGITAL' or mode=='FT8' or mode.find('PSK')>=0 or mode.find('JT')>=0:
            if not self.v4:
                mode='PSK-U'           # For some reason, this was changed in version 4
            else:
                mode='PKT-U'    
        print('mode=',mode,self.v4)

        # Translate mode into something fldigi understands
        if mode2=='DIGITAL' or mode2.find('JT')>=0 or mode2=='FT8':
            mode2='RTTY'
        elif mode2=='USB' or mode2=='LSB' or mode2=='AM':
            mode2='SSB'
        elif mode2=='PSK':
            mode2='BPSK31'
        print('mode2=',mode2)

        if VFO=='A':
        
            self.lock.acquire()
            self.s.rig.set_mode(mode)  
            if self.fldigi_active:
                mold=self.s.modem.set_by_name(mode2)
                print('mold=',mold)
                mout=self.s.modem.get_name()
            else:
                print('*** FLDIGI_IO: Warning - unable to read modem name ***')
                mout=self.s.rig.get_mode()
            self.lock.release()
            print("mout=",mout)

        else:
            c = modes[mode]["Code"]
            self.send('FR4;MD'+c+';')
            time.sleep(DELAY)
            self.send('FR0;')
            mout=mode

        print("SET MODE Done.")
        return mout

    # Function to set call 
    def set_call(self,call):
        print("SET CALL:",call)
        self.lock.acquire()
        x=self.s.log.set_call(call)
        self.lock.release()
        return x

    # Function to set log fields
    def set_log_fields(self,fields):
        if self.active:
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
        self.lock.acquire()
        call    = self.s.log.get_call()
        name    = self.s.log.get_name()
        qth     = self.s.log.get_qth()
        rst_in  = self.s.log.get_rst_in()
        rst_out = self.s.log.get_rst_out()
        ser_in  = self.s.log.get_serial_number()
        ser_out = self.s.log.get_serial_number_sent()
        self.lock.release()

        return {'Call':call,'Serial_In':ser_in,'Serial_Out':ser_out,\
                'Name':name,'QTH':qth,\
                'RST_in':rst_in,'RST_out':rst_out}

    def get_serial_out(self):
        self.lock.acquire()
        x=self.s.log.get_serial_number_sent()
        self.lock.release()
        return x

    def set_serial_out(self,x):
        self.lock.acquire()
        #x=self.s.main.set_serial_number_sent()
        self.s.main.set_counter(x)
        self.lock.release()

    # Functions to send a command directly to the rig & get the response
    def send(self,cmd):
        #print 'SEND: Waiting for LOCK...'
        self.lock.acquire()
        #print 'SEND: Got LOCK...'
        if self.active:
            #print "FLDIGI SEND:",cmd
            self.reply = self.s.rig.send_command(cmd,100)
            #print 'SEND: REPLY=',self.reply
        else:
            self.reply = ''
        #print 'SEND: Releasing LOCK...'
        self.lock.release()
        #print 'SEND: Done.'

    # Function to run a macro
    def run_macro(self,idx):
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
        if VERBOSITY>0:
            print('Sending CMD ... ',cmd)
        self.send(cmd)
        if VERBOSITY>0:
            print('Waiting for response ...')
        buf = self.recv(1024).rstrip()
        if VERBOSITY>0:
            print('...Got it',buf)

        return buf

    def set_ant(self,a):
        buf=self.get_response('BY;AN0'+str(a)+';')
        if a==1 or a==2:
            # Make sure ant tuner is on for ports 1 & 2
            buf=self.get_response('BY;AC001;')
        else:
            # Make sure ant tuner is off for port 3
            buf=self.get_response('BY;AC000;')
        
    def get_ant(self):

        for ntry in range(5):
            buf = self.get_response('AN0;')
            print('GET_ANT: buf=',buf,'/t',ntry)
            try:
                ant=int(buf[3])
                break
            except:
                ant=None
        else:
            print('$$$$$$$$ FLDIGI GET_ANT - Unable to read current antenna $$$$$$$$$$$$')

        return ant

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
        print('FLDIGI_IO PTT:',on_off,VFO)
        if VFO=='A':
            
            self.lock.acquire()
            if on_off:
                if self.fldigi_active:
                    self.s.main.tx()
                else:
                    self.s.rig.set_ptt(1)
            else:
                if self.fldigi_active:
                    self.s.main.rx()
                else:
                    self.s.rig.set_ptt(0)
            self.lock.release()

        else:
            
            if on_off:
                self.send('FT3;TX1;')
            else:
                self.send('TX0;')
                time.sleep(DELAY)
                self.send('FT2;')
                
        print('FLDIGI/FLRIG PTT Done.')



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


        
