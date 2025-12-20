############################################################################################
#
# rttyru.py - Rev 1.1
# Copyright (C) 2021-5 by Joseph B. Attili, joe DOT aa2il AT gmail DOT com
#
# Routines for scoring ARRL RTTY ROUNDUP, ARRL 10m, CQ 160m and FT8 ROUNDUP.
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
from dx.spot_processing import Station, Spot, WWV, Comment, ChallengeData
from utilities import reverse_cut_numbers,error_trap
from tkinter import END

############################################################################################
    
# Scoring class for ARRL RTTY RU - Inherits the base contest scoring class
class ARRL_RTTY_RU_SCORING(CONTEST_SCORING):
 
    def __init__(self,P,contest,TRAP_ERRORS=False):
        CONTEST_SCORING.__init__(self,P,contest)

        print('RTTY RU Scoring Init...')
        print('\tcontest=',contest)
        print('\tTrap Errors=',TRAP_ERRORS)

        self.rttyru = contest =='ARRL-RTTY'
        self.ft8ru  = contest =='FT8-RU'
        self.ten_m  = contest =='ARRL-10'
        self.cq160m = contest =='CQ-160'
        if not self.rttyru and not self.ft8ru and not self.ten_m and not self.cq160m:
            print('*** UNKNOWN CONTEST ***',contest)
            sys.exit(0)        
        elif self.ten_m:
            self.secs = TEN_METER_SECS
            self.BANDS = ['10m']
        elif self.cq160m:
            self.secs = STATES + PROVINCES2 
            self.BANDS = CONTEST_BANDS
        elif self.ft8ru:
            self.secs = FTRU_SECS
            self.BANDS = CONTEST_BANDS
        else:
            self.secs = RTTYRU_SECS
            self.BANDS = CONTEST_BANDS
        self.sec_cnt  = np.zeros(len(self.secs),dtype=int)
        self.band_cnt = np.zeros(len(CONTEST_BANDS),dtype=int)
        
        if self.rttyru:
            self.my_mode = 'MIXED'

        self.rtty_qsos = 0
        self.ft4_qsos  = 0
        self.ft8_qsos  = 0
        self.cw_qsos   = 0

        # History file
        self.history = os.path.expanduser( '~/Python/history/data/master.csv' )
        
        # Determine contest dates
        now = datetime.datetime.utcnow()
        if self.ft8ru:

            # Contest occurs on 1st full weekend of December
            day1=datetime.date(now.year,12,1).weekday()                    # Day of week of 1st of month 0=Monday, 6=Sunday
            sat2=1 + ((5-day1) % 7)                                        # Day no. for 1st Saturday = 1 since day1 is the 1st of the month
                                                                           # No. days until 1st Saturday (day 5) + 7 more days 
            self.date0=datetime.datetime(now.year,now.month,sat2,18)       # Contest starts at 1800 UTC on Saturday ...
            self.date1 = self.date0 + datetime.timedelta(hours=30)         # ... and ends at 0000 UTC on Sunday
            print('day1=',day1,'\tsat2=',sat2,'\tdate0=',self.date0)

        elif self.ten_m:
            
            # Contest occurs on 2nd full weekend of Dec
            year=now.year
            #year=2020
            day1=datetime.date(year,12,1).weekday()                        # Day of week of 1st of month 0=Monday, 6=Sunday
            sat2=1 + ((5-day1) % 7) + 7                                    # Day no. for 1st Saturday = 1 since day1 is the 1st of the month
                                                                           # No. days until 1st Saturday (day 5) + 7 more days 
            self.date0=datetime.datetime(year,12,sat2,0)                   # Contest starts at 0000 UTC on Saturday (Friday night local) ...
            #self.date0 = datetime.datetime.strptime( "20201212 0000" , "%Y%m%d %H%M")  # Override Start of contest
            self.date1 = self.date0 + datetime.timedelta(hours=48)         # ... and ends at 1200 UTC on Sunday
            print('day1=',day1,'\tsat2=',sat2,'\tdate0=',self.date0)
            
        elif self.cq160m:
            
            # Contest occurs on 4th full weekend of Jan
            year=now.year
            day1=datetime.date(year,1,1).weekday()                        # Day of week of 1st of month 0=Monday, 6=Sunday
            sat2=1 + ((5-day1) % 7) + 3*7                                  # Day no. for 1st Saturday = 1 since day1 is the 1st of the month
                                                                           # No. days until 1st Saturday (day 5) + 7 more days 
            self.date0=datetime.datetime(year,1,sat2,0)                   # Contest starts at 0000 UTC on Saturday (Friday night local) ...
            #self.date0 = datetime.datetime.strptime( "20201212 0000" , "%Y%m%d %H%M")  # Override Start of contest
            self.date1 = self.date0 + datetime.timedelta(hours=48)         # ... and ends at 1200 UTC on Sunday
            print('day1=',day1,'\tsat2=',sat2,'\tdate0=',self.date0)
            
        else:

            # Contest occurs on 1st full weekend of January except if Jan. 1
            day1=datetime.date(now.year,1,1).weekday()                     # Day of week of 1st of month 0=Monday, 6=Sunday
            sat2=1 + ((5-day1) % 7)                                        # Day no. for 1st Saturday = 1 since day1 is the 1st of the month
                                                                           # No. days until 1st Saturday (day 5) + 7 more days
            if sat2==1:
                sat2+=7                                                    # If New Years (as in 2022), its the following weekend
            self.date0=datetime.datetime(now.year,now.month,sat2,18)       # Contest starts at 1800 UTC on Saturday ...
            self.date1 = self.date0 + datetime.timedelta(hours=30)         # ... and ends at 0000 UTC on Sunday
            print('day1=',day1,'\tsat2=',sat2,'\tdate0=',self.date0)

        if False:
            # Manual override
            #self.date0 = datetime.datetime.strptime( "20181201 1800" , "%Y%m%d %H%M")  # Start of contest - FT RU
            self.date0 = datetime.datetime.strptime( "20201205 1800" , "%Y%m%d %H%M")  # Start of contest - FT RU
            self.date1 = self.date0 + datetime.timedelta(hours=30)

            self.date0 = datetime.datetime.strptime( "20190105 1800" , "%Y%m%d %H%M")  # Start of contest
            self.date1 = self.date0 + datetime.timedelta(hours=30)
            
        # Name of output file
        #self.output_file = self.MY_CALL+'_FTRU_'+str(self.date0.year)+'.LOG'
        self.output_file = self.MY_CALL+'_'+contest+'_'+str(self.date0.year)+'.LOG'

        self.init_otf_scoring()
        
        #sys.exit(0)

        
    # Contest-dependent header stuff
    def output_header(self,fp):
        fp.write('LOCATION: %s\n' % self.MY_STATE)
        fp.write('ARRL-SECTION: %s\n' % self.MY_SECTION)

    # Function to search ALL.TXT file
    def search_ALL_TXT(self,call):
        cmd='fgrep -i '+call+' ALL.TXT | fgrep '+self.MY_CALL
        print('\ncmd=',cmd)
        os.system(cmd)
        print(' ')

    # Convert RST to 5x9 format since some ops don't set contest mode correctly
    def convert_rst(self,rst):
        # WSJT RST mapping:  (emperically determined from ALL.TXT - only partially determined)
        # 18 --> 599
        # 13 16 --> 589
        # 9 10 11 --> 579
        # 0 1 3 4 5 --> 569
        # -2 ... -6   ---> 559
        # -8 ... -15  ---> 549
        # -16  ---> 539

        #print('CONVERT_RST:',rst)
        rst=int(rst)
        if rst>=18:
            return '599'
        elif rst>=13 and rst<=16:
            return '589'
        elif rst>=9 and rst<=11:
            return '579'
        elif rst>=0 and rst<=5:
            return '569'
        elif rst>=-6 and rst<=-2:
            return '559'
        elif rst>=-15 and rst<=-8:
            return '549'
        elif rst>=-16:
            return '539'
        else:
            print('CONVERT_RST: Dont know ow to map this value',rst)
            sys.exit(0)
        
    # Check validity of RST
    def check_rst(self,rst):
        if len(rst)!=3:
            return False
        elif rst[0]!='5' or  rst[2]!='9':
            return False
        else:
            return True

    # Scoring routine for ARRL RTTY Round Up
    def qso_scoring(self,rec,dupe,qsos,HIST,MY_MODE,HIST2):
        #print 'RU_SECS=',RU_SECS
        #sys.exit(0)
        #print(rec)

        keys=list(HIST.keys())

        # Pull out relavent entries
        call = rec["call"]
        freq_khz = int( 1000*float(rec["freq"]) + 0.0 )
        band = rec["band"]
        mode = rec["mode"]
        RST_OUT = rec["rst_sent"]
        RST_IN  = reverse_cut_numbers( rec['rst_rcvd'] )

        if 'country' in rec :
            country = rec["country"]
        else:
            #print('QSO SCORING: call=',call)
            dx_station = Station(call)
            country = dx_station.country
        #print(country)

        #print('HEY1')
        if country in ['USA','United States','Canada']:
            #print('HEY2')
            try:
                if 'state' in rec:
                    qth = rec["state"]
                else:
                    qth = rec["qth"]
            except Exception as e: 
                print(e)
                print('\n',call,"*** EXPECTING STATE/PROVINCE ***")
                if TRAP_ERRORS:
                    print(rec)
                    if self.ft8ru:
                        self.search_ALL_TXT(call)
                    sys.exit(0)
                else:
                    return
                
        elif 'state' in rec and len(rec["state"])>0:
            #print('HEY3')
            qth = rec["state"]
        elif self.ft8ru:
            #print('HEY4')
            try:
                qth = rec["srx"]
            except:
                print('\nNo STATE or SRX field for call',call,band,mode, \
                      ' - cant determine QTH.')
                print('rec=',rec)
                if TRAP_ERRORS:
                    if self.ft8ru:
                        self.search_ALL_TXT(call)
                    sys.exit(0)
                else:
                    return 
        elif 'qth' in rec :
            qth = rec["qth"]
        elif 'name' in rec :
            qth = rec["name"]
        elif 'srx' in rec :
            qth = rec["srx"]
        elif int(RST_IN)<111:
            print('\n',call,"*** EXPECTING 5xx RST ***")
            if TRAP_ERRORS:
                if self.ft8ru:
                    self.search_ALL_TXT(call)
                print(rec)
                sys.exit(0)
            else:
                return 
            
        else:
            print('\n',call,"*** CAN'T DETERMIINE QTH ***")
            if TRAP_ERRORS:
                if self.ft8ru:
                    self.search_ALL_TXT(call)
                print(rec)
                sys.exit(0)
            else:
                return 
        
        qth=qth.upper() 

        #if mode=='FT8' or mode=='FT4' or mode=='MFSK':
        if mode=='FT8':
            mode='DG'
            if not dupe:
                self.ft8_qsos += 1
        elif mode=='FT4' or mode=='MFSK':
            mode='DG'
            if not dupe:
                self.ft4_qsos += 1
        elif mode=='RTTY':
            mode='RY'
            if not dupe:
                self.rtty_qsos += 1
        elif self.ten_m or self.cq160m:
            if mode=='CW':
                if not dupe:
                    self.cw_qsos += 1
            else:
                print('RTTYRU SCORING: Unknown mode',mode,' - EXPCETING CW')
                sys.exit(0)
        else:
            print('RTTYRU SCORING: Unknown mode',mode)
            sys.exit(0)
            
        date_off = datetime.datetime.strptime( rec["qso_date_off"] , "%Y%m%d").strftime('%Y-%m-%d')
        time_off = datetime.datetime.strptime( rec["time_off"] , '%H%M%S').strftime('%H%M')

        self.countries.add(country)
        try:
            idx1 = self.secs.index(qth)
            self.sec_cnt[idx1] = 1
            dx=False
        except:
            if country=='United States' or country=='Canada' or (self.ten_m and country=='Mexico'):
                print('\n*** ERROR *** qth=',qth,' not found in list of Sections - call=',call,country)
                print('\nrec=',rec)
                if TRAP_ERRORS:
                    if self.ft8ru:
                        self.search_ALL_TXT(call)
                    sys.exit(0)
            else:
                dx=True
                try:
                    qth=reverse_cut_numbers( qth )
                    val=int(qth)
                except Exception as e:
                    print('\n',e)
                    print('Invalid serial for DX: qth=',qth,'\t',self.ft8ru)
                    print('call     =',call)
                    print('time off =',time_off)
                    print('rec=',rec)
                    if TRAP_ERRORS:
                        if self.ft8ru:
                            self.search_ALL_TXT(call)
                        sys.exit(0)
                    
        if not dupe:

            if self.ten_m:
                if mode=='PH':
                    qso_points=2
                elif mode=='CW':
                    qso_points=4
                else:
                    print('RTTYRU - Unknown mode',mode)
                    sys.exit(0)
            else:
                qso_points=1

            # Non-duplicate & points
            self.nqsos2 += 1;
            self.total_points += qso_points
            idx2 = self.BANDS.index(band)
            self.band_cnt[idx2] += 1

        #sys.exit(0)

        # Check RSTs
        if not self.check_rst(RST_OUT):
            print('\nInvalid RST_OUT field for call',call,band,mode,RST_OUT)
            print('rec=',rec)
            RST_OUT2=self.convert_rst(RST_OUT)
            print('Recorded RST OUT=',RST_OUT,'\tConverted RST OUT=',RST_OUT2)
            if not self.ft8ru and not self.ten_m and dx:
                RST_OUT='599'
            elif TRAP_ERRORS:
                RST_OUT=RST_OUT2
                if RST_OUT=='?':
                    sys.exit(0)
        
        if not self.check_rst(RST_IN):
            print('\nInvalid RST_IN field for call',call,'\tband=',band,'\tmode=',mode,'\tRTS IN=',RST_IN)
            #print('rec=',rec)
            RST_IN2=self.convert_rst(RST_IN)
            print('Recorded RST=',RST_IN,'\tConverted RST=',RST_IN2)
            if not self.ft8ru and not self.ten_m and dx:
                RST_IN='599'
            elif TRAP_ERRORS:
                RST_IN=RST_IN2
                if RST_IN=='?':
                    sys.exit(0)
                
        if False:
            if RST_IN=='':
                RST_IN = '599'
                print(call,'\t*** WARNING - Bad RST IN')
                if TRAP_ERRORS:
                    sys.exit(0)
            if dx and RST_IN==qth:
                RST_IN='599'
            if RST_IN!='599' and False:
                print('*** WARNING ***',call,'\tBad RST IN:',RST_IN)
                #sys.exit(0)

        # Info for multi-qsos
        #print('INFO:',call,dx)
        if self.ft8ru:
            if dx:
                exch_in={'TRUE RST':RST_IN,'NR':qth}
            else:
                exch_in={'TRUE RST':RST_IN,'QTH':qth}
        else:
            exch_in={'RST':RST_IN,'QTH':qth}
        if call in self.EXCHANGES.keys():
            self.EXCHANGES[call].append(exch_in)
        else:
            self.EXCHANGES[call]=[exch_in]
                        
        # Count no. of CWops guys worked
        self.count_cwops(call,HIST,rec)
                        
#                              --------info sent------- -------info rcvd--------
#QSO: freq  mo date       time call          rst exch   call          rst exch  
#QSO: ***** ** yyyy-mm-dd nnnn ************* nnn ****** ************* nnn ******
#QSO: 28079 RY 2003-01-04 1827 VE3IAY        599 ON     W5KFT         599 TX   
#QSO: 28079 RY 2003-01-04 1828 VE3IAY        599 ON     KP2D          599 035   

        #line='QSO: %5d %2s %10s %4s %-13s %3s %-6s %-13s %3s %-6s' % \
        #    (freq_khz,mode,date_off,time_off,MY_CALL,'599',MY_STATE,call,RST_IN,qth)
        line='QSO: %5d %2s %10s %4s %-12s %3s %-9s %-12s %3s %-9s' % \
            (freq_khz,mode,date_off,time_off, \
             self.MY_CALL,RST_OUT,self.MY_STATE,call,RST_IN,qth)

        # Check against history
        if call in keys:
            state = HIST[call]['state']
            if state=='':
                state = HIST[call]['sec']
            if len(state)==3 and state[1:] in ['TX','PA']:
                state='TX'
            #print call,qth,state
            if qth!=state and not dx and state!='':
                print('\n$$$$$$$$$$ Difference from history $$$$$$$$$$$')
                #print(rec)
                #print(line)
                print('CALL:',call,'\t Rx:',qth,'\t Hist:',state)
                print('time off =',time_off)
                #print(HIST[call])
                #sys,exit(0)
                
        elif False:
            print('\n*** Warning - no history for call:',call)
            self.list_all_qsos(call,qsos)
            self.list_similar_calls(call,qsos)
                        
        #print line
        #sys,exit(0)
        
        return line

    # Summary & final tally
    def summary(self):

        missing=[]
        nstates=0
        for i in range(len(self.secs)):
            if self.sec_cnt[i]==0:
                missing.append(self.secs[i])
            else:
                nstates+=1
        print('\nNo. States:',nstates)
        print('Missing: ',missing)

        dxcc = list( self.countries )
        dxcc.sort()
        print('\nCountries:',len(dxcc))
        for i in range(len(dxcc)):
            print('   ',dxcc[i])
            
        mults = len(dxcc) + int( np.sum(self.sec_cnt) )
        #print('\nBy Band:',self.band_cnt,sum(self.band_cnt))
        print('\nBand\tQSOs')
        for i in range(len(self.BANDS)):
            print(self.BANDS[i],'\t',self.band_cnt[i])
        print('\nTotals:\t',sum(self.band_cnt))
    
        print('\nNo. QSOs        =\t',self.nqsos1)
        print('No. Unique QSOs =\t',self.nqsos2)
        if self.rttyru:
            print('No. RTTY QSOs   =\t',self.rtty_qsos)
        if self.rttyru or self.ft8ru:
            print('No. FT8 QSOs    =\t',self.ft8_qsos)
            print('No. FT4 QSOs    =\t',self.ft4_qsos)
        if self.ten_m:
            print('No. CW QSOs     =\t',self.cw_qsos)
        print('Multipliers     =\t',mults)
        print('Claimed Score   =\t',self.total_points*mults)

        print('\n# CWops Members =',self.num_cwops,' =',
              int( (100.*self.num_cwops)/self.nqsos1+0.5),'%')

    #######################################################################################

        
    # On-the-fly scoring - need to combine with SST
    def otf_scoring(self,qso):
        print("\nRTTY RU OTF SCORING: qso=",qso)
        self.nqsos+=1

        try:
            if 'CALL' in qso:
                call=qso['CALL']
                #freq_khz = int( 1000*float(qso["FREQ"]) + 0.0 )
                band = qso["BAND"]
                mode = qso["MODE"]
                qth  = qso["QTH"].upper()
            else:
                call=qso['call']
                #freq_khz = int( 1000*float(qso["freq"]) + 0.0 )
                band = qso["band"]
                mode = qso["mode"]
                qth  = qso["qth"].upper()
        except:
            error_trap('RTTY RU->OTF SCORING - Unexpected error!')
            print('qso=',qso)
            return

        dx_station = Station(call)
        country = dx_station.country
        #itu = dx_station.ituz
        #self.zones.add(itu)

        #idx = self.BANDS.index(band)

        if country in ['United States','Canada','Alaska','Hawaii'] or (self.ten_m and country=='Mexico'):
            try:
                idx1 = self.secs.index(qth)
            except:
                if self.P.gui:
                    self.P.gui.status_bar.setText('Unrecognized/invalid section!')
                error_trap('RTTY RU->OTF SCORING - Unrecognized/invalid section!')
                return
            self.sec_cnt[idx1] = 1
        else:
            self.countries.add(country)

        if self.ten_m:
            if mode=='PH':
                qso_points=2
            elif mode=='CW':
                qso_points=4
        else:
            qso_points=1
        self.total_points += qso_points
            
        mults = np.sum(self.sec_cnt) + len(self.countries) + len(self.zones)
        self.score=self.total_points * mults
        print("RTTY RU OTF SCORING: score=",self.score,'\tnqsos=',self.nqsos,'\tnmults=',mults)

        self.txt='{:3d} QSOs  x {:3d} Mults = {:6,d} \t\t\t Last Worked: {:s}' \
            .format(self.nqsos,mults,self.score,call)
        if self.P.gui:
            self.P.gui.status_bar.setText(self.txt)

            
    # Function to check for new multipliers - need to combine with SST (same code)
    def new_multiplier(self,call,band):
        band=str(band)
        if band[-1]!='m':
            band+='m'
        print('RTTY RU->NEW MULTIPLIER: call=',call,'\tband=',band)

        new_mult=False
        try:
            if call in self.keys:
                #print 'hist=',HIST[call]
                #state=self.P.HIST[call]['state']
                state=self.P.MASTER[call]['state']
                #print('\tstate=',state)
                if state in self.secs:
                    idx1 = self.secs.index(state)
                    #idx = self.BANDS.index(band)
                    new_mult = self.sec_cnt[idx1] == 0
                    #print('\tidx1,idx,new=',idx1,idx,new_mult)
                    
            if not new_mult:
                dx_station = Station(call)
                country = dx_station.country
                #itu = dx_station.ituz
                new_mult = country not in ['United States','Canada','Alaska','Hawaii'] and \
                    (self.ten_m and country!='Mexico')  and (country not in self.countries)
                # or itu not in self.zones)
                    
        except:
            #error_trap('RTTY RU->NEW MULTIPLIER: Ooops!')
            pass

        return new_mult
            


    # Put summary info in big text box
    def otf_summary(self):

        mults = np.sum(self.sec_cnt) + len(list(self.countries)) # + len(self.zones)
        nqsos = np.sum(self.band_cnt)
        score = 4*nqsos*mults

        txt = '\nNum Secs:'+str(np.sum(self.sec_cnt))+'\n'
        self.P.gui.txt.insert(END,txt,('highlight'))
                    
        txt = 'Countries:'+str(self.countries)+'\n'
        self.P.gui.txt.insert(END,txt,('highlight'))
                    
        #txt = 'Zones:'+str(self.zones)+'\n'
        #self.P.gui.txt.insert(END,txt,('highlight'))
                    
        #missing,txt = self.missing_mults(CQP_MULTS)
        #self.P.gui.txt.insert(END,txt,('highlight'))
                    
        for i in range(len(self.BANDS)):
            txt = '{:s} \t {:3d}\n'.format(self.BANDS[i],self.band_cnt[i])
            self.P.gui.txt.insert(END, txt, ('highlight'))
                                
        txt = '{:s} \t {:3d} x\t {:3d} = {:5d}\n'.format('Totals:',nqsos,mults,score)        
        self.P.gui.txt.insert(END, txt, ('highlight'))
        self.P.gui.txt.see(END)

        
