#########################################################################################
#
# settings.py - Rev. 1.0
# Copyright (C) 2021-4 by Joseph B. Attili, aa2il AT arrl DOT net
#
# Gui for basic settings.
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
#########################################################################################

import sys
import os
import json
if sys.version_info[0]==3:
    from tkinter import *
    import tkinter.font
else:
    from Tkinter import *
    import tkFont
import time
from rig_io import SATELLITE_LIST

#from PyQt5 import QtCore
#from PyQt5.QtWidgets import *

#########################################################################################

KEYER_ATTRIBUTES = ['Call','Operator',
                    'Name','State','Sec','Cat','Grid','City','County',
                    'CQ Zone','ITU Zone','Prec','Check','Club',
                    'CWops','SKCC','FISTS','FOC',
                    'Rig','Ant','Age','Ham Age','Occupation']

# Function to read config params
def read_settings(fname,attr=None):

    # Read config file
    RCFILE=os.path.expanduser("~/"+fname)
    print('Reading config file ...',RCFILE)
    SETTINGS=None
    if os.path.isfile(RCFILE):
        
        with open(RCFILE) as json_data_file:
            SETTINGS = json.load(json_data_file)

        if attr==None:
            attr=KEYER_ATTRIBUTES
        for a in attr:
            attrib='MY_'+a.upper().replace(' ','_')
            if attrib not in SETTINGS:
                SETTINGS[attrib]=''                
            #print(attrib,'\t:\t',SETTINGS[attrib])
        
    else:
        
        print(RCFILE,' not found!\n')
        s=SETTINGS_GUI(None,None,attr)
        while not SETTINGS:
            try:
                if s.win==None:
                    print('Giving up - Must have basic settings!')
                    sys.exit(0)
                s.win.update()
            except Exception as e: 
                print( str(e) )
            SETTINGS=s.SETTINGS
            time.sleep(.1)

        print('Settings:',SETTINGS)
        print('Writing settings to',RCFILE,'...')
        with open(RCFILE, "w") as outfile:
            json.dump(SETTINGS, outfile)

    # Fill in the blanks
    if ('MY_OPERATOR' not in SETTINGS) or (SETTINGS['MY_OPERATOR'] == ''):
        if 'MY_CALL' in SETTINGS:
            SETTINGS['MY_OPERATOR'] = SETTINGS['MY_CALL'] 
    for attr in ['MY_CITY','MY_STATE']:
        if attr not in SETTINGS:
            SETTINGS[attr] = ''
                
    SETTINGS['MY_QTH']=SETTINGS['MY_CITY']+', '+SETTINGS['MY_STATE']
            
    #sys,exit(0)
    return SETTINGS,RCFILE

#########################################################################################

# Structure to contain config params
class CONFIG_PARAMS:
    def __init__(self,fname,attr=None):
        self.SETTINGS,self.RCFILE=read_settings(fname,attr)

#########################################################################################

class SETTINGS_GUI():
    def __init__(self,root,P,attrib=None,refreshCB=None):

        # Init
        self.root=root
        self.P = P
        self.refreshCB=refreshCB
        
        if root:
            self.win=Toplevel(root)
            self.hide()
            #print('Top-level')
        else:
            self.win = Tk()
            #print('Root')
        self.win.title("Settings")

        if P:
            self.SETTINGS=self.P.SETTINGS
        else:
            self.SETTINGS=None

        if attrib:
            self.ATTRIBUTES = attrib
        else:
            self.ATTRIBUTES = KEYER_ATTRIBUTES            

        row=-1
        self.boxes=[]
        for attr in self.ATTRIBUTES:
            row+=1
            txt='My '+attr
            Label(self.win, text=txt+':').grid(row=row, column=0)
            box = Entry(self.win)
            box.grid(row=row,column=1,sticky=E+W)
            #box.delete(0, END)  
            self.boxes.append(box)
            try:
                attr2=txt.upper().replace(' ','_')
                box.insert(0,P.SETTINGS[attr2])
            except:
                pass
        
        row+=1
        button = Button(self.win, text="OK",command=self.Dismiss)
        button.grid(row=row,column=0,sticky=E+W)

        button = Button(self.win, text="Cancel",command=self.hide)
        button.grid(row=row,column=1,sticky=E+W)

        #self.root.protocol("WM_DELETE_WINDOW", self.Quit)        
        self.win.protocol("WM_DELETE_WINDOW", self.hide)        
        
        #self.win.update()
        #self.win.deiconify()
        self.show()


    def Dismiss(self):
        print('DISMISS: P=',self.P)
        self.SETTINGS = {}
        for attr,box in zip(self.ATTRIBUTES,self.boxes):
            attr2='MY_'+attr.upper().replace(' ','_')
            if attr in KEYER_ATTRIBUTES:
                self.SETTINGS[attr2] = box.get().upper()
            else:
                self.SETTINGS[attr2] = box.get()

        if self.P:
            if 'MY_CITY' in self.SETTINGS and 'MY_STATE' in self.SETTINGS:
                self.SETTINGS['MY_QTH']=self.SETTINGS['MY_CITY']+', ' \
                    +self.SETTINGS['MY_STATE']
            self.P.SETTINGS=self.SETTINGS
            print('Writing settings to',self.P.RCFILE,'...')
            print(self.P.SETTINGS)
            with open(self.P.RCFILE, "w") as outfile:
                json.dump(self.P.SETTINGS, outfile)
                outfile.write('\n')

        if self.refreshCB:
            self.refreshCB()
        
        #self.win.destroy()
        self.hide()

    def show(self):
        print('Show Settings Window ...')
        self.win.update()
        self.win.deiconify()
        
    def hide(self):
        print('Hide Settings Window ...',self.root)
        if self.root:
            self.win.withdraw()
        else:
            print('Bye Bye')
            self.win.destroy()
            self.win=None

"""
# This doesn't work on its own
class SETTINGS_GUI_QT(QMainWindow):
    def __init__(self,P,parent=None):
        super(SETTINGS_GUI_QT, self).__init__(parent)

        # Init
        self.P=P
        self.win  = QWidget()
        self.setCentralWidget(self.win)
        self.setWindowTitle('pySat Settings')
        self.grid = QGridLayout(self.win)

        # Boxes to hold geographic info (i.e. gps data)
        row=0
        col=0
        labels=['My Call:','My Grid:','Latitude:','Longitude:','Altitude (m):']
        self.items=['MY_CALL','MY_GRID','MY_LAT','MY_LON','MY_ALT']
        self.eboxes=[] 
        for label,item in zip(labels,self.items):
            
            lab = QLabel(self)
            lab.setAlignment(QtCore.Qt.AlignCenter | QtCore.Qt.AlignVCenter)
            lab.setText(label)
            self.grid.addWidget(lab,row,col,1,1)

            ebox = QLineEdit(self)
            try:
                txt=str(self.P.SETTINGS[item])
            except:
                txt=''
            ebox.setText(txt)
            ebox.setAlignment(QtCore.Qt.AlignCenter | QtCore.Qt.AlignVCenter)
            self.grid.addWidget(ebox,row,col+1,1,1)
            
            self.eboxes.append(ebox)            
            row+=1

        # Separater for next section
        lab = QLabel(self)
        lab.setAlignment(QtCore.Qt.AlignCenter | QtCore.Qt.AlignVCenter)
        lab.setText('----- Known Satellites: -----')
        self.grid.addWidget(lab,row,col,1,1)

        if False:
            row+=1
            lab = QLabel(self)
            lab.setAlignment(QtCore.Qt.AlignCenter | QtCore.Qt.AlignVCenter)
            lab.setText('Known Satellites:')
            self.grid.addWidget(lab,row,col,1,1)

        # List of available satellites, whether we want them & tuning offsets
        self.cboxes=[]
        self.eboxes1=[]
        self.eboxes2=[]
        isat=0
        OFFSETS=self.P.SETTINGS['OFFSETS']
        row0=row+1
        for sat in SATELLITE_LIST:
            row+=1
            if row>row0+16:
                row=row0
                col+=4
            
            cbox = QCheckBox(sat)
            self.grid.addWidget(cbox,row,col,1,1)
            self.cboxes.append(cbox)
            if sat!='None' and sat in P.SATELLITE_LIST:
                cbox.setChecked(True)
                
            ebox = QLineEdit(self)
            self.eboxes1.append(ebox)
            try:
                #txt="0"   # str(OFFSETS[sat][0])
                txt=str(OFFSETS[sat][0])
            except:
                txt="0"
            ebox.setText(txt)
            ebox.setAlignment(QtCore.Qt.AlignCenter | QtCore.Qt.AlignVCenter)
            self.grid.addWidget(ebox,row,col+1,1,1)
            
            ebox = QLineEdit(self)
            self.eboxes2.append(ebox)
            try:
                txt=str(OFFSETS[sat][1])
            except:
                txt="0"
            ebox.setText(txt)
            ebox.setAlignment(QtCore.Qt.AlignCenter | QtCore.Qt.AlignVCenter)
            self.grid.addWidget(ebox,row,col+2,1,1)
            
            isat+=1
                
        # Buttons to complete or abandon the update
        row+=2
        col+=1
        button1 = QPushButton('OK')
        button1.setToolTip('Click to Update Settings')
        button1.clicked.connect(self.Update)
        self.grid.addWidget(button1,row,col,1,1)
        
        col+=1
        button2 = QPushButton('Cancel')
        button2.setToolTip('Click to Cancel')
        button2.clicked.connect(self.Cancel)
        self.grid.addWidget(button2,row,col,1,1)
        
        self.hide()

    # Function to update settings and write them to resource file
    def Update(self):

        # Collect things related to the list of sats
        ACTIVE=[]
        OFFSETS={}
        for sat,cbox,ebox1,ebox2 in zip(SATELLITE_LIST,self.cboxes,self.eboxes1,self.eboxes2):
            if sat!='None':
                OFFSETS[sat] = [int(ebox1.text()) , int(ebox2.text())]
                if cbox.isChecked():
                    ACTIVE.append(sat)

        # Bundle all into a common structure
        self.P.SETTINGS = {}
        for item,ebox in zip(self.items,self.eboxes):
            self.P.SETTINGS[item]=ebox.text()
        self.P.SETTINGS['ACTIVE']=ACTIVE
        self.P.SETTINGS['OFFSETS']=OFFSETS
        self.P.SATELLITE_LIST=ACTIVE
        
        # Write out the resource file
        with open(self.P.RCFILE, "w") as outfile:
            json.dump(self.P.SETTINGS, outfile)

        # Hide the sub-window
        self.hide()

    # Abaondon the update, just close the sub-window
    def Cancel(self):
        self.hide()
        

"""
