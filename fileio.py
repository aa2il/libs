#######################################################################################
#
# File IO - Rev 1.0
# Copyright (C) 2021-4 by Joseph B. Attili, aa2il AT arrl DOT net
#
# Functions related to file I/O
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

import sys
import os
import re
import csv
from collections import OrderedDict
from zipfile import ZipFile
from io import TextIOWrapper
from utilities import error_trap

import time
import numpy as np
import wave
import struct
from scipy.io import wavfile
from sig_proc import up_dn

#######################################################################################

# Function to save GPS location info
def save_gps_coords(loc,fname=None,VERBOSITY=1):
    if VERBOSITY>0:
        print('Saving location info ',loc,'...' )
    if not fname:
        fname=os.path.expanduser('~/.gpsrc')
    fp=open(fname,'w')
    fp.write('%f\n%f\n%f\n%s\n' % loc)
    fp.close()

# Function to read GPS location info
def read_gps_coords(fname=None,VERBOSITY=1):
    if VERBOSITY>0:
        print('Reading location info ...')
    if not fname:
        fname=os.path.expanduser('~/.gpsrc')
    fp=open(fname,'r')
    lat=float( fp.readline() )
    lon=float( fp.readline() )
    alt=float( fp.readline() )
    gridsq=fp.readline()
    if VERBOSITY>0:
        print('lat=',lat,'\tlon=',lon,'\talt=',alt,'\ngrid=',gridsq)
    fp.close()
    return [lat,lon,alt,gridsq]

#######################################################################################

# Function to split a file name into its component parts
def parse_file_name(fname):
    p, f = os.path.split(fname)
    #f = os.path.basename(fname)
    n, e = os.path.splitext(f)

    return (p,n,e)

#######################################################################################

def sort_keys(KEYS):
    KEYS=sorted( list(KEYS) )
    #print('Keys=',KEYS)
    KEYS.remove('call')
    keys1=['srx_string','qth','name']
    for key in keys1:
        if key in KEYS:
            KEYS.remove(key)
    KEYS2=['call']+KEYS+keys1
    return KEYS2

#######################################################################################

# Function to read list of qsos from simple log file
def parse_simple_log(fn,args):

    DEBUG=True
    DEBUG=False

    f = open(fn,'r')             # rb in Python 2
    csv_f = csv.reader(f)
    if DEBUG:
        print('csv_f=',csv_f)

    logbook =[]
    nrec=0;
    for row in csv_f:
        nrec+=1
        if DEBUG:
            print('nrec,row=',nrec,row)
        
        if nrec==1:
            tags = row
            if DEBUG:
                print('tags=',tags)
        else:
            qso = {}
            for i in range(len(row)):
                if DEBUG:
                    print('i,row(i)=',i,row[i])
                try:
                    qso[tags[i].lower()] = row[i]
                except:
                    error_trap('Problem parsing simple log - probably caused by bad header line')
                    sys.exit(0)
                    
            if args.naqpcw or args.naqprtty or args.cwops:
                a=row[6].split(',')
                if len(a)==2:
                    qso['name']=a[0]
                    qso['qth']=a[1]
                else:
                    qso['name']=''
                    qso['qth'] =''
                #print qso
                #sys.exit(0)
            elif args.cols13:
                a=row[6].split(' ')
                #print row
                #print a
                qso['rst_in']=a[0]
                qso['qth']=a[1]

            qso['freq'] = str( 1e-3*float(qso['freq']) )
            logbook.append(qso)

    return logbook

#######################################################################################


# This is an experimental routine
import codecs
def read_adif(fname):
    logbook =[]
    #fp=open(fn)
    #lines = []
    
    #with open(fname) as f:
    with codecs.open(fname, 'r', encoding='utf-8',
                 errors='ignore') as f:
        lines = f.readlines()

        #line = f.readline()
        #while line:
        #    line = f.readline()
        #    print(line)

    # Find end of header
    cnt=0
    for line in lines:
        if line.strip()=='<eoh>':
            print('Found end of header at line',cnt)
        cnt+=1

    # Find 
    done=False
    
            
    print(len(lines))
    sys.exit(0)

# Function to read list of qsos from input file
def parse_adif(fname,line=None,upper_case=False,verbosity=0,REVISIT=False):
    logbook =[]

    if verbosity>0:
        print('PARSE_ADIF - Reading',fname,'...')

    #if not hasattr(parse_adif, "fname"):
    #    parse_adif.fname=fname
    if not hasattr(parse_adif, "fp"):
        parse_adif.fp=None

    try:
        
        if line==None:
            if not parse_adif.fp:
                parse_adif.fp=codecs.open(fname, 'r', encoding='utf-8',
                                              errors='ignore')
            raw1 = re.split('(?i)<eoh>',parse_adif.fp.read() )
            if not REVISIT:
                parse_adif.fp.close()
                parse_adif.fp=None
        else:
            raw1 = re.split('(?i)<eoh>',line )
            
    except:
        
        error_trap('FILE_IO->PARSE_ADIF: *** Unable to open file or other error')
        print('fname=',fname)
        return logbook
        
    raw = re.split('(?i)<eor>',raw1[-1] )

    for record in raw:
        if verbosity>0:
            print(record,len(record))
        if len(record)<=1:
            continue
        
        qso = {}
        tags = re.findall('<(.*?):(\d+).*?>([^<]+)',record.replace('<RST> <CNTR>','A AA2IL 78 CA'))

        for tag in tags:
            if upper_case:
                qso[tag[0].upper()] = tag[2][:int(tag[1])]
            else:
                qso[tag[0].lower()] = tag[2][:int(tag[1])]

        if 'call' in qso or 'CALL' in qso:
            if upper_case:
                if 'QSO_DATE_OFF' not in qso:
                    qso['QSO_DATE_OFF'] = qso['QSO_DATE']
                if 'TIME_OFF' not in qso:
                    qso['TIME_OFF'] = qso['TIME_ON']
            else:
                if 'qso_date_off' not in qso:
                    qso['qso_date_off'] = qso['qso_date']
                if 'time_off' not in qso:
                    qso['time_off'] = qso['time_on']
            logbook.append(qso)

    return logbook


# Convert dict keys to upper case
#def upper_dict_keys(d):
#   new_dict = dict((key.upper(), value) for key, value in d.items())
#   return new_dict


# Function to create entire ADIF record and write it to a file
def write_adif_record(fp,rec,P,long=False,sort=True,VERBOSITY=0):
    #VERBOSITY=2
    if VERBOSITY>=1:
        print('rec=',rec)

    try:
        contest = P.contest_name
    except:
        contest = ''
    MY_CALL = P.SETTINGS['MY_CALL']
    MY_GRID = P.SETTINGS['MY_GRID']
    try:
        MY_CITY = P.SETTINGS['MY_CITY']+', '+P.SETTINGS['MY_STATE']
    except:
        MY_CITY = ''

    if long:
        NL='\n'
    else:
        NL=' '
        
    # Convert keys to upper case to avoid further complications
    if VERBOSITY>0:
        print('\nqso in  =',rec)
    qso = dict((key.upper(), value) for key, value in rec.items())
    if VERBOSITY>0:
        print('\nqso out =',qso)
        print('WRITE_ADIF_RECORD: keys=',list(qso.keys()))
        print('contest=',contest)
        print('MY Call/Grid/City=',MY_CALL,MY_GRID,MY_CITY)

    if 'QSO_DATE' not in qso:
        try:
            qso['QSO_DATE'] = qso['QSO_DATE_OFF']
        except:
            error_trap('FILE_IO->WRITE ADIF REC - Cant figure out QSO Date - giving up')
            print('qso=',qso)
            sys,exit(0)
            
    if 'TIME_ON' not in qso:
        qso['TIME_ON'] = qso['TIME_OFF']
    if 'RST_SENT' not in qso:
        qso['RST_SENT']='599'
    if 'RST_RCVD' not in qso:
        qso['RST_RCVD']='599'
    if 'STATION_CALLSIGN' not in qso:
        qso['STATION_CALLSIGN']=MY_CALL
    if 'MY_GRIDSQUARE' not in qso:
        qso['MY_GRIDSQUARE']=MY_GRID
    if 'MY_CITY' not in qso and len(MY_CITY)>2:
        qso['MY_CITY']=MY_CITY

    if contest=='NAQP-CW' or contest=='CW Ops Mini-Test':
        exch=qso['SRX_STRING'].split(',')
        qso['NAME'] = exch[0]
        qso['QTH']  = exch[1]
        
    fields = list(qso.keys())
    if sort:
        fields.sort()
    if VERBOSITY>1:
        print('keys=',fields)
    for fld in fields:
        val = qso[fld]
        if VERBOSITY>1:
            print('WRITE_ADIF_RECORD:',fld,val)

        if fld in ['FILE_NAME'] and True:
            # Skip these fields
            continue
        
        elif fld=='SAT_NAME':
            if val!='None' and val!='':
                if val=='ISS':
                    val='ARISS'
                fp.write('<%s:%d>%s%s' % (fld,len(val),val,NL) )
                fld2='PROP_MODE'
                val2='SAT'
                fp.write('<%s:%d>%s%s' % (fld2,len(val2),val2,NL) )
        elif fld=='TIME_STAMP':
            pass
        else:
            if fld[:4]=='FREQ' and len(val)>8:
                val=val[0:8]
            elif fld[:4]=='TIME' and len(val)>0 and len(val)!=6:
                val=str(val).replace(':','').zfill(6)
            if VERBOSITY>1:
                print(fld,val)
            if len(val)>0:
                fp.write('<%s:%d>%s%s' % (fld,len(val),val,NL) )

    """
    try:
        val=P.CONTEST_ID
        if val and len(val)>0:
            fld='CONTEST_ID'
            fp.write('<%s:%d>%s%s' % (fld,len(val),val,NL) )
    except Exception as e:
        print('\nADIF WRITE RECORD: Problem writing contest id')
        print('Error msg:\t',getattr(e, 'message', repr(e)))
        print('rec=',rec)
    """
        
    fp.write('<EOR>\n\n')
    fp.flush()


# Function to write out an ADIF file 
#FIELDS=['FREQ','CALL','MODE','NAME','QSO_DATE','QSO_DATE_OFF','TIME_OFF','TIME_ON','QTH','RST_RCVD','RST_SENT','BAND', \
#        'COUNTRY','SRX_STRING','STATION_CALLSIGN','MY_GRIDSQUARE','MY_CITY'
def write_adif_log(qsos,fname,P,SORT_KEYS=True):
    VERBOSITY=0
    
    fname2 = fname.replace('.LOG','.adif')
    print("WRITE_ADIF_LOG: ADIF file name=",fname2)
    fp = open(fname2, 'w')
    fp.write('Simple Log Export<eoh>\n')

    for qso in qsos:
        if SORT_KEYS:
            keys=sort_keys(qso.keys())
        else:
            keys=qso.keys()

        # LoTW requires these fields
        if 'qso_date' not in keys:
            keys.append('qso_date')
        if 'time_on' not in keys:
            keys.append('time_on')
        if VERBOSITY>0:
            print('\nqso=',qso,'\nkeys=',keys)
            
        qso2=OrderedDict()
        #print('qso=',qso)
        for key in keys:
            if VERBOSITY>0:
                print('key=',key)
            if key=='X-Notes' and True:
                continue
            if key in qso:
                # Fill in any missing fields that LoTW requires
                if key=='qso_date' and len(qso[key])==0:
                    qso[key] = qso['qso_date_off']
                if key=='time_on' and len(qso[key])==0:
                    qso[key] = qso['time_off']
                qso2[key.upper()] = qso[key]
                
        if VERBOSITY>0:
            print(qso2)
        
        write_adif_record(fp,qso2,P,sort=False)
        
    fp.close()
            

# Function to compute length of time for a qso
def qso_time(rec):
    if 'time_on' in rec :
        ton = rec["time_on"]
#        print "time on  = ",ton
    if 'time_off' in rec :
        toff = rec["time_off"]
#        print "time off = ",toff

    dt = 3600.*( int(toff[0:2]) - int(ton[0:2]) ) + 60.*(int(toff[2:4]) - int(ton[2:4])) + 1.*( int(toff[4:6]) - int(ton[4:6]) )
    return dt




def read_csv_file(fname,delim=','):

    name=os.path.splitext(fname)[0]
    ext=os.path.splitext(fname)[1]
    print('READ_CSV_FILE: name=',name,'\text=',ext)

    hdr=[]
    QSOs=[]
    keys=None
    if ext=='.zip':

        # Added this to handle zipped csv files from the RBN
        with ZipFile(fname, 'r') as zipf:
            with zipf.open(name+'.csv', 'r') as f:
                rows = csv.reader(TextIOWrapper(f, 'utf-8'),delimiter=delim)

                for row in rows:
                    #print(row)
                    if row[0][0]=='#':
                        hdr.append(row)
                    elif keys==None:
                        keys=row
                    else:
                        qso={}
                        for i in range(len(row)):
                            qso[keys[i]]=row[i]
                        QSOs.append(qso)
                
    else:

        # Normal csv text file
        with open(fname) as f:
            rows = csv.reader(f,delimiter=delim)

            for row in rows:
                #print(row)
                if row[0]=='':
                    print('Skipping row=',row)
                elif row[0][0]=='#':
                    hdr.append(row)
                elif keys==None:
                    keys=row
                else:
                    qso={}
                    for key,val in zip(keys,row):
                        if key[:4]=='time':
                            #print(key,'\t',val)
                            val=val.replace("'","")
                        qso[key]=val
                    QSOs.append(qso)

    return QSOs,hdr



def write_csv_file(fname,keys,qsos):
    fp = open(fname, "w")
    #print('keys=',keys)

    # Write header
    sep=','
    for key in keys:
        #print(key)
        if key==keys[-1]:
            sep='\n'
        fp.write(str(key)+sep)

    # Write list of q's
    for qso in qsos:
        sep=','
        for key in keys:
            if key==keys[-1]:
                sep='\n'
            try:
                val = str( qso[key] )
                #if key[:4]=='time':
                #    print(qso[key],'\t',val)
                #if key[:4]=='time' and len(val)>0 and len(val)!=6:
                #    val='"'+str(val).zfill(6)+'"'
                #elif ',' in val or val[0]=='0':
                if key[:4]=='time':                    
                    val="'"+val
                elif ',' in val:
                    val='"'+val+'"'
            except:
                val=''
            fp.write(val+sep)
    
    #fp.flush()
    fp.close()





# Function to read a simple text file
def read_text_file(fname,KEEP_BLANKS=True,UPPER=False):

    # Line by line so we can do some better filtering
    lines=[]
    if os.path.exists(fname):
        Done=False
        with open(fname,encoding='utf8') as f:
            while not Done:
                try:
                    line = f.readline()
                except Exception as e:
                    print('READ TEXT FILE: Problem reading line')
                    print('Error msg:\t',getattr(e, 'message', repr(e)))
                    line=''
                if not line:
                    Done=True
                else:
                    line=line.strip()
                    if UPPER:
                        line=line.upper()
                    if KEEP_BLANKS or len(line)>0:
                        lines.append(line)

    return lines

############################################################################
############################################################################
#
# Routines related to I/O of SDR generated files.
#
############################################################################
############################################################################

# A playpen for alg dev
def alg_dev():
    print('Hey &&&&')
    fname='demod1.dat'
    hdr,tag,x = read_data(fname)             # This needs to be updated

    print('hdr=',hdr)
    print('tag=',tag)
    print('x=',x[0:10],' ... ',x[-1],len(x))

    # Plot IQ data
    app = QApplication(sys.argv)
    plotter = plot1d()
    plotter.plot(x)

    # Event loop
    app.exec_()
    
###################################################################

def limiter(x,a):
    return np.maximum( np.minimum(x,a) ,-a)


class sdr_fileio:
    def __init__(self,fname,rw,P=None,nchan=2,tag=''):
        self.P     = P
        self.fname = fname
        self.nchan = nchan
        self.nbytes = 2
        self.tag   = tag.upper()
        self.fp    = None
        self.WAVE_OUT = False

        ext = os.path.splitext(self.fname)[1]
        print('ext=',ext)
        self.WAVE_IN  = ext=='.wav'

        if rw=='r':
            self.hdr = self.read_header()

            # Position pointer to start of requested data
            if P:
                P.SRATE     = self.srate
                P.REPLAY_FC = self.fc
                P.FC        = self.fc
                if self.fname.find('baseband_iq'):
                    P.FS_OUT=P.SRATE
                P.UP , P.DOWN   = up_dn(P.SRATE , P.FS_OUT )
                P.FS_OUT        = int( P.SRATE * P.UP / P.DOWN   )
                
                if not hasattr(P,'REPLAY_START'):
                    P.REPLAY_START=0
                istart = int( P.REPLAY_START*60*self.srate*self.nchan*4 )
                if istart>0:
                    if self.WAVE_IN:
                        print('*** SDR_FILE_IO - Seek not yet supported for wav files ***')
                    else:
                        print('Seeking',istart/1024,'Kbytes into file - Start time=', \
                              P.REPLAY_START,'min')
                        self.fp.seek(istart, os.SEEK_CUR)

        elif rw=='w':
            self.hdr_written = False
            
        else:
            print('ERROR - rw must be r or w',rw)
            sys.exit(1)

    # Function to close the file nicely
    def close(self):
        self.hdr_written = False
        if self.fp:
            print('Closing',self.fname2)
            self.fp.close()
            self.fp=None
            if self.WAVE_OUT and True:       # Was False
                #wave.close(self.fp_wav)
                self.fp_wav.close()
                print('Closed',self.wave_fname)
                self.WAVE_OUT=False

    # Functions to read data from disk
    def read_header(self):

        VERBOSITY=1

        if self.WAVE_IN:
            fp = wave.open(self.fname, 'rb')
            hdr_ver =  0.0
        else:
            fp = open(self.fname,'rb')
            hdr_ver = float( np.fromfile(fp,np.float32,1) )
        self.fp = fp

        # Read header
        if hdr_ver==0.0:
            # Wave file
            self.nchan = fp.getnchannels()
            self.srate = fp.getframerate()
            self.fc    = 0
            self.duration = 0
            hdr=[]
        elif hdr_ver==1.0:
            # SDR file - Next version should include IF, foffset,bw...
            hdr_len = int( np.fromfile(fp,np.float32,1) )
            if VERBOSITY>0:
                print('hdr_len=',hdr_len)
            hdr = np.fromfile(fp,np.float32,hdr_len-2)
            if VERBOSITY>0:
                print('hdr=',hdr)

            self.srate    = hdr[0]
            self.fc       = hdr[1]
            self.duration = hdr[2]
            self.nchan    = int( hdr[3] )
            
            tag_len       = int( hdr[4] )
            self.tag      = fp.read(tag_len)
            if VERBOSITY>0:
                print('tag=',self.tag)

            chk     = np.fromfile(fp,np.float32,2)
            if VERBOSITY>0:
                print('chk=',chk)

        else:
            print('Unknown file format')
            sys.exit(1)

        if self.nchan == 2:
            self.dtype = np.complex64
        else:
            self.dtype = np.float32

        if VERBOSITY>0:
            print('READ_HEADER: hdr_ver=',hdr_ver)
            sz = os.path.getsize(self.fname)
            print('\tfname       =',self.fname)
            print('\thdr      =',hdr)
            print('\tsrate    =',self.srate)
            print('\tfc       =',self.fc)
            print('\tduration =',self.duration)
            print('\tnchan    =',self.nchan)
            print('\ttag      =',self.tag)
            print('\tsize     =',sz,'bytes')
            print('\tduration = ',float(sz)/float( self.srate*self.nchan*4*60 ),' minutes')
            print(' ')

        return hdr

    # Function to read data
    def read_data(self):

        # Read the data
        print('Reading data...',self.fp,self.dtype)
        if self.WAVE_IN:
            samplerate, data = wavfile.read(self.fname)
            print('ndim,shape=',np.ndim(data),np.shape(data))
            if np.ndim(data)==1:
                x=data
            else:
                x=data[:,0]
            print('shape=',np.shape(x))
            
            #CHUNK = 1024
            #data = self.fp.readframes(CHUNK)
            #print('type=',type(data))
            #while len(data) > 0:
            #    data = self.fp.readframes(CHUNK)
            #    print('type=',type(data))


        else:        
            x = np.fromfile(self.fp,self.dtype,-1)
        
        # Close the file
        self.fp.close()

        return x


    # Function to write header info to disk
    def write_header(self,P,fname,nchan,tag):

        # Open output files & write a simple header
        s=time.strftime("_%Y%m%d_%H%M%S", time.gmtime())      # UTC
        dirname='../data/'
        dirname=''
        self.fname2 = dirname+fname+s+'.dat'
        print('\nOpening',self.fname2,'...')
        self.fp     = open(self.fname2,'wb')

        if nchan==2:
            self.dtype = np.complex64
        else:
            self.dtype = np.float32

        hver=1.0
        if tag=='RAW_IQ':
            self.fs = P.SRATE
            self.WAVE_OUT = False
        elif tag=='BASEBAND_IQ':
            self.fs = P.FS_OUT
            self.WAVE_OUT = False
        else:
            self.fs = P.FS_OUT
            self.WAVE_OUT = True
            
        hdr = [hver,0,self.fs, P.FC[0],P.DURATION,nchan,len(tag),0]
        hdr[1] = len(hdr)
        hdr = np.array(hdr, np.float32)
        print("hdr=",hdr,tag)
        hdr.tofile(self.fp)
        self.fp.write(tag.encode())
        chk = np.array([12345,0], np.float32)
        chk.tofile(self.fp)

        
    # Function to write data to disk
    def save_data(self,x,VERBOSITY=0):

        if VERBOSITY>0:
            print('SAVE_DATA: Saving chunk',len(x),'\ttag=',self.tag)

        # If this is the first block, write out a simple header
        if not self.hdr_written:
            if VERBOSITY>0:
                print('SAVE_DATA: Writing header ...')
            self.write_header(self.P,self.fname,self.nchan,self.tag)
            self.hdr_written = True

            if self.WAVE_OUT:
                self.wave_fname = self.fname2.replace('.dat','.wav')
                print('SAVE_DATA: wave_name=',self.wave_fname,'\tnchan=',self.nchan)
                self.fp_wav = wave.open(self.wave_fname, "w")
                self.nbytes=2
                #self.nbytes=4          # Signed ints (32-bits) doesnt work
                self.fp_wav.setparams((self.nchan, self.nbytes, self.fs, 0, 'NONE', 'not compressed'))

        # Convert data to 32-bit floats & write it out
        if len(x)>0:

            # Save raw data - logic here needs to be impoved so we can do both??
            if not self.WAVE_OUT:                   # Was False --> didn't save anything
                if self.nchan==1:
                    x.real.astype(self.dtype).tofile(self.fp)
                else:
                    x.astype(self.dtype).tofile(self.fp)

            # Save wav data
            if self.WAVE_OUT:
                # In Python3, this seemed to get a whole lot easier - or maybe I was just over thinking it!
                if sys.version_info[0]==3:
                    sc=32767.  #/4
                    if self.nchan==1:
                        # Convert singale channel data to ints - can't figure out how to write floats to wave?
                        #xx = (sc*x.real).astype(np.int16)
                        xx = (sc*limiter(x.real,1.)).astype(np.int16)
                    else:
                        # Interleave data - there probably is a better way but this seems to work
                        #print('x=',x)
                        xx = np.empty( 2*x.size, dtype=np.int16 )
                        #xx[0::2] = sc*x.real
                        #xx[1::2] = sc*x.imag
                        xx[0::2] = sc*limiter(x.real,1.)
                        xx[1::2] = sc*limiter(x.imag,1.)
                        #print('xx=',xx)

                    self.fp_wav.writeframes(xx)
                    return

                # Old Python 2 code - doesn't work quite right but good enough for now ...
                
                mask = 0xffffffff
                #xx = np.int(32767*x.real) + 1j*np.int(32767*x.imag)                      # Doesn't work
                sc=32767.
                sc=sc/4
                #sc=1
                #sc=.1
                #xx = np.int32(sc*x.real) + 1j*np.int32(sc*x.imag)                      # Works
                xx = np.int16(sc*x.real) + 1j*np.int16(sc*x.imag)                      # Works

                #print 'Should be saving wave data ...',x[0:5],xx[0:5]

                #xx = np.maximum( np.minimum(x.real,1.) , -1. ) + 1j*np.maximum( np.minimum(x.imag,1.) , -1. )
                
                #packed = "".join((struct.pack('h', 32767.*item ) for item in x))
                #packed = "".join((struct.pack('h', (32767.*item) & 0xffffffff ) for item in x))

                #packed = "".join((struct.pack('h', 32767.*item ) for item in xx))
                #print x

                #print limits.shrt_max
                #print xx

                if self.nbytes==2:
                    packed = "".join((struct.pack('h', item) for item in xx))   # Signed shorts (16-bits)
                else:
                    packed = "".join((struct.pack('i', item) for item in xx))   # Signed ints (32-bits) doesnt work
                
                self.fp_wav.writeframes(packed)
 
