############################################################################################
#
# Hamlib Rig IO - Rev 1.0
# Copyright (C) 2021-4 by Joseph B. Attili, aa2il AT arrl DOT net
#
# Socket I/O routines related to commanding the radio via hamlib.
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

from .ft_tables import *
from .direct_io import direct_connect
import socket
import time
import select
from .icom_io import icom_civ
import threading
from datetime import timedelta,datetime
from pytz import timezone
from .icom_io import show_hex

############################################################################################

VERBOSITY=0
USE_LOCK=True

############################################################################################

# Object for connection via hamlib
# We use direct_connect as the base class so we can inherit all the
# direct commands that we may need as hamlib doesn't provide everything
class hamlib_connect(direct_connect):
    def __init__(self,host,port,baud,tag=''):
        if baud==0:
            baud = BAUD  

        if host==0:
            host = HOST

        self.fldigi_active=False
        self.flrig_active=False
        self.host=host
        self.baud=baud
        if USE_LOCK:
            self.lock       = threading.Lock()             # Avoid collisions between various threads

        if port==0:
            if tag=='ROTOR':
                port=DEFAULT_PORTS["HAMLIB"]['ROTOR']
            elif tag=='KEYER':
                port = HAMLIB_PORT+0
            else:
                port = HAMLIB_PORT
        self.port=port

        self.wpm       = 0
        self.freq      = 0                # in Hz
        self.band      = ''
        self.mode      = ''
        self.rig_type  = 'Hamlib'
        self.rig_type1 = 'Hamlib'
        self.rig_type2 = 'Hamlib'
        self.tlast     = 0
        self.pl_tone   = 0
        self.rotor     = False
        self.last_cmd  = ''
        self.sub_dial_func=None
        
        try:
            self.s = socket.socket()
            self.s.connect((host, port))

            # So far so good - make sure its really an active connection
            print('\n*** HAMLIB_IO: Hamlib Server Detected - checking if it is still active...',host,port)
            self.s.settimeout(2.0)
            if tag=='ROTOR':
                frq = self.get_position()[0]
            else:
                frq = self.get_freq()
                if frq==-1:
                    # Try again
                    frq = self.get_freq()
            print('HAMLIB_IO: frq=',frq,' on port',port)
            self.s.settimeout(None)

            if frq>=0:
                print('\nHAMLIB_IO: Opened HAMLIB socket on host',host,' @ port',port)
                self.connection='HAMLIB'
                self.active=True
            else:
                print('\nHAMLIB_IO: *** Unable to create HAMLIB socket on host',host,' @ port',port,'***')
                self.active=False
                return
                
        except socket.error:
            print('\nHAMLIB_IO: *** Socket Error - Unable to create HAMLIB socket on host',host,' @ port',port,'***')
            self.active=False
            return

        # Determine which rig is on the other end
        print('HAMLIB_IO: Hamlib Server so far so good - rig on other end ...',host,port)
        #caps = self.get_response('1',N=100).splitlines()       # Read capabilities - this is a long one
        caps = self.get_response('1',wait=True).splitlines()       # Read capabilities - this is a long one
        print('HAMLIB_IO: caps=',caps)
        caps2 = OrderedDict()
        for line in caps:
            a=line.split(':')
            caps2[a[0]]=''.join(a[1:]).strip()
        print('HAMLIB_IO: caps2=',caps2)
        print('HAMLIB_IO: Model=',caps2['Model name'])
        
        # Most rigs will respond with a unique ID
        # Those that don't, we do it the hard way
        x = self.get_response('_')
        print('HAMLIB_IO: info=',x)
        if caps2['Model name']=='pySDR':
            self.rig_type1 = 'SDR'
            self.rig_type2 = 'pySDR'            # pySDR
        elif x=='ID0460':
            self.rig_type1 = 'Yaesu'
            self.rig_type2 = 'FTdx3000'
        elif x=='ID0670':
            self.rig_type1 = 'Yaesu'
            self.rig_type2 = 'FT991a'
        elif caps2['Model name']=='FT-2000':
            self.rig_type1 = 'Yaesu'
            self.rig_type2 = 'FT-2000'            # Was dummy for hamlibserver
        elif caps2['Model name']=='TS-850':
            self.rig_type1 = 'Kenwood'
            self.rig_type2 = 'TS850'
        elif caps2['Model name']=='IC-9700':
            self.rig_type1 = 'Icom'
            self.rig_type2 = 'IC9700'
            self.civ = icom_civ(self.rig_type2)            
        elif caps2['Model name']=='IC-7300':
            self.rig_type1 = 'Icom'
            self.rig_type2 = 'IC7300'
            self.civ = icom_civ(self.rig_type2)            
        elif caps2['Model name']=='GS-232B':
            self.rig_type1 = 'Yaesu'
            self.rig_type2 = 'GS-232B'
            self.rotor     = True
        elif caps2['Model name']=='Dummy':
            self.rig_type1 = 'Dummy'
            self.rig_type2 = 'Dummy'
            self.rotor     = True
        else:
            print('\n*** HAMLIB_IO - HAMLIB INIT: Unknown rig on the other end ***',x)
            print('Giving up & aborting :-(')
            self.rig_type  = 'UNKNOWN'
            self.rig_type1 = 'UNKNOWN'
            self.rig_type2 = 'UNKNOWN'
            sys.exit(0)

        print('HAMLIB_IO: Rig type=',self.rig_type,self.rig_type2)

        if self.rotor:
            try:
                self.min_az = float( caps2['Min Azimuth'] )
                self.max_az = float( caps2['Max Azimuth'] )
                self.min_el = float( caps2['Min Elevation'] )
                self.max_el = float( caps2['Max Elevation'] )
            except:
                self.min_az = -180
                self.max_az = 180
                self.min_el = 0
                self.max_el = 180
            print('Min/Max Az:',self.min_az,self.max_az,'\t',\
                  'Min/Max El:',self.min_el,self.max_el)
        
        if False:
            # Test to make sure hamlib is still alive
            #self.s.settimeout(1.0)
            #print 'hey 4'

            x = self.get_response('f')
            print('f=',x)
            x = self.get_response('m')
            print('m=',x)
            x = self.get_response('v')
            print('v=',x)
            x = self.get_response('t')
            print('t=',x)
            x = self.get_response('y')
            print('ant=',x)

            #x = self.get_response('F760000')
            #print 'F=',x
                
        
    def send(self,cmd):
        if VERBOSITY>0:
            print( 'HAMLIB_IO->SEND: cmd='+cmd)
        self.last_cmd=cmd
        self.s.send(cmd.encode())
    
    def recv(self,n=1024):
        #self.s.settimeout(1.0)
        x = self.s.recv(n).decode("utf-8") 
        #self.s.settimeout(None)
        if VERBOSITY>0:
            print('HAMLIB_IO->RECV: x=',x)

        if x[:4]=='RPRT':
            print('HAMLIB_IO->RECV: x=',x,'\tlen=',len(x),'\tcmd=',self.last_cmd)
            if int(x.split(' ')[1])<0:
                print('HAMLIB_IO->RECV: *** WARNING *** Error code returned *** cmd=',
                      self.last_cmd,'\tresponse=',x)
            
        return x.rstrip()                     # Remove newline at end

    def get_response(self,cmd,N=1,wait=False,VERBOSITY=0):
        USE_TIMEOUT=True
        if VERBOSITY>0:
            print('HAMLIB_IO: Get response: cmd=',cmd,'\t',cmd[-1])

        if USE_LOCK:
            if VERBOSITY>0:
                print('HAMLIB_IO GET_RESPONSE - Waiting for lock')
            self.lock.acquire()

        if USE_TIMEOUT:
            self.s.settimeout(2.0)
            
        if cmd[-1] == ';':
            # Yaseu/Kenwood command
            #print '************************* HAMLIB_IO: GET_RESPONSE - Direct commands not working yet',cmd
            #return ''
            #cmd2='w '+cmd[:-1]+'\n'
            cmd2='w '+cmd[:-1]
            if cmd2[-1]!=';':
                cmd2+=';\n'
            else:
                cmd2+='\n'
            if VERBOSITY>0:
                print('HAMLIB GET_RESPONSE: Sending Yaesu/Kenwood',cmd2)
            print('HAMLIB GET_RESPONSE: **** WARNING *** Yaesu/Kenwood direct commands are flaky !!!!!',cmd2)
            if False:
                if USE_LOCK:
                    self.lock.release()
                return ''
            self.send(cmd2)
        elif cmd[0].lower() in 'fmtvy1_':
            if VERBOSITY>0:
                print('HAMLIB_IO: Get_Response: Single letter command:',cmd)
            self.send(cmd+'\n')
        elif cmd[0]=='w' and cmd[-1]!=';':
            cmd2=cmd+';'
            self.send(cmd2)
        else:
            if VERBOSITY>0:
                print('HAMLIB_IO: Get Response - **** WARNING *** Not sure what to do????',cmd)
            self.send(cmd+'\n')
            
        x=self.recv(N*1024)
        
        if USE_TIMEOUT:
            self.s.settimeout(None)

        if wait:

            #s.setblocking(0)
            to=0.1
            time.sleep(1)
            ready = select.select([self.s], [], [], to)
            while ready[0]:
                xx=self.recv(1024)
                x+=xx
                time.sleep(to)
                ready = select.select([self.s], [], [], to)
                print(len(x),len(xx),ready[0])

            if USE_LOCK:
                self.lock.release()
                if VERBOSITY>0:
                    print('HAMLIB_IO GET_RESPONSE - Lock released 1')
            return x
        
            # This doesn't work
            done=False
            self.s.settimeout(0.1)
            while not done:
                try:
                    xx=self.recv(1024)
                    x+=xx
                    print(len(x),len(xx))
                except:
                    done = True
                    print('Socket timeout')
            self.s.settimeout(None)
        
        if VERBOSITY>0:
            print('resp=',x)
        if USE_LOCK:
            self.lock.release()
            if VERBOSITY>0:
                print('HAMLIB_IO GET_RESPONSE - Lock released 2')
        return x

    
    def get_freq(self,VFO='A'):
        #VERBOSITY=0
        if VERBOSITY>0:
            print('HAMLIB_IO: GET_FREQ: vfo=',VFO)
        if self.rig_type1 == 'Icom' or False:
            # This actually might work for all rigs but only tested on 9700 so far
            self.select_vfo(VFO)            
        elif VFO!='A':
            #print('*** ERROR *** HAMLIB_IO: GET_FREQ: VFO B not implemented yet - ',self.rig_type1)
            #return
            # Need to clean this up!!!!
            # Hamlib doesn't seem to have a nice way of changing freq of VFO B without interrupting the
            # rig so just issue the direct FB command for Yaesu and Kenwood rigs
            buf = self.get_response('F'+VFO+';')
            if buf[0]=='?':
                buf = self.get_response('F'+VFO+';')
        
            try:
                frq = float(buf[2:-1])
            except:
                print('HAMLIB GET_FREQ: Unable to read freq - buf=',buf)
                frq=0

            self.freq=frq
            return frq
            
        # Hamlib can be rather slow so do a crude "debouncing"
        # Not sure why I thought this was necessary???!!!!  Perhaps for v3.3???
        # If this works out, get rid of dt and tlast
        dt = time.time() - self.tlast
        #print 'HAMLIB_IO: GET_FREQ: B',dt
        if dt>1.5 or True:
            #print 'HAMLIB_IO: GET_FREQ: C'
            cmd='f'
            x = self.get_response('f')
        else:
            cmd='bounce'
            x=self.freq
        #print 'HAMLIB_IO: GET_FREQ: x=',x,type(x)
        
        try:
            if isinstance(x,str):
                a=x.split('\n')
                x=a[0]
            frq=float(x)
        except:
            print('HAMLIB_IO: GET_FREQ: Unable to read freq',x)
            return -1
        if VERBOSITY>0:
            print('HAMLIB_IO: Get freq',frq,VFO)
            
        self.freq = frq
        #print('HAMLIB_IO: Get Freq',cmd,frq)
        return frq
    

    def set_freq(self,frq_KHz,VFO='A'):
        #VERBOSITY=1
        if VERBOSITY>0:
            print('HAMLIB_IO->SET FREQ: frq=',frq_KHz,'\tVFO=',VFO,
                  '\tself.freq=',self.freq)

        if self.rig_type1 == 'Icom' or False:
            # This actually might work for all rigs but only tested on 9700 so far
            self.select_vfo(VFO)            
        #elif VFO!='A':
            #print('\n*** ERROR *** HAMLIB_IO SET_FREQ: VFO B not implemented yet\n')
            #return
            
        self.tlast = time.time()
        if VFO=='A' or self.rig_type1 == 'Icom':
            # Change freq of VFO A using regular hamlib F command
            self.freq  = frq_KHz*1e3
            cmd='F '+str( int(self.freq) ).zfill(8)
        elif VFO=='B' and self.rig_type1 == 'Dummy':
            frq  = int( frq_KHz*1000 )
            cmd='I '+str( int(frq) ).zfill(8)
        else:
            # Hamlib doesn't seem to have a nice way of changing freq of VFO B without interrupting the
            # rig so just issue the direct FB command for Yaesu and Kenwood rigs
            # The second FB is just to make sure rig responds
            frq  = int(frq_KHz*1000)
            cmd = 'F'+VFO+str(frq).zfill(8)+";FB;"

        if VERBOSITY>0:
            print('cmd=',cmd)
        buf=self.get_response(cmd)
        if VERBOSITY>0:
            print('HAMLIB SET_FREQ: buf=',buf)
            
        return self.freq

    def set_band(self,b):
        if VERBOSITY>0:
            print('HAMLIB_IO: Set band',b)
            
        b=str(b)
        if b[-1]!='m':
            b = b+'m'
        code = bands[b]["Code"]
        cmd = 'BY;BS'+str(code).zfill(2)+';'
        print('HAMLIB_IO SET_BAND:',b,cmd)
        buf=self.get_response(cmd)
        print('HAMLIB_IO SET_BAND:',buf)

    def set_mode(self,mode,VFO='A',Filter=None):
        #VERBOSITY=1
        if VERBOSITY>0:
            print('HAMLIB_IO - SET MODE: mode=',mode,'\tVFO=',VFO,'\tFilter=',Filter)

        bw=None
        if Filter and type(Filter) is list:
            bw=Filter[1]
            Filter=Filter[0]
            
        if mode==None:
            return
        elif mode in ['RTTY','DIGITAL','FT8'] or mode.find('PSK')>=0 or mode.find('JT')>=0:
            mode='PKTUSB'
            if not bw:
                bw=2400
        elif mode in ['CW','CWUSB','CW-USB']:
            mode='CW'
            if not bw:
                if Filter=='Wide':
                    bw=500
                else:
                    bw=200
        elif mode in ['CWLSB','CW-LSB','CW-R']:
            mode='CWR'
            if not bw:
                if Filter=='Wide':
                    bw=500
                else:
                    bw=200
        else:
            if not bw:
                bw=2400

        # Form hamlib command
        if VFO in 'AM':
            # VFO A or Main
            cmd  = 'M '+mode+' '+str(bw)
        elif VFO in 'BS':
            # VFO B or Sub
            cmd  = 'X '+mode+' '+str(bw)
        else:
            print('HAMLIB_IO - SET MODE: Unknown VFO',VFO,mode)
            return

        # Send command to set mode & filter BW
        buf=self.get_response(cmd)
        if VERBOSITY>0:
            print('HAMLIB_IO - SET MODE: mode,VFO=',mode,VFO,'\tcmd=',cmd)
            print('HAMLIB_IO - SET MODE: Response buf=',buf)

        # Set roofing filter also
        if self.rig_type1=='Yaesu':
            if mode in ['CW','CWR']:
                cmd  = 'L ROOFINGFILTER 4'
            elif mode in ['AM']:
                cmd  = 'L ROOFINGFILTER 2'
            elif mode in ['FM']:
                cmd  = 'L ROOFINGFILTER 1'
            else:
                cmd  = 'L ROOFINGFILTER 3'

            buf=self.get_response(cmd)
            if VERBOSITY>0:
                print('HAMLIB_IO - SET MODE: Setting roofing filter cmd=',cmd)
                print('HAMLIB_IO - SET MODE: Response buf=',buf)
        
                
    def get_mode(self,VFO='A'):
        #VERBOSITY=1
        if VERBOSITY>0:
            print('HAMLIB_IO: Get mode - vfo=',VFO)

        use_direct=False     # True
            
        if VFO=='A':
            cmd  = 'm'
        elif VFO=='B':
            # Hamlib interrupts the rig so do it using direct commands instead
            if self.rig_type1=='Yaesu' and use_direct:
                cmd = 'OI;'
                if self.rig_type2=='FT991a':
                    idx = 21
                else:
                    idx = 20
            else:
                cmd  = 'x'
        else:
            print('HAMLIB_IO: Get mode Unknwo VFO',VFO)
            return ''
        
        buf = self.get_response(cmd)
        if VERBOSITY>0:
            print('HAMLIB_IO: GET_MODE: cmd=',cmd,'\tbuf=',buf)

        if VFO=='B' and self.rig_type1=='Yaesu' and use_direct:
            print('idx=',idx)
            mode = Decode_Mode( buf[idx] )
        else:
            x=buf.split("\n")
            mode=x[0]

        if VERBOSITY>0:
            print('HAMLIB_IO: Get Mode',cmd,mode)
        return mode


    def set_filter(self,filt,mode=None):
        #VERBOSITY=1
        if VERBOSITY>0:
            print('\nHAMLIB_IO SET_FILTER: filt=',filt,'\tmode=',mode,mode[0:2])

        if mode==None:
            mode=self.get_mode()
            
        if filt in ['Auto','Narrow','Wide']:
            if mode in ['USB','SSB','LSB']:
                filt=['Wide','2400']
            elif mode[0:2]=='CW':
                filt=['Narrow','200']           # Was 500
            elif mode in ['RTTY','DATA']:
                filt=['Wide','3000']
            elif filt=='Auto':
                filt=['Wide']
                
        if not type(filt) is list:
            filt=[filt]
        
        if VERBOSITY>0:
            print('\nHAMLIB_IO SET_FILTER: filt=',filt,'\tmode=',mode)

        self.set_mode(mode,Filter=filt)
        #sys.exit(0)
        
    
    def get_ant(self):
        VERBOSITY=1
        if VERBOSITY>0:
            print('HAMLIB_IO: Get Ant',self.rig_type,self.rig_type1,self.rig_type2)
        
        if True:
            # The 'y' command isn't available on all rigs but its really
            # only useful for the FTdx3000 anyway
            if self.rig_type2=='FTdx3000':
                if False:
                    # V3 
                    ant = int( self.get_response('y') ) + 1         # V3
                elif False:
                    # They seemed to have hosed this up in v4.2 so just do it directly for now
                    buf = self.get_response('AN0;')
                    ant=int(buf[3])
                else:
                    # They changed command and response in V4 - ugh!
                    # Need my code patch to hamlib for this to work.
                    if VERBOSITY>0:
                        print('HAMLIB_IO: Sending y command...')
                    x = self.get_response('y 0',VERBOSITY=VERBOSITY).split('\n')
                    if VERBOSITY>0:
                        print('HAMLIB_IO: Get Ant: x=',x)
                    xx=x[0]
                    if len(xx)==1 and False:
                        ant=int(xx)
                    else:
                        ant=int( xx[3] )
                    if VERBOSITY>0:
                        print('HAMLIB_IO: Get Ant: ant=',ant)
            else:
                ant = 1
        else:
            try:
                ant = int( self.get_response('y') ) + 1
            except:
                ant = 1

        if VERBOSITY>0:
            print('HAMLIB_IO GET_ANT: buf=',ant)
        return ant

    def set_ant(self,a,VFO='A'):
        if VERBOSITY>0:
            print('HAMLIB_IO: Set ant',a)
        # The 'Y' command isn't avaiable on all rigs but its really
        # only useful for the FTdx3000 anyway
        if self.rig_type2=='FTdx3000':
            if False:
                # V3 
                buf = self.get_response('Y'+str(int(a)-1))
            else:
                # They changed command and response in V4 - ugh!
                buf = self.get_response('Y '+str(int(a))+' 0' )
            if a==1 or a==2:
                # Make sure ant tuner is on for ports 1 & 2
                self.tuner(1)
            else:
                # Make sure ant tuner is off for port 3
                self.tuner(0)

    # Function to effect pressing of TUNE button
    def tuner(self,opt):
        if VERBOSITY>0:
            print('HAMLIB TUNER:',opt)
        if opt==-1:
            if self.rig_type2=='FT991a':
                # Hamlib really doesn't work too well
                buf=self.get_response('AC;')
                print('TUNER: buf=',buf)
                return int(buf[4])
            else:
                buf=self.get_response('u tuner')
                print('TUNER: buf=',buf)
                return buf
        elif opt==0 or opt==1:
            buf=self.get_response( 'U TUNER '+str(opt) )
        elif opt==2:
            # Hamlib doesnt work
            buf=self.get_response('BY;AC00'+str(opt)+';')
        else:
            print('HAMLIB TUNER - Invalid option:',opt)


    def get_PLtone(self):
        if VERBOSITY>0:
            print('\nHAMLIBIO: Get PL Tone ...')

        if self.rig_type2=='FT991a':

            # Hamlib 'c' command doesn't work for this rig so do it using rig CAT commands
            # Note that there are some mods needed to rigctl_parse.c for this to work properly
            buf = self.get_response('CT0;')
            on_off = int(buf[3])
            if VERBOSITY>0:
                print('HAMLIB GET_PL_TONE: CT buf=',buf,on_off)
            if on_off==0:
                tone=0
            else:
                buf = self.get_response('CN00;')
                if VERBOSITY>0:
                    print('HAMLIB_IO GET_PL_TONE: CN buf=',buf)
                idx = int(buf[4:7])
                tone = PL_TONES[idx]
                if VERBOSITY>0:
                    print('HAMLIB_IO GET_PL_TONE: CN idx=',buf[4:8],idx,tone)

        else:
            buf=self.get_response('u TONE')
            if VERBOSITY>0:
                print('HAMLIB_IO GET_PL_TONE: u TONE buf=',buf)
            buf=self.get_response('c')
            if VERBOSITY>0:
                print('HAMLIB_IO GET_PL_TONE: c buf=',buf)
            tone=0
            
        return tone
            
    def set_PLtone(self,tone):
        if VERBOSITY>0:
            print('HAMLIB Set PL Tone ...')

        if self.rig_type2=='FT991a':
            # Hamlib 'C' command doesn't work for this rig so do it using rig CAT commands
            # Note that there are some mods needed to rigctl_parse.c for this to work properly
            if tone==0:
                buf = self.get_response('BY;CT00;')
                if VERBOSITY>0:
                    print('HAMLIB_IO SET_PL_TONE: CT buf=',buf)
            else:
                p3 = str( np.where(PL_TONES==tone)[0][0] ).zfill(3)
                cmd='BY;CN00'+p3+';CT02;'
                buf = self.get_response(cmd)
                if VERBOSITY>0:
                    print('HAMLIB_IO SET_PL_TONE: CT buf=',buf)

        else:
            print('Function not yet implemented')
            
            
    def get_fldigi_mode(self):
        # I think we really want this to use xlmrpc to get the fldigi mode but it was probably
        # put in like this just as a place holder ???????
        print('HAMLIB - GET_FLDIGI_MODE - Not sure this is really doing what we want??????')
        x=self.get_mode()
        if VERBOSITY>0:
            print('HAMLIB_IO: Get FLDIGI mode',x)
        return x

    def set_log_fields(self,fields):
        if VERBOSITY>0:
            print('*** WARNING *** Ignored call to HAMLIB_IO SET_LOG_FIELDS ***')
        pass

    def get_log_fields(self):
        if VERBOSITY>0:
            print('*** WARNING *** Ignored call to HAMLIB_IO GET_LOG_FIELDS ***')

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
            print('*** WARNING *** Ignored call to HAMLIB_IO SET_CALL ***')
        
    def close(self):
        if VERBOSITY>0:
            print('HAMLIB_IO: Close')
        self.s.close()

    def get_info(self):
        print('HAMLIB_IO: GET_INFO...')
        buf = 'UNKNOWN'      # self.get_response('ID;')
        print('HAMLIB_IO GET_INFO buf=',buf)
        #buf=buf[:6]
        if buf=='ID0460':
            self.rig_type2 = 'FTdx3000'
        elif buf=='ID0670':
            self.rig_type2 = 'FT991a'
        else:
            print('\n*** HAMLIB_IO GET_INFO: Unknown rig on the other end ***',buf)
            self.rig_type2 = ''
        print('HAMLIB_IO GET_INFO rig_type2=', self.rig_type2)
        return buf
        
    def read_speed(self):
        #VERBOSITY=1
        if VERBOSITY>0:
            print('HAMLIB READing keyer SPEED ...',self.rig_type,self.rig_type2)

        if self.rig_type2=='TS850':
            print('HAMLIB READ_SPEED - Command doesnt seem to work for the TS850')
            return 0
            
        reply = self.get_response("l KEYSPD")
        buf = reply
        if VERBOSITY>0:
            print('HAMLIB read_speed:',reply,buf)

        try:
            wpm=int(buf)
        except:
            wpm=0

        return wpm

        
    def set_speed(self,wpm):
        if VERBOSITY>0:
            print('HAMLIB SETting keyer SPEED ...',self.rig_type,self.rig_type2,wpm)
        cmd='L KEYSPD '+str(wpm)
        reply = self.get_response(cmd)
        #print 'reply=',reply



    def read_meter_hamlib(self,meter):
        if VERBOSITY>0:
            print('HAMLIB READ_METER:',meter)

        # Hamlib does not work - use direct verion instead
        buf = self.get_response('p METER')
        print('HAMLIB READ_MEATER: buf=',buf)
        #print('buf=',buf[idx:-1])
        return



    # Function to turn PTT on and off
    def ptt(self,on_off,VFO='A'):
        if VERBOSITY>0:
            print('\nHAMLIB PTT:',on_off,VFO)

        if on_off:
            buf=self.get_response('T 1')
        else:
            buf=self.get_response('T 0')

                
    # Read rotor position - if at first we don't succeed, try try again
    def get_position(self):
        ntries=0
        while ntries<3:
            x = self.get_response('p').split('\n')
            #print('x=',x,ntries)
            try:
                pos = [float(x[0]),float(x[1])]                
                if VERBOSITY>0 or False:
                    print('\nHAMLIB - GET_POSITION:',pos)
                return pos
            except:
                ntries+=1
        else:
            print('\nHAMLIB - GET_POSITION - Unable to read rotor position')
            return [None,None]

            
    # Set rotor position
    def set_position(self,pos):
        #VERBOSITY=1
        if VERBOSITY>0:
            print('\nHAMLIB - SET_POSITION: pos=',pos)
        if pos[0]==None or pos[1]==None:
            print('\nHAMLIB - SET_POSITION - Invalid position',pos)
            return

        # Make sure az is between 0 and 360-deg ...
        if pos[0]<self.min_az:
            pos[0]+=360
        if pos[0]>self.max_az:
            pos[0]-=360

        # It woul be really nice to have ome code here to keep
        # from banging against stops at +/-180-deg but I haven't
        # figure it out yet!
        #pos[0]=max(-175,min(175,pos[0]))
        #pos[0]=max(0,min(359.9,pos[0]))
        try:
            az_prev=self.last_pos[0]
            print('last az=',az_prev,'\tnew az=',pos[0])
            #if pos[0]>az_prev and pos[0]>177 and pos[0]<180:
            if pos[0]>175 and pos[0]<180:
                pos[0]=175
                print('Limiting CW movement to 175-deg')
            #elif pos[0]<az_prev and pos[0]<183 and pos[0]>180:
            elif pos[0]<185 and pos[0]>180:
                pos[0]=183
                print('Limiting CW movement to 185-deg')
        except:
            pass

        # ... and that el is between 0 and 180-deg
        pos[1]=max(self.min_el,min(self.max_el,pos[1]))

        # Form and issue rotor psoitioning comand 
        cmd='P '+str(int(pos[0]))+' '+str(int(pos[1]))
        x = self.get_response(cmd)

        self.last_pos=pos
        
        if VERBOSITY>0:
            print('HAMLIB - SET_POSITION: Adjusted pos=',pos)
            print('cmd=',cmd)
            print('x=',x)
            
        return 

            
    # Routine to put rig into split mode
    def split_mode(self,opt):
        #VERBOSITY=1
        if VERBOSITY>0:
            print('HAMLIB - SPLIT_MODE: opt=',opt)

        if opt==-1:
            #print('\nQuerying split ...')
            buf=self.get_response('s')
            if VERBOSITY>0:
                print('SPLIT: buf=',buf)
            return buf[0]=='1'

        elif opt==0:
            
            buf=self.get_response('S 0 VFOA')
            #print('SPLIT0: buf=',buf)
                
        elif opt==1:
            
            buf=self.get_response('S 1 VFOB')
            #print('SPLIT1: buf=',buf)
                
        else:
            
            print('HAMLIB - SPLIT_MODE: Invalid opt',opt)
            return -1
            

    # Routine to put rig into sat mode
    def sat_mode(self,opt):
        if VERBOSITY>0:
            print('HAMLIB - SAT_MODE:',opt)

        if self.rig_type2!='IC9700':
            print('SAT_MODE: Noop for rig=',self.rig_type2)
            return -1
            
        elif opt==-1:
            # Read current sat mode setting
            buf=self.get_response('u SATMODE')
            return buf[0]=='1'
    
        elif opt<2:
            # Turn it on/off
            buf=self.get_response('U SATMODE '+str(opt))

        else:
            print('SAT_MODE: Invalid opt',opt)
            return -1


    # Function to get active VFO
    def get_vfo(self):
        VERBOSITY=1
        buf = self.get_response('v')
        if VERBOSITY>0:
            print('HAMLIB_IO - GET_VFO: buf=',buf)
        return buf[0]
    
    # Function to set active VFO
    def select_vfo(self,VFO):
        #VERBOSITY=1
        if VERBOSITY>0:
            print('HAMLIB SELECT_VFO:',VFO,self.rig_type2)

        if self.rig_type2=='FT991a':
            # RX VFO is always A, able to select VFO-B for tx using S 1 VFOB command but not yet implemented
            if VFO!='A':
                print('HAMLIB SELECT_VFO: Only VFO-A supported for FT991a (for now)')
            return
            
        elif self.rig_type1 != 'Icom':
            #print('HAMLIB SELECT_VFO - Not available for Non-ICOM rigs???')
            #return
            if VFO=='A':
                VFO='M'
            elif VFO=='B':
                VFO='S'
            
        if VFO=='A':
            cmd='V VFOA'
        elif VFO=='B':
            cmd='V VFOB'
        elif VFO=='M':
            cmd='V Main'
        elif VFO=='S':
            cmd='V Sub'
        elif VFO=='X':
            cmd='G XCHG'         # Exchange
        else:
            print('HAMLIB SELECT_VFO - Invalid VFO:',VFO)
                
        buf = self.get_response(cmd)
        if VERBOSITY>0:
            if self.rig_type1 == 'Icom':
                print('HAMLIB SELECT_VFO: buf=',show_hex(buf))
            else:
                print('HAMLIB SELECT_VFO: cmd/buf=',cmd,buf)
                

    # Function to control RIT
    # This doesn't work quite right so use direct commands for now.
    # It did work in v4 but not latest v4.1 --> look at newcat
    # Hopefully, this will be fixed in a future version Hamlib
    # When it does, also enable commands in socket_io->ClarReset
    #
    # Disabled broken code in newcat.c so now this works
    # Keep an eye on it
    def rit(self,opt,df,VFO='A'):
        if VERBOSITY>0 or False:
            print('HAMLIB RIT:',opt,df,VFO)

        if opt==-1:
            # Read current rit setting
            buf1=self.get_response('u RIT')
            buf2=self.get_response('j')
            return [buf1,buf2]
    
        elif opt<2:
            # Turn it on/off
            buf2=self.get_response('j')               # Get current shift
            #print('buf2=',buf2)
            offset = int(buf2) +df                    # Compute new shift
            buf=self.get_response('U RIT '+str(opt))
            buf2=self.get_response('J '+str(offset))

        else:

            print('HAMLIB RIT: Invalid opt',opt)
            return -1



    # Function to get monitor level
    def get_monitor_gain(self):
        #VERBOSITY=1
        buf = self.get_response('l MONITOR_GAIN')
        if VERBOSITY>0:
            print('HAMLIB_IO - GET_MONITOR_GAIN: buf=',buf)
        return int( 100*float(buf) )
    
        
    # Function to set monitor level
    def set_monitor_gain(self,gain):
        #VERBOSITY=1
        #print('gain=',gain)
        cmd  = 'L MONITOR_GAIN '+str(.01*float(gain))
        buf=self.get_response(cmd)
        if VERBOSITY>0:
            print('HAMLIB_IO - SET_MONITOR_GAIN: buf=',buf)
    
        
    # Function to turn audio recording on/off - for use with SDR
    def recorder(self,on_off=None):
        #VERBOSITY=1
        if VERBOSITY>0:
            print('HAMLIB_IO: Recorder',on_off)

        if self.rig_type2 == 'pySDR':
            
            if on_off==None:
                buf=self.get_response('w REC;')
            elif on_off:
                buf=self.get_response('w REC1;REC;')
            else:
                buf=self.get_response('w REC0;REC;')
            val = buf[3]=='1'

        else:
            if VERBOSITY>0:
                print('HAMLIB_IO: Recorder - Not available for this rig',self.rig_type2)
            val=False

        return val
    





    # Routine to set date & time 
    def set_date_time(self,VERBOSITY=0):
        now_utc = datetime.now(timezone('UTC'))
        date = now_utc.strftime("%Y%m%d")
        time = now_utc.strftime("%H%M%S")

        if self.rig_type2=='FT991a':

            print('\nSetting Rig Date ...',date)
            cmd='w DT0'+date+';BY;'
            buf=self.get_response(cmd)
            print('cmd=',cmd,'\tbuf=',buf)
            
            print('\nSetting Rig Time ...',time)
            cmd='w DT1'+time+';BY;'
            buf=self.get_response(cmd)
            print('cmd=',cmd,'\tbuf=',buf)

            print('Setting Rig UTC offset ...')
            cmd='w DT2+0000;BY;'
            buf=self.get_response(cmd)
            print('cmd=',cmd,'\tbuf=',buf)
            
        else:

            print('DIRECT SET_DATE_TIME - Unknown rig',self.rig_type2)
            sys.exit(0)
            
    def set_power(self,p):
        if VERBOSITY>0:
            print('HAMLIB_IO SET_POWER: p=',p)

        p=min(max(p,5),100)
        cmd = 'L RFPOWER '+str(.01*p)
        buf=self.get_response(cmd)
        
            
    def set_breakin(self,onoff):
        if VERBOSITY>0:
            print('HAMLIB_IO SET_BREAKIN: onoff=',onoff)
        cmd='U FBKIN '+str(onoff)
        self.get_response(cmd)


    def set_if_shift(self,shift):
        if VERBOSITY>0:
            print('HAMLIB_IO SET_IF_SHIFT: shift=',shift)
        cmd='L IF '+str(shift)
        buf=self.get_response(cmd)


    def set_vfo(self,rx=None,tx=None,op=None):
        VERBOSITY=1
        if VERBOSITY>0:
            print('HAMLIB_IO SET_VFO: rx=',rx,'\ttx=',tx,'\top=',op)

        if op=='A->B':
            cmd='G CPY'
        elif op=='B->A':
            print('HAMLIB_IO SET_VFO: WARNING - B2A not implemented')
            return
        elif op=='A<->B':
            cmd='G XCHG'
        
        else:
            
            if self.rig_type2=='FT991a' and rx!='A':
                print('HAMLIB_IO SET_VFO: *** WARNING *** RX is always on VFO A for the FT991a *** rx,tx=',rx,tx)
                rx='A'

            if rx==None and tx==None:
                print('HAMLIB_IO SET_VFO: Nothing to see here!')
                return
                
            if rx=='A' or rx=='M':
                rx='Main'
            elif rx=='B' or rx=='S':
                rx='Sub'
            else:
                rx='Main'                
                
            if tx=='A' or tx=='M':
                tx='Main'
            elif tx=='B' or tx=='S':
                tx='Sub'
            else:
                tx='Main'                

            if tx==rx:
                cmd='S 0 '+tx
            else:
                cmd='S 1 '+tx
            
        if VERBOSITY>0:
            print('HAMLIB_IO SET_VFO: cmd=',cmd)
        buf = self.get_response(cmd)
        if VERBOSITY>0:
            print('HAMLIB_IO SET_VFO: buf=',buf)

        

    """
    # Set sub-dial function on Yaesu rigs
    def set_sub_dial(self,func='CLAR'):

        if self.rig_type1!='Yaesu':
            #if self.rig_type2!='FTdx3000':
            print('*** WARNING *** HAMLIB SET SUB DIAL only available for Yaesu Rigs')
            return
            
        if func=='CLAR':
            cmd='BY;SF5;'
        elif func=='VFO-B':
            cmd='BY;SF4;'
        else:
            self.sub_dial_func=None
            print('HAMLIB_IO - SET_SUB_DIAL - Unknown Function',func)
            return
        
        buf = self.get_response(cmd)
        self.sub_dial_func=func
        
        return
    """            



    # Function to read the clarifier
    def read_clarifier(self):
        VERBOSITY=0
        if VERBOSITY>0:
            print('HAMLIB_IO: READ_CLARIFIER ...')
        
        buf1  = self.get_response('u RIT')           # On/Off
        buf2  = self.get_response('j')               # Shift
        rx    = int(buf1)*int(buf2)
        
        buf3  = self.get_response('u XIT')
        #buf4  = self.get_response('z')
        #shift = buf.split(':')[1]
        tx    = int(buf3)*int(buf2)
        
        if VERBOSITY>0:
            print('buf1=',buf1)
            print('buf2=',buf2)
            print('buf3=',buf3)
            #print('buf4=',buf4)
            print('rx=',rx,'\ttx=',tx)   # ,'\tshift=',shift)
        
        return rx,tx
        
    
    
