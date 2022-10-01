#########################################################################################
#
# settings.py - Rev. 1.0
# Copyright (C) 2021 by Joseph B. Attili, aa2il AT arrl DOT net
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

#########################################################################################

# Function to read config params
def read_settings(fname):

    # Read config file
    RCFILE=os.path.expanduser("~/"+fname)
    print('Reading config file ...',RCFILE)
    SETTINGS=None
    try:
        with open(RCFILE) as json_data_file:
            SETTINGS = json.load(json_data_file)
    except:
        print(RCFILE,' not found!\n')
        s=SETTINGS_GUI(None,None)
        while not SETTINGS:
            try:
                s.win.update()
            except:
                pass
            SETTINGS=s.SETTINGS
            time.sleep(.1)
        print('Settings:',SETTINGS)
        print('Writing settings to',RCFILE,'...')
        with open(RCFILE, "w") as outfile:
            json.dump(SETTINGS, outfile)

    SETTINGS['MY_QTH']=SETTINGS['MY_CITY']+', '+SETTINGS['MY_STATE']
            
    #sys,exit(0)
    return SETTINGS,RCFILE

#########################################################################################

# Structure to contain config params
class CONFIG_PARAMS:
    def __init__(self,fname):
        self.SETTINGS,self.RCFILE=read_settings(fname)

#########################################################################################

ATTRIBUTES = ['Call','Name','State','Sec','Cat','Grid','City','County',
              'CQ Zone','ITU Zone','Prec','Check','Club','SKCC','FISTS','CWops',
              'Rig','Ant','Age','Ham Age','Occupation']

class SETTINGS_GUI():
    def __init__(self,root,P):
        self.P = P
        if P:
            self.SETTINGS=self.P.SETTINGS
        else:
            self.SETTINGS=None
        
        if root:
            self.win=Toplevel(root)
        else:
            self.win = Tk()
        self.win.title("Settings")

        row=-1
        self.boxes=[]
        for attr in ATTRIBUTES:
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
        for attr,box in zip(ATTRIBUTES,self.boxes):
            attr2='MY_'+attr.upper().replace(' ','_')
            self.SETTINGS[attr2] = box.get().upper()

        if self.P:
            self.SETTINGS['MY_QTH']=self.SETTINGS['MY_CITY']+', ' \
                +self.SETTINGS['MY_STATE']
            self.P.SETTINGS=self.SETTINGS
            print('Writing settings to',self.P.RCFILE,'...')
            print(self.P.SETTINGS)
            with open(self.P.RCFILE, "w") as outfile:
                json.dump(self.P.SETTINGS, outfile)
        
        #self.win.destroy()
        self.hide()
        print('Hey4')

    def show(self):
        print('Show Settings Window ...')
        self.win.update()
        self.win.deiconify()
        
    def hide(self):
        print('Hide Settings Window ...')
        self.win.withdraw()
