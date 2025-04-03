############################################################################################
#
# presets.py - Rev 1.0
# Copyright (C) 2021-5 by Joseph B. Attili, joe DOT aa2il AT gmail DOT com
#
# Routines for handling preset memory programming
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

from .ft_tables import *
from .icom_io import *
import xlrd
if sys.version_info[0]==3:
    import tkinter.messagebox
else:
    import tkMessageBox

############################################################################################

# Various preferences for the different modes
preset_prefs = OrderedDict()
preset_prefs['AM']   = ('10 KHz','5 KHz')
preset_prefs['SSB']  = ('10 KHz','3 KHz')
preset_prefs['USB']  = ('10 KHz','3 KHz')
preset_prefs['LSB']  = ('10 KHz','3 KHz')
preset_prefs['CW']   = ('10 KHz','500 Hz')
preset_prefs['IQ']   = ('Max','Max')
preset_prefs['WFM']  = ('200 KHz','10 KHz')
preset_prefs['WFM2'] = ('200 KHz','10 KHz')
preset_prefs['NFM']  = ('10 KHz','5 KHz')
preset_prefs['FT8']   = ('10 KHz','4 KHz')
preset_prefs['FT4']   = ('10 KHz','4 KHz')
preset_prefs['PKTUSB']   = ('10 KHz','4 KHz')


# Function to read presets from a spreadsheet
def read_presets2(rig_type,sheet_name):

    book  = xlrd.open_workbook(PRESETS_FNAME,formatting_info=True)
    sheet = book.sheet_by_name(sheet_name)

    keys = []
    for j in range(0, sheet.ncols):
        keys.append( str(sheet.cell(0,j).value) )
    #print('keys=',keys

    presets = []
    for i in range(1, sheet.nrows):
        row=OrderedDict()
        for j in range(0, sheet.ncols):
            try:
                row[keys[j]] = str(sheet.cell(i, j).value)
            except:
                print( i,j,keys[j],sheet.cell(i, j).value )
                print( [ord(c) for c in sheet.cell(i, j).value] )
                sys.exit(0)
                
        if row['Group']=='Sats' and False:
            print(i,row)
            for j in range(0, sheet.ncols):
                print(i,j,sheet.cell(i, j))

        # Fix-up entries
        #print('\n',i,row)
        if len(row['Tag'])>0:
            row['Freq1 (KHz)'] = float( row['Freq1 (KHz)'] )
            if len(row['Group'])==0:
                row['Group']=group
            else:
                group=row['Group']
            if len(row['Mode'])==0:
                row['Mode']=mode
            else:
                mode=row['Mode']
            if len(row['Step (KHz)'])==0:
                row['Step (KHz)']=step
            else:
                step=row['Step (KHz)']

            for attr in ['Freq2 (KHz)','PL','Video BW (KHz)','Audio BW (KHz)','Uplink','Downlink']:
                try:
                    row[attr] = float( row[attr] )
                except:
                    row[attr] = 0
                
            presets.append(row)

    if False:
        for line in presets:
            print( line)
        #groups=set([line['Group'] for line in presets])
        #print(groups
        sys.exit(0)
        
    return presets
        
        

# Function to read presets from a spreadsheet
def read_presets_OLD(rig_type):
    presets = OrderedDict()

    book  = xlrd.open_workbook(PRESETS_FNAME,formatting_info=True)
    sheet1 = book.sheet_by_name('Presets')
    sheet2 = book.sheet_by_name('Hops')

    hdr = []
    for j in range(0, sheet1.ncols):
        hdr.append( sheet1.cell(0, j).value )
    #print('hdr=',hdr
    idx_grp = hdr.index('Group')
    idx_tag = hdr.index('Tag')
    idx_mode = hdr.index('Mode')
    if rig_type:
        idx_memchan = hdr.index(rig_type)
    else:
        idx_memchan = -1
    idx_pl = hdr.index('PL')
    idx_uplink = hdr.index('Uplink')
    #print(idx_grp,idx_tag,idx_mode,idx_memchan

    for i in range(1, sheet1.nrows):
        row=[]
        for j in range(0, sheet1.ncols):
            row.append( sheet1.cell(i, j).value )

        # Check for a new group
        if len(row[idx_grp])>0:
            group = row[idx_grp]
            presets[group]=OrderedDict()

        # Check for a new entry (tag)
        if len(str(row[idx_tag]))>0:
            tag = str(row[idx_tag])

            # Read freq(s)
            f1  = float( row[2] )
            if row[3]!='':
                f2 = float( row[3] )
            else:
                f2 = f1

            # Determine mode & demo params
            if len(row[idx_mode])>0:
                mode = row[idx_mode]
                if mode=='IQ' and f1!=f2:
                    videobw = str(int(f2-f1))+' KHz'
                    audiobw = videobw
                else:
                    videobw = preset_prefs[mode][0]
                    audiobw = preset_prefs[mode][1]
                if row[6]!='':
                    videobw = str(int(row[6])) + ' KHz'
                if row[7]!='':
                    audiobw = str(int(row[7])) + ' KHz'

            # Determine tuning step
            if row[5]!='':
                step = float( row[5] )

            # Determine mem channel
            if idx_memchan<0 or row[idx_memchan]=='':
                mem_chan = 0
            else:
                mem_chan = int( row[idx_memchan] )

            # Determine PL (CTCSS) tone
            if row[idx_pl]=='':
                pl = 0.
            else:
                pl = row[idx_pl]

            # Determine uplink freq
            if row[idx_uplink]=='':
                uplink = 0.
            else:
                uplink = row[idx_uplink]

        # Put it all together
        presets[group][tag]=(f1,mode,f2,step,videobw,audiobw,mem_chan,pl,uplink)

        #print('READ_PRESETS:',i,row 
        #print(presets[group][tag]

    #sys.exit(0)
    return presets

############################################################################################

# Routine to read contents of IC706 or IC9700 memories
def read_mem_icom(self):

    NCHAN=99
    NCHAN=6

    # Select memory mode
    print('Selecting memory mode ...')
    cmd =  self.sock.civ.icom_form_command([0x08]) 
    #print('cmd=',cmd
    x=self.sock.get_response(cmd)
    #print('x=',x
    y=self.sock.civ.icom_response(cmd,x)
    print('y=',y)

    for band in ['2m','70cm']:
        print('\n',band,' mem chans:++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++')
        for ch in range(NCHAN):
            read_mem_chan_icom(self,ch,band)

        
# Routine to read contents of a single meory channel
def read_mem_chan_icom(self,ch,band):
        
    if self.sock.rig_type2=='IC760':
        # Need to retest this with 706
        ch2  = int2bcd(ch+1,1)
        print('\nReading mem',ch+1,ch2)
        cmd =  self.sock.civ.icom_form_command([0x08,0x0]+ch2)              # Select memory channel
    else:
        ch2  = int2bcd(ch+1,2,1)
        print('\nReading mem',ch+1,ch2)

        if band=='2m':
            band_select=0x1
        elif band=='70cm':
            band_select=0x2
        else:
            print('READ_MEM_CHAN_ICOM: Unknown band')
            sys.exit(0)
            
        #cmd =  self.sock.civ.icom_form_command([0x1a,0x0,0x1,0x0]+ch2)            # Get contents of mem channel
        cmd =  self.sock.civ.icom_form_command([0x1a,0x0,band_select]+ch2)            # Get contents of mem channel
                
        # This works to clear a memory channel!
        # cmd =  self.sock.civ.icom_form_command([0x1a,0x0,0x1]+ch2+[0xff])

    print('cmd=',show_hex(cmd))
    x=self.sock.get_response(cmd)
    print('x=',show_hex(x))
    y=self.sock.civ.icom_response(cmd,x)
    print('y=',y,len(y))

    print('band:       ',y[1],int(y[1],16))
    print('chan:       ',y[2:4],bcd2int(y[2:4],1))
    print('mem setting:',y[4],int(y[4],16))
    if int(y[4],16)==255:
        print('Empty channel')
    else:
        print('freq:       ',y[5:10],bcd2int(y[5:10]))
        print('mode & filt:',y[10:12],bcd2int(y[10:12],1))
        print('data mode:  ',y[12],int(y[12],16))
        print('dup & tone: ',y[13],int(y[13],16))
        print('digi squel: ',y[14],int(y[14],16))
        print('rptr tone:  ',y[15:18],bcd2int(y[15:18],1))
        print('squel tone: ',y[18:21],bcd2int(y[18:21],1))
        print('dtcs tone:  ',y[21:24],bcd2int(y[21:24],1))
        print('dv:         ',y[24],int(y[24],16))
        print('dup offset: ',y[25:28],bcd2int(y[25:28]))
        # Table is incomplete
        print('name:       ',y[52:68])
    

        

############################################################################################


class MEM_CHAN:
    def __init__(self):
        self.chan=None
        self.freq=None
        self.mode=None
        self.clar_offset=None
        self.rx_clar_on_off=None
        self.tx_clar_on_off=None
        self.ctcss=None
        self.tone=None
        self.shift=None
        self.tag=None
        self.response=None


# Routine to read contents of FTdx3000 or FT991a memories
# At some point, might want to use MT command for FT991a instead since
# it will return tag as well but for now ...
def read_mem_yaesu(self,chan):

    for ch in [chan]:
        cmd = 'BY;MC'+str(ch+1).zfill(3)+';'
        buf=self.sock.get_response(cmd)
        print('\nReading channel',ch,cmd)
        print('response=',buf)

        if self.sock.rig_type2=='FT991a':    
            cmd = 'MT'+str(ch+1).zfill(3)+';'
        else:
            cmd = 'MR'+str(ch+1).zfill(3)+';'
        buf=self.sock.get_response(cmd)
        print('\nReading channel',ch,cmd)
        print('response=',buf)

        return resp2struct(self,buf)
        

def resp2struct(self,buf):
    mem=MEM_CHAN()
    print('\nresp2struct: buf=',buf)

    if True:
        if buf[0:2] in ['MR','MT','MW']:
            P2=buf[2:5]
            mem.chan=int(P2)
            print('P2=',P2,'\tChan=',mem.chan)
            
            if self.sock.rig_type2=='FTdx3000':
                last=13
            else:
                last=14
            P3=buf[5:last]
            mem.freq=float(P3)/1000.
            print('P3=',P3,'\tf=',mem.freq,'KHz')

            first=last
            last=last+5
            P4=buf[first:last]
            mem.clar_offset=float(P4)
            print('P4=',P4,'\tClar Offset=',mem.clar_offset,'Hz')
            
            P5=buf[last]
            last=last+1
            mem.rx_clar_on_off=OFF_ON[int(P5)]
            print('P5=',P5,'\tRX Clar=',mem.rx_clar_on_off)
            
            P6=buf[last]
            last=last+1
            mem.tx_clar_on_off=OFF_ON[int(P6)]
            print('P6=',P6,'\tTX Clar=',mem.tx_clar_on_off)
            
            P7=buf[last]
            last=last+1
            mem.mode=FTDX_MODES[int(P7,16)]
            print('P7=',P7,'\tmode=',mem.mode)
            
            P8=buf[last]
            last=last+1
            print('P8=',P8,'\tVFO/Mem=',VFO_MEM[int(P8)])

            P9=buf[last]
            last=last+1
            mem.ctcss=CTCSS[int(P9)]
            print('P9=',P9,'\tCTCSS=',mem.ctcss)
            
            first=last
            last=last+2
            P10=buf[first:last]
            mem.tone=PL_TONES[ int(P10) ]
            print('P10=',P10,'\tTone=',mem.tone)
            
            P11=buf[last]
            mem.shift=SHIFTS[int(P11)]
            print('P11=',P11,'\tShift=',mem.shift)
            
            first=last+2
            last=first+12
            P12=buf[first:last]
            mem.tag=P12
            print('P12=',P12,'\tTag=',mem.tag,len(mem.tag))

            mem.response=buf
            
        else:
            print('Mem channel not programmed')
            mem=None
        
    return mem
            
############################################################################################

# Routine to write a single memory channel of FTdx3000 or FT991a
# The memories can be cleared by holding the A-M key while turinging on the FT991a
# The processor can be cleared by holding the FAST and LOCK keys while turinging on the FT991a
# After reset, eed to set baud rate to 38400 (menu 031)
def write_mem_yaesu(self,grp,lab,ch,KHz,mode,pl,frq2,inverting):

    print(' ') 
    print('Writing:',lab,ch,KHz,mode,pl,frq2)
    mem_chan = str(ch).zfill(3)
    if self.sock.rig_type2=='FTdx3000':
        frq = str( int( 1000*KHz )).zfill(8)
    else:
        frq = str( int( 1000*KHz )).zfill(9)

    # Select memory channel
    buf=self.sock.get_response('MC'+mem_chan+';')
    print('MC select:',buf)
    if self.sock.rig_type2=='FT991a':    
        mem_buf=self.sock.get_response('MT'+mem_chan+';')
    else:
        mem_buf=self.sock.get_response('MR'+mem_chan+';')
    print('MR read:',mem_buf)
        
    # Don't alter satellites already stored - these need special attention
    # See page 109 of the user's manual as to how to do this.  Requires pressing PTT and
    # A->B simultaneously and there is no way to do this via CAT - UGH!

    # Construct Mem Write with Tag command
    P1=mem_chan          # Mem chan number
    P2=frq               # VFO A Freq
    P3='+0000'           # Clarifier offset
    P4='0'               # RX clarifer off
    P5='0'               # TX clarifer off
                    
    if mode=='NFM' or mode=='WFM':
        mode='FM'
    elif mode=='IQ':
        mode='USB'
    elif mode=='PKTUSB':
        mode='PKT-U'
    P6=hex(FTDX_MODES.index(mode))[2].upper()         # Mode
    P7='0'

    # Check for a satellite
    MEM_SPLIT=False
    if grp=='Satellites' or (frq2>0 and KHz!=frq2):
        print('Howdy Ho! Satellite/split time',KHz,frq2)
        msg='Need to program memory split.\n'+\
            'The FT991a does not have a nice way of doing this via CAT so we have to provide '+ \
            'some adult supervision.\n'+\
            'Do you want to proceed?'
        if frq2>0:
            if sys.version_info[0]==3:
                result=tkinter.messagebox.askyesno(lab,msg)
            else:
                result=tkMessageBox.askyesno(lab,msg)
            if not result:
                print('Cancelled')
                return
            else:
                MEM_SPLIT=True

        if pl>0:
            P8='2'                                # Use PL tone
            print('RIG TYPE2=',self.sock.rig_type2)
            if self.sock.rig_type2=='FTdx3000':
                p2 = str( np.where(PL_TONES==pl)[0][0] ).zfill(2)
                cmd2='CN0'+p2+';CT02;'
            else:
                p3 = str( np.where(PL_TONES==pl)[0][0] ).zfill(3)
                cmd2='CN00'+p3+';CT02;'
        else:
            P8='0'                          # No PL tone
            cmd2='CT00;'                    # CTCSS off

        if inverting:
            mode2='LSB'
        else:
            mode2=mode
            
        P10='0'                               # We have to program memory splits manually

    # Check for a repeater
    elif pl>0:
        P8='2'                                # Use PL tone

        # 2-Meter Repeater Output Frequency	Standard Input Frequency Offset
        # 145.1 MHz - 145.5 MHz	-600 kHz
        # 146.0 MHz - 146.4 MHz	+600 kHz
        # 146.6 MHz - 147.0 MHz	-600 kHz
        # 147.0 MHz - 147.4 MHz	+600 kHz
        # 147.6 MHz - 148.0 MHz	-600 kHz
        
        # Amateur Radio Repeater Offsets
        
        # Output Frequency  	Input Frequency Offset  
        # 51-52	                     - 0.5 MHz
        # 52-54	                     - 1.0 MHz
        # 144.51-144.89	             + 0.6 MHz
        # 145.11-145.49	             - 0.6 MHz
        # 146.0-146.39               + 0.6 MHz
        # 146.61-147.0               - 0.6 MHz
        # 147.0-147.39               + 0.6 MHz
        # 147.6-147.99	             - 0.6 MHz
        # 223-225                    - 1.6 MHz
        # 440-445	             + 5.0 MHz
        # 445-450	             - 5.0 MHz
        # 918-922	             - 12 MHz
        # 927-928	             - 25 MHz
        
        f=KHz*1e-3
        if (f>145.75 and f<146.5) or (f>=147. and f<147.5) or (f>=440 and f<445):
            P10='1'                          # Shift
        else:
            P10='2'

        # Select PL Tone
        try:
            print('RIG TYPE2=',self.sock.rig_type2)
            if self.sock.rig_type2=='FTdx3000':
                p2 = str( np.where(PL_TONES==pl)[0][0] ).zfill(2)
                cmd2='CN0'+p2+';CT02;'
            else:
                p3 = str( np.where(PL_TONES==pl)[0][0] ).zfill(3)
                cmd2='CN00'+p3+';CT02;'
        except:
            print('Error looking up PL tone - probably a bad value',pl)
            print(PL_TONES)
            sys.exit(0)
        #print(p3)
        #sys.exit(0)

    else:
        P8='0'                          # No PL tone
        cmd2='CT00;'                    # CTCSS off
        if frq2==0 or True:
            split=0
            P10='0'                     # No shift (simplex)
        else:
            # See page 109 of the user's manual as to how to program these manually.
            # Requires pressing PTT and A->B simultaneously and there is no way to do this via CAT - UGH!
            # May be able to use Auto Repeater shift (ARS) & menu functions 082 & 084 to get by for ISS but who knows.
            split=abs(KHz-frq2)
            print( 'Hmmmmmmm - split mode ...',frq,frq2,split)
            if KHz>frq2:
                P10='2'                          # -Offset 
            elif KHz<frq2:
                P10='1'                          # +Offset 
            
    P9='00'                         # Fixed
    P11='0'                         # Fixed 
    P12=lab.ljust(12)               # Mem label
    P12=P12[0:12]
        
    # Make sure tuner is off
    buf=self.sock.get_response('AC000;')

    print('Chan No.       = P1 =',P1)
    print('Freq           = P2 =',P2,len(P2))
    print('Clar Offset    = P3 =',P3)
    print('RX Clar Off/On = P4 =',P4)
    print('TX Clar Off/On = P5 =',P5)
    print('Mode           = P6 =',P6)
    print('Fixed Zero     = P7 =',P7)
    print('PL Tone Off/ON = P8 =',P8)
    print('Fixed 00       = P9 =',P9)
    print('Shift/Offest   = P10=',P10)
    print('Zero?          = P11=',P11)
    print('Label          = P12=',P12,len(P12),lab)

    # Generate memory write tag command
    if self.sock.rig_type2=='FTdx3000':
        cmd = 'MW'+P1+P2+P3+P4+P5+P6+P7+P8+P9+P10+';'
        correct_len=27
    else:
        cmd = 'MT'+P1+P2+P3+P4+P5+P6+P7+P8+P9+P10+P11+P12+';'
        correct_len=41
    if len(cmd)!=correct_len:
        print(cmd,len(cmd))
        print('*** Rut-Roh - command is not correct ***')

    # Compare comand to what is alreay stored there
    print('mem=',mem_buf)
    mem_buf=mem_buf[:22]+'0'+mem_buf[23:]
    print('mem=',mem_buf)
    print('cmd=',cmd)
    SAME = cmd==mem_buf
    print('Same=',SAME)
    if not SAME:
        resp2struct(self,mem_buf)
        resp2struct(self,cmd)
    else:
        return SAME

    # Execute command that turns PL on & off
    print('P8=',P8)
    print('cmd2=',cmd2,len(cmd2))
    buf=self.sock.get_response(cmd2)
    print('buf=',buf)

    if False:
        
        msg='CMD2 executed - Continue?'
        if sys.version_info[0]==3:
            result=tkinter.messagebox.askyesno(lab,msg)
        else:
            result=tkMessageBox.askyesno(lab,msg)
        if not result:
            print('Cancelled')
            return
    
    # Execute memory write tag command
    print(cmd,len(cmd))
    buf=self.sock.get_response(cmd)
    print('buf=',buf)

    # Readback
    buf=self.sock.get_response('MR'+mem_chan+';')
    print('MR read:',buf)
    if self.sock.rig_type2=='FT991a':    
        buf=self.sock.get_response('MT'+mem_chan+';')
        print('MT read:',buf)
    buf=self.sock.get_response('CT0;')
    print('CT read:',buf)
    if self.sock.rig_type2=='FTdx3000':
        buf=self.sock.get_response('CN0;')
    else:
        buf=self.sock.get_response('CN00;')
    print('CN read:',buf)

    if False:
        msg='CMD executed - Continue?'
        if sys.version_info[0]==3:
            result=tkinter.messagebox.askyesno(lab,msg)
        else:
            result=tkMessageBox.askyesno(lab,msg)
        if not result:
            print('Cancelled')
            return
    
    # Handle split
    if MEM_SPLIT:
        print('Setting freq & mode',frq2,mode2)
        self.sock.set_freq(frq2)
        frq3 = self.sock.get_freq()
        print('frq3=',frq3)
        self.sock.set_mode(mode2)
        msg='First, Press A->M to bring up list of memory channels.  Make sure its still on correct channel.\n'+\
            'Next, Press and hold PTT then A->M until a double beep sounds.\n'+\
            'Finally, Click OK to go on'  
        if sys.version_info[0]==3:
            tkinter.messagebox.showinfo(lab,msg)
        else:
            tkMessageBox.showinfo(lab,msg)
      
        #self.Quit()
        #sys.exit(0)
        
                
    return SAME
        
                
############################################################################################

# Routine to write a single memory channel to IC706 or IC9700
# This looks like a dead-end for the 706 as far as repeaters since there is no way
# to program the CTCSS tones via CI-V. We'll therefore concentrate on the 9700.
def write_mem_icom(self,grp,lab,ch,frq,mode,pl,frq2,inverting):

    mem_chan = int2bcd(ch,2,1)
    print('\nWriting:',lab,mem_chan,frq,mode,pl,frq2)

    # Turn off dual watch
    if False:
        print('Turning off dual watch ...')
        #cmd =  self.sock.civ.icom_form_command([0x07,0x0])  # Select VFO A
        cmd =  self.sock.civ.icom_form_command([0x16,0x59,0x0])  
        x=self.sock.get_response(cmd)
        y=self.sock.civ.icom_response(cmd,x)
        print('y=',y)
        #return
    
    # Construct Mem Write command
    if frq<200e3:
        P0=1
    elif frq<500e3:
        P0=2
    else:
        P0=3
    P0=int2bcd(P0,1,1)
    P1=int2bcd(ch,2,1)                     # Mem chan number
    P2=int2bcd(int(1000*frq),5,1)          # VFO A Freq
    P2=P2[::-1]

    if mode=='NFM' or mode=='WFM':
        mode='FM'
    elif mode=='IQ':
        mode='USB'
    P6 =[ icom_modes[mode]["Code"] ]         # Mode
    if inverting:
        if mode=='CW':
            mode2='CW-R'
        elif mode=='USB':
            mode2='LSB'
        P62 =[ icom_modes[mode2]["Code"] ]         # Mode2
    else:
        P62=P6
        mode2=mode
    P22=[]

    # Check for a satellite
    SATELLITE=False
    #if grp=='Satellites':
    if grp=='Sats':
        SATELLITE=True
        print('Satellite',frq,frq2,pl)

        P8 = 0x01                              # Use PL tone
        P9 = int2bcd(10*pl,3,1)
        split=600
        P22=int2bcd(int(1000*frq2),5,1)        # VFO B Freq
        P22=P22[::-1]

    # Check for a repeater
    elif pl>0:
        
        # 2-Meter Repeater Output Frequency	Standard Input Frequency Offset
        # 145.1 MHz - 145.5 MHz	-600 kHz
        # 146.0 MHz - 146.4 MHz	+600 kHz
        # 146.6 MHz - 147.0 MHz	-600 kHz
        # 147.0 MHz - 147.4 MHz	+600 kHz
        # 147.6 MHz - 148.0 MHz	-600 kHz
        
        # Amateur Radio Repeater Offsets
        
        # Output Frequency  	Input Frequency Offset  
        # 51-52	- 0.5 MHz
        # 52-54	- 1.0 MHz
        # 144.51-144.89	+ 0.6 MHz
        # 145.11-145.49	- 0.6 MHz
        # 146.0-146.39	+ 0.6 MHz
        # 146.61-147.0	- 0.6 MHz
        # 147.0-147.39	+ 0.6 MHz
        # 147.6-147.99	- 0.6 MHz
        # 223-225	- 1.6 MHz
        # 440-445	+ 5.0 MHz
        # 445-450	- 5.0 MHz
        # 918-922	- 12 MHz
        # 927-928	- 25 MHz
        
        f=frq*1e-3
        print('f=',f)
        if (f>145.75 and f<146.5) or (f>=147. and f<147.5) or (f>=440 and f<445):
            P8=0x21                          # +Offset w/ tone
        else: 
            P8=0x11                          # -Offset w/ tone
        P9 = int2bcd(10*pl,3,1)

        if f<200:
            split=600
        else:
            split=5000

    else:
        # Can't seem to get split mode to work in memory so we use duplex function instead
        if frq2==0:
            split=0
            P8=0x0                           # No PL tone or shift
        else:
            split=abs(frq-frq2)
            print('Hmmmmmmm - split mode ...',frq,frq2,split)
            if frq>frq2:
                P8=0x10                          # -Offset w/o tone
            elif frq<frq2:
                P8=0x20                          # +Offset w/o tone
        P9 = int2bcd(10*88.5,3,1)            # Dummy to satisfy mem write command

    # Dup offset
    P10 = int2bcd(10*split,3,1)
    P10=P10[::-1]
                        
    # Mem label
    P12=lab.ljust(16)
    P12=[ord(c) for c in P12[0:16] ]
    
    # Execute memory write tag command
    print('P0 =',P0)
    print('P1 =',P1,ch)
    print('P2 =',show_hex(P2),frq)
    print('P6 =',P6,mode)
    print('P62 =',P62,mode2)
    print('P8 =',P8)
    print('P9 =',pl,show_hex(P9))
    print('P10=',show_hex(P10),split)
    print('P12=',show_hex(P12),len(P12),lab)
    print('P22=',show_hex(P22),frq2)

    if SATELLITE:
        self.sock.sat_mode(1)                # Put rig into sat mode

        # Select memory channel
        if False:
            print('Selecting channel ...',mem_chan)
            cmd =  self.sock.civ.icom_form_command([0x08]+mem_chan)  
            x=self.sock.get_response(cmd)
            y=self.sock.civ.icom_response(cmd,x)
            print('y=',y)
        
        # There are some obvious discrepancies in the manual
        # Debug - Try reading mem chan
        if False:
            cmd =  self.sock.civ.icom_form_command([0x1a,0x7]+P1)
            print('cmd=',show_hex(cmd),len(cmd))
            x=self.sock.get_response(cmd)
            print('x=',show_hex(x))
            y=self.sock.civ.icom_response(cmd,x)
            print('y=',y,len(y))

        # Form the command - see page 18 of IC9700 CIV manual
        DOWN=P1+P2+P6+[0x1] + [0x00,0x01,0x00] + 2*P9 + [0x0,0x0,0x23,0x0] + 24*[0x20]
        print('\nDOWN=',show_hex(DOWN),len(DOWN))
        UP  =  P22+P62+[0x1] + [0x00,0x01,0x00] + 2*P9 + [0x0,0x0,0x23,0x0] + 24*[0x20]
        print('UP  =',show_hex(UP),len(UP))
        print(len(DOWN)+len(UP)+len(P12),46+44+16,'\n')

        # Compare byte by byte
        if False:
            yy = show_hex( [0x7]+DOWN+UP+P12 )
            print('yy=',yy,len(yy))
            for i in range(len(y)):
                print(i,y[i],yy[i],y[i]==yy[i])
            return

        cmd =  self.sock.civ.icom_form_command([0x1a,0x7]+DOWN+UP+P12)
        print('cmd=',show_hex(cmd),len(cmd), 46+(46-3+1)+16 + 7,55+44+7)
        x=self.sock.get_response(cmd)
        print('x=',show_hex(x))
        y=self.sock.civ.icom_response(cmd,x)
        print('y=',y)

        if y=='NG':
            print('*** ERROR programing mem channel - giving up')
            self.Quit()
            sys.exit(0)
            
        self.sock.sat_mode(0)                # Take rig out of sat mode
        return
        
    elif not SATELLITE and True:

        self.sock.sat_mode(0)                      # Put rig into non-sat mode

        # Use extended command - doesn't quite work as the manual says but seems ok
        # Manual seems to be wrong???
        P51=P0+P1+[0x0]+P2+P6+[0x1] + [0x0,P8,0x0] +2*P9+ [0x0,0x0,0x23,0x0] + P10 + 24*[0x20]
        print('P51=',show_hex(P51),len(P51),'\n')

        #P51b=P0+P1+[0x0]+P22+P6+[0x1] + [0x0,P8,0x0] +2*P9+ [0x0,0x0,0x23,0x0] + P10 + 24*[0x20]
        #print('P51b=',show_hex(P51b),len(P51b),'\n')
        
        #cmd =  self.sock.civ.icom_form_command([0x1a,0x0]+P51+P51b[4:]+P12)
        cmd =  self.sock.civ.icom_form_command([0x1a,0x0]+P51+P12)
        print('cmd=',show_hex(cmd),len(cmd), 51+(51-5+1)+16 + 7)
        x=self.sock.get_response(cmd)
        print('x=',show_hex(x))
        y=self.sock.civ.icom_response(cmd,x)
        print('y=',y)

        if y=='NG':
            print('*** ERROR programing mem channel - giving up')
            self.Quit()
            sys.exit(0)
            
    else:
        
        # Program each step individually - useful for debugging full comands 
        SPLIT=False
        if SATELLITE:
            self.sock.split_mode(0)                    # Put rig into non-split mode
            self.sock.sat_mode(1)                      # Put rig into sat mode
            self.sock.select_vfo('M')
        else:
            self.sock.sat_mode(0)                      # Put rig into non-sat mode
            if frq2!=frq:
                print('\nHmmmmmmm - split mode ...')
                self.sock.split_mode(1)                # Put rig into split mode
                self.sock.select_vfo('A')              # Select VFO A
                SPLIT=True
            else:
                self.sock.split_mode(0)                # Put rig into non-split mode
        
        # Select memory channel
        print('Selecting channel ...',mem_chan)
        cmd =  self.sock.civ.icom_form_command([0x08]+mem_chan)  
        x=self.sock.get_response(cmd)
        y=self.sock.civ.icom_response(cmd,x)
        print('y=',y)

        # Set radio freq and mode
        print('Setting freq(s) and mode(s) ...',frq,mode,frq2,mode)
        self.sock.set_freq(frq)
        self.sock.set_mode(mode)
        if SATELLITE:
            self.sock.select_vfo('S')
            self.sock.set_freq(frq2)
            self.sock.set_mode(mode)
        elif SPLIT:
            self.sock.select_vfo('B')              # Select VFO B
            self.sock.set_freq(frq2)
            self.sock.select_vfo('A')              # Select VFO A
        
        # Set PL tone
        print('Setting PL tone',pl,P8*pl)
        self.sock.set_PLtone(P8*pl)
            
        # Write these setting to memory channel
        print('Writing to memory',mem_chan)
        cmd =  self.sock.civ.icom_form_command([0x09]) 
        x=self.sock.get_response(cmd)
        y=self.sock.civ.icom_response(cmd,x)
        print('y=',y)


############################################################################################
        
# Routine to make list of various ham band presets
def make_ham_presets(BandList,bands,pan_bw=0,rig_if=0):
    ham_bands = OrderedDict()
    for b in bands:
        if b in BandList:
            if b=='2m':
                ham_bands[b]=(bands[b]["CW1"],'NFM')
            else:
                ham_bands[b]=(bands[b]["CW1"],'IQ')

            if bands[b]["CW1"]<200e3:
                bb = b+" cw"
                if True:
                    f  = bands[b]["CW1"] + 30
                elif pan_bw>0:
                    f  = bands[b]["CW1"] + pan_bw/2000.
                else:
                    f  = (bands[b]["CW1"] + bands[b]["CW2"])/2
                if rig_if==0:
                    ham_bands[bb]=(f,'IQ')
                else:
                    ham_bands[bb]=(f,'CW')
                    
                bb = b+" rtty"
                f  = (bands[b]["RTTY1"] + bands[b]["RTTY2"])/2
                if rig_if==0:
                    ham_bands[bb]=(f,'IQ')
                else:
                    ham_bands[bb]=(f,'USB')

                bb = b+" ft8"
                f  = bands[b]["FT8"]
                ham_bands[bb]=(f,'USB',f,2,'10 KHz','4 KHz')
            
                bb = b+" ft4"
                f  = bands[b]["FT4"]
                ham_bands[bb]=(f,'USB',f,2,'10 KHz','4 KHz')
            
                bb = b+" ssb"
                f  = (bands[b]["SSB1"] + bands[b]["SSB2"])/2
                if f<10e3:
                    ham_bands[bb]=(f,'LSB')
                else:
                    ham_bands[bb]=(f,'USB')

    return ham_bands


# Routine to make list of various ham band presets
def make_ham_presets2(b,bands,pan_bw=0,rig_if=0):
    ham_bands=[]

    for mode in ['','cw','rtty','ft8','ft4','ssb']:
        row=OrderedDict()

        row['Tag']=str(b)+' '+mode
        if mode=='':
            key='CW1'
        elif mode=='ft8' or mode=='ft4':
            key=mode.upper()
        else:
            key = mode.upper()+"1"
        row['Freq1 (KHz)'] = bands[b][key]
        
        for attr in ['Freq2 (KHz)','PL','Video BW (KHz)','Audio BW (KHz)','Uplink','Downlink']:
            row[attr] = 0
        
        if mode=='cw':
            row['Freq1 (KHz)'] += 25             # Bump up start freq to 25KHz from band edge
            row['Mode']='CW'
            row['Video BW (KHz)']='45 KHz'
            row['Audio BW (KHz)']='100 Hz'
        elif mode=='ft8' or mode=='ft4':
            row['Mode']='USB'
            row['Video BW (KHz)']='10 KHz'
            row['Audio BW (KHz)']='4 KHz'
        elif mode=='ssb':
            if row['Freq1 (KHz)'] > 100e3:
                row['Mode']='NFM'
                row['Tag']=str(b)+' NFM'
            elif row['Freq1 (KHz)']  <10e3:
                row['Mode']='LSB'
            else:
                row['Mode']='USB'
        else:
            row['Mode']='IQ'

            
        ham_bands.append(row)
    return ham_bands
