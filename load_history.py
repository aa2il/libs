#######################################################################################
#
# Load History - Rev 1.0
# Copyright (C) 2022-5 by Joseph B. Attili, joe DOT aa2il AT gmail DOT com
#
# Function to load a history file
#
# Notes:
#      1) May need to install pandas:           pip3 install pandas
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
import time
from collections import OrderedDict
import csv
import os.path

#import xlrd                # Doesn't work anymore for xlsx files
#import openpyxl            # This doesn't seem to work very well
import pandas               # Need to learn how to use this more
#import math

from unidecode import unidecode
from dx.spot_processing import Station
from dx.cluster_connections import get_logger
from pprint import pprint
import glob 
from rig_io import NAQP_SECS,ARRL_SECS
from zipfile import ZipFile
from counties import COUNTIES

###################################################################

# Function to load history file
def load_history(history,DEBUG_CALL=None):

    # Init
    COMMENT_CHARS=['#','!']
    HIST = OrderedDict()
    ALL_FIELDS=['name','state','sec','check','county','cwops',       \
                'fdcat','fdsec','ituz','cqz','grid','skccnr','city', \
                'fistsnr','foc','names','status']

    # If no history file, we're done
    if history=='':
        return HIST,history
    elif '*' in history:

        # Expand wildcards and only keep the most recent history file
        files=[]
        for fname in glob.glob(history):
            files.append(fname)
        if len(files)==0:
            print('file=',files)
            print('LOAD HISTORY - No files found matching',history)
            sys.exit(0)
        files.sort()
        history=files[-1]
        #print(files[-1]) 
        #sys.exit(0)
    print('LOAD_HISTORY: History=',history)
     
    # Open logger file used by spot_processing routines
    rootlogger = "dxcsucker"
    logger = get_logger(rootlogger)
     
    # Get file extension
    fname=os.path.basename(history)
    ext=os.path.splitext(history)[1]
    print('\nHistory file=',history,'\tfname=',fname,'\text=',ext)

    # Check for state QPs
    if fname[:5]=='QSOP_':
        STATE_QP=fname[5:7]
    else:
        STATE_QP=None
    print('STATE_QP=',STATE_QP)

    if ext=='.xlsx':
        if history.find('CWops')>=0:
            #book  = xlrd.open_workbook(history)  #,formatting_info=True)
            #sheet = book.sheet_by_name('Roster')
            #book = openpyxl.load_workbook(history)
            #sheet = book['Roster']
            sheet = pandas.read_excel(history, sheet_name='Roster')
            #print(sheet)
            #print(sheet.iloc[2,1])
            #print(sheet.shape[0])

            #nrows=sheet.nrows
            #nrows=sheet.max_row
            nrows=sheet.shape[0]
            #nrows=5
            #print('HEY:',sheet.values['B2'])
            for i in range(1, nrows):
                #print( i,sheet.cell(i, 2).value )
                #print( i,sheet.values.cell(row=i, column=2) )
                #print( i,sheet.iloc[i,2] )
                #if sheet.cell(i,2).value.find('Callsign')>=0:
                if sheet.iloc[i,2]=='Callsign':
                    i1=i+1
                    break
            else:
                print('CW ops - Did not find start of table - aborting')
                sys.exit(1)
                
            for i in range(i1, nrows):
                #call   = sheet.cell(i, 2).value
                call   = str( sheet.iloc[i,2] )
                if len(call)==0 or call=='nan':
                    continue
                #number = sheet.cell(i, 3).value
                number = sheet.iloc[i,3]
                #name   = unidecode( sheet.cell(i, 4).value )
                name   = str( sheet.iloc[i,4] )
                #state  = sheet.cell(i, 7).value
                state  = str( sheet.iloc[i,7] )
                if state=='--' or state=='nan':
                    state=''

                HIST[call] = OrderedDict()
                for field in ALL_FIELDS:
                    if field=='names':
                        HIST[call][field]=[]
                    else:
                        HIST[call][field]=''
                HIST[call]['name']   = name.upper()
                HIST[call]['state']  = state.upper()
                HIST[call]['cwops']  = str( int(number) )

                if True:
                    status  = str( sheet.iloc[i,1] )
                    HIST[call]['status']  = status

                if call==DEBUG_CALL:
                    print('\nLOAD_HISTORY 0: call=',call)
                    print('iloc:',sheet.iloc[i,:])
                    print('call=',call,'\tnumber=',number,name,state)
                    print(HIST[call])
                    #sys.exit(0)
                
        else:
            print('Unknown spreadsheet - aborting')
            sys.exit(1)

        return HIST,history

    # There seems to be a lot of issues trying to use csv reader or pandas to
    # read these files so we'll do it our selves!!!
    print('LOAD HISTORY:',history)
    if 'skcc' in history:
        delim='|'
    else:
        delim=','

    if ext=='.zip':

        # Added this to handle zipped csv files from the RBN
        name=os.path.splitext(fname)[0]
        with ZipFile(history, 'r') as zipf:
            with zipf.open(name+'.csv', 'r') as csvfile:
                hist = csvfile.read().decode("utf-8")
                hist = hist.split("\n")
                csvfile.close()

    else:
        
        with open(history,'r',encoding='utf-8') as csvfile:
            hist = csvfile.read()
            hist = hist.split("\n")
            csvfile.close()

    if True:
        nrows=len(hist)
        if False:
            print(nrows)
            for i in range(10):
                #row=hist.iloc[i].tolist()
                row=hist[i].split(delim)
                print(i,row)
            print(type(row))
            sys.exit(0)
        #print(hist)

        for n in range(nrows):
            row=hist[n].split(delim)
            #print(row,len(row))

            if len(row)>0 and len(row[0])>0 and row[0]!=' ':

                if row[0][0]=='!' or \
                   (n==0 and ('skcc' in history or 'fists' in history)):
                    #print('Howdy Ho!')
                    KEYS=[]
                    #print('row=',row)
                    for item in row:
                        #print(item)
                        #if not pandas.isna(item) and len(item)>0 and \
                        if len(item)>0 and item[0] not in COMMENT_CHARS and item!='nan':
                            key = item.strip().lower()
                            if key=='sect':
                                if fname[:4]=='IARU':
                                    key='ituz'
                                else:
                                    key='sec'
                            elif key=='ck':
                                key='check'
                            elif fname[:5]=='FD_20' or fname[:5]=='WFD_2':
                                if key=='exch1':
                                    key='fdcat'
                                elif key=='sec':
                                    key='fdsec'
                            elif fname[:7]=='ARRL160' and key=='exch1':
                                key='sec'
                            elif STATE_QP and key=='exch1':
                                key='qth'
                            elif fname[:7]=='13COLON' and key=='exch1':
                                key='state'
                            elif (fname[:6]=='CQWWCW' or fname[:7]=='CQWWSSB') \
                                 and key=='exch1':
                                key='cqz'
                            elif fname[:6]=='CWOPS_' and key=='exch1':
                                key='cwops'
                            elif fname=='foc.txt' and key=='exch1':
                                key='foc'
                            elif fname[:8]=='K1USNSST' and key=='exch1':
                                key='state'
                            elif key=='loc1':
                                key='grid'
                            elif key=='callsign':
                                key='call'
                            elif key=='member number':
                                key='fistsnr'
                            elif 'fists' in fname and item==row[-1]:
                                key=''
                            KEYS.append( key )
                    #print('KEYS=',KEYS)
                    #if 'skcc' in history:
                    #    sys.exit(0)

                elif row[0][0] not in COMMENT_CHARS:

                    #print('KEYS=',KEYS)
                    #print('row=',row)

                    # Find the call & init struct for this call
                    idx=KEYS.index("call")
                    call=row[idx].upper()

                    if call in ['WAKL','F61112']:
                        print('Skipping invalid call',call)
                        #sys.exit(0)
                        continue

                    if call in HIST.keys():
                        if False:
                            print('\nLOAD_HISTORY: Call already seen in this file',call)
                            #print('HIST=',HIST[call])
                    else:
                        HIST[call] = OrderedDict()
                        for field in ALL_FIELDS:
                            if field=='names':
                                HIST[call][field]=[]
                            else:
                                HIST[call][field]=''

                    if call==DEBUG_CALL:
                        print('\nLOAD_HISTORY 1: row=',row)
                        print('call=',call)
                        print('HIST=',HIST[call])
                        #sys.exit(0)

                    # Disect the data for this call
                    for i in range(len(KEYS)):
                        key=KEYS[i].strip()
                        if len(row)>i:
                            val = row[i].replace(',',' ').upper()
                            val = val.encode('ascii',errors='ignore').decode()
                        elif hasattr(HIST[call],key):
                            val = HIST[call][key]
                        else:
                            val = ''
                        if val=='NAN':
                            val=''

                        if key=='loc1':
                            key='grid'
                            
                        elif STATE_QP and key=='qth':
                            
                            if val in COUNTIES[STATE_QP] or val[2:] in COUNTIES[STATE_QP] or '/' in val:
                                # In state --> county or county line
                                # Some tack on the abbrev for the state in front, hence the 2: above
                                key='county'
                            elif (STATE_QP in ['PA','NV']) and (val in ARRL_SECS):
                                # Out of state - A few send arrl section
                                key='sec'
                            elif val in NAQP_SECS:
                                # Out of state - most send state
                                key='state'
                            else:
                                if len(val)>0:
                                    print('LOAD HISTORY - STATE QP *** WARNING *** Skipping unknown val=',val,'for key=',key,'\tstate=',STATE_QP)
                                    print('row=',row)
                                    print(val in ARRL_SECS)
                                key=''
                                
                        if key in ALL_FIELDS:
                            if key=='names':
                                HIST[call][key].append(val)
                            else:
                                HIST[call][key] = val
                                if STATE_QP and val in COUNTIES[STATE_QP]:
                                    HIST[call]['state'] = STATE_QP
                                    
                        elif key not in ['',' ','call','usertext','misc','ccnr','mbrdate']:
                            print('\nLOAD_HISTORY: Unknown field ...',key)
                            print('row=',row)
                            print('key=',key,'\ti=',i)     # ,'\tval=',row[i],'\n')
                            sys.exit(0)

                    if call==DEBUG_CALL:
                        print('\nLOAD_HISTORY 2: row=',row)
                        print('call=',call)
                        print('HIST=',HIST[call])
                        #sys.exit(0)
                            
    # Some fix-ups
    for call in HIST.keys():
        # Fix-up for Field day
        if len(HIST[call]['fdcat'])>0 and len(HIST[call]['fdsec'])==0:
            HIST[call]['fdsec'] = HIST[call]['sec']
        
        # Fill in ITU & CQ Zones
        if len(HIST[call]['cqz'])==0 or len(HIST[call]['ituz'])==0:
            #print call
            #print HIST[call]
            dx_station = Station(call)
            if len(HIST[call]['cqz'])==0:
                HIST[call]['cqz'] = str( dx_station.cqz )
            if len(HIST[call]['ituz'])==0:
                HIST[call]['ituz'] = str( dx_station.ituz )

        if call==DEBUG_CALL:
            print('LOAD_HISTORY 3 - After fix-ups: call=',call,'\nHIST=',HIST[call])
            pprint(vars(dx_station))
            #sys.exit(0)
                
    if False:
        print(HIST)
        sys.exit(0)

    return HIST,history


