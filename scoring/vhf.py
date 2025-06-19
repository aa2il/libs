############################################################################################
#
# vhf.py - Rev 1.0
# Copyright (C) 2021-5 by Joseph B. Attili, aa2il AT arrl DOT net
#
# Routines for scoring ARRL & CQ VHF contests.
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
from rig_io.ft_tables import *
from scoring import CONTEST_SCORING
from dx.spot_processing import Station, Spot, WWV, Comment, ChallengeData
from pyhamtools.locator import calculate_distance
from latlon2maiden import distance_maidenhead
from utilities import reverse_cut_numbers,error_trap
from tkinter import END

############################################################################################
    
# Scoring class for ARRL & CQ VHF contest - Inherits the base contest scoring class
class VHF_SCORING(CONTEST_SCORING):

    def __init__(self,P,SPONSER=None,TRAP_ERRORS=False):

        self.SPONSER=SPONSER

        self.BANDS = ['6m','2m','1.25m','70cm','33cm','23cm']
        self.sec_cnt = np.zeros(len(self.BANDS),dtype=int)
        
        # Determine contest based on sponser and month
        now = datetime.datetime.utcnow()
        month = now.strftime('%b').upper()
        print('month=',month)

        # Init base class
        dm=0
        if SPONSER==None:
            if 'ARRL' in P.CONTEST_ID:
                SPONSER='ARRL'
            else:
                print('VHF SCORING: Cant figure out sponser - giving up')
                print('VHF SCORING: CONTEST_ID=',P.CONTEST_ID)
                sys.exit(0)

        if SPONSER=='ARRL':
            contest_name=SPONSER+'-VHF-'+month
            if month=='JUL':
                month='JUN'
                dm=1
        elif SPONSER=='CQ':
            contest_name=SPONSER+'-VHF'
        elif SPONSER=='CSVHF':
            contest_name='SPRING-SPRINT'
        elif SPONSER=='SVHFS':
            contest_name='50MHZ-FALL-SPRINT'
        elif SPONSER=='NAMSS':
            contest_name='NA-METEOR-SCATTER-SPRINT'
            if month=='SEP':
                month='AUG'
                dm=1
        else:
            print('\nVHF SCORING: *** ERROR - Invalid sponser ***\n')
            print('SPONSER=',SPONSER)
            sys.exit(0)
        CONTEST_SCORING.__init__(self,P,contest_name,mode='MIXED',TRAP_ERRORS=TRAP_ERRORS)

        self.NQSOS = OrderedDict()
        grids = []
        for b in self.BANDS:
            grids.append((b,set([])))
            self.NQSOS[b]=0
        self.grids = OrderedDict(grids)
        self.nqsos=0
        self.category_band='VHF-3-BAND'

        self.MODES=['CW','DG','PH']
        self.Nmode = OrderedDict()
        for m in self.MODES:
            self.Nmode[m]=0

        # ARRL contest occurs on 2nd full weekend of June and Sept. For Jan, either 3rd or 4th
        # CQ contest occurs on 3rd full weekend in July ?
        day1=datetime.date(now.year,now.month-dm,1).weekday()             # Day of week of 1st of month 0=Monday, 6=Sunday
        sat2=1 + ((5-day1) % 7) + 7                                    # Day no. for 2nd Saturday = 1 since day1 is the 1st of the month
                                                                       #    no. days until 1st Saturday (day 5) + 7 more days 
        if month=='JAN':
            sat2+=7                                                    # 3rd Saturday
            start=19                                                   # Jan starts at 1900 UTC on Saturday ...
            hrs=33                                                     # ARRl contest is for 33 hours
        elif SPONSER=='CQ' and month=='JUL':
            # CQ WW VHF
            sat2+=7                                                    # 3rd Saturday
            start=18                                                   # CQ WW starts at 1800 UTC on Saturday ...
            hrs=27                                                     # CQ contest is for 27 hours

            self.DIR_NAME = os.path.expanduser('~/Python/pyKeyer/CQ_VHF')
            self.fname = 'CQ_VHF.adif'
            
        elif SPONSER=='CSVHF':
            # Central State VHF Soc Spring Sprints - not sure what their scheme is so just hardwire for noe
            sat2=13
            start=23
            hrs=4
        elif SPONSER=='SVHFS':
            # SE VHF Soc 50 MHz Fall Sprint - not sure what their scheme is so just hardwire for noe
            sat2=13
            start=23
            hrs=4
        elif SPONSER=='NAMSS':
            # NA Meteor Scatter Sprint - not sure what their scheme is so just hardwire for noe
            sat2=12
            start=15
            hrs=48
        else:
            start=18                                                   # June & Sept start at 1800 UTC on Saturday ...
            hrs=33                                                     # ARRl contest is for 33 hours
        self.date0=datetime.datetime(now.year,now.month-dm,sat2,start) 
        self.date1 = self.date0 + datetime.timedelta(hours=hrs)    
        print('day1=',day1,'\tsat2=',sat2,'\tdate0=',self.date0)
        #sys.exit(0)

        # Manual override
        if False:
            self.date0 = datetime.datetime.strptime( "20210612 1800" , "%Y%m%d %H%M")  # Start of contest
            self.date0 = datetime.datetime.strptime( "20210911 1800" , "%Y%m%d %H%M")  # Start of contest
            self.date1 = date0 + datetime.timedelta(hours=33)

        # Playing with dates
        if False:
            print('now=',now,now.month-dm,month)
            print(SPONSER)
            print('day1=',day1,datetime.date(now.year,now.month-dm,1))
            print(self.date0)
            print(self.date1)
            sys.exit(0)
            
        # Name of output file
        self.output_file = self.MY_CALL+'_'+SPONSER+'_'+month+'_VHF_'+str(self.date0.year)+'.LOG'

        MY_CALL = P.SETTINGS['MY_CALL']
        self.history = os.path.expanduser('~/'+MY_CALL+'/master.csv')
        
    # Contest-dependent header stuff
    def output_header(self,fp):
        fp.write('LOCATION: %s\n' % self.MY_SEC)
        fp.write('ARRL-SECTION: %s\n' % self.MY_SEC)
        fp.write('GRID-LOCATOR: %s\n' % self.MY_GRID)
                    
    # Scoring routine for ARRL VHF contest for a single qso
    def qso_scoring(self,rec,dupe,qsos,HIST,MY_MODE,HIST2):
        keys=list(HIST.keys())

        if False:
            print('\nrec=',rec)
            #print('\nqsos=',qsos)
            #print('\nHIST=',HIST)
            print('TRAP_ERRORS =',self.TRAP_ERRORS)
            sys,exit(0)

        # Pull out relavent entries
        call = rec["call"]
        if '?' in call:
            print('Whooops - unknown CALL!',call)
            sys.exit(0)            
        
        band = rec["band"]
        if band=='6m':
            freq_mhz=50
        elif band=='2m':
            freq_mhz=144
        elif band=='1.25m':
            freq_mhz=222
        elif band=='70cm':
            freq_mhz=432
        elif band=='33cm':
            freq_mhz=902
        elif band=='23cm':
            freq_mhz=1290
        else:
            print('Whooops - unknown Band!',call,band)
            sys.exit(0)

        if 'gridsquare' in rec:
            grid = rec["gridsquare"].upper()
        elif 'srx_string' in rec:
            grid = rec["srx_string"].upper()
        else:
            print('\nUnable to determine grid',rec)
            if self.TRAP_ERRORS:
                sys.exit(0)

        if ',' in grid:
            a=grid.split(',')
            grid=a[0]
            print(call,a,grid)

        # Check for valid band and grid 
        valid = len(grid)==4 and grid[0:2].isalpha() and grid[2:4].isdigit()
        valid2 = band in self.BANDS
        if not valid2:
            print('Skipping QSO from',band,'band')
            print('valid=',valid,valid2)
            print(self.BANDS)
            if self.TRAP_ERRORS:
                sys.exit(0)
            else:
                return
        elif not valid:
            print('\nVHF SCORING: Not a valid grid: call=',call,'\tgrid=',grid,'\tband=',band)
            if self.TRAP_ERRORS:
                sys.exit(0)
        else:
            # Add to list of grids for each band
            self.grids[band].add(grid)
        
        #print('call=',call)
        
        # Check mode vs freq
        freq=float(rec['freq'])
        mode=rec['mode']
        if mode=='SSB':
            mode='USB'
        if band=='6m':
            valid3 = (freq<50.11 and mode=='CW') or (freq<50.2 and freq>50.11 and mode=='USB') or (freq>50.3 and mode=='FT8')
        elif band=='2m':
            valid3 = (freq<144.5 and mode in ['SSB','USB','FT8']) or (freq>145. and mode=='FM')
        elif band=='1.25m':
            valid3 = mode=='FM'
        elif band=='70cm':
            valid3 = (freq<435 and mode=='USB') or (freq>445. and mode=='FM') # or (freq>144.3 and mode=='FT8')
        elif band=='23cm':
            valid3 = mode in ['FM','USB']
        else:
            valid3=False

        if not valid3:
            print('Skipping QSO from',band,'band - \tfreq=',freq,'\tmode=',mode)
            print('valid3=',valid3)
            print('freq=',freq)
            print('mode=',mode)
            if self.TRAP_ERRORS:
                sys.exit(0)
            else:
                return
            
        dx_station = Station(call)
        date_off = datetime.datetime.strptime( rec["qso_date_off"] , "%Y%m%d").strftime('%Y-%m-%d')
        time_off = datetime.datetime.strptime( rec["time_off"] , '%H%M%S').strftime('%H%M')

        if self.SPONSER=='NAMSS' and rec["mode"] not in ['MSK144']:
            return
        elif rec["mode"] in ['FT8','FT4','MSK144']:
            mode='DG'
        elif rec["mode"]=='CW':
            mode='CW'
        elif rec["mode"] in ['FM','USB','SSB']:
            mode='PH'
        else:
            print('\n******** VHF SCORING: Unknown mode:',rec["mode"])
            print('\nrec=',rec)
            if self.TRAP_ERRORS:
                print(' ')
                sys.exit(0)

        self.nqsos+=1
        if not dupe:
            idx2 = self.BANDS.index(band)
            self.sec_cnt[idx2] += 1

            if self.SPONSER=='NAMSS':
                dx_km1 = calculate_distance(grid,self.MY_GRID)
                dx_km  = distance_maidenhead(self.MY_GRID,grid,False)
                print('------------ call=',call,'\tgrid=',grid,'\tdx=',dx_km1,dx_km)
                if dx_km<500 or dx_km>2400:
                    dx_km=1
                else:
                    dx_km=int( dx_km + 0.5 )
                if band=='2m':
                    qso_points = 2*dx_km
                else:
                    qso_points = dx_km
                print('------------ pts=',qso_points)
            elif self.SPONSER=='CQ' and band=='2m':
                qso_points=2
            elif band=='33cm' or band=='23cm':
                qso_points=3
            elif band=='70cm' or band=='1.25m':
                qso_points=2
            else:
                qso_points=1
            
            self.nqsos2 += 1;
            self.total_points += qso_points

            self.NQSOS[band] += 1
            self.Nmode[mode] += 1

#                              --------info sent------- -------info rcvd--------
#QSO: freq  mo date       time call              grid   call              grid 
#QSO: ***** ** yyyy-mm-dd nnnn ***************** ****** ***************** ******
#QSO:   144 PH 2003-06-14 2027 NJ2L              FN12fr VE3FHU            FN25
#0000000001111111111222222222233333333334444444444555555555566666666667777777777
#1234567890123456789012345678901234567890123456789012345678901234567890123456789

        line='QSO: %5d %2s %10s %4s %-17s %-6s %-17s %-6s' % \
            (freq_mhz,mode,date_off,time_off, \
             self.MY_CALL,self.MY_GRID[:4],call,grid)

        # Check against history
        # Assume WSJT decode was correct and only show cw/phone qsos
        if call in keys:
            grid2=HIST[call]['grid']
            if grid!=grid2 and rec["mode"]!='FT8':
                print('\n$$$$$$$$$$ Difference from history $$$$$$$$$$$')
                print(call,':  Current:',grid,' - History:',grid2)
                self.list_all_qsos(call,qsos)
                print(' ')

        else:
            if rec["mode"]!='FT8':
                print('\n++++++++++++ Warning - no history for call:',call)
                #self.list_all_qsos(call,qsos)
        
        #print(line)
        return line



    # Routine to check for dupes
    def check_dupes(self,rec,qsos,i,istart):

        # Count no. of raw qsos
        self.nqsos1+=1

        # Pull out info
        call = rec["call"]
        band = rec["band"]
        mode = rec["mode"]
        if mode in ['FT8','FT4']:
            grid  = rec["gridsquare"]
        else:
            grid  = rec["qth"]
       
        # Check for dupes
        duplicate=False
        rapid=False
        for j in range(istart,i):
            rec2  = qsos[j]
            call2 = rec2["call"]
            band2 = rec2["band"]
            mode2 = rec2["mode"]
            if mode2 in ['FT8','FT4']:
                grid2 = rec2["gridsquare"]
            else:
                grid2 = rec2["qth"]
                
            dupe  = call==call2 and band==band2 and grid==grid2

            if dupe:
                if i-j<=2:
                    print("\n*** WARNING - RAPID Dupe",call,band,' ***')
                    rapid = True
                else:
                    print("\n*** WARNING - Dupe",call,band,' ***')
                print(j,rec2)
                print(i,rec)
                print(" ")
                duplicate = True

        return (duplicate,rapid)

    

    # Routine to sift through station we had multiple contacts with to identify any discrepancies
    def check_multis(self,qsos):

        print('There were multiple qsos with the following stations:')
        qsos2=qsos.copy()
        qsos2.sort(key=lambda x: x['call'])
        calls=[]
        for rec in qsos2:
            calls.append(rec['call'])
        #print(calls)
        uniques = list(set(calls))
        uniques.sort()
        #print(uniques)

        for call in uniques:
            #print(call,calls.count(call))
            if calls.count(call)>1:
                for rec in qsos:
                    if rec['call']==call:
                        mode = rec["mode"]
                        band = rec["band"]
                        if 'qth' in rec:
                            qth  = rec["qth"].upper()
                        else:
                            qth  = rec["gridsquare"].upper()
                        print(call,'\t',band,'\t',mode,'\t',qth)
                print(' ')
                        

    # Summary & final tally
    def summary(self):
        
        print('GRIDS:',self.grids)
        if self.SPONSER=='NAMSS':
            mults=1
        else:
            mults=0
            for b in self.BANDS:
                grids = list( self.grids[b] )
                grids.sort()
                print('\n',b,'Grids:',grids)
                print(' No. QSOs,Mults:',self.NQSOS[b],len(grids))
                mults+=len(grids)

        print('\nBy Band:\tQSOs\tMults')
        for b in self.BANDS:
            idx2 = self.BANDS.index(b)
            grids = list( self.grids[b] )
            print('\t',b,':\t',self.sec_cnt[idx2],'\t',len(grids))
        print('\nBy Mode:')
        for m in self.MODES:
            print('\t',m,':\t',self.Nmode[m])
        print('\nNo. QSOs      =',self.nqsos)
        print('No. Uniques   =',self.nqsos2)
        print('QSO points    =',self.total_points)
        print('Multipliers   =',mults)
        print('Claimed Score =',self.total_points*mults)
    


    # Function to list all qsos with a particular call
    def list_all_qsos(self,call2,qsos):
        print('All QSOs with ',call2,':')
        same=True
        qth_old = None
        for rec in qsos:
            call = rec["call"].upper()
            if call==call2:
                print(rec)
                if 'qth' in rec:
                    qth  = rec["qth"].upper()
                else:
                    qth  = rec["gridsquare"].upper()
                band = rec["band"]
                print('call=',call,'\tqth=',qth,'\tband=',band)

                if qth_old:
                    same = same and (qth==qth_old)
                qth_old = qth

        if not same:
            print('\n&*&*&*&*&*&*&*& QTH MISMATCH *&*&*&*&*&*&*&&*&\n')
            print(call,'/R' in call2)
            if '/R' in call2:
                print('??? Move over ROVER ???\n')
            elif self.TRAP_ERRORS:
                sys.exit(0)

        
    # On-the-fly scoring
    def otf_scoring(self,qso):
        #print("\nVHF OTF SCORING: qso=",qso)

        try:
            if 'CALL' in qso:
                call=qso['CALL']
                band = qso["BAND"]
                mode = qso["MODE"]
            else:
                call=qso['call']
                band = qso["band"]
                mode = qso["mode"]
        except:
            error_trap('VHF->OTF SCORING - Unexpected error!')
            print('qso=',qso)
            sys.exit(0)


        if self.SPONSER=='CQ' and band=='2m':
            qso_points=2
        elif band=='33cm' or band=='23cm':
            qso_points=3
        elif band=='70cm' or band=='1.25m':
            qso_points=2
        else:
            qso_points=1

        mults=1
        self.nqsos+=1
        self.total_points += qso_points
        self.score=self.total_points*mults
        print("VHF->SCORING: score=",self.score,self.nqsos)

        self.txt='{:3d} QSOs  x {:3d} Mults = {:6,d} \t\t\t Last Worked: {:s}' \
            .format(self.nqsos,mults,self.score,call)
        if self.P.gui:
            self.P.gui.status_bar.setText(self.txt)

            
    # Put summary info in big text box
    def otf_summary(self):

        #print('GRIDS:',self.grids)
        txt = 'GRIDS: '+' \t '.join(sorted( self.grids ))+'\n'
        self.P.gui.txt.insert(END, txt, ('highlight'))
        
        mults=0
        for b in self.BANDS:
            grids = list( self.grids[b] )
            mults+=len(grids)
            txt = '{:s} \t {:d}\n'.format(b,len(grids))
            self.P.gui.txt.insert(END, txt, ('highlight'))

        txt = '{:s} \t {:d} QSOs x {:d} Grids = {:,d}\n'.\
            format('Totals:',self.nqsos,mults,self.score)
        self.P.gui.txt.insert(END, txt, ('highlight'))
        self.P.gui.txt.see(END)
