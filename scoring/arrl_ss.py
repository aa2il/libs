############################################################################################
#
# arrl_ss.py - Rev 1.0
# Copyright (C) 2021-5 by Joseph B. Attili, joe DOT aa2il AT gmail DOT com
#
# Routines for scoring ARRL CW Sweepstakes contest.
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
from rig_io.ft_tables import ARRL_SECS
from scoring import CONTEST_SCORING
from dx.spot_processing import Station
import numpy as np
from utilities import reverse_cut_numbers, error_trap
from tkinter import END

#######################################################################################
    
# Scoring class for ARRL CW Sweepstakes - Inherits the base contest scoring class
class ARRL_SS_SCORING(CONTEST_SCORING):
 
    def __init__(self,P,TRAP_ERRORS=False):
        super().__init__(P,'ARRL-SS-CW',mode='CW')
        
        self.BANDS = ['160m','80m','40m','20m','15m','10m']
        self.band_cnt = np.zeros(len(self.BANDS),dtype=np.int32)
        self.sec_cnt  = np.zeros(len(ARRL_SECS), dtype=np.int32)
        self.TRAP_ERRORS = TRAP_ERRORS
        self.nproblems=0
        self.nwarnings=0

        # Contest occurs on 1st full weekend of November
        now = datetime.datetime.utcnow()
        year=now.year
        #year=2022               # Testing
        
        day1=datetime.date(year,11,1).weekday()                        # Day of week of 1st of month 0=Monday, 6=Sunday
        sat2=1 + ((5-day1) % 7)                                        # Day no. for 1st Saturday = 1 since day1 is the 1st of the month
                                                                       # No. days until 1st Saturday (day 5) + 7 more days 
        self.date0=datetime.datetime(year,now.month,sat2,21)           # Contest starts at 2100 UTC on Saturday ...
        self.date1 = self.date0 + datetime.timedelta(hours=30)         # ... and ends at 0300 UTC on Sunday
        print('day1=',day1,'\tsat2=',sat2,'\tdate0=',self.date0)
        #sys.exit(0)

        if False:
            # Manual override
            self.date0 = datetime.datetime.strptime( "20201107 2100" , "%Y%m%d %H%M")  # Start of contest
            self.date1 = self.date0 + datetime.timedelta(hours=30)

        # Name of output file
        self.output_file = self.MY_CALL+'_CW_SS'+'_'+str(self.date0.year)+'.LOG'
            
    # Contest-dependent header stuff
    def output_header(self,fp):
        fp.write('LOCATION: %s\n' % self.MY_STATE)
        fp.write('ARRL-SECTION: %s\n' % self.MY_SECTION)
                    
    # Scoring routine for ARRL CW Sweepstakes
    def qso_scoring(self,rec,dupe,qsos,HIST,MY_MODE,HIST2):
        #print rec
        keys=list(HIST.keys())
        if len(keys)==0:
            print('*** WARNING *** No History !!!! ***')
            if self.TRAP_ERRORS:
                sys.exit(0)

        # Pull out relavent entries
        call = rec["call"]
        freq_khz = int( 1000*float(rec["freq"]) +0.5 )
        band = rec["band"]
        date_off = datetime.datetime.strptime( rec["qso_date_off"] , "%Y%m%d").strftime('%Y-%m-%d')
        time_off = datetime.datetime.strptime( rec["time_off"] , '%H%M%S').strftime('%H%M')

        if 'srx_string' in rec:

            # Things should be properly formatted by pyKeyer
            rexch  = rec["srx_string"]
            if '?' in rexch:
                print('\ncall=',call,'\trexech=',rexch)
                print('Uncertain field(s) - need to fix ADIF entry')
                if self.TRAP_ERRORS:
                    sys.exit(0)
                else:
                    rexch=rexch.replace('?','')
                    self.nproblems+=1
                        
            rexch=rexch.strip().upper().split(',')
            try:
                s=reverse_cut_numbers( rexch[0] )
                if s=='':
                    print('Invalid serial s=',s)
                    if self.TRAP_ERRORS:
                        sys.exit(0)
                    else:
                        s=0
                serial = int(s)
                    
                prec   = rexch[1]
                call2  = rexch[2]
                
                if rexch[3]=='':
                    print('Invalid check =',rexch[3])
                    if self.TRAP_ERRORS:
                        sys.exit(0)
                    else:
                        rexch[3]=0
                check  = int( rexch[3] )
                sec    = rexch[4]
                
            except Exception as e: 
                print('Problem unpacking rx exchange')
                print( str(e) )
                print('rexch=',rexch)
                print(rec)
                if self.TRAP_ERRORS:
                    sys.exit(0)

        else:
            print(" ")
            print("*** ERROR - Problem with record")
            print(rec)
            print(" ")
            if self.TRAP_ERRORS:
                sys.exit(0)

        # Construct sent data
        try:
            serial_out = int( reverse_cut_numbers( rec["stx"] ) )
        except:
            print('BAD Serial Out:',rec["stx"] )
            serial_out = -1
            if self.TRAP_ERRORS:
                print(rec)
                sys.exit(0)

        # Some simple error checking
        if not prec in ['Q','A','B','U','M','S']:
            print('\n*** ERROR - Bad PREC:',prec,'\tcall=',call)
            print(rec)
            if self.TRAP_ERRORS:
                sys,exit(0)

        if call!=call2:
            print('\n*** ERROR - Bad CALL:',call,'\tcall2=',call2)
            print(rec)
            if self.TRAP_ERRORS:
                sys,exit(0)
                        
        self.check_serial_out(serial_out,rec,self.TRAP_ERRORS)

        idx2 = self.BANDS.index(band)
        self.band_cnt[idx2] += 1
            
        if not dupe:
            self.nqsos2 += 1;

            try:
                idx1 = ARRL_SECS.index(sec)
                self.sec_cnt[idx1] += 1
            except Exception as e: 
                print('\n$$$$$$$$$$$$$$$$$$$$$$')
                print( str(e) )
                print(sec,' not found in list of ARRL sections',len(sec))
                print(rec)
                print('$$$$$$$$$$$$$$$$$$$$$$')
                if self.TRAP_ERRORS:
                    sys.exit(0)
    
            # Info for multi-qsos
            exch_in=str(serial)+' '+prec+' '+str(check)+' '+sec
            if call in self.EXCHANGES.keys():
                self.EXCHANGES[call].append(exch_in)
            else:
                self.EXCHANGES[call]=[exch_in]

            # Count no. of CWops guys worked
            self.count_cwops(call,HIST,rec)

            # Keep score vs time history
            self.compute_score(rec)
                
#                              --------info sent------- -------info rcvd--------
#QSO: freq  mo date       time call       nr   p ck sec call       nr   p ck sec
#QSO: ***** ** yyyy-mm-dd nnnn ********** nnnn a nn aaa ********** nnnn a nn aaa
#QSO: 21042 CW 1997-11-01 2102 N5KO          3 B 74 STX K9ZO          2 A 69 IL
#0000000001111111111222222222233333333334444444444555555555566666666667777777777
#1234567890123456789012345678901234567890123456789012345678901234567890123456789

        line='QSO: %5d CW %10s %4s %-10s %4d %1s %2s %-3s %-10s %4d %1s %2d %-3s' % \
            (freq_khz,date_off,time_off,self.MY_CALL,serial_out,\
             self.MY_PREC,self.MY_CHECK,self.MY_SECTION, \
             call,serial,prec,check,sec)

        # Check against history
        if call in keys:
            sec9=HIST[call]['sec']
            check9=HIST[call]['check']
            if sec!=sec9 or str(check)!=check9:
                print('\n$$$$$$$$$$ Difference from history $$$$$$$$$$$')
                #print(rec)
                #print(line)
                print(call,'\tCurrent:',sec,check,'\tHistory:',sec9,check9)
                #print(len(sec),len(check),len(sec9),len(check9))
                #print(HIST[call])
                self.nwarnings+=1
                #sys,exit(0)
                
        if '?' in line:
            print('Something is fishy here:')
            print(line)
            if self.TRAP_ERRORS:
                sys,exit(0)
        
        return line

    # Routine to compute current score
    def compute_score(self,rec=None):

        mults=0
        for i in range(len(ARRL_SECS)):
            if self.sec_cnt[i]>0:
                mults += 1

        score = 2*mults*self.nqsos2

        self.gather_scores(rec,score)
        
        return score,mults

            
    # Summary & final tally
    def summary(self):

        mults=0
        for i in range(len(ARRL_SECS)):
            print(i,'\t',ARRL_SECS[i],'\t',int( self.sec_cnt[i] ))
            if self.sec_cnt[i]>0:
                mults+=1

        print(' ')
        for i in range(len(ARRL_SECS)):
            if self.sec_cnt[i]==1:
                print('Only one: ',ARRL_SECS[i])

        if all(self.sec_cnt)>0:
            print('\n!!! CLEAN SWEEP !!!')
        else:
            print(' ')
            for i in range(len(ARRL_SECS)):
                if self.sec_cnt[i]==0:
                    print('Missing: ',ARRL_SECS[i])

        print('\nNo. QSOs        =',self.nqsos1)
        print('No. Uniques     =',self.nqsos2)
        print('No. Problems    =',self.nproblems)
        print('No. Warnings    =',self.nwarnings)
        print('Raw QSOs by Band:')
        for i in range(len(self.band_cnt)):
            print(i,'\t',self.BANDS[i],'\t',int(self.band_cnt[i]) )
        print('Band Count      =',self.band_cnt,'  =  ',int(sum(self.band_cnt)))
        print('mults=',mults)
        print('score=',2*self.nqsos2*mults)
    


    # On-the-fly scoring
    def otf_scoring(self,qso):
        print("\nSS OTF SCORING: qso=",qso)
        self.nqsos+=1        

        try:
            if 'CALL' in qso:
                call=qso['CALL']
                qth  = qso["QTH"].upper()
            else:
                call=qso['call']
                qth  = qso["qth"].upper()
        
            idx1 = ARRL_SECS.index(qth)
            self.sec_cnt[idx1] = 1
            
        except:
            error_trap('ARRL_SS->OTF SCORING - Unexpected error!')
            if self.P.gui:
                self.P.gui.status_bar.setText('ARRL_SS->OTF SCORING - Unexpected error!')
            return
        
        mults = np.sum(self.sec_cnt)
        self.score = 2*self.nqsos * mults
        print("ARRL_SS OTF SCORING: score=",self.score,self.nqsos,mults)

        self.txt='{:3d} QSOs  x {:3d} Mults = {:6,d} \t\t\t Last Worked: {:s}' \
            .format(self.nqsos,mults,self.score,call)
        if self.P.gui:
            self.P.gui.status_bar.setText(self.txt)
    

    # Put summary info in big text box
    def otf_summary(self):

        #txt = 'SS-> OTF SUMMARY: len(secs)='+str(len(ARRL_SECS))
        #self.P.gui.txt.insert(END,txt,('highlight'))

        mults = np.sum(self.sec_cnt)
        nqsos = np.sum(self.band_cnt)
        score = 3*nqsos*mults

        missing,txt = self.missing_mults(ARRL_SECS)
        self.P.gui.txt.insert(END,txt,('highlight'))
                    
        for i in range(len(self.BANDS)):
            txt = '{:s} \t {:3d}\n'.format(self.BANDS[i],self.band_cnt[i])
            self.P.gui.txt.insert(END, txt, ('highlight'))
        txt = '{:s} \t {:3d} x\t {:3d} = {:5d}\n'.format('Totals:',nqsos,mults,score)        
        self.P.gui.txt.insert(END, txt, ('highlight'))
        self.P.gui.txt.see(END)
        

    # Function to check for new multipliers - need to combine with NAQP (same code, different mult list)
    def new_multiplier(self,call,band,VERBOSITY=0):
        #VERBOSITY=1
        
        band=str(band)
        if band[-1]!='m':
            band+='m'
        if VERBOSITY:
            print('SS->NEW MULTIPLIER: call=',call,'\tband=',band)
            #print('\tkeys=',self.keys)

        new_mult=False
        idx1=None
        state=None
        try:
            if call in self.keys:
                #print 'hist=',HIST[call]
                #state=self.P.HIST[call]['state']
                state=self.P.MASTER[call]['state']
                if state in ARRL_SECS:
                    idx1 = ARRL_SECS.index(state)
                    new_mult = self.sec_cnt[idx1] == 0
        except:
            pass

        if VERBOSITY:
            #print('\tARRL_SECS=',ARRL_SECS,len(ARRL_SECS))
            print('\tstate=',state,'\tidx1=',idx1,'new_mult=',new_mult)
            
        return new_mult
