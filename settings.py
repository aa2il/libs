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

#########################################################################################

# Function to read config params
def read_settings(fname):

    # Read config file
    print('Reading config file ...')
    RCFILE=os.path.expanduser("~/"+fname)
    SETTINGS=None
    try:
        with open(RCFILE) as json_data_file:
            SETTINGS = json.load(json_data_file)
    except:
        print(RCFILE,' not found - need call!\n')
        s=SETTINGS_GUI(None,self)
        while not SETTINGS:
            try:
                s.win.update()
            except:
                pass
            time.sleep(.01)
        print('Settings:',SETTINGS)

    #sys,exit(0)
    return SETTINGS

#########################################################################################

# Structure to contain config params
class CONFIG_PARAMS:
    def __init__(self,fname):
        self.SETTINGS=read_settings(fname)

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
            self.call.insert(0,P.MY_CALL)
        except:
            pass

        row+=1
        Label(self.win, text='My Name:').grid(row=row, column=0)
        self.name = Entry(self.win)
        self.name.grid(row=row,column=1,sticky=E+W)
        try:
            self.name.insert(0,P.MY_NAME)
        except:
            pass
        
        row+=1
        Label(self.win, text='My State:').grid(row=row, column=0)
        self.state = Entry(self.win)
        self.state.grid(row=row,column=1,sticky=E+W)
        try:
            self.state.insert(0,P.MY_STATE)
        except:
            pass
        
        row+=1
        Label(self.win, text='My Section:').grid(row=row, column=0)
        self.sec = Entry(self.win)
        self.sec.grid(row=row,column=1,sticky=E+W)
        try:
            self.sec.insert(0,P.MY_SEC)
        except:
            pass

        row+=1
        Label(self.win, text='My Grid:').grid(row=row, column=0)
        self.gridsq = Entry(self.win)
        self.gridsq.grid(row=row,column=1,sticky=E+W)
        try:
            self.gridsq.insert(0,P.MY_GRID)
        except:
            pass

        row+=1
        Label(self.win, text='My City:').grid(row=row, column=0)
        self.city = Entry(self.win)
        self.city.grid(row=row,column=1,sticky=E+W)
        try:
            self.city.insert(0,P.MY_CITY)
        except:
            pass

        row+=1
        Label(self.win, text='My County:').grid(row=row, column=0)
        self.county = Entry(self.win)
        self.county.grid(row=row,column=1,sticky=E+W)
        try:
            self.county.insert(0,P.MY_COUNTY)
        except:
            pass

        row+=1
        Label(self.win, text='My CQ Zone:').grid(row=row, column=0)
        self.cqz = Entry(self.win)
        self.cqz.grid(row=row,column=1,sticky=E+W)
        try:
            self.cqz.insert(0,P.MY_CQ_ZONE)
        except:
            pass
        
        row+=1
        Label(self.win, text='My ITU Zone:').grid(row=row, column=0)
        self.ituz = Entry(self.win)
        self.ituz.grid(row=row,column=1,sticky=E+W)
        try:
            self.ituz.insert(0,P.MY_ITU_ZONE)
        except:
            pass

        row+=1
        Label(self.win, text='My Prec:').grid(row=row, column=0)
        self.prec = Entry(self.win)
        self.prec.grid(row=row,column=1,sticky=E+W)
        try:
            self.prec.insert(0,P.MY_PREC)
        except:
            pass

        row+=1
        Label(self.win, text='My Check:').grid(row=row, column=0)
        self.check = Entry(self.win)
        self.check.grid(row=row,column=1,sticky=E+W)
        try:
            self.check.insert(0,P.MY_CHECK)
        except:
            pass
        
        row+=1
        button = Button(self.win, text="OK",command=self.Dismiss)
        button.grid(row=row,column=1,sticky=E+W)

        self.win.update()
        self.win.deiconify()
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
                           'MY_CITY'     : self.city.get().upper(), \
                           'MY_COUNTY'   : self.county.get().upper(), \
                           'MY_SEC'      : self.sec.get().upper(),    \
                           'MY_PREC'     : self.prec.get().upper(),   \
                           'MY_CHECK'    : self.check.get().upper(),  \
                           'MY_CQ_ZONE'  : self.cqz.get().upper(),    \
                           'MY_ITU_ZONE' : self.ituz.get().upper()    }
                           
        with open(self.P.RCFILE, "w") as outfile:
            json.dump(self.P.SETTINGS, outfile)
        
        print('Hey3')
        self.win.destroy()
        print('Hey4')

        