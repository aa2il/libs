############################################################################################
#
# iaru.py - Rev 1.0
# Copyright (C) 2021-5 by Joseph B. Attili, aa2il AT arrl DOT net
#
# Routines for scoring IARU HF contest.
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
import os
import datetime
from rig_io.ft_tables import SST_SECS
from scoring import CONTEST_SCORING
from dx.spot_processing import Station, Spot, WWV, Comment, ChallengeData
from pprint import pprint
from utilities import reverse_cut_numbers,error_trap
from tkinter import END
from collections import OrderedDict
import csv

############################################################################################

# Scoring class for IARU HF contest - Inherits the base contest scoring class
# Eventaully, all contests should use this model 
class IARU_HF_SCORING(CONTEST_SCORING):
 
    def __init__(self,P,TRAP_ERRORS=False):
        CONTEST_SCORING.__init__(self,P,'IARU-HF',mode='CW',TRAP_ERRORS=TRAP_ERRORS)
        print('IARU HF Scoring Init...')

        self.MY_ITU_ZONE = int( P.SETTINGS['MY_ITU_ZONE'] )

        self.BANDS = ['160m','80m','40m','20m','15m','10m']
        self.NQSOS = OrderedDict()
        self.POINTS = OrderedDict()
        zones = []
        for b in self.BANDS:
            zones.append((b,set([])))
            self.NQSOS[b]=0
            self.POINTS[b]=0
        self.ZONES = OrderedDict(zones)
        self.wrtc = set([])
        self.init_otf_scoring()

        # Determine contest time - Contest occurs on 2nd full weekend of July
        now = datetime.datetime.utcnow()
        year=now.year
        #year=2022                                                     # Override for testing
        day1=datetime.date(year,7,1).weekday()                     # Day of week of 1st of month 0=Monday, 6=Sunday
        sat2=1 + ((5-day1) % 7) + 7                                    # Day no. for 1st Saturday = 1 since day1 is the 1st of the month
                                                                       # No. days until 1st Saturday (day 5) + 7 more days 
        self.date0=datetime.datetime(year,7,sat2,12)       # Contest starts at 1200 UTC on Saturday ...
        self.date1 = self.date0 + datetime.timedelta(hours=24)         # ... and ends at 1200 UTC on Sunday
        print('day1=',day1,'\tsat2=',sat2,'\tdate0=',self.date0)
        #sys.exit(0)

        if False:
            # Manual override
            self.date0 = datetime.datetime.strptime( "20210710 1200" , "%Y%m%d %H%M")  # Start of contest
            self.date1 = self.date0 + datetime.timedelta(hours=24)
                
        # Name of output file
        self.output_file = self.MY_CALL+'_IARU_HF_CHAMPS_'+str(self.date0.year)+'.LOG'

        # Names of input files
        MY_CALL = P.SETTINGS['MY_CALL']
        self.history = os.path.expanduser('~/'+MY_CALL+'/master.csv')
        if year==now.year:
            self.fname = MY_CALL+'.adif'
        else:
            self.fname = MY_CALL+'_'+str(year)+'.adif'
        self.DIR_NAME = os.path.expanduser('~/'+MY_CALL+'/')
        
        # Create a list of IARU member societies
        societies=set([])
        fname7 = os.path.expanduser('~/Python/contest/iaru.txt')
        with open(fname7) as f:
            rows = csv.reader(f)
            for row in rows:
                #print('row=',row)
                
                # Skip comments
                if row[0][0]!='#':
                    a=row[0].split()
                    #print(a)
                    societies.add(a[1])
                    
        self.societies=list(societies)
        print('\nIARU Societies:',self.societies,'\n')
        #sys.exit(0)
            
    # Contest-dependent header stuff
    def output_header(self,fp):
        fp.write('LOCATION: %s\n' % self.MY_STATE)
        fp.write('ARRL-SECTION: %s\n' % self.MY_SECTION)
                    
    # Scoring routine for IARU HF
    def qso_scoring(self,rec,dupe,qsos,HIST,MY_MODE,HIST2):
        #print('rec=',rec)
        keys=list(HIST.keys())
        #print(keys)
        #sys.exit(0)

        # Pull out relavent entries
        call = rec["call"].upper()
        rx   = rec["srx_string"].strip().upper()
        a    = rx.split(',')
        rst_in = reverse_cut_numbers( a[0] )

        if '?' in a[0] or '?' in a[1]:
            print('\n???????? Need to correct ADIF file - ????????')
            print('rec=',rec)
            print('a=',a)
            if self.TRAP_ERRORS:
                self.list_all_qsos(call,qsos)
                sys.exit(0)
        
        if len(a[1])<=2 and a[1] not in self.societies+SST_SECS:
            num_in = reverse_cut_numbers( a[1] , 2)
            if not num_in.isnumeric() and self.TRAP_ERRORS:
                print('\n$$$$$$$$$$ Problem interpretting Zone/Society info $$$$$$$$$$$')
                print('rec=',rec)
                print('a=',a,'\tnum_in=',num_in)
                sys.exit(0)
        else:
            num_in = a[1]
        if num_in.isdigit():
            zone = int(num_in)
        else:
            zone = 0                    # Presumably, an HQ station
            
        tx   = rec["stx_string"].strip().upper()
        b    = tx.split(',')
        rst_out = reverse_cut_numbers( b[0] )
        num_out = reverse_cut_numbers( b[1] )
        
        freq_khz = int( 1000*float(rec["freq"]) +0.5 )
        band = rec["band"]
        date_off = datetime.datetime.strptime( rec["qso_date_off"] , "%Y%m%d").strftime('%Y-%m-%d')
        time_off = datetime.datetime.strptime( rec["time_off"] , '%H%M%S').strftime('%H%M')
        if MY_MODE=='CW':
            mode='CW'
        else:
            print('Invalid mode',MY_MODE)          # Need to add SSB if I ever do it!
            sys.exit(1)

        # Some simple checks
        if rst_in!='599':
            print('*** WARNING *** RST in =',rst_in)
            if self.TRAP_ERRORS:
                sys.exit(0)

        # Some error checking
        dx_station = Station(call)
        #if len(num_in)==0 or zone>75:
        if len(num_in)==0 or (num_in.isnumeric() and int(num_in)>75) or\
           (not num_in.isnumeric() and  num_in not in self.societies):
            print('\nHouston, we have problem - invalid zone:',num_in)
            print('rec=',rec)
            pprint(vars(dx_station))
            print('call     =',call)
            print('exch out =',rst_out,num_out)
            print('exch in  =',rst_in,num_in)
            if self.TRAP_ERRORS:
                self.list_all_qsos(call,qsos)
                sys,exit(0)
        if dx_station.ituz!=zone and False:
            print('\nWarning - ITU Zone mismatch')
            print('rec=',rec)
            print('call     =',call)
            print('Zone     =',dx_station.ituz,zone)
            print(' ')
            sys,exit(0)

        # Determine multipliers
        # Seems like there are always some problem children
        SPECIAL_CALLS=['WR1TC/MM','W2XX']                # For 2021: ['TO5GR']
        if not dupe:

            # Trying to reconcile diff between my calcs and raw score when submitted log - let's see if this is it
            # In 2023, there was a MM station that I think was the culprit
            if dx_station.mm:
                if not dx_station.continent and zone==63:
                    dx_station.continent='OC'
                else:
                    print("HELP - not sure what to do with this ????")
                    pprint(vars(dx_station))
                    print('call     =',call)
                    print('zone=',zone)
                    print('num_in=',num_in)
                    if self.TRAP_ERRORS and False:
                        sys.exit(0)

            if zone==self.MY_ITU_ZONE or zone==0:
                qso_points = 1
            elif dx_station.continent=='NA':    # or call in SPECIAL_CALLS:
                qso_points = 3
            elif dx_station.continent in ['SA','EU','OC','AF','AS']:
                qso_points = 5
            else:
                print('\n*** IARU HF: Not Sure what to do with this??!! ***')
                pprint(vars(dx_station))
                print('call     =',call)
                print('zone=',zone)
                if self.TRAP_ERRORS:
                    sys.exit(0)
                else:
                    qso_points = 1

            if dx_station.country:
                self.countries.add(dx_station.country)

            if len(call)==4 and call[:2]=='I4' and False:
                self.wrtc.add(call)
                    
            #print(call,zone,self.MY_ITU_ZONE,qso_points)
            self.ZONES[band].add(num_in)
            self.NQSOS[band]+=1
            self.nqsos2 += 1;
            self.total_points += qso_points
            self.POINTS[band] += qso_points

            # Info for multi-qsos
            exch_in=rst_in+' '+num_in
            if call in self.EXCHANGES.keys():
                self.EXCHANGES[call].append(exch_in)
            else:
                self.EXCHANGES[call]=[exch_in]
            
            # Count no. of CWops guys worked
            self.count_cwops(call,HIST,rec)
            
#                              --------info sent------- -------info rcvd--------
#QSO: freq  mo date       time call          rst exch   call          rst exch  
#QSO: ***** ** yyyy-mm-dd nnnn ************* nnn ****** ************* nnn ******
#QSO: 21303 PH 1999-07-10 1202 K5TR          59  07     NU1AW         59  IARU
#QSO: 14199 PH 1999-07-10 1202 K5TR          59  07     K1JN          59  08
#0000000001111111111222222222233333333334444444444555555555566666666667777777777
#1234567890123456789012345678901234567890123456789012345678901234567890123456789
        line='QSO: %5d %2s %10s %4s %-13s %-3s %-6s %-13s      %-3s %-6s' % \
            (freq_khz,mode,date_off,time_off,
             self.MY_CALL,rst_out,num_out,
             call,rst_in,num_in)

        # Check against history
        if call in keys:
            #print('hist=',HIST[call])
            ITUz=HIST[call]['ituz']
            if not ITUz in [str(zone),num_in]:
                print('\n$$$$$$$$$$ Difference from history $$$$$$$$$$$')
                print('rec=',rec)
                print(call,':  Current:',num_in,' - History:',ITUz)
                self.list_all_qsos(call,qsos)
                print(' ')
                if not ITUz.isdigit() and self.TRAP_ERRORS:
                    #sys.exit(0)
                    input('Pres <CR> to continue ...')

        else:
            print('\n++++++++++++ Warning - no history for call:',call)
            scp=self.SCP.match(call)
            if len(scp)>0 and call==scp[0]:
                txt='*** Known Contester - YIPPEE! ***'
            else:
                txt='*** Uh oh - call not a known contester :-( :-( :-('
            print('Calls matching',call,':',scp,'\t',txt)
            print('\nrec=',rec)
            self.list_all_qsos(call,qsos)
            self.list_similar_calls(call,qsos)
            if dx_station.ituz!=zone and zone>0 and not call in SPECIAL_CALLS:
                print('Zone     =',dx_station.ituz,zone)
                pprint(vars(dx_station))
                if self.TRAP_ERRORS:
                    sys.exit(0)
        
        return line

    # Summary & final tally
    def summary(self):

        dxcc = sorted( list( self.countries ) )
        print('\nCountries:\t',len(dxcc))
        for i in range(len(dxcc)):
            print('   ',dxcc[i])

        if False:
            wrtc = sorted( list( self.wrtc ) )
            print('\nWRTCs:\t',len(wrtc))
            for i in range(len(wrtc)):
                print('   ',wrtc[i])

        #print('\nZONES:',self.ZONES)
        nmults=0
        nzones=0
        nhq=0
        for b in self.BANDS:
            mults = list( self.ZONES[b] )
            mults.sort()
            print(' ')
            #print('\n',b,'Mults:',mults)
            hq    = []
            zones = []
            for mult in mults:
                if mult.isnumeric():
                    zones.append(mult)
                else:
                    hq.append(mult)
            print(b,'Zones   :',zones,len(zones))
            print(b,'HQ      :',hq,len(hq))
            print(b,'No. QSOs:',self.NQSOS[b],'\tZones:',len(zones),'\tHQ:',len(hq),'\tPoints:',self.POINTS[b])
            nzones += len(zones)
            nhq    += len(hq)
            nmults += len(zones)+len(hq)

        print('\nNo. QSOs        =',self.nqsos1)
        print('No. Uniques     =',self.nqsos2)
        print('QSO points      =',self.total_points)
        print('No. Zones       =',nzones)
        print('No. HQ          =',nhq)
        print('No. Multipliers =',nmults)
        print('Claimed Score   =',self.total_points*nmults)
        
        print('\nNo. CWops Members =',self.num_cwops,' =',
              int( (100.*self.num_cwops)/self.nqsos1+0.5),'%')
        print('No. QSOs Running  =',self.num_running,' =',
              int( (100.*self.num_running)/self.nqsos1+0.5),'%')
        print('No. QSOs S&P      =',self.num_sandp,' =',
              int( (100.*self.num_sandp)/self.nqsos1+0.5),'%')
        


    # On the fly scoring 
    def otf_scoring(self,qso):
        #print("\nIARU->OTF SCORING: qso=",qso)
        self.nqsos+=1

        try:
            if 'CALL' in qso:
                call = qso['CALL']
                band = qso["BAND"]
                mode = qso['MODE']
                rx   = qso["SRX_STRING"]
            else:
                call = qso['call']
                band = qso["band"]
                mode = qso['mode']
                rx   = qso["srx_string"]
            mode = self.group_modes(mode)
            rx   = rx.strip().upper().split(',')
        except:
            error_trap('FD->OTF SCORING - Unexpected error!')
            print('qso=',qso)
            return

        num_in = reverse_cut_numbers( rx[1] , 2)
        if num_in.isdigit():
            zone = int(num_in)
        else:
            zone = 0                    # Presumably, an HQ station

        dx_station = Station(call)
        #if dx_station.country:
        #    self.countries.add(dx_station.country)

        print('IARU->OTF SCORING: call=',call,'\tband=',band,'\tnum_in=',num_in,'\tmode=',mode,'\tzone=',zone)
        
        if zone==self.MY_ITU_ZONE or zone==0:
            qso_points = 1
        elif dx_station.continent=='NA':    # or call in SPECIAL_CALLS:
            qso_points = 3
        elif dx_station.continent in ['SA','EU','OC','AF','AS']:
            qso_points = 5
        else:
            qso_points = 0

        self.nqsos2 += 1;
        self.ZONES[band].add(num_in)
        self.NQSOS[band]+=1
        #self.POINTS[band] += qso_points
        self.total_points += qso_points

        nmults=0
        for b in self.BANDS:
            nmults += len( self.ZONES[b] )
        self.score=self.total_points*nmults
        
        self.txt='{:3d} QSOs  x {:3d} Mults = {:6,d} Points \t\t\t Last Worked: {:s}' \
            .format(self.nqsos,nmults,self.score,call)
        if self.P.gui:
            self.P.gui.status_bar.setText(self.txt)
    

    # Put summary info in big text box 
    def otf_summary(self):

        txt='Band\tQSOs\tMults'
        self.P.gui.txt.insert(END, txt, ('highlight'))
        
        nmults=0
        nqsos=0
        for b in self.BANDS:
            mults = len( self.ZONES[b] )
            nmults+=mults
            nqsos+=self.NQSOS[b]
            txt = '{:s} \t {:d} \t {:d}\n'.format(b,self.NQSOS[b],mults)
            self.P.gui.txt.insert(END, txt, ('highlight'))

        txt = '{:s} \t {:d} \t {:d}\n'.format('Totals:',nqsos,nmults)
        self.P.gui.txt.insert(END, txt, ('highlight'))
        self.P.gui.txt.see(END)

        
