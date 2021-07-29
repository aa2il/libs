#######################################################################################
#
# Load History - Rev 1.0
# Copyright (C) 2021 by Joseph B. Attili, aa2il AT arrl DOT net
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

from rig_io.ft_tables import NAQP_SECS

###################################################################

# Function to load history file
def load_history(history):
    
    COMMENT_CHARS=['#','!']
    HIST = OrderedDict()
    if history=='':
        return HIST

    ALL_FIELDS=['name','state','sec','check','county','cwops', \
                'fdcat','fdsec','ituz','cqz','grid']

    # Open logger file used by spot_processing routines
    rootlogger = "dxcsucker"
    logger = get_logger(rootlogger)
     
    # Get file extension
    fname=os.path.basename(history)
    ext=os.path.splitext(history)[1]
    print('\nHistory file=',history,fname,ext)

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

                if call=='AA5B' and False:
                    print(call)
                    print(sheet.iloc[i,:])
                    print(call,number,name,state)
                
                HIST[call] = OrderedDict()
                HIST[call]['name']   = name.upper()
                HIST[call]['sec']    = ''
                HIST[call]['state']  = state.upper()
                HIST[call]['check']  = ''
                HIST[call]['county'] = ''
                HIST[call]['cwops']  = str( int(number) )
                HIST[call]['fdcat']  = ''
                HIST[call]['fdsec']  = ''
                HIST[call]['ituz']   = ''
                HIST[call]['cqz']    = ''
                HIST[call]['grid']   = ''

        else:
            print('Unknown spreadsheet - aborting')
            sys.exit(1)

        #print HIST
        #print HIST['AA3B']
        return HIST


    print('LOAD HISTORY:',history)
    with open(history,'r') as csvfile:   # This was ok under 2.7 but sometimes not 3
    # In FD.txt, it doesn't like the e' in VE2CVN
    #with open(history,'r',errors='ISO-8859-1') as csvfile:   # This used to work
    #with open(history,'r',errors='replace') as csvfile:       # So does this
    #with open(history,'r',newline='',encoding='utf-8') as csvfile:  # This does not
        #csvfile = open(history, 'r') 
        hist = csv.reader(csvfile, delimiter=',', quotechar='|')

        #print(hist)

        for row in hist:
            
            if len(row)>0:

                if row[0][0]=='!':
                    #print('Howdy Ho!')
                    KEYS=[]
                    print('row=',row)
                    for item in row:
                        if len(item)>0 and item[0] not in COMMENT_CHARS:
                            key = item.strip().lower()
                            if key=='sect':
                                key='sec'
                            elif key=='ck':
                                key='check'
                            elif fname[:5]=='FD_20':
                                if key=='exch1':
                                    key='fdcat'
                                elif key=='sec':
                                    key='fdsec'
                            elif fname[:7]=='QSOP_CA':
                                if key=='exch1':
                                    key='qth'
                            elif fname[:6]=='CWOPS_' and key=='exch1':
                                key='cwops'
                            elif fname[:8]=='K1USNSST' and key=='exch1':
                                key='state'
                            elif fname[:7]=='ARRLVHF' and key=='loc1':
                                key='grid'
                            KEYS.append( key )
                    print('KEYS=',KEYS)
                    #sys.exit(0)

                elif row[0][0] not in COMMENT_CHARS:

                    #print('KEYS=',KEYS)
                    #print('row=',row)
                    for i in range(len(KEYS)):
                        if i==0:
                            call=row[0]
                            HIST[call] = OrderedDict()
                            for field in ALL_FIELDS:
                                HIST[call][field]=''
                        else:
                            key=KEYS[i]
                            if len(row)>i:
                                val = row[i].upper()
                            else:
                                val = ''
                            if key=='qth':
                                if val in NAQP_SECS:
                                    key='state'
                                elif len(val)==4:
                                    key='county'
                            if key in ALL_FIELDS:
                                HIST[call][key] = val
                            elif key!='usertext' and len(val)>0:
                                print(row)
                                print('key/val=',key,row[i])
                                #sys.exit(0)

                    if False:
                        print('row=',row)
                        print('call=',call)
                        print('HIST=',HIST[call])
                        sys.exit(0)
                            
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

        if False and call=='W1WEF':
            print(call,HIST[call])
                
    if False:
        print(HIST)
        sys.exit(0)

    return HIST

