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
from dx.cluster_connections import get_logger
from dx.spot_processing import Station
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
            time.sleep(.01)
        print('Settings:',SETTINGS)

    #sys,exit(0)
    return SETTINGS,RCFILE

#########################################################################################

# Structure to contain config params
class CONFIG_PARAMS:
    def __init__(self,fname):
        self.SETTINGS,self.RCFILE=read_settings(fname)

#########################################################################################

class SETTINGS_GUI():
    def __init__(self,root,P):
        self.P = P
        
        if root:
            self.win=Toplevel(root)
        else:
            self.win = Tk()
        self.win.title("Settings")

        row=0
        Label(self.win, text='My Call:').grid(row=row, column=0)
        self.call = Entry(self.win)
        self.call.grid(row=row,column=1,sticky=E+W)
        #self.call.delete(0, END)
        try:
            self.call.insert(0,P.SETTINGS['MY_CALL'])
        except:
            pass

        row+=1
        Label(self.win, text='My Name:').grid(row=row, column=0)
        self.name = Entry(self.win)
        self.name.grid(row=row,column=1,sticky=E+W)
        try:
            self.name.insert(0,P.SETTINGS['MY_NAME'])
        except:
            pass
        
        row+=1
        Label(self.win, text='My State:').grid(row=row, column=0)
        self.state = Entry(self.win)
        self.state.grid(row=row,column=1,sticky=E+W)
        try:
            self.state.insert(0,P.SETTINGS['MY_STATE'])
        except:
            pass
        
        row+=1
        Label(self.win, text='My Section:').grid(row=row, column=0)
        self.sec = Entry(self.win)
        self.sec.grid(row=row,column=1,sticky=E+W)
        try:
            self.sec.insert(0,P.SETTINGS['MY_SEC'])
        except:
            pass

        row+=1
        Label(self.win, text='My Category:').grid(row=row, column=0)
        self.cat = Entry(self.win)
        self.cat.grid(row=row,column=1,sticky=E+W)
        try:
            self.cat.insert(0,P.SETTINGS['MY_CAT'])
        except:
            pass

        row+=1
        Label(self.win, text='My Grid:').grid(row=row, column=0)
        self.gridsq = Entry(self.win)
        self.gridsq.grid(row=row,column=1,sticky=E+W)
        try:
            self.gridsq.insert(0,P.SETTINGS['MY_GRID'])
        except:
            pass

        row+=1
        Label(self.win, text='My City:').grid(row=row, column=0)
        self.city = Entry(self.win)
        self.city.grid(row=row,column=1,sticky=E+W)
        try:
            self.city.insert(0,P.SETTINGS['MY_CITY'])
        except:
            pass

        row+=1
        Label(self.win, text='My County:').grid(row=row, column=0)
        self.county = Entry(self.win)
        self.county.grid(row=row,column=1,sticky=E+W)
        try:
            self.county.insert(0,P.SETTINGS['MY_COUNTY'])
        except:
            pass

        row+=1
        Label(self.win, text='My CQ Zone:').grid(row=row, column=0)
        self.cqz = Entry(self.win)
        self.cqz.grid(row=row,column=1,sticky=E+W)
        try:
            self.cqz.insert(0,P.SETTINGS['MY_CQ_ZONE'])
        except:
            pass
        
        row+=1
        Label(self.win, text='My ITU Zone:').grid(row=row, column=0)
        self.ituz = Entry(self.win)
        self.ituz.grid(row=row,column=1,sticky=E+W)
        try:
            self.ituz.insert(0,P.SETTINGS['MY_ITU_ZONE'])
        except:
            pass

        row+=1
        Label(self.win, text='My Prec:').grid(row=row, column=0)
        self.prec = Entry(self.win)
        self.prec.grid(row=row,column=1,sticky=E+W)
        try:
            self.prec.insert(0,P.SETTINGS['MY_PREC'])
        except:
            pass

        row+=1
        Label(self.win, text='My Check:').grid(row=row, column=0)
        self.check = Entry(self.win)
        self.check.grid(row=row,column=1,sticky=E+W)
        try:
            self.check.insert(0,P.SETTINGS['MY_CHECK'])
        except:
            pass
        
        row+=1
        Label(self.win, text='My SKCC No.:').grid(row=row, column=0)
        self.skcc = Entry(self.win)
        self.skcc.grid(row=row,column=1,sticky=E+W)
        try:
            self.skcc.insert(0,P.SETTINGS['MY_SKCC'])
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
        print('Hey2')

    # Cant seem to get this to work :-(
    def call_changed(self):
        print('Call change:')
        call=self.call.get()
        print('Call change:',call)
        #station = Station(call)
        #print(station)
        #pprint(vars(station))

    def Dismiss(self):
        self.P.SETTINGS = {'MY_CALL'     : self.call.get().upper(),   \
                           'MY_NAME'     : self.name.get().upper(),   \
                           'MY_STATE'    : self.state.get().upper(),  \
                           'MY_GRID'     : self.gridsq.get().upper(), \
                           'MY_CITY'     : self.city.get().upper(),   \
                           'MY_COUNTY'   : self.county.get().upper(), \
                           'MY_SEC'      : self.sec.get().upper(),    \
                           'MY_CAT'      : self.cat.get().upper(),    \
                           'MY_PREC'     : self.prec.get().upper(),   \
                           'MY_CHECK'    : self.check.get().upper(),  \
                           'MY_CQ_ZONE'  : self.cqz.get().upper(),    \
                           'MY_ITU_ZONE' : self.ituz.get().upper(),   \
                           'MY_SKCC'     : self.ituz.get().upper()    }
                           
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
