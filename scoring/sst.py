############################################################################################
#
# sst.py - Rev 1.0
# Copyright (C) 2021-5 by Joseph B. Attili, joe DOT aa2il AT gmail DOT com
#
# Routines for scoring K1USN Slow Speed Mini Tests (SSTs).
# Also for NS and NCJ Sprints.
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
from utilities import error_trap
from tkinter import END

############################################################################################
    
UTC = datetime.UTC

############################################################################################
    
# Scoring class for slow-speed mini tests - Inherits the base contest scoring class
class SST_SCORING(CONTEST_SCORING):
 
    def __init__(self,P,contest,TRAP_ERRORS=False):
        super().__init__(P,contest,mode='CW')

        # Inits
        self.BANDS = ['MW','160m','80m','40m','20m','15m','10m']         # Need MW for practice mode
        self.band_cnt = np.zeros(len(self.BANDS),dtype=np.int32)
        self.sec_cnt = np.zeros((len(SST_SECS),len(self.BANDS)),dtype=np.int32)
        self.TRAP_ERRORS = TRAP_ERRORS
        self.init_otf_scoring()

        # Determine contest time - assumes this is dones within a few hours of the contest
        # Working on relaxing this restriction because I'm lazy sometimes!
        now = datetime.datetime.utcnow()
        weekday = now.weekday()
        print('now=',now,'\tweekday=',weekday,'\tcontest=',contest)
        if contest=='SPRINT':
            pass
        elif weekday in [1,2,3]:
            # If we finally getting around to running this on Tuesday, Weds or Thurs, roll back date to Monday
            now = now - datetime.timedelta(hours=24*weekday)
        elif weekday in [5,6]:
            # If we finally getting around to running this on Saturday or Sunday, roll back date to Friday
            now = now - datetime.timedelta(hours=24*(weekday-4))

        weekday = now.weekday()
        today = now.strftime('%A')
        if contest=='SPRINT':
            start_hour= 2
            start_min = 30
            duration  = 0.5
        elif today == 'Friday':
            start_hour= 20
            start_min = 0
            duration  = 1
        else:
            start_hour= 0
            start_min = 0
            duration  = 1            
        self.date0=datetime.datetime(now.year,now.month,now.day,start_hour,start_min)
        self.date1 = self.date0 + datetime.timedelta(hours=duration+1./60.)

        # Playing with dates
        if False:
            print('weekday=',weekday)
            print(now)
            print(now.day,now.weekday())
            print(today)
            print('Start:',self.date0)
            print('End:',self.date1)
            sys.exit(0)

        # Name of output file
        self.output_file = self.MY_CALL+'.LOG'
            
    # Contest-dependent header stuff
    def output_header(self,fp):
        fp.write('LOCATION: %s\n' % self.MY_STATE)
        fp.write('ARRL-SECTION: %s\n' % self.MY_SECTION)
                    
    # Scoring routine for Slow Speed Mini Tests
    def qso_scoring(self,rec,dupe,qsos,HIST,MY_MODE,HIST2):
        #print 'rec=',rec
        keys=list(HIST.keys())

        # Pull out relavent entries
        call = rec["call"].upper()
        if 'qth' in rec:
            qth  = rec["qth"].upper()
        else:
            qth=''
            print('No QTH for',call)
            print(rec)
            return
            sys.exit(0)
        if qth in ['BOND','CHAM','MADN'] and False:
            qth='IL'
            
        name = rec["name"].upper()
        freq_khz = int( 1000*float(rec["freq"]) +0.5 )

        band = rec["band"]
        idx = self.BANDS.index(band)
        self.band_cnt[idx] += 1
        
        date_off = datetime.datetime.strptime( rec["qso_date_off"] , "%Y%m%d").strftime('%Y-%m-%d')
        time_off = datetime.datetime.strptime( rec["time_off"] , '%H%M%S').strftime('%H%M')
        if MY_MODE=='CW':
            mode='CW'
        else:
            print('Invalid mode',MY_MODE)
            sys.exit(1)

        dx_station = Station(call)
        #print(dx_station)
        country    = dx_station.country
        qso_points = 1
        if country!='United States' and country!='Canada':
            self.countries.add(country)

        try:
            idx1 = SST_SECS.index(qth)
        except:
            print('\n*************** WHOOOOOOOPS !!!!!!!!!!!!!!!!!!!!')
            print('\nrec=',rec)
            print('\n',qth,'not in list of of SST Sections - call=',call)
            idx1=None
            if self.TRAP_ERRORS:
                print('Giving up!\n')
                sys.exit(0)
        if idx1!=None:
            self.sec_cnt[idx1,idx] = 1
        
        self.total_points_all += qso_points
        if not dupe:
            self.nqsos2 += 1;
            self.total_points += qso_points
        else:
            print('??????????????? Dupe?',call)
        #print call,self.nqsos2

        # Sometimes, I'll put a "?" to indicate that I need to review
        if '?' in call+name+qth:
            print('\n??? Check this one again: ???')
            print('call=',call,'\t\tname=',name,'\t\tqth=',qth,'\ttime=',time_off)
            if self.TRAP_ERRORS:
                sys.exit(0)

        # Check against history
        if call in keys:
            #print 'hist=',HIST[call]
            state=HIST[call]['state']
            name9=HIST[call]['name']
            #print call,qth,state
            if qth!=state or name!=name9:
                print('\n$$$$$$$$$$ Difference from history $$$$$$$$$$$')
                print(call,':  Current:',qth,name,' - History:',state,name9)
                self.list_all_qsos(call,qsos)
                print(' ')

        else:
            print('\n++++++++++++ Warning - no history for call:',call)
            self.list_all_qsos(call,qsos)
            self.list_similar_calls(call,qsos)

        # Info for multi-qsos
        exch_in=name+' '+qth
        if call in self.EXCHANGES.keys():
            self.EXCHANGES[call].append(exch_in)
        else:
            self.EXCHANGES[call]=[exch_in]
                        
        # Count no. of CWops guys worked
        self.count_cwops(call,HIST,rec)
                
        line='QSO: %5d %2s %10s %4s %-10s      %-10s %-3s %-10s      %-10s %-3s' % \
            (freq_khz,mode,date_off,time_off,
             self.MY_CALL,self.MY_NAME,self.MY_STATE,
             call,name,qth)
        
        return line
                        
    # Summary & final tally
    def summary(self):

        dxcc = list( self.countries )
        dxcc.sort()
        print('Countries:')
        for i in range(len(dxcc)):
            print('   ',dxcc[i])
            
        print('States/Provs:')
        sec_cnts=np.sum(self.sec_cnt,axis=1)>0
        for i in range(len(SST_SECS)):
            if sec_cnts[i]>0:
                print(' ',SST_SECS[i],end='')
        print('')
                
        mults1 = np.sum(self.sec_cnt,axis=0)
        mults = [int(i) for i in mults1]
        
        print('No. QSOs         =',self.nqsos2,\
              '\t(',self.nqsos1,')')
        print('\nBand\tQSOs\tMults')        
        for i in range(len(self.BANDS)):
            print(self.BANDS[i],'\t',self.band_cnt[i],'\t',mults[i],'\t',end='')
            for j in range(len(SST_SECS)):
                if self.sec_cnt[j,i]>0:
                    print(' ',SST_SECS[j],end='')
            print('')
                
        print('Totals:\t',self.total_points,'\t',sum(mults),'\n')
        
        print('QSO Points       =',self.total_points,\
              '\t(',self.total_points_all,')')
        print('Claimed score    =',self.total_points*sum(mults),\
              '\t(',self.total_points_all*sum(mults),')')

        print('\n# CWops Members =',self.num_cwops,' =',
              int( (100.*self.num_cwops)/self.nqsos1+0.5),'%')
        print('# QSOs Running  =',self.num_running,' =',
              int( (100.*self.num_running)/self.nqsos1+0.5),'%')
        print('# QSOs S&P      =',self.num_sandp,' =',
              int( (100.*self.num_sandp)/self.nqsos1+0.5),'%')
    
        
    # On-the-fly scoring
    def otf_scoring(self,qso):
        print("\nSST OTF SCORING: qso=",qso)
        self.nqsos+=1

        try:
            if 'CALL' in qso:
                call = qso['CALL']
                band = qso["BAND"]
                qth  = qso["QTH"].upper()
            else:
                call = qso['call']
                band = qso["band"]
                qth  = qso["qth"].upper()
        except:
            error_trap('SST->OTF SCORING - Unexpected error!')
            print('qso=',qso)
            return

        try:
            idx = self.BANDS.index(band)
            idx1 = SST_SECS.index(qth)
        except:
            if self.P.gui:
                self.P.gui.status_bar.setText('Unrecognized/invalid band or section!')
            error_trap('SST->OTF SCORING - Unrecognized/invalid band or section!')
            return
        self.band_cnt[idx] += 1
        self.sec_cnt[idx1,idx] = 1
        
        mults = np.sum( np.sum(self.sec_cnt,axis=0) )
        self.score=self.nqsos * mults
        print("SST OTF SCORING: score=",self.score,self.nqsos,mults)

        self.txt='{:3d} QSOs  x {:3d} Mults = {:6,d} \t\t\t Last Worked: {:s}' \
            .format(self.nqsos,mults,self.score,call)
        if self.P.gui:
            self.P.gui.status_bar.setText(self.txt)

    # Put summary info in big text box
    def otf_summary(self):

        mults1 = np.sum(self.sec_cnt,axis=0)
        mults = [int(i) for i in mults1]
        
        for i in range(1,len(self.BANDS)):
            #print(self.BANDS[i],'\t',self.band_cnt[i],'\t',mults[i])
            txt = '{:s} \t {:3d} \t {:3d}\n'.format(self.BANDS[i],self.band_cnt[i],mults[i])
            self.P.gui.txt.insert(END, txt, ('highlight'))
        txt = '{:s} \t {:3d} x\t {:3d} = {:5d}\n'.format('Totals:',np.sum(self.band_cnt),np.sum(mults),self.score)        
        self.P.gui.txt.insert(END, txt, ('highlight'))
        #self.P.gui.txt.insert(END, self.txt+'\n', ('highlight'))
        self.P.gui.txt.see(END)
            
        
    # Function to check for new multipliers - need to combine with NAQP (same code)
    def new_multiplier(self,call,band):
        band=str(band)
        if band[-1]!='m':
            band+='m'
        print('SST->NEW MULTIPLIER: call=',call,'\tband=',band)

        new_mult=False
        try:
            if call in self.keys:
                #print 'hist=',HIST[call]
                #state=self.P.HIST[call]['state']
                state=self.P.MASTER[call]['state']
                print('\tstate=',state,'\t Valid State=',state in SST_SECS)
                if state in SST_SECS:
                    idx1 = SST_SECS.index(state)
                    idx = self.BANDS.index(band)
                    new_mult = self.sec_cnt[idx1,idx] == 0
                    print('\tidx1,idx=',idx1,idx,
                          '\tcnt=',self.sec_cnt[idx1,idx],
                          '\tnew mult=',,new_mult)
        except:
            pass

        return new_mult

        
