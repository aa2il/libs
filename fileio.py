#######################################################################################
#
# File IO - Rev 1.0
# Copyright (C) 2021 by Joseph B. Attili, aa2il AT arrl DOT net
#
# Functions related to file io.
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
from rig_io.ft_tables import *
import csv
from collections import OrderedDict
from zipfile import ZipFile
from io import TextIOWrapper

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
                    print('Problem parsing simple log - probably caused by bad header line')
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
def parse_adif(fn,line=None,upper_case=False,verbosity=0):
    logbook =[]

    if verbosity>0:
        print('PARSE_ADIF - Reading',fn,'...')

    try:
        if line==None:
            if False:
                fp=open(fn)
                raw1 = re.split('<eoh>(?i)',fp.read() )
                fp.close()
            else:
                with codecs.open(fn, 'r', encoding='utf-8',
                                 errors='ignore') as fp:
                    raw1 = re.split('<eoh>(?i)',fp.read() )
            
        else:
            raw1 = re.split('<eoh>(?i)',line )
    except Exception as e:
        print('*** Unable to open file or other error in PARSE_ADIF ***')
        print('fn=',fn)
        print('Error msg:\t',getattr(e, 'message', repr(e)))
        return logbook
        
    raw = re.split('<eor>(?i)',raw1[-1] )

    #print('raw[0] =',raw[0])
    #print('raw[1] =',raw[1])
    #raw.pop(0)  #remove header - this deletes 1st qso if there is no header!!!
    #raw.pop()   #remove last empty item

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
                    #print('qso=',qso)
                    qso['QSO_DATE_OFF'] = qso['QSO_DATE']
                if 'TIME_OFF' not in qso:
                    qso['TIME_OFF'] = qso['TIME_ON']
            else:
                if 'qso_date_off' not in qso:
                    #print('qso=',qso)
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
def write_adif_record(fp,rec,P,long=False,sort=True):
    VERBOSITY=0

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
            print('FILE_IO - Write Adif Rec - Cant figure out QSO Date - giving up')
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
    #print('keys=',fields)
    for fld in fields:
        val = qso[fld]
        #print('WRITE_ADIF_RECORD:',fld,val)
        if fld=='SAT_NAME':
            if val!='None':
                if val=='ISS':
                    val='ARISS'
                fp.write('<%s:%d>%s%s' % (fld,len(val),val,NL) )
                fld2='PROP_MODE'
                val2='SAT'
                fp.write('<%s:%d>%s%s' % (fld2,len(val2),val2,NL) )
        elif fld=='TIME_STAMP':
            pass
        else:
            if fld=='FREQ' and len(val)>8:
                val=val[0:8]
            elif fld[:4]=='TIME' and len(val)>0 and len(val)!=6:
                val=str(val).zfill(6)
            #print(fld,val)
            if len(val)>0:
                fp.write('<%s:%d>%s%s' % (fld,len(val),val,NL) )

    try:
        val=P.CONTEST_ID
        if len(val)>0:
            fld='CONTEST_ID'
            fp.write('<%s:%d>%s%s' % (fld,len(val),val,NL) )
    except:
        pass
        
    #fp.write('<EOR>\n'+NL)
    fp.write('<EOR>\n\n')
    fp.flush()


# Function to write out an ADIF file 
#FIELDS=['FREQ','CALL','MODE','NAME','QSO_DATE','QSO_DATE_OFF','TIME_OFF','TIME_ON','QTH','RST_RCVD','RST_SENT','BAND', \
#        'COUNTRY','SRX_STRING','STATION_CALLSIGN','MY_GRIDSQUARE','MY_CITY'
def write_adif_log(qsos,fname,P):
    VERBOSITY=0
    
    fname2 = fname.replace('.LOG','.adif')
    print("WRITE_ADIF_LOG: ADIF file name=",fname2)
    fp = open(fname2, 'w')
    fp.write('Simple Log Export<eoh>\n')

    for qso in qsos:
        keys=sort_keys(qso.keys())
        if VERBOSITY>0:
            print('\nqso=',qso,'\nkeys=',keys)
        qso2=OrderedDict()
        for key in keys:
            if VERBOSITY>0:
                print('key=',key)
            if key in qso:
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
    print('name=',name,'\text=',ext)

    hdr=[]
    QSOs=[]
    keys=None
    if ext=='.zip':

        # Added this to handle zipped csv files from the RBN
        with ZipFile(fname, 'r') as zip:
            with zip.open(name+'.csv', 'r') as f:
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
                if row[0][0]=='#':
                    hdr.append(row)
                elif keys==None:
                    keys=row
                else:
                    qso={}
                    for key,val in zip(keys,row):
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
                #if key[:4]=='time' and len(val)>0 and len(val)!=6:
                #    val='"'+str(val).zfill(6)+'"'
                #elif ',' in val or val[0]=='0':
                if ',' in val:
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
        with open(fname) as f:
            while not Done:
                line = f.readline()
                if not line:
                    Done=True
                else:
                    line=line.strip()
                    if UPPER:
                        line=line.upper()
                    if KEEP_BLANKS or len(line)>0:
                        lines.append(line)

    return lines

