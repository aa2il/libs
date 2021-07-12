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

from rig_io.ft_tables import SST_SECS

###################################################################

# Function to load history file
def load_history(history):
    
    HIST = OrderedDict()
    if history=='':
        return HIST

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

                if call=='K5WSN' and False:
                    print(call)
                    print(sheet.iloc[i,:])
                    print(call,number,name,state)
                
                HIST[call] = OrderedDict()
                HIST[call]['name']   = name.upper()
                HIST[call]['sec']    = ''
                HIST[call]['state']  = state.upper()
                HIST[call]['check']  = ''
                HIST[call]['county'] = ''
                HIST[call]['CWops']  = str( int(number) )
                HIST[call]['FDcat']  = ''
                HIST[call]['FDsec']  = ''
                HIST[call]['ITUz']   = ''
                HIST[call]['CQz']    = ''
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
        nrows=0

        caqp = fname=='CQP-CH-N1MM-05Oct2018.txt'
        
        for row in hist:
            #print(row)
            #print(type(row))
            #for el in row:
            #    print( [ord(c) for c in el] )  
            valid=False
            if len(row)>0:

                if row[0][0]!='#' and row[0][0]!='!':
                    
                    # N1MM Logger helper file OR AZ Outlaws history file
                    call = row[0]
                    name = row[1]
                    number = ''

                    if fname[:6]=='CWOPS_':
                        if row[2].isnumeric():
                            number = row[2]
                            try:
                                qth=row[3].split(' ')
                            except:
                                qth=''
                            if len(qth)>0 and qth[-1] in SST_SECS:
                                state=qth[-1]
                            else:
                                state=''
                        else:
                            state=row[2]
                            number=''

                        if call=='KC1KUG':
                            print('row=',row)
                            print('state=',state)
                            
                    else:
                        if len(row)>=6 and False:
                            state = row[5]                 # AZ format - haven't used this in quite some time
                            print('LOAD_HISTORY: Rut-roh')
                            print('row=',row,'\t',len(row))
                            sys.exit(0)
                        elif len(row)>=3:
                            state = row[2]                 # N1MM format
                        else:
                            state = ''

                        #try:
                        #    state = row[5]                 # AZ format - haven't used this in quite some time
                        #except:
                        #    state = row[2]                 # N1MM format
                            #try:
                            #except:
                            #    print('LOAD_HISTORY: Rut-roh')
                            #    print('row=',row,'\t',len(row))
                            #    sys.exit(0)

                    try:
                        unknown = row[3]
                    except:
                        unknown = ''
                    try:
                        sec = row[4]
                    except:
                        sec =''
                    try:
                        check = row[6]
                    except:
                        check = ''
                    try:
                        county = row[7]
                    except:
                        county = ''

                    if number=='':
                        try:
                            number = row[8]
                        except:
                            number = ''
                        
                    try:
                        FDcat = row[9]
                    except:
                        FDcat = ''
                    try:
                        FDsec = row[10]
                    except:
                        FDsec = ''
                    try:
                        ITUz = row[11]
                    except:
                        ITUz = ''
                    try:
                        CQz = row[12]
                    except:
                        CQz = ''
                    try:
                        gridsq = row[13]
                    except:
                        gridsq = ''

                    valid=True

                    # Fix-up for CA QSO Party
                    if caqp:
                        check = ''
                        sec=''
                        if len(state)==4:
                            county=state
                            state='CA'

                    # Fix-up for Sweepstakes
                    if fname=='SSCW.txt':
                        sec = row[1]
                        check = row[3]
                        name=''
                        
                    # Fix-up for SST
                    #if fname=='K1USNSST-017.txt':
                    #    sec = row[1]
                    #    check = row[3]
                    #    name=''
                        
                    # Fix-up for Field day
                    if fname[0:5]=='FD_20' and ext=='.txt':
                        FDcat = name.upper()
                        name=''
                        FDsec = state.upper()
                        state=''

                    # ITU
                    if fname[0:4]=='IARU' and ext=='.txt':
                        ITUz = name.upper()
                        name=''
                    #else:
                    #    ITUz = ''

                    # ARRL VHF
                    if fname[0:7]=='ARRLVHF' and ext=='.txt':
                        gridsq = state.upper()
                        state=''
                    #else:
                    #    gridsq = ''
                                            
                if valid:
                    HIST[call] = OrderedDict()
                    HIST[call]['name']   = name.upper()
                    HIST[call]['state']  = state.upper()
                    HIST[call]['sec']    = sec.upper()
                    HIST[call]['check']  = check
                    HIST[call]['county'] = county.upper()
                    HIST[call]['CWops']  = number
                    HIST[call]['FDcat']  = FDcat
                    HIST[call]['FDsec']  = FDsec
                    HIST[call]['ITUz']   = ITUz
                    HIST[call]['CQz']    = CQz
                    HIST[call]['grid']   = gridsq

                    if call=='K5WSN' and False:
                        print(row)
                        print(HIST[call])
                        #sys.exit(0)

    # Fill in ITU & CQ Zones
    calls=list(HIST.keys())
    for call in calls:
        if len(HIST[call]['CQz'])==0 or len(HIST[call]['ITUz'])==0:
            #print call
            #print HIST[call]
            dx_station = Station(call)
            if len(HIST[call]['CQz'])==0:
                HIST[call]['CQz'] = str( dx_station.cqz )
            if len(HIST[call]['ITUz'])==0:
                HIST[call]['ITUz'] = str( dx_station.ituz )

        if False and call=='W1WEF':
            print(call,HIST[call])
                
    if False:
        print(HIST)
        sys.exit(0)

    return HIST

