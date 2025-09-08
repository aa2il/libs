############################################################################################
#
# cwopen.py - Rev 1.0
# Copyright (C) 2021-5 by Joseph B. Attili, joe DOT aa2il AT gmail DOT com
#
# Routines for scoring CWops CW Open.
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
import datetime
from rig_io.ft_tables import *
from scoring import CONTEST_SCORING
from dx.spot_processing import Station
from pprint import pprint
from utilities import reverse_cut_numbers, error_trap

############################################################################################

# Scoring class for CWops CW Open - Inherits the base contest scoring class
class CWOPEN_SCORING(CONTEST_SCORING):

    def __init__(self,P,session=None,TRAP_ERRORS=False):
        #CONTEST_SCORING.__init__(self,P,'CW-OPEN',mode='CW')
        super().__init__(P,'CW-OPEN',mode='CW')
        
        self.BANDS = ['160m','80m','40m','20m','15m','10m']
        self.sec_cnt = np.zeros((len(self.BANDS)),dtype=np.int32)
        self.calls=set([])
        self.last_num_out=0

        self.MY_CALL     = P.SETTINGS['MY_CALL']
        self.MY_NAME     = P.SETTINGS['MY_NAME']
        self.MY_SECTION  = P.SETTINGS['MY_SEC']
        self.MY_STATE    = P.SETTINGS['MY_STATE']
        self.TRAP_ERRORS = TRAP_ERRORS
        
        # History file
        self.history = os.path.expanduser( '~/Python/history/data/master.csv' )
        
        # Determine contest date/time - first Sat in Sept.
        now = datetime.datetime.utcnow()
        day1=datetime.date(now.year,9,1).weekday()                     # Day of week of 1st of month 0=Monday, 6=Sunday
        sat2=1 + ((5-day1) % 7)                                        # Day no. for 1st Saturday = 1 since day1 is the 1st of the month
                                                                       #    plus no. days until 1st Saturday (day 5)
        day   = now.day
        hour  = now.hour
        today = now.strftime('%A')

        # Determine start time assuming this code is run shortly after the contest
        if not session:
            session='ALL'
            start_time=0                                               # 1st session is 0000-0400 UTC
            duration=24
        elif session==00 or session==1:
            start_time=0                                               # 1st session is 0000-0400 UTC                           
            duration=4
        elif session==12 or session==2:
            start_time=12                                              # 2nd session is 1200-1600 UTC                           
            duration=4
        elif session==20 or session==3:
            start_time=20                                              # 3rd session is 2000-2400 UTC
            duration=4
        else:
            print('\n*** Need to specify a valid session ***\n')
            sys.exit(0)

        self.date0=datetime.datetime(now.year,9,sat2,start_time)       # Need to add more code for other sessions next year
        self.date1 = self.date0 + datetime.timedelta(hours=duration)          # Each session is 4hrs long
        print('day1=',day1,'\tsat2=',sat2,'\tdate0=',self.date0)
        #sys.exit(0)

        # Manual override
        if False:
            self.date0 = datetime.datetime.strptime( "20210904 0000" , "%Y%m%d %H%M")  # Start of contest
            self.date1 = self.date0 + datetime.timedelta(hours=4)
        
        if True:
            print('session=',session)
            print('now=',now)
            print('today=',today)
            print('hour=',hour)
            print('date0=',self.date0)
            print('date1=',self.date1)
            #sys.exit(0)
            
        # Name of output file
        self.output_file = 'CWOPEN_'+self.MY_CALL+'_'+str(session)+'.LOG'

        # Inits
        #self.init_otf_scoring()
                
    # Contest-dependent header stuff
    def output_header(self,fp):
        fp.write('LOCATION: %s\n' % self.MY_STATE)
        fp.write('ARRL-SECTION: %s\n' % self.MY_SECTION)

    # Scoring routine for CW Ops CW Open
    def qso_scoring(self,rec,dupe,qsos,HIST,MY_MODE,HIST2):
        #print 'rec=',rec
        keys=list(HIST.keys())

        # Pull out relavent entries
        call = rec["call"].upper()
        rx   = rec["srx_string"].strip().upper()
        a    = rx.split(',')
        try:
            num_in = str( int( a[0] ) )
        except:
            num_in = reverse_cut_numbers( a[0] )
            print('Hmmmmmmmmmmm:',call,a[0],num_in)
        name_in = a[1]
        #name = rec["name"].upper()
        name_in2 = rec["name"].upper()

        freq_khz = int( 1000*float(rec["freq"]) +0.5 )
        band = rec["band"]
        date_off = datetime.datetime.strptime( rec["qso_date_off"] , "%Y%m%d").strftime('%Y-%m-%d')
        time_off = datetime.datetime.strptime( rec["time_off"] , '%H%M%S').strftime('%H%M')
        
        tx   = rec["stx_string"].strip().upper()
        b    = tx.split(',')
        num_out  = int( reverse_cut_numbers( b[0] ) )
        name_out = b[1]
        #my_call = rec["station_callsign"].strip().upper()
                
        if '?' in str(num_in)+name_in or not name_in.isalpha() or not num_in.isnumeric() or (name_in!=name_in2):
            print('\n*** ERROR *** "?" in serial number and/or name and/or name contains numbers or serial is not numeric ***')
            print('call   =',call)
            print('serial =',num_in)
            print('name   =',name_in)
            print('Time   =',time_off)
            print('rec=',rec)
            self.list_all_qsos(call,qsos)
            if self.TRAP_ERRORS:
                sys.exit(0)
        
        if num_out-self.last_num_out!=1:
            print('\n*** ERROR *** Jump in serial out??? ***',self.last_num_out,num_out)
            print('call   =',call)
            print('serial =',num_in)
            print('name   =',name_in)
            print('Time   =',time_off)
            if self.TRAP_ERRORS and False:
                sys.exit(0)
        self.last_num_out = num_out

        if MY_MODE=='CW':
            mode='CW'
        else:
            print('Invalid mode',MY_MODE)
            sys.exit(1)

        self.calls.add(call)

        if False:
            print('call   =',call)
            print('serial =',num_in)
            print('name   =',name_in)
            print('calls =',self.calls)

        if not dupe:
            idx2 = self.BANDS.index(band)
            self.sec_cnt[idx2] += 1
            self.nqsos2 += 1;
        else:
            print('??????????????? Dupe?',call)
        #print call,self.nqsos2

        # Check for DX calls
        if call not in keys and '/' in call:
            dx_station = Station(call)
            #pprint(vars(dx_station))
            call2 = dx_station.homecall
            #print(HIST[call])
            #sys.exit(0)
        else:
            call2=call

        # Check against history
        if call2 in keys:
            #print 'hist=',HIST[call2]
            name9=HIST[call2]['name']
            #print call2,qth,state
            if name_in!=name9:
                print('\n$$$$$$$$$$ Difference from history $$$$$$$$$$$')
                print(call,':  Current:',name_in,' - History:',name9)
                print('serial =',num_in)
                print('Time   =',time_off)
                self.list_all_qsos(call,qsos)
                print(' ')

        else:
            print('\n++++++++++++ Warning - no history for call:',call)
            self.list_all_qsos(call,qsos)
            self.list_similar_calls(call,qsos)

        # Info for multi-qsos
        exch_in=name_in
        if call in self.EXCHANGES.keys():
            self.EXCHANGES[call].append(exch_in)
        else:
            self.EXCHANGES[call]=[exch_in]
                
        # Count no. of CWops guys worked
        self.count_cwops(call,HIST,rec)
                
#000000000111111111122222222223333333333444444444455555555556666666666777777777788
#123456789012345678901234567890123456789012345678901234567890123456789012345678901
#                              -----info sent------       -----info rcvd------
#QSO: freq  mo date       time  call      nr   ex1        call       nr   name
#QSO: ***** ** yyyy-mm-dd nnnn ********** nnnn aaaaaaaaaa ********** nnnn aaaaaaaaaa
#QSO: 14042 CW 2011-09-20 0000 N5TJ          1 JEFF       N6TR       1    TREE

        line='QSO: %5d %2s %10s %4s %-10s %4s %-11s %-10s %4s %-11s' % \
            (freq_khz,mode,date_off,time_off,
             self.MY_CALL,num_out,name_out,
             call,num_in,name_in)
        
        return line
                        
    # Summary & final tally
    def summary(self):
        
        mults = len(self.calls)
        print('Calls =',self.calls)
        print('mults=',mults)

        print('\nNo. QSOs        =',self.nqsos1)
        print('No. Uniques     =',self.nqsos2)
        print('No. Skipped     =',self.nskipped)

        #print('band count =',self.sec_cnt)
        print('\nBand\tQSOs\tMults')
        for i in range(len(self.BANDS)):
            print(self.BANDS[i],'\t',self.sec_cnt[i],'\t','-')
        print('\nTotals:\t',sum(self.sec_cnt),'\t',mults)
        print('Claimed score=',mults*self.nqsos2)

        print('\n# CWops Members =',self.num_cwops,' =',
              int( (100.*self.num_cwops)/self.nqsos1+0.5),'%')
        print('# QSOs Running  =',self.num_running,' =',
              int( (100.*self.num_running)/self.nqsos1+0.5),'%')
        print('# QSOs S&P      =',self.num_sandp,' =',
              int( (100.*self.num_sandp)/self.nqsos1+0.5),'%')
        
