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

#######################################################################################

# Function to split a file name into its component parts
def parse_file_name(fname):
    p, f = os.path.split(fname)
    #f = os.path.basename(fname)
    n, e = os.path.splitext(f)

    return (p,n,e)

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

# Function to read list of qsos from input file
def parse_adif(fn,line=None):
    logbook =[]
    
    try:
        if line==None:
            #raw = re.split('<eor>|<eoh>(?i)',open(fn).read() )
            raw1 = re.split('<eoh>(?i)',open(fn).read() )
        else:
            raw1 = re.split('<eoh>(?i)',line )
    except Exception as e:
        print('*** Unable to open file or other error in PARSE_ADIF ***')
        print('Error msg:\t',getattr(e, 'message', repr(e)))
        return logbook
        
    raw = re.split('<eor>(?i)',raw1[-1] )

    #print('raw[0] =',raw[0])
    #print('raw[1] =',raw[1])
    #raw.pop(0)  #remove header - this deletes 1st qso if there is no header!!!
    #raw.pop()   #remove last empty item

    for record in raw:
        #print(record,len(record))
        if len(record)<=1:
            continue
        
        qso = {}
        tags = re.findall('<(.*?):(\d+).*?>([^<]+)',record.replace('<RST> <CNTR>','A AA2IL 78 CA'))
#        print tags
        for tag in tags:
            qso[tag[0].lower()] = tag[2][:int(tag[1])]
        logbook.append(qso)
#        sys.exit(0)
    return logbook


# Convert dict keys to upper case
#def upper_dict_keys(d):
#   new_dict = dict((key.upper(), value) for key, value in d.items())
#   return new_dict


# Function to create entire ADIF record and write it to a file
def write_adif_record(fp,rec,P):
    VERBOSITY=0

    contest = P.contest_name
    MY_CALL = P.SETTINGS['MY_CALL']
    MY_GRID = P.SETTINGS['MY_GRID']
    MY_CITY = P.SETTINGS['MY_CITY']+', '+P.SETTINGS['MY_STATE']

    if True:
        # Convert keys to upper case to avoid further complications
        if VERBOSITY>0:
            print('\nqso in  =',rec)
        qso = dict((key.upper(), value) for key, value in rec.items())
        if VERBOSITY>0:
            print('\nqso out =',qso)

    if VERBOSITY>0:
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
    if 'MY_CITY' not in qso:
        qso['MY_CITY']=MY_CITY

    if contest=='NAQP-CW' or contest=='CW Ops Mini-Test':
        exch=qso['SRX_STRING'].split(',')
        qso['NAME'] = exch[0]
        qso['QTH']  = exch[1]
        
    fields = list(qso.keys())
    #print('keys=',fields)
    fields.sort()
    for fld in fields:
        val = qso[fld]
        #print('WRITE_ADIF_RECORD:',fld,val)
        if fld=='SAT_NAME':
            if val!='None':
                fp.write('<%s:%d>%s ' % (fld,len(val),val) )
                fld2='PROP_MODE'
                val2='SAT'
                fp.write('<%s:%d>%s ' % (fld2,len(val2),val2) )
        elif fld=='TIME_STAMP':
            pass
        else:
            if fld=='FREQ' and len(val)>8:
                val=val[0:8]
            fp.write('<%s:%d>%s ' % (fld,len(val),val) )
    fp.write('<EOR>\n')
    fp.flush()


# Function to write out an ADIF file 
#FIELDS=['FREQ','CALL','MODE','NAME','QSO_DATE','QSO_DATE_OFF','TIME_OFF','TIME_ON','QTH','RST_RCVD','RST_SENT','BAND', \
#        'COUNTRY','SRX_STRING','STATION_CALLSIGN','MY_GRIDSQUARE','MY_CITY'
def write_adif_log(qsos,fname,contest=''):
    fname2 = fname.replace('.LOG','.adif')
    print("WRITE_ADIF_LOG: ADIF file name=",fname2)
    fp = open(fname2, 'w')
    fp.write('Simple Log Export<eoh>\n')

    for qso in qsos:
        qso['freq'] = str( 1e-3*float( qso['freq'] ) )
        qso2 =  {key.upper(): val for key, val in list(qso.items())}
        write_adif_record(fp,qso2,contest)
        
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
