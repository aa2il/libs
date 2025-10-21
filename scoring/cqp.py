###########################################################################################
#
# cqp.py - Rev 1.0
# Copyright (C) 2021-5 by Joseph B. Attili, joe DOT aa2il AT gmail DOT com
#
# Routines for scoring Commie-fornia QSO Party.
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
import numpy as np
from rig_io.ft_tables import CQP_MULTS,COUNTIES,CQP_COUNTRIES,CQP_STATES
from scoring import CONTEST_SCORING
from dx.spot_processing import Station, Spot, WWV, Comment, ChallengeData
from pprint import pprint
from fileio import parse_adif
from utilities import reverse_cut_numbers,Oh_Canada, error_trap
from tkinter import END
from collections import OrderedDict 

############################################################################################

# Scoring class for CQP - Inherits the base contest scoring class
class CQP_SCORING(CONTEST_SCORING):
 
    def __init__(self,P,TRAP_ERRORS=False):
        super().__init__(P,'CQP',mode='CW')
        print('CQP Scoring Init ... TRAP_ERRORS=',TRAP_ERRORS)
        #sys.exit(0)
        
        # Inits
        self.BANDS       = ['160m','80m','40m','20m','15m','10m']           
        self.sec_cnt     = np.zeros(len(CQP_MULTS),dtype=np.int32)
        self.dx_cnt      = 0
        self.calls       = []
        self.county_cnt  = np.zeros(len(COUNTIES['CA']),dtype=np.int32)
        self.band_cnt    = np.zeros(len(self.BANDS),dtype=np.int32)
        self.nq          = 0
        self.TRAP_ERRORS = TRAP_ERRORS
        self.init_otf_scoring()

        self.MY_CALL     = P.SETTINGS['MY_CALL']
        self.MY_NAME     = P.SETTINGS['MY_NAME']
        self.MY_SECTION  = P.SETTINGS['MY_SEC']
        self.MY_COUNTY   = P.SETTINGS['MY_COUNTY']
        self.min_time_gap  = 15  # Minutes

        # History file
        #self.history = os.path.expanduser( '~/Python/history/data/master.csv' )
                
        # Determine contest date/time - first Sat in Oct.
        now = datetime.datetime.utcnow()
        year=now.year
        #year=2021               # Testing

        day1=datetime.date(year,10,1).weekday()                     # Day of week of 1st of month 0=Monday, 6=Sunday
        sat2=1 + ((5-day1) % 7)                                     # Day no. for 1st Saturday = 1 since day1 is the 1st of the month
                                                                    #    plus no. days until 1st Saturday (day 5)
        start_time=16                                               # 1600 UTC
        self.date0=datetime.datetime(year,10,sat2,start_time)       # Need to add more code for other sessions next year
        self.date1 = self.date0 + datetime.timedelta(hours=30)      # Contest is 30-hrs long
        print('day1=',day1,'\tsat2=',sat2,'\tdate0=',self.date0)
        #sys.exit(0)

        # Manual override
        if False:
            self.date0 = datetime.datetime.strptime( "20201003 1600" , "%Y%m%d %H%M")  # Start of contest
            self.date1 = self.date0 + datetime.timedelta(hours=30)
        elif False:
            # Practice session the day b4
            self.date0 = datetime.datetime.strptime( "20220930 2330" , "%Y%m%d %H%M")  # Start of contest
            self.date1 = self.date0 + datetime.timedelta(hours=1)

        if False:
            print('now=',now)
            print('day1=',day1,'\tsat2=',sat2)
            print('date0=',self.date0)
            print('date1=',self.date1)
            #sys.exit(0)

        # Name of output file
        #MY_CALL2 = self.SETTINGS['MY_CALL'].replace('/','_')
        MY_CALL2 = self.MY_CALL.split('/')[0]
        self.output_file = MY_CALL2+'_CQP'+'_'+str(self.date0.year)+'.LOG'
        
            
    # Contest-dependent header stuff
    def output_header(self,fp):
        fp.write('LOCATION: %s\n' % self.MY_COUNTY)
        fp.write('ARRL-SECTION: %s\n' % self.MY_SECTION)

    # Scoring routine for CQP
    def qso_scoring(self,rec,dupe,qsos,HIST,MY_MODE,HIST2):
        #print('rec=',rec)
        if len(HIST2)>0 and False:
            print('We have a 2nd HIST file')
            print(HIST2)
            sys.exit(0)
        if len(HIST2)==0 and False:
            HIST2=HIST
            if self.TRAP_ERRORS and False:
                print('\n**** WARNING **** Dup hist files - check this!!! ****\n')
                sys.exit(0)
                
        keys=list(HIST.keys())
        keys2=list(HIST2.keys())
        #sys.exit(0)

        # Pull out relavent entries
        call = rec["call"].upper()
        if len(call)==3:
            self.special_calls.add(call)
        rx   = rec["srx_string"].strip().upper()
        if "station_callsign" in rec:
            my_call = rec["station_callsign"].strip().upper()
        else:
            my_call = self.MY_CALL
        tx   = rec["stx_string"].strip().upper()

        freq_khz = int( 1000*float(rec["freq"]) +0.5 )
        band = rec["band"]
        date_off = datetime.datetime.strptime( rec["qso_date_off"] , "%Y%m%d").strftime('%Y-%m-%d')
        time_off = datetime.datetime.strptime( rec["time_off"] , '%H%M%S').strftime('%H%M')
        
        a    = rx.split(',') 
        qth_in = a[1]

        b    = tx.split(',')
        num_out = int( reverse_cut_numbers( b[0] ) )
        qth_out = b[1]

        # Begin error checking process
        if '?' in rx+call:
            print('\n$$$$$$$$$$$$$ Questionable RX Entry $$$$$$$$$$$$$$')
            self.nq+=1
            print('Call   =',call)
            print('Serial In =',a[0],'\tSerial Out =',num_out)
            print('QTH    =',qth_in)
            print('Date   =',rec["qso_date_off"])
            print('Time   =',rec["time_off"])
            print('rec=',rec)
            self.list_all_qsos(call,qsos)
            if self.TRAP_ERRORS:
                sys.exit(0)
            else:
                qth_in = qth_in.replace('?','')
                a[0] = a[0].replace('?','')
                if 'qth' in rec:
                    rec['qth'] = rec['qth'].replace('?','')
                    
        if 'qth' in rec:
            if qth_in != rec['qth']:
                print('@@@@@@@@@@@@@ QTH Mismatch @@@@@@@@@@@@@')
                print('Call   =',call)
                print('QTH    =',qth_in,rec['qth'])
                print('rec=',rec)
                print('Date   =',rec["qso_date_off"])
                print('Time   =',rec["time_off"])
                self.list_all_qsos(call,qsos)
                if self.TRAP_ERRORS:
                    sys.exit(0)
                
        try:
            num_in = int( reverse_cut_numbers( a[0] ) )
        except:
            print('Cant find serial number!!!!')
            print('a0=',a[0])
            print('rec=',rec)
            print('Problem with serial:',a)
            if self.TRAP_ERRORS:
                sys.exit(0)
            else:
                num_in=0

        if num_in<=0:
            print('Bad serial number!!!!')
            print('num_in=',num_in,'\ta0=',a[0])
            print('rec=',rec)
            print('Problem with serial:',a)
            if self.TRAP_ERRORS:
                sys.exit(0)
                
        self.check_serial_out(num_out,rec,self.TRAP_ERRORS)
        
        if MY_MODE=='CW':
            mode='CW'
        else:
            print('Invalid mode',MY_MODE)
            sys.exit(1)

        dx_station = Station(call)
        country    = dx_station.country
        if False:
            print('rec=',rec)
            pprint(vars(dx_station))
            print('call     =',call)
            print('prefix   =',dx_station.prefix)
            print('exch out =',num_out,qth_out)
            print('exch in  =',num_in,qth_in)
            sys,exit(0)

        # Determine multipliers
        county_line=False
        if '/' in qth_in:
            # County line
            print('County line ...',qth_in)
            self.county_liners += 1
            qth_in2=qth_in.split('/')
            for qth1 in qth_in2:
                print(qth1)
                self.county_line_qsos += 1
                if qth1 in COUNTIES['CA']:
                    qth='CA'
                    idx1 = COUNTIES['CA'].index(qth1)
                    self.county_cnt[idx1] += 1
                    county_line=True
                else:
                    county_line=False
                    if self.TRAP_ERRORS:
                        print('\nI have no idea what Im doing here!')
                        print(rec)
                        sys.exit(0)
            
        elif qth_in in COUNTIES['CA']:
            qth='CA'
            idx1 = COUNTIES['CA'].index(qth_in)
            self.county_cnt[idx1] += 1
        elif qth_in in ['NB', 'NL', 'NS', 'PE','MAR'] and False:
            # Canada secs prior to 2023 - no longer used but keeping this
            # stuff around in case they change their minds!
            print('*** WARNING *** Changing QTH from',qth_in,'to MR')
            print('call     =',call)
            print('rec=',rec)
            qth_in='MR'
            qth='MR'
        else:
            qth=qth_in

        idx1 = self.BANDS.index(band)
        self.band_cnt[idx1] += 1
            
        if dupe:
            self.ndupes += 1;
            self.dupers.append(call)
            pass
        else:
            self.nqsos2 += 1;
            self.calls.append(call)
            
            try:
                if qth!='DX':
                    idx1 = CQP_MULTS.index(qth)
                    self.sec_cnt[idx1] += 1
                else:
                    self.dx_cnt += 1
            except:
                print('\n$$$$$$$$$$$$$$$$$$$$$$',self.nqsos2)
                print(qth,' not found in list of CQP sections')
                print(rec)
                if self.TRAP_ERRORS:
                    print('History=',call,HIST[call])
                    sys.exit(0)
                print('$$$$$$$$$$$$$$$$$$$$$$')
        
        # Error checking
        if country=='Canada':
            qth2,secs2=Oh_Canada(dx_station,CQP=True)
            if qth2!=qth_in and self.TRAP_ERRORS:
                print('rec     =',rec)
                print('call    =',call)
                print('Oh Canada: qth_in=',qth_in,'\tqth2=',qth2)
                sys.exit(0)
        
        if( (country not in CQP_COUNTRIES and qth_in!='DX') or \
            (country in CQP_COUNTRIES and qth_in not in CQP_STATES and not county_line) ):
            pprint(vars(dx_station))
            print('rec     =',rec)
            print('call    =',call)
            print('Country =',country)
            print('QTH in  =',qth_in,county_line)
            print('Received qth '+qth_in+' not recognized - srx=',rx)
            try:
                print('History=',HIST[call])
            except:
                print('Hmmm - cant show history for this call')
            if self.TRAP_ERRORS:
                sys.exit(0)

        # Compare to history
        call2  = dx_station.homecall
        if call2 in keys2 and call2 not in []:   # ['WB2RPW','WU6X','N6IE']:
            qth2=HIST2[call2]
            if qth_in!=qth2:
                print('\n$-$-$-$-$-$-$-$-$-$ Difference from history2 $-$-$-$-$-$-$-$-$-$-$')
                print(call,':  Current:',qth_in,' - History:',qth2)
                print('HIST2=',HIST2[call2])
                print('Date   =',rec["qso_date_off"])
                print('Time   =',rec["time_off"])
                self.list_all_qsos(call,qsos)
                print(' ')
                if self.TRAP_ERRORS:
                    sys.exit(0)
            
        elif call2 in keys:
            if qth=='CA':
                state=HIST[call2]['county']
            else:
                state=HIST[call2]['state']
            if qth_in!=state and qth_in!='DX':
                print('\n$$$$$$$$$$ Difference from history $$$$$$$$$$$')
                print(call,':  Current:',qth_in,' - History:',state)
                print('History=',call,HIST[call2])
                self.list_all_qsos(call,qsos)
                print(' ')

        elif qth_in!='DX':
            print('\n++++++++++++ Warning - no history for call:',call,call2)
            print('Date   =',rec["qso_date_off"])
            print('Time   =',rec["time_off"])
            self.list_all_qsos(call,qsos)
            #self.list_similar_calls(call,qsos)

            #print 'dist=',similar('K5WA','N5WA')
            #sys.exit(0)
        
        # Info for multi-qsos
        #exch_in=qth_in
        exch_in={'NR':num_in,'QTH':qth_in}
        if call in self.EXCHANGES.keys():
            self.EXCHANGES[call].append(exch_in)
        else:
            self.EXCHANGES[call]=[exch_in]
                        
        # Count no. of CWops guys worked
        self.count_cwops(call,HIST,rec)

        # Keep score vs time history
        self.compute_score(rec)
        
        # Generate cabrillo file line for this qso
#000000000111111111122222222223333333333444444444455555555556666666666777777777788
#123456789012345678901234567890123456789012345678901234567890123456789012345678901
#                              -----info sent------ -----info rcvd------
#QSO: freq  mo date       time call       nr   ex1  call       nr   ex1
#QSO: ***** ** yyyy-mm-dd nnnn ********** nnnn aaaa ********** nnnn aaaa 
#QSO: 28050 CW 2012-10-06 1600 K6AAA         1 SCLA W1AAA         1 ME 
#QSO: 28450 PH 2012-10-06 1601 K6AAA         2 SCLA K6ZZZ         2 AMAD 

        if False:
            # This will not split up qsos with county-line ops - seems to be accepted
            line='QSO: %5d %2s %10s %4s %-10s %4s %-4s %-10s %4s %-4s' % \
                (freq_khz,mode,date_off,time_off,
                 my_call,str(num_out),qth_out,
                 call,str(num_in),qth_in.replace('?',''))
        else:
            # This splits up qsos with county-line ops
            line=[]
            for qth_in2 in qth_in.split('/'):
                line.append(
                    'QSO: %5d %2s %10s %4s %-10s %4s %-4s %-10s %4s %-4s' % \
                    (freq_khz,mode,date_off,time_off,
                     my_call,str(num_out),qth_out,
                     call,str(num_in),qth_in2.replace('?','')) )

        return line

    # Routine to compute current score
    def compute_score(self,rec=None):

        mults=0
        for i in range(len(self.sec_cnt)):
            if self.sec_cnt[i]>0:
                mults += 1

        nqsos = self.nqsos2 + self.county_line_qsos - self.county_liners
        score = 3*min(mults,58)*nqsos

        self.gather_scores(rec,score)
        
        return score,mults

        
    
    # Summary & final tally
    def summary(self):

        print('\nStates & Provinces:')
        mults=0
        for i in range(len(self.sec_cnt)):
            if self.sec_cnt[i]>0:
                mults += 1
                if self.sec_cnt[i]<=2:
                    tag='+++++'
                else:
                    tag=''
            else:
                tag='*****'
            print(i,'\t',CQP_MULTS[i],'\t',int(self.sec_cnt[i]),'\t',tag)

        print('\nCA Counties:')
        for i in range(len(self.county_cnt)):
            if self.county_cnt[i]>0:
                tag=''
            else:
                tag='*****'
            print(i,'\t',COUNTIES['CA'][i],'\t',int(self.county_cnt[i]),'\t',tag)

        print('\nRaw QSOs by Band:')
        for i in range(len(self.band_cnt)):
            print(i,'\t',self.BANDS[i],'\t',int(self.band_cnt[i]) )

        uniques = np.unique( self.calls )
        uniques.sort()
        print('\nThere were',len(uniques),'unique calls:\n',uniques)
        print('\nDUPERS:',self.dupers)
        print('Special Calls:',self.special_calls)

        print('\nNo. raw QSOs (nqsos1)    =\t',self.nqsos1)
        print('No. unique QSOs (nqsos2) =\t',self.nqsos2)
        print('No. Dupes                =\t',self.ndupes)
        print('No. County Line ops      =\t',self.county_liners,'\tQSOs =',self.county_line_qsos)
        self.nqsos2 += self.county_line_qsos - self.county_liners
        print('Total QSO Count          =\t',self.nqsos2)
        print('Multipiers               =\t',mults,'\tCapped at 58')
        print('Claimed Score            =\t',3*min(mults,58)*self.nqsos2)
        print('No. flagged QSOS         =\t',self.nq)

        print('\n# CWops Members =',self.num_cwops,' =',
              int( (100.*self.num_cwops)/self.nqsos1+0.5),'%')
        print('# QSOs Running  =',self.num_running,' =',
              int( (100.*self.num_running)/self.nqsos1+0.5),'%')
        print('# QSOs S&P      =',self.num_sandp,' =',
              int( (100.*self.num_sandp)/self.nqsos1+0.5),'%')

        # They did this in 2020
        if False:
            print('\nThe SEQUOIA Challenge:')
            for ch in ['S','E','Q','U','O','I','A']:
                print(ch,':\t',end=' ')
                for w in ['K','N','W']:
                    call2=w+'6'+ch
                    if call2 in uniques:
                        print(call2,'\t',end=' ')
                    else:
                        print('\t',end=' ')
                print(' ')
            


    def read_hist2(self,fname):

        print('READ_HIST2 - fname=',fname)
        #HIST2=[]
        HIST2 = OrderedDict()
        if len(fname)>0:
            print('Well, we have a histroy file ...',fname)
            qsos = parse_adif(fname)
            print('# QSOs=',len(qsos))
            print('First QSO:',qsos[0])

            for qso in qsos:
                #print(qso)
                call=qso['call']
                dxcc=int( qso['dxcc'] )
                if dxcc in [1,110,291]:        # Canada, HI, USA, need AK also
                    state=qso['state']
                    if state=='CA':
                        try:
                            county=qso['cnty'].split(',')
                            a=county[1]
                            b=a.split(' ')
                            if len(b)==1:
                                qth=a[0:4]
                            elif b[0]=='EL':
                                qth=b[0]+b[1][0:2]
                            else:
                                if b[0][0:3] in ['LOS','SAN']:
                                    qth=b[0][0]+b[1][0:3]
                                else:
                                    qth=a
                                
                        except:
                            #qth='*******************'
                            qth=''
                    else:
                        qth=state
                        if qth in ['NB','NL','NS','PE']:
                            qth='MR'
                else:
                    qth='DX'

                #rec={'call':call,'qth':qth}
                #print(rec)
                #HIST2.append( rec )
                if call in HIST2.keys():
                    qth2=HIST2[call]
                    if qth!=qth2:
                        print('Houston, there is a turd in the punch bowl')
                        print(qth,qth2)
                else:
                    HIST2[call]=qth
                        
            print('HIST2:',len(HIST2))
            for call in HIST2.keys():
                print(call,'\t',HIST2[call])
            #sys.exit(0)

        return HIST2

    
    # On-the-fly scoring
    def otf_scoring(self,qso):
        print("\nCQP OTF SCORING: qso=",qso)
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
        
            if '/' in qth:
                qth=qth.split('/')[0]
            if qth in COUNTIES['CA']:
                qth='CA'
            if qth!='DX':
                idx1 = CQP_MULTS.index(qth)
            idx2 = self.BANDS.index(band)
            
        except:
            error_trap('CQP->OTF SCORING - Unexpected error!')
            if self.P.gui:
                self.P.gui.status_bar.setText('CQP->OTF SCORING - Unexpected error!')
            return
        
        self.band_cnt[idx2] += 1
        if qth!='DX':
            self.sec_cnt[idx1] = 1
        
        mults = np.sum(self.sec_cnt)
        self.score = 3*self.nqsos * mults
        print("CQP OTF SCORING: score=",self.score,self.nqsos,mults)

        self.txt='{:3d} QSOs  x {:3d} Mults = {:6,d} \t\t\t Last Worked: {:s}' \
            .format(self.nqsos,mults,self.score,call)
        if self.P.gui:
            self.P.gui.status_bar.setText(self.txt)
    

    # Put summary info in big text box
    def otf_summary(self):

        mults = np.sum(self.sec_cnt)
        nqsos = np.sum(self.band_cnt)
        score = 3*nqsos*mults

        missing,txt = self.missing_mults(CQP_MULTS)
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
            print('CQP->NEW MULTIPLIER: call=',call,'\tband=',band)
            #print('\tkeys=',self.keys)

        new_mult=False
        idx1=None
        state=None
        try:
            if call in self.keys:
                #print 'hist=',HIST[call]
                #state=self.P.HIST[call]['state']
                state=self.P.MASTER[call]['state']
                if state in CQP_MULTS:
                    idx1 = CQP_MULTS.index(state)
                    new_mult = self.sec_cnt[idx1] == 0
        except:
            pass

        if VERBOSITY:
            #print('\tCQP_MULTS=',CQP_MULTS)
            print('\tstate=',state,'\tidx1=',idx1,'new_mult=',new_mult)
            
        return new_mult

        

"""

# Routine to give QTH of a Canadian station
def oh_canada2_OLD(dx_station):

    Prefixes	Province/Territory
    VE1 VA1	Nova Scotia
    VE2 VA2	Quebec	
    VE3 VA3	Ontario	
    VE4 VA4	Manitoba	
    VE5 VA5	Saskatchewan	
    VE6 VA6	Alberta	
    VE7 VA7	British Columbia	
    VE8	Northwest Territories	
    VE9	New Brunswick	
    VE0*	International Waters
    VO1	Newfoundland
    VO2	Labrador
    VY1	Yukon	
    VY2	Prince Edward Island
    VY9**	Government of Canada
    VY0	Nunavut	
    CY0***	Sable Is.[16]	
    CY9***	St-Paul Is.[16]	

    For the CQP b4 2023:
    MR      Maritimes
    QC      Quebec
    ON      Ontario
    MB      Manitoba
    SK      Saskatchewan
    AB      Alberta
    BC      British Columbia
    NT

    # For Cali QSO Party prior to 2023:
    # MR = Maritime provinces plus Newfoundland and Labrador (NB, NL, NS, PE)

    qth=''
    #print('Oh Canada ... 1')
    #pprint(vars(dx_station))
    if dx_station.country=='Canada':
        print('OH CANADA2 - Dont do this anymoe!!!')
        sys.exit(0)
        if dx_station.prefix in ['VO2','VY2','VE9']:
            qth='MR'
        elif dx_station.prefix in ['VY1']:
            # YT --> NT for CQP
            qth='NT'
        else:
            num=int( dx_station.call_number )
            if num>=0 and num<len( CQP_VE_CALL_AREAS ):
                qth=CQP_VE_CALL_AREAS[num-1]
            else:
                print('**** ERROR *** CQP - Oh Canada2 - having trouble with',\
                      dx_station.call,dx_station.call_number,num)

    else:
        print('OH CANADA2 - I dont know what I am doing here')
        
    return qth
"""

