################################################################################
#
# WSJT Helper - Rev 1.0
# Copyright (C) 2021-4 by Joseph B. Attili, aa2il AT arrl DOT net
#
# Objects for deciphering the ALL.TXT file produced by WSJTX
#
################################################################################
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
################################################################################

from time import sleep
from datetime import datetime,date,time  
import pytz
import sys
import os

################################################################################

#123456789 123456789 123456789 123456789 123456789 123456789 123456789 123456789
#DX de VK3FFB-#:  28228.0  ZL3TEN       CW 5 dB 12 WPM BEACON          0301Z
#      123456789 12345678  123456789012 123456789 123456789 123456789 
#DX de AA2IL-#:    3574.0  K0APC        FT8 -8 dB                      0335Z

# These are still used in wsmap.py
WSJT_LOGFILE  = os.path.expanduser('~/.local/share/WSJT-X/ALL.TXT')
WSJT_LOGFILE2 = os.path.expanduser('~/.local/share/WSJT-X - SDR/ALL.TXT')
WSJT_LOGFILE3 = os.path.expanduser('~/.local/share/WSJT-X - SDR1/ALL.TXT')
WSJT_LOGFILE4 = os.path.expanduser('~/.local/share/WSJT-X - SDR2/ALL.TXT')
WSJT_LOGFILE5 = os.path.expanduser('~/.local/share/WSJT-X - SDR3/ALL.TXT')
WSJT_LOGFILE6 = os.path.expanduser('~/.local/share/WSJT-X - CONTEST/ALL.TXT')
WSJT_LOGFILE7 = os.path.expanduser('~/.local/share/WSJT-X - CONTEST2/ALL.TXT')

#WSJT_LOGFILE34 = os.path.expanduser('~/.local/share/WSJT-X - SDR14/ALL.TXT')
#WSJT_LOGFILE44 = os.path.expanduser('~/.local/share/WSJT-X - SDR24/ALL.TXT')
#WSJT_LOGFILE54 = os.path.expanduser('~/.local/share/WSJT-X - SDR34/ALL.TXT')

def freq2band(frq_KHz):

    if frq_KHz:
        frq = .001*frq_KHz
    else:
        frq=0
        
    if frq<3:
        band=160
    elif frq<5:
        band=80
    elif frq<6:
        band=60
    elif frq<9:
        band=40
    elif frq<12:
        band=30
    elif frq<16:
        band=20
    elif frq<20:
        band=17
    elif frq<23:
        band=15
    elif frq<27:
        band=12
    elif frq<40:
        band=10
    else:
        band=6

    return str(band)+'m'



class wsjt_helper:
    def __init__(self,fnames,MAX_AGE_DAYS):
        self.nsleep=0
        self.now = datetime.utcnow().replace(tzinfo=pytz.utc)
        self.age=1e20
        self.line=''
        self.date2 = None
        self.time2 = None
        self.frq = None
        self.new_frq = None
        self.mode = None
        self.new_date_time = None
        self.old_date_time = None

        if type(fnames) is str:
            fnames = [ fnames ]

        self.fps=[]
        all_lines=[]
        for i in range(len(fnames)):
            fname = fnames[i]
            print('\nWSJT_HELPER: Reading',fname,' ...')

            if not os.path.isfile(fname):
                fp = open(fname,'w+')
                fp.close()
            fp = open(fname,'r')

            self.fps.append(fp)
            self.lines = fp.readlines()
            istart=self.find_recent_spots(MAX_AGE_DAYS*60.*24.)
            all_lines = all_lines + self.lines[istart:]
            print(len(self.lines),len(all_lines))
        self.lines = all_lines
            
    def age_secs(self):
        print('date=',self.date2)
        print('time=',self.time,len(self.time))
        date_time = self.date2 + " " + self.time
        #print 'date_time=',date_time
        
        if len(self.date2)==10:
            fmt1 = "%Y-%m-%d"
        elif len(self.date2)==6:
            fmt1 = "%y%m%d"
        else:
            print('AGE_SECS: Unknown date format',date_time)
            fmt1 = "%Y-%m-%d"
            sys.exit(0)

        if len(self.time)==5:
            fmt2 = "%H:%M"
        elif len(self.time)==6:
            fmt2 = "%H%M%S"
        elif len(self.time)==4:
            fmt2 = "%H%M"
        else:
            print('AGE_SECS: Unknown time format',date_time)
            fmt2 = "%H:%M"
            sys.exit(0)

        date_time = datetime.strptime( date_time, fmt1+' '+fmt2).replace(tzinfo=pytz.utc)
        age = (self.now - date_time).total_seconds() # In seconds
        #print self.date2,self.time,self.now,'     - age=',age/3600.

        return age

    
    def age_secs2(self,verbosity=0):

        if verbosity>=2:
            print('AGE_SEC2: date=',self.date2,'\t\ttime=',self.time2)

        if self.time2!=None and self.date2!=None:
            self.date_time = datetime.combine(self.date2, self.time2).replace(tzinfo=pytz.utc)
            age = (self.now - self.date_time).total_seconds() # In seconds
        else:
            print('AGE_SECS2: Rut-row',self.date2,self.time2)
            age=None

        if verbosity>=2:
            #print self.date,self.time
            print('mod data_time=',self.date_time)
            print('now=',self.now,'     - age=',age/3600.)

        #sys.exit(0)
        return age

    
    # Convert spot to format used by cluster network
    def convert_spot(self,spot):
        #print len(spot)
        if len(spot)==0:
            line=''
        else:
            #print 'CONVERT_SPOT:',spot
            #print spot['time'],spot['time'].strftime("%H%M")
            line = 'DX de %-9s %8.1f  %-12s %-30s %4sZ' % \
                   ('AA2IL'+'-#:',spot['freq'],spot['call2'],
                    spot['mode']+' '+str(spot['snr'])+' dB '+str(spot['df'])+' Hz',
                    spot['time'].strftime("%H%M") )
        return line

    # Read all the spots in the file
    def read_all_spots(self,MAX_AGE_DAYS=1e6):

        #istart=self.find_recent_spots(MAX_AGE_DAYS*60.*24.)
        istart=0
        
        print('Reading spot list...',len(self.lines),MAX_AGE_DAYS,istart)
        print(istart,self.lines[istart])

        spot_list=[]
        nlines = len(self.lines)
        for i in range(istart,nlines):
            if i%100000 ==0:
                print(i,nlines)

            spot=self.get_spot2(self.lines[i],0)
            #print self.age,MAX_AGE_DAYS*24*3600.,MAX_AGE_DAYS
            if spot and self.age<MAX_AGE_DAYS*24*3600.:
                spot_list.append(spot)

        print('Total of',len(spot_list),' spots read')

        return spot_list

            
    # Get next spot
    def get_spot(self,verbosity=0):

        spot={}
        line=self.fps[0].readline()
        if line:
            self.nsleep=0
            self.line=line
        
            line = line.strip().split()
            if verbosity>=2:
                print(line)
            while len(line)<8:
                line.append('')

            # Determine line type
            #print line,len(line)
            n=len(line[0])
            call1=line[5]
            call2=line[6]
            msg=''
            if len(call2)==2:
                call2=line[7]
                if len(line)>8:
                    msg = line[8]
            else:
                if len(line)>7:
                    msg = line[7]
                
            if n==6 or n==4:
                # Time,SNR,dT,df,Mode_Flag,Call1,Call2,Msg
                if verbosity>=1:
                    print(call1,'called by',call2)

                self.time = line[0]
                snr = int(line[1])
                df  = int(line[3])
                #t   = line[0][0:4]
                frq=self.frq + 0.001*float(df)
                mode=self.mode
                #spot = 'DX de %-9s %8.1f  %-12s %-30s %4sZ' % \
                #       ('AA2IL'+'-#:',frq,call2,mode+' '+str(snr)+' dB',t)
                spot = {'call2':call2, 'freq':frq, 'df':df, 'mode':mode, 'snr':snr,
                        'time':self.time, 'date':self.date2, 'msg':msg}

            elif n==10:
                # Date,Time,frq,frq_units,Mode
                self.date2 = line[0]
                self.time = line[1]
                self.frq  = float(line[2])*1000.
                self.mode = line[4]
                if verbosity>=1:
                    print('Band/Mode change to',line[2],line[3],line[4])
            
            elif n==13:
                # Date_Time,Transmitting,frq,frq_units,mode,Call1,Call2,Msg
                self.date2 = line[0][0:6]
                self.time = line[0][7:]
                if verbosity>=1:
                    print(call1,'called by',call2,' - My TX')
            else:
                print(line)
                print('GET_SPOT: Unknown line format')
                sys.exit(0)
            
            self.age = self.age_secs()
            
        else:
            
            self.nsleep+=1
            self.age = 0
            if self.nsleep==2:
                print('\nSnoozing ...\n')
            sleep(1) 

        return spot


    
    # Get next spot
    def get_spot2(self,line,verbosity=0):

        verbosity=0

        spot={}
        if line==None:
            line = self.fps[0].readline()

        if line:
            line=line.replace('\x00','')   # Sometimes, the ALL.TXT file gets hosed
            self.nsleep=0
            self.line=line
        
            line = line.strip().split()
            if verbosity>=2:
                print(' ')
                print(line,len(line))
            while len(line)<8:
                line.append('')

            # Determine line type
            n=len(line[0])
            nfields=len(line)
            if line[2]=='Rx' or line[2]=='Tx':
                # NEW format: the kitchen sink - much simpler as of V2.0.1
                #190227_024500     7.074 Rx FT8     -5  0.1 2316 FR5ZE K5TH EM00
                d = line[0][0:6]
                year  = 2000+int( d[0:2] )
                month = int( d[2:4] )
                day   = int( d[4:6] )
                self.date2 = date( year,month,day)

                t = line[0][7:]
                hour = int( t[0:2] )
                min  = int( t[2:4] )
                sec  = int( t[4:6] )
                self.time2 = time( hour,min,sec)
                self.date_time = datetime.combine(self.date2, self.time2).replace(tzinfo=pytz.utc)
                
                self.frq  = float(line[1])*1000.
                df  = int(line[6])
                frq = self.frq + 0.001*float(df)
                mode = line[3]
                snr = int(line[4])

                #print line,len(line)
                if len(line)>7:
                    call1=line[7]
                else:
                    call1=''
                if len(line)>8:
                    call2=line[8]
                else:
                    call2=''
                msg=''
                if len(call2)==2 and len(line)>9:
                    call2=line[9]
                    if len(line)>10:
                        msg = line[10]
                else:
                    if len(line)>9:
                        msg = line[9]

                call2 = ( call2.replace("<","") ).replace(">","")
                        
                spot = {'call2':call2, 'freq':frq, 'df':df, 'mode':mode, 'snr':snr,
                        'time':self.time2, 'date':self.date2, 'msg':msg,
                        'country':' ','lat':0,'lon':0,'band':' ',
                        'TimeStamp':self.date_time}

                self.age = self.age_secs2(verbosity)
                
                #print line,len(line)
                return spot

            
            # OLD Format - what a mess
            call1=line[5]
            call2=line[6]
            msg=''
            if len(call2)==2:
                call2=line[7]
                if len(line)>8:
                    msg = line[8]
            else:
                if len(line)>7:
                    msg = line[7]
                
            if n==6 or n==4:
                # Regular QSO entry
                # Time,SNR,dT,df,Mode_Flag,Call1,Call2,Msg  ,e.g.
                # 222445 -19  1.0  586 ~  CQ AI4FR EL88   
                t    = line[0]
                if len(t)==6:
                    hour = int( t[0:2] )
                    min  = int( t[2:4] )
                    sec  = int( t[4:6] )
                elif len(t)==4:
                    hour = int( t[0:2] )
                    min  = int( t[2:4] )
                    sec  = 0
                else:
                    print('GET_SPOT2: Unknown time format',t)
                    sys.exit(0)
                self.time2 = time( hour,min,sec)
                #print 'GET_SPOT2:',self.date2, self.time2
                self.date_time = datetime.combine(self.date2, self.time2).replace(tzinfo=pytz.utc)

                # Check for band/mode changes since last QSO
                if self.new_date_time and self.old_date_time:
                    age1 = (self.date_time - self.new_date_time).total_seconds() # Secs since last band change
                    age2 = (self.date_time - self.old_date_time).total_seconds() # Secs since last QSO before last band change
                else:
                    age1 = 0
                    age2 = 0
                if age1>15 or age2>15:
                    self.date2 = self.new_date
                    self.frq  = self.new_frq
                    self.mode = self.new_mode
                    #pass
                
                if verbosity>=1:
                    print(line)
                    print(call1,'called by',call2)
                    print('Last band change:',self.new_date_time,'\t\t\t',self.new_frq)
                    print('Last QSO:        ',self.old_date_time)
                    print('Current QSO:     ',self.date_time,age1,age2,'\t',self.frq)

                snr = int(line[1])
                df  = int(line[3])
                if self.frq:
                    frq = self.frq + 0.001*float(df)
                else:
                    frq = None
                mode= self.mode

                spot = {'call2':call2, 'freq':frq, 'df':df, 'mode':mode, 'snr':snr,
                        'time':self.time2, 'date':self.date2, 'msg':msg,
                        'country':' ','lat':0,'lon':0,'band':' ',
                        'TimeStamp':self.date_time}

            elif n==10:
                # OLD format - Band change:
                # Date,Time,frq,frq_units,Mode, e.g.
                # 2017-09-07 01:27  10.136 MHz  FT8

                d     = line[0]
                year  = int( d[0:4] )
                month = int( d[5:7] )
                day   = int( d[8:10] )
                
                t    = line[1]
                if len(t)==5:
                    hour = int( t[0:2] )
                    min  = int( t[3:5] )
                    sec  = 0
                else:
                    print('GET_SPOT2: Unknown time format',date_time)
                    sys.exit(0)

                if False:
                    self.date2 = date( year,month,day)
                    self.time2 = time( hour,min,sec)
                    self.frq  = float(line[2])*1000.
                    self.mode = line[4]
                else:
                    self.new_date = date( year,month,day)
                    if self.date2==None:
                        self.date2 = self.new_date
                    old_date = self.date2
                    
                    new_time = time( hour,min,sec)
                    if self.time2==None:
                        self.time2 = new_time
                    old_time = self.time2

                    self.new_date_time = datetime.combine(self.new_date, new_time).replace(tzinfo=pytz.utc)
                    self.old_date_time = datetime.combine(old_date, old_time).replace(tzinfo=pytz.utc)
                    
                    self.new_frq  = float(line[2])*1000.
                    if not self.frq:
                        self.frq = self.new_frq
                    self.new_mode = line[4]
                    if not self.mode:
                        self.mode = self.new_mode
                    
                if verbosity>=1:
                    print(line)
                    print('GET_SPOT2: Band/Mode change to',line[2],line[3],line[4])
                    
            elif n==13:
                #elif n==10 and nfields>5:
                # OLD format:Date_Time,Transmitting,frq,frq_units,mode,Call1,Call2,Msg
                
                #print '13!!!!!!!'
                #print line[0]
                d = line[0][0:6]
                year  = 2000+int( d[0:2] )
                month = int( d[2:4] )
                day   = int( d[4:6] )
                self.date2 = date( year,month,day)

                t = line[0][7:]
                hour = int( t[0:2] )
                min  = int( t[2:4] )
                sec  = int( t[4:6] )
                self.time2 = time( hour,min,sec)

                if verbosity>=1:
                    print(call1,'called by',call2,' - My TX')

                #print n,line
                #sys.exit(0)
                    
            else:
                print('********* GET_SPOT2: Unknown line format *********')
                print(line)
                print('********* GET_SPOT2: Unknown line format *********')
                #sys.exit(0)
            
            self.age = self.age_secs2(verbosity)
            
        else:

            self.nsleep+=1
            self.age = 0
            if self.nsleep==2:
                print('\nGET_SPOT2: Snoozing ...\n')
            sleep(1)

        return spot




    def find_recent_spots(self,mins):

        print('Searching for recent spots...',mins)
        if False:
            i=0
            while self.age>60.*mins and i<len(self.lines):
                spot=self.get_spot2(self.lines[i],0)
                #print i,len(self.lines),self.age
                i+=1
                #print 'FIND_RECENT:',i,self.age
        else:
            today = date.today()
            days_min = 1 + mins/(60*24.)
            print('FIND_RECENT: Today:',today,days_min,len(self.lines))
            i=-1
            for line in self.lines:
                line = line.strip().split()
                #print 'line=',line
                n=len(line[0])
                i+=1
                d=None
                if line[2]=='Rx' or line[2]=='Tx':
                    # NEW format: the kitchen sink - much simpler as of V2.0.1
                    #190227_024500     7.074 Rx FT8     -5  0.1 2316 FR5ZE K5TH EM00
                    d = line[0].replace('\x00','')[0:6]
                    year  = 2000+int( d[0:2] )
                    month = int( d[2:4] )
                    day   = int( d[4:6] )

                elif n==10:
                    d     = line[0]
                    year  = int( d[0:4] )
                    month = int( d[5:7] )
                    day   = int( d[8:10] )

                if d:
                    self.date2 = date( year,month,day)
                    days = (today - self.date2).days
                    if days<=days_min:
                        print(line)
                        print(days,mins)
                        break

            if i<0:
                print('Did not find anything')
                return None

            print('\nSearching from ',i)
            print(self.lines[i])
            spot=None
            while self.age>60.*mins and i<len(self.lines):
                spot=self.get_spot2(self.lines[i],0)
                i+=1
        istart=i

        #if self.age and True:
        if True:
            print('FIND_RECENT: age=',self.age/60.,mins,istart)
            print(spot)
            print('line=',self.line)
            #print 'date/time=',self.date2,self.time
            print('now=',self.now)
            #sys.exit(0)

        return istart


    def last_band(self):
        return freq2band(self.frq)
