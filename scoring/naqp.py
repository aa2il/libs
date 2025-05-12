############################################################################################
#
# naqp.py - Rev 1.1
# Copyright (C) 2021-5 by Joseph B. Attili, joe DOT aa2il AT gmail DOT com
#
# Routines for scoring NAQP CW & RTTY contests
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
from utilities import error_trap

############################################################################################
    
# Scoring class for NAQP CW & RTTY - Inherits the base contest scoring class
class NAQP_SCORING(CONTEST_SCORING):
 
    def __init__(self,P,contest,TRAP_ERRORS=False):
        print('NAQP Scoring Init: contest=',contest,'...')

        # Jan CW contest occurs on 2nd full weekend of Jan
        # Aug CW contest occurs on 1st full weekend of Aug
        now = datetime.datetime.utcnow()
        year=now.year
        MONTH = now.strftime('%b').upper()
        print('month=',MONTH)

        if MONTH=='JAN':
            m=1
            dd=7
            MODE='CW'
        elif MONTH=='FEB':
            m=2
            dd=21
            MODE='RTTY'
        elif MONTH=='JUL':
            m=7
            dd=21
            MODE='RTTY'
        elif MONTH=='AUG':
            m=8
            dd=7
            MODE='CW'
        else:
            m=8
            dd=0

        # Inits
        super().__init__(P,contest,mode=MODE)
            
        self.BANDS = ['160m','80m','40m','20m','15m','10m']
        self.band_cnt = np.zeros((len(self.BANDS)),dtype=np.int32)
        self.sec_cnt = np.zeros((len(NAQP_SECS),len(self.BANDS)),dtype=np.int32)
        self.TRAP_ERRORS = TRAP_ERRORS
        self.checked = []
        
        self.init_otf_scoring()

        day1=datetime.date(year,m,1).weekday()                      # Day of week of 1st of month 0=Monday, 6=Sunday
        sat1=1 + ((5-day1) % 7)  +dd                                # Day no. for 1st or 2nd Saturday = 1 since day1 is the 1st of the month
        start_hour=18
        self.date0=datetime.datetime(year,m,sat1,start_hour)       # Contest starts at 1800 UTC on Saturday ...
        self.date1 = self.date0 + datetime.timedelta(hours=12)         # ... and ends at 0600 UTC on Sunday
        print('day1=',day1,'\tsat1=',sat1,'\tdate0=',self.date0)
        #sys.exit(0)

        # Name of output file - stupid web uploader doesn't recognize .LOG extenion!
        # !!!!!!!!!!!!!! MUST BE .TXT !!!!!!!!!!!!!!!
        self.output_file = self.MY_CALL+'_NAQP_'+MONTH+'_'+MODE+'_'+str(self.date0.year)+'.TXT'
        

    # Contest-dependent header stuff
    def output_header(self,fp):
        fp.write('LOCATION: %s\n' % self.MY_STATE)
        fp.write('ARRL-SECTION: %s\n' % self.MY_SECTION)
                            
    # Scoring routine for NAQP CW and RTTY
    def qso_scoring(self,rec,dupe,qsos,HIST,MY_MODE,HIST2):
        #print('rec=',rec)
        keys=list(HIST.keys())

        # Pull out relavent entries
        id = rec["contest_id"].upper()
        if id not in ['NAQP-RTTY','NAQP-CW']:
            print(id)
            return
        
        call = rec["call"].upper()
        if 'qth' in rec:
            qth  = rec["qth"].upper()
        else:
            qth='?'
        if 'name' in rec:
            name = rec["name"].upper()
        else:
            name='?'
        freq_khz = int( 1000*float(rec["freq"]) +0.5 )
        band = rec["band"]
        date_off = datetime.datetime.strptime( rec["qso_date_off"] , "%Y%m%d").strftime('%Y-%m-%d')
        time_off = datetime.datetime.strptime( rec["time_off"] , '%H%M%S').strftime('%H%M')
        if MY_MODE=='CW':
            mode='CW'
        elif MY_MODE=='RTTY':
            mode='RY'
        else:
            print('Invalid mode',MY_MODE)
            sys.exit(1)

        # There is some duplication in the adif file
        if "srx_string" in rec:
            rx_string = rec["srx_string"].upper().split(',')
            if rx_string[0]!=name or rx_string[1]!=qth:
                print('\n******** Houston, we have a problem - inconsitency in recorded  exchange')
                print('\tcall=',call)
                print('\tqth=',qth)
                print('\tname=',name)
                print('\trx_string=',rx_string)
                if self.TRAP_ERRORS:
                    sys.exit(0)
            
        """
        # In 2017, there was some inconsistancies in how the name & state were saved
        if call=='AA2IL' or qth==name:
            print('\n******** Houston, we have a problem:')
            print('\tcall=',call)
            print('\tqth=',qth)
            print('\tname=',name)
            sys.exit(0)
        elif len(qth)>2 and len(name)==2:
            tmp=qth
            qth=name
            name=tmp
        elif len(qth)==2 and len(name)==2 and (not (qth in NAQP_SECS)) or (name in NAQP_SECS):
            print('\n--- Check this one for to make sure name & qth are not reversed ---')
            print('call=',call,'\t\tname=',name,'\t\tqth=',qth)
        """

        # Sometimes, I'll put a "?" to indicate that I need to review
        if '?' in call+name+qth:
            print('\n??? Check this one again: ???')
            print('call=',call,'\t\tname=',name,'\t\tqth=',qth)
            self.list_all_qsos(call,qsos)
            if self.TRAP_ERRORS:
                print('HIST=',HIST[call.replace('?','')])
                sys.exit(0)

        # Misc fix-ups
        if qth in ['PY','ZL']:
            qth='DX'

        if not dupe:
            self.nqsos2 += 1;

            try:
                idx1 = NAQP_SECS.index(qth)
                idx2 = self.BANDS.index(band)
                self.band_cnt[idx2] += 1
                self.sec_cnt[idx1,idx2] = 1
            except:
                print('\n$$$$$$$$$$$$$$$$$$$$$$')
                print(qth,' not found in list of NAQP sections',len(qth))
                print(rec)
                print('$$$$$$$$$$$$$$$$$$$$$$')
                if self.TRAP_ERRORS:
                    sys.exit(0)
    
            # Info for multi-qsos
            exch_in=name+' '+qth
            if call in self.EXCHANGES.keys():
                self.EXCHANGES[call].append(exch_in)
            else:
                self.EXCHANGES[call]=[exch_in]
                
            # Count no. of CWops guys worked
            self.count_cwops(call,HIST,rec)
                
#                              ----------info sent----------- ----------info rcvd----------- 
#QSO: freq  mo date       time call            ex1        ex2 call            ex1        ex2 t
#QSO: ***** ** yyyy-mm-dd nnnn **********      aaaaaaaaaa aaa **********      aaaaaaaaaa aaa n
#QSO: 14042 CW 1999-09-05 0000 N5KO            TREY       CA  N6TR          1 TREE       OR

        line='QSO: %5d %2s %10s %4s %-10s      %-10s %-3s %-10s      %-10s %-3s' % \
            (freq_khz,mode,date_off,time_off, \
             self.MY_CALL,self.MY_NAME,self.MY_STATE,
             call,name,qth)
        #print line

        # Check against history
        if call in keys:
            state=HIST[call]['state']
            if state=='':
                sec  =HIST[call]['sec']
                if sec in STATES+PROVINCES2:
                    state=sec
            name9=HIST[call]['name']
            #print call,qth,state
            if call not in self.checked and (qth!=state or name!=name9):
                self.checked.append(call)
                print('\n$$$$$$$$$$ Difference from history $$$$$$$$$$$')
                print(call,':  Current:',qth,name,' - History:',state,name9)
                self.list_all_qsos(call,qsos)
                print('hist=',HIST[call])
                print(' ')

        else:
            print('\n++++++++++++ Warning - no history for call:',call)
            self.list_all_qsos(call,qsos)
            self.list_similar_calls(call,qsos)

            #print 'dist=',similar('K5WA','N5WA')
            #sys.exit(0)

        return line
            
    # Summary & final tally
    def summary(self):

        mults1 = np.sum(self.sec_cnt,axis=0)
        mults = [int(i) for i in mults1]
        
        print('\nNo. QSOs        =',self.nqsos1)
        print('No. Uniques     =',self.nqsos2)
        print('No. Skipped     =',self.nskipped)
        print('\nBand\tQSOs\tMults')
        for i in range(len(self.BANDS)):
            print(self.BANDS[i],'\t',self.band_cnt[i],'\t',mults[i])
        print('\nTotals:\t',sum(self.band_cnt),'\t',sum(mults))
        print('Claimed score=',sum(mults)*self.nqsos2)

        print('\n# CWops Members =',self.num_cwops,' =',
              int( (100.*self.num_cwops)/self.nqsos1+0.5),'%')
        print('# QSOs Running  =',self.num_running,' =',
              int( (100.*self.num_running)/self.nqsos1+0.5),'%')
        print('# QSOs S&P      =',self.num_sandp,' =',
              int( (100.*self.num_sandp)/self.nqsos1+0.5),'%')

        
    # On-the-fly scoring - need to combine with SST
    def otf_scoring(self,qso):
        print("\nNAQP OTF SCORING: qso=",qso)
        self.nqsos+=1

        try:
            if 'CALL' in qso:
                call=qso['CALL']
                band = qso["BAND"]
                qth  = qso["QTH"].upper()
            else:
                call=qso['call']
                band = qso["band"]
                qth  = qso["qth"].upper()
        except:
            error_trap('NAQP->OTF SCORING - Unexpected error!')
            print('qso=',qso)
            return

        idx = self.BANDS.index(band)

        try:
            idx1 = NAQP_SECS.index(qth)
        except:
            if self.P.gui:
                self.P.gui.status_bar.setText('Unrecognized/invalid section!')
            error_trap('NAQP->OTF SCORING - Unrecognized/invalid section!')
            return
        self.sec_cnt[idx1,idx] = 1
        
        mults = np.sum( np.sum(self.sec_cnt,axis=0) )
        self.score=self.nqsos * mults
        print("NAQP OTF SCORING: score=",self.score,'\tnqsos=',self.nqsos,'\tnmults=',mults)

        self.txt='{:3d} QSOs  x {:3d} Mults = {:6,d} \t\t\t Last Worked: {:s}' \
            .format(self.nqsos,mults,self.score,call)
        if self.P.gui:
            self.P.gui.status_bar.setText(self.txt)

            
    # Function to check for new multipliers - need to combine with SST
    def new_multiplier(self,call,band):
        band=str(band)
        if band[-1]!='m':
            band+='m'
        print('NAQP->NEW MULTIPLIER: call=',call,'\tband=',band)

        new_mult=False
        try:
            if call in self.keys:
                #print 'hist=',HIST[call]
                #state=self.P.HIST[call]['state']
                state=self.P.MASTER[call]['state']
                #print('\tstate=',state)
                if state in NAQP_SECS:
                    idx1 = NAQP_SECS.index(state)
                    idx = self.BANDS.index(band)
                    new_mult = self.sec_cnt[idx1,idx] == 0
                    #print('\tidx1,idx,new=',idx1,idx,new_mult)
        except:
            #error_trap('NAQP->NEW MULTIPLIER: Ooops!')
            pass

        return new_mult
            
