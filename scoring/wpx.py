############################################################################################
#
# wpx.py - Rev 1.1
# Copyright (C) 2021-5 by Joseph B. Attili, aa2il AT arrl DOT net
#
# Routines for scoring CQ WPX CW contest.
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
from utilities import reverse_cut_numbers,error_trap
from tkinter import END

############################################################################################

# Scoring class for CQ WPX and CQMM contests - Inherits the base contest scoring class
class CQ_WPX_SCORING(CONTEST_SCORING):
    def __init__(self,P,MODE,CONTEST,TRAP_ERRORS=False):

        print('CQ WPX Scoring Init: contest=',CONTEST,'...')
        self.prev_num_out=0
        self.TRAP_ERRORS = TRAP_ERRORS
        
        if 'WPX' in CONTEST:
            CONTEST_NAME='CQ-WPX-'+MODE
            self.WPX=True
            hrs1=0
            hrs=48
            if MODE=='CW':
                # The WPX CW Contest occurs on the last full weekend of May
                month=5
                ndays=21                                                   # 4th Sat
            else:
                # The WPX RTTY Contest occurs on 2nd full weekend of Feb
                month=2
                ndays=7                                                    # 2nd Sat
        elif CONTEST=='CQMM':
            # The CQMM occurs on 3rd weekend in April
            CONTEST_NAME='CQMM'
            self.WPX=False
            month=4
            ndays=14                                                       # 3rd Sat
            hrs1=9
            hrs=48-hrs1
        else:
            print('WPX SCORING INIT: I dont know what I am doing here!!!!!')
            sys.exit(0)
        
        # Inits
        super().__init__(P,CONTEST_NAME,MODE)

        if MODE=='CW':
            self.BANDS = ['160m','80m','40m','20m','15m','10m']
        else:
            self.BANDS = ['80m','40m','20m','15m','10m']
        self.sec_cnt = np.zeros(len(self.BANDS),dtype=int)
        self.calls=set([])
        self.dxccs = set([])
        sa_prefixes  = []
        for b in self.BANDS:
            sa_prefixes.append((b,set([])))
        self.sa_prefixes = OrderedDict(sa_prefixes)
        self.init_otf_scoring()

        # Determine start & end dates/times
        now = datetime.datetime.utcnow()
        year=now.year
        #year=2021
        day1=datetime.date(year,month,1).weekday()                     # Day of week of 1st of month - 0=Monday, 6=Sunday
        sat2=1 + ((5-day1) % 7) + ndays                                # Day no. for 2nd or 4th Saturday = 1 since day1 is the 1st of the month
                                                                       #    no. days until 1st Saturday (day 5) + 7 more days 
        if CONTEST=='WPX' and MODE=='CW' and sat2+7<=30:
            sat2+=7                                                    # Make sure we get last weekend
            
        self.date0=datetime.datetime(year,month,sat2,0) + datetime.timedelta(hours=hrs1) 
        self.date1 = self.date0 + datetime.timedelta(hours=hrs)        # ... and ends at 0300/0400 UTC on Monday
        print('day1=',day1,'\tsat2=',sat2,'\tdate0=',self.date0,'\tdate1=',self.date1)
        #sys.exit(0)
        
        # Manual override
        if False:
            if MODE=='CW':
                #self.date0 = datetime.datetime.strptime( "20190525 0000" , "%Y%m%d %H%M")  # Start of contest
                self.date0 = datetime.datetime.strptime( "20210529 0000" , "%Y%m%d %H%M")  # Start of contest
                self.date1 = self.date0 + datetime.timedelta(hours=48)
            else:
                self.date0 = datetime.datetime.strptime( "20190209 0000" , "%Y%m%d %H%M")  # Start of contest
                self.date1 = self.date0 + datetime.timedelta(hours=48)
            
        # Name of output file
        self.output_file = self.MY_CALL+'_'+CONTEST_NAME+'_'+str(self.date0.year)+'.LOG'
        
        
    # Contest-dependent header stuff
    def output_header(self,fp):
        fp.write('LOCATION: %s\n' % self.MY_SEC)
        fp.write('ARRL-SECTION: %s\n' % self.MY_SEC)
            
    # Scoring routine for CQ WPX
    def qso_scoring(self,rec,dupe,qsos,HIST,MY_MODE,HIST2):
        #print('rec=',rec)
        #sys.exit(0)

        # Pull out relavent entries
        id = rec["contest_id"].upper()
        if id not in ['CQMM','CQ-WPX-CW']:
            print(id)
            return
        
        call = rec["call"].upper()
        if 'srx_string' in rec:
            rx   = rec["srx_string"].strip().upper()
        else:
            print('rec=',rec)
            print('WPX.PY - Hmmm - cant find rx string')
            if self.TRAP_ERRORS:
                sys.exit(0)
            else:
                rx='0'
        a    = rx.split(',')
        #a    = rx.split(' ')                    # Note - there was a bug in 2019 - this should be a comma
        if len(a)>1:
            rst_in = reverse_cut_numbers( a[0] )
            if self.WPX:
                num_in = reverse_cut_numbers( a[1] )
            else:
                num_in = a[1]
        else:
            rst_in = rec["rst_rcvd"].strip().upper()
            if self.WPX:
                num_in = reverse_cut_numbers( a[0] )
            else:
                num_in = a[1]

        if 'stx_string' in rec:
            tx   = rec["stx_string"].strip().upper()
        elif 'stx' in rec:
            tx   = rec["stx"].strip().upper()
        else:
            print('rec=',rec)
            print('WPX.PY - Hmmm - cant find tx string')
            if self.TRAP_ERRORS:
                sys.exit(0)
            else:
                tx='0'
        b    = tx.split(',')
        if len(b)>1:
            rst_out = reverse_cut_numbers( b[0] )
            if self.WPX:
                num_out = reverse_cut_numbers( b[1] )
            else:
                num_out = 'NA'     # b[1]
        else:
            if True:
                rst_out = rec["rst_sent"].strip().upper()
            else:
                # If the format as string ? box isn't checked in libreoffice,
                # it will hose up "599,100" and return 599100 - ugh!
                rst_out=599
                tx   = rec["stx"].strip().upper()
                b    = tx.split(',')
                
            if self.WPX:
                num_out = reverse_cut_numbers( b[0] )
            else:
                num_out = 'NA'    # b[1]
            
        freq_khz = int( 1000*float(rec["freq"]) +0.5 )
        band = rec["band"]
        date_off = datetime.datetime.strptime( rec["qso_date_off"] , "%Y%m%d").strftime('%Y-%m-%d')
        time_off = datetime.datetime.strptime( rec["time_off"] , '%H%M%S').strftime('%H%M')

        mode = rec["mode"].strip().upper()
        if mode!=MY_MODE:
            print('Invalid mode',MY_MODE)
            sys.exit(1)

        # Some simple checks
        if rst_in!='599':
            print('*** WARNING *** RST in =',rst_in)
            if self.TRAP_ERRORS:
                sys.exit(0)
                
        if self.WPX:
            if not num_in.isdigit():
                print('\n*** ERROR *** NUM IN =',num_in)
                print('rec=',rec,'\n')
                if self.TRAP_ERRORS:
                    print('call     =',call)
                    print('date     =',date_off)
                    print('time     =',time_off)
                    sys.exit(0)

            if int(num_out)!=self.prev_num_out+1:
                print('\n*** WARNING *** NUM OUT =',num_out,' not consecutive, ',
                      'prev=',self.prev_num_out)
                print('call     =',call)
                print('date     =',date_off)
                print('time     =',time_off)
                if int(num_out)<=0 and self.TRAP_ERRORS:
                    sys.exit(0)
            self.prev_num_out=int(num_out)


        # Determine multipliers
        dx_station = Station(call)
        #prefix = dx_station.call_prefix + dx_station.call_number
        prefix = dx_station.prefix
        if dx_station.prefix==dx_station.call_prefix:
            prefix = dx_station.call_prefix + dx_station.call_number
            print(prefix)
        self.calls.add(prefix)
        continent = dx_station.continent
        country   = dx_station.country
        self.dxccs.add(country)
        if False:
            pprint(vars(dx_station))
            sys.exit(0)

        if not self.WPX:
            if num_in[0:2]!=continent:
                print('\nWPX - Continent Mismatch!!!\trx=',num_in,'\tactual=',continent)
                print('rec=',rec)
                sys.exit(0)
            if len(num_in)==3:
                cat=num_in[2]
            else:
                cat=''
                
        if not self.WPX and cat in ['M','Y','Q']:
                qso_points = 10
                
        elif country=='United States':
            if not self.WPX or MY_MODE=='CW':
                qso_points = 1
            else:
                if band in ['160m','80m','40m']:
                    qso_points = 2
                elif band in ['20m','15m','10m']:
                    qso_points = 1
                else:
                    pprint(vars(dx_station))
                    print('band=',band)
                    sys.exit(0)
                    
        elif continent=='NA':
            if band in ['160m','80m','40m']:
                qso_points = 4
            elif band in ['20m','15m','10m']:
                qso_points = 2
            else:
                pprint(vars(dx_station))
                print('band=',band)
                sys.exit(0)
                
        elif continent in ['SA','EU','OC','AF','AS']:
            if band in ['160m','80m','40m']:
                qso_points = 6
            elif band in ['20m','15m','10m']:
                qso_points = 3
            else:
                pprint(vars(dx_station))
                print('band=',band)
                sys.exit(0)
                
        else:
            print('\n*** WPX: Not Sure what to do with this??!! ***')
            pprint(vars(dx_station))
            sys.exit(0)

        if not self.WPX and continent=='SA':
            self.sa_prefixes[band].add(prefix)
            #if prefix=='K1':
            #    print('rec=',rec)
            #    pprint(vars(dx_station))
            #    sys.exit(0)
            
        if False:
            print('rec=',rec)
            pprint(vars(dx_station))
            print('call     =',call)
            print('prefix   =',prefix)
            print('exch out =',rst_out,num_out)
            print('exch in  =',rst_in,num_in)
            #sys,exit(0)

        if not dupe:
            idx2 = self.BANDS.index(band)
            self.sec_cnt[idx2] += 1
            self.nqsos2 += 1;
            self.total_points += qso_points
            
        # Info for multi-qsos
        exch_in=rst_in+' '+num_in
        if call in self.EXCHANGES.keys():
            self.EXCHANGES[call].append(exch_in)
        else:
            self.EXCHANGES[call]=[exch_in]
                        
        # Count no. of CWops guys worked
        self.count_cwops(call,HIST,rec)
                
#000000000111111111122222222223333333333444444444455555555556666666666777777777788
#123456789012345678901234567890123456789012345678901234567890123456789012345678901
#                               --------info sent------- -------info rcvd--------
#QSO: freq  mo date       time call          rst exch   call          rst exch   t
#QSO: ***** ** yyyy-mm-dd nnnn ************* nnn ****** ************* nnn ****** n
#QSO:  3799 PH 1999-03-06 0711 HC8N          59  001    W1AW          59  001    0
        line='QSO: %5d %2s %10s %4s %-13s %-3s %-6s %-13s      %-3s %-6s' % \
            (freq_khz,mode,date_off,time_off,
             self.MY_CALL,rst_out,num_out,
             call,rst_in,num_in)
        
        return line
                        
    # Summary & final tally
    def summary(self):

        print('\nNo. QSOs         =',self.nqsos2)
        #print('Band Count       =',self.sec_cnt)

        print('\nBand\t# QSOs\t# SA Prefixes')
        mults=0
        for i in range( len(self.BANDS) ):
            b=self.BANDS[i]
            pre=self.sa_prefixes[b]
            print(b,'\t',self.sec_cnt[i],'\t',len(pre),'\t',pre)
            mults+=len(pre)

        print('\nDXCCs =',sorted( self.dxccs ),len(self.dxccs))
        if self.WPX:
            print('\nPrefixes         =',sorted( self.calls ),len(self.calls))
            mults = len(self.calls)
        else:
            mults += len(self.dxccs)
            
        print('\nNo. QSOs         =',self.nqsos2)
        print('QSO Points       =',self.total_points)
        print('Mults            =',mults)
        print('Claimed score    =',self.total_points*mults)

        print('\nNo. CWops Members =',self.num_cwops,' =',
              int( (100.*self.num_cwops)/self.nqsos1+0.5),'%')
        print('No. QSOs Running  =',self.num_running,' =',
              int( (100.*self.num_running)/self.nqsos1+0.5),'%')
        print('No. QSOs S&P      =',self.num_sandp,' =',
              int( (100.*self.num_sandp)/self.nqsos1+0.5),'%')
        
        
    # On-the-fly scoring
    def otf_scoring(self,qso):
        #print("\nWPX OTF SCORING: qso=",qso)

        try:
            if 'CALL' in qso:
                call=qso['CALL']
                band = qso["BAND"]
                rx = qso["SRX_STRING"]
                mode = qso["MODE"]
            else:
                call=qso['call']
                band = qso["band"]
                rx = qso["srx_string"]
                mode = qso["mode"]
            rx = rx.strip().upper()
        except:
            error_trap('WPX->OTF SCORING - Unexpected error!')
            print('qso=',qso)
            sys.exit(0)
            return

        self.nqsos+=1
        a    = rx.split(',')
        if len(a)>1:
            rst_in = reverse_cut_numbers( a[0] )
            if self.WPX:
                num_in = reverse_cut_numbers( a[1] )
            else:
                num_in = a[1]
        else:
            rst_in = qso["rst_rcvd"].strip().upper()
            if self.WPX:
                num_in = reverse_cut_numbers( a[0] )
            else:
                num_in = a[1]

        # Determine multipliers
        dx_station = Station(call)
        #if '/' in call:
        #    print('\nFile: wpx.py - problem with call parser - call=',call)
        #    pprint(vars(dx_station))
        prefix = dx_station.prefix
        if dx_station.prefix==dx_station.call_prefix:
            prefix = dx_station.call_prefix + dx_station.call_number
        if isinstance(prefix, str):
            self.calls.add(prefix)
        continent = dx_station.continent
        country   = dx_station.country
        if isinstance(country, str):
            self.dxccs.add(country)

        # Scoring
        if not self.WPX and cat in ['M','Y','Q']:
                qso_points = 10
                
        elif country=='United States':
            if not self.WPX or mode=='CW':
                qso_points = 1
            else:
                if band in ['160m','80m','40m']:
                    qso_points = 2
                elif band in ['20m','15m','10m']:
                    qso_points = 1
                else:
                    qso_points = 0
                    
        elif continent=='NA':
            if band in ['160m','80m','40m']:
                qso_points = 4
            elif band in ['20m','15m','10m']:
                qso_points = 2
            else:
                qso_points = 0
                
        elif continent in ['SA','EU','OC','AF','AS']:
            if band in ['160m','80m','40m']:
                qso_points = 6
            elif band in ['20m','15m','10m']:
                qso_points = 3
            else:
                qso_points = 0
                
        else:
            qso_points = 0
            
        idx2 = self.BANDS.index(band)
        self.sec_cnt[idx2] += 1
        self.total_points += qso_points

        if not self.WPX and continent=='SA':
            self.sa_prefixes[band].add(prefix)
            
        if self.WPX:
            """
            try:
                print('\nPrefixes         =',sorted( self.calls ),len(self.calls))
            except:
                error_trap('WPX->OTF SCORING - Error with prefix list?!')
                print('\nPrefixes         =',self.calls,len(self.calls))
            """
            mults = len(self.calls)
        else:
            mults = len(self.dxccs)
            for i in range( len(self.BANDS) ):
                b=self.BANDS[i]
                pre=self.sa_prefixes[b]
                mults+=len(pre)

        self.score = self.total_points*mults
        self.txt='{:4d} QSOs  x {:3d} Mults = {:8,d} \t\t\t Last Worked: {:s}' \
            .format(self.nqsos,mults,self.score,call)
        if self.P.gui:
            self.P.gui.status_bar.setText(self.txt)

            
    # Put summary info in big text box
    def otf_summary(self):

        txt = 'Prefixes = '+' '.join(sorted( self.calls ))+'\n'
        self.P.gui.txt.insert(END, txt, ('highlight'))
        for i in range(len(self.BANDS)):
            txt = '{:s} \t {:d}\n'.format(self.BANDS[i],self.sec_cnt[i])
            self.P.gui.txt.insert(END, txt, ('highlight'))
        txt = '{:s} \t {:d} QSOs x {:d} Prefixes = {:,d}\n'.format('Totals:',np.sum(self.sec_cnt),len(self.calls),self.score)
        self.P.gui.txt.insert(END, txt, ('highlight'))
        #txt='No. Unique Calls = {:d}\n'.format(len(self.calls))
        #self.P.gui.txt.insert(END, txt, ('highlight'))
        #self.P.gui.txt.insert(END, self.txt+'\n', ('highlight'))
        self.P.gui.txt.see(END)
        
