#! /usr/bin/python3
############################################################################################
#
# TK Widgets - Rev 1.1
# Copyright (C) 2021-4 by Joseph B. Attili, aa2il AT arrl DOT net
#
# Modified/augmented gui widgets
#
# To Do - does the standalone version work under python3?
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
if sys.version_info[0]==3:
    import tkinter as tk
    import tkinter.font
else:
    import Tkinter as tk
    import tkFont

from datetime import datetime,time
    
################################################################################

# LCD which responds to mouse wheel & has a call back
# Used in setclock.pu
class DigitalClock():
 
    def __init__(self,parent=None,fmt='hh:mm:ss',val=0,wheelCB=None):
        self.wheelCB = wheelCB

        self.val=val
        FONT_SIZE=48    # 120

        # Determine total number of display "digits" including spaced and decimal point
        self.nspaces = 2
        ntot    = 3*self.nspaces+2

        # Create label & bind mouse wheel events
        self.digitCount = ntot                                # Set no. of digits
        self.label = tk.Label(parent, font=('courier', FONT_SIZE, 'bold'), \
                         width=ntot,anchor='e')
        self.set(val)                                         # Display starting value
        self.label.bind("<Button-4>", self.wheelEvent)
        self.label.bind("<Button-5>", self.wheelEvent)


    # Callback for mouse wheel event
    def wheelEvent(self,event):
        #print("wheelEvent:",self.val,event.num,event.x,event.y )

        # Determine which digit the mouse was over when the wheel was spun
        x    = event.x                                    # Width of lcd widget
        ndig = self.digitCount                            # Includes spaces & dec point
        w    = self.label.winfo_width()                   # Width of the display
        edge = 0*.028*w                                     # Offset of border
        idx1 = (w-x-edge)*float(ndig) / (w-2*edge)        # Indicator of digit with mouse but...
        print('\nx=',x,'ndig=',ndig,'w=',w,'edge=',edge,'idx1=',idx1)

        # ... Need to adjust for decimal point and spaces
        for n in range(self.nspaces):
            ns = 2*(n+1)
            if idx1>ns and idx1<ns+1:
                idx1 -= 0.5                    # We're over a colon
                #print('Over',n,ns)
            elif idx1>ns+1:
                idx1 -= 1                      # We're to the left of a colon
        idx = int(idx1)                        # Finally, we can determine which digit it is
        print('idx=',idx,ndig)

        # Adjust step size based on digit 
        self.step = pow(10,idx)
        if event.num == 5:
            delta = -1
        if event.num == 4:
            delta = 1

        # Display new value
        #print('val in=',self.val)
        val=self.val.replace(':','')
        #xx = str( int(val) + self.step*delta ).zfill(6)
        xx = int(val) + self.step*delta
        #print('xx1=',xx)
        if xx<0:
            xx+=240000
        #print('xx2=',xx)
        xx = str( xx ).zfill(6)
        print('val=',self.val,int(val),'\tstep=',self.step,'\tdelta=',delta,'\txx=',xx)
        
        h=int(xx[0:2])
        m=int(xx[2:4])
        s=int(xx[4:])
        print('h m s=',h,m,s)
        if s>80:
            s-=99-59
        elif s>=60:
            s-=60
            m+=1
        if m>80:
            m-=99-59
        elif m>=60:
            m-=60
            h+=1
        #if h>80:
        #    h-=99-23
        if h>=24:
            h-=24
        newval = time(h,m,s).strftime("%H:%M:%S")
        print('xx=',xx,'\tnewval=',newval)
        self.set(newval)

        # Do additional work if necessary
        if self.wheelCB:
            self.wheelCB(xx)


    # Function to set LCD display value
    def set(self,t):
        if t!=None:
            self.val=t
            #self.display(format(self.val,self.fmt))
            self.label['text'] = self.val
            #self.label['text'] = format(self.val,self.fmt)
            #print('val=',t)


    # Function to get LCD display value
    def get(self):
        return self.val

################################################################################

# LCD which responds to mouse wheel & has a call back
class MyLCDNumber():
 
    def __init__(self,parent=None,ndigits=7,nfrac=1,signed=False,leading=False,val=0,wheelCB=None):
        self.wheelCB = wheelCB

        self.val=val
        FONT_SIZE=48    # 120

        # Determine total number of display "digits" including spaced and decimal point
        self.signed  = signed
        self.nfrac   = nfrac                                  # No. fractional position to right of decima
        self.nspaces = int( (ndigits-1)/3 )                   # No. spaces
        if self.nfrac>0:
            self.nspaces += 1
        ntot    = ndigits + self.nspaces + self.nfrac         # Total no. display digits
        if signed:
            ntot+=1
            
        if self.nfrac>0:
            self.fmt = str(ntot-1)+',.'+str(nfrac)+'f'            # Format spec for displaying value
        else:
            self.fmt = str(ntot)+',.'+str(nfrac)+'f'              # Format spec for displaying value
            
        if leading:
            self.fmt = '0'+self.fmt
        if signed:
            # This should cause plus signs but it doesn't
            self.fmt = '+'+self.fmt
        self.max_val = pow(10.,ndigits)-pow(10.,-nfrac)       # Maximum value
        if signed:
            self.min_val = -self.max_val
        else:
            self.min_val = 0
        #self.sc   = 1./120.                                   # Wheel scaling factor
        #print ndigits,self.nfrac,self.nspaces,ntot
        #print('fmt=',self.fmt)

        # Create label & bind mouse wheel events
        self.digitCount = ntot                                # Set no. of digits
        self.label = tk.Label(parent, font=('courier', FONT_SIZE, 'bold'), \
                         width=ntot,anchor='e')
        #self.label.pack(padx=40, pady=40)
        #self.label.pack()
        self.set(val)                                         # Display starting value
        #self.setFocusPolicy(Qt.StrongFocus)
        self.label.bind("<Button-4>", self.wheelEvent)
        self.label.bind("<Button-5>", self.wheelEvent)


    # Callback for mouse wheel event
    def wheelEvent(self,event):
        #print("wheelEvent:",self.val,event.num,event.x,event.y )

        if False:
            if event.num == 5 or event.delta == -120:
                self.val -= 1
            if event.num == 4 or event.delta == 120:
                self.val += 1
            self.set( self.val )
            return

        # Determine which digit the mouse was over when the wheel was spun
        x    = event.x                                    # Width of lcd widget
        ndig = self.digitCount                            # Includes spaces & dec point
        w    = self.label.winfo_width()                   # Width of the display
        edge = 0*.028*w                                     # Offset of border
        idx1 = (w-x-edge)*float(ndig) / (w-2*edge)        # Indicator of digit with mouse but...
        #print('x=',x,'ndig=',ndig,'w=',w,'edge=',edge,'idx1=',idx1)

        # ... Need to adjust for decimal point and spaces
        for n in range(self.nspaces):
            ns = 3*n+self.nfrac
            if idx1>ns and idx1<ns+1:
                idx1 -= 0.5                    # We're over a space or decimal point
            elif idx1>ns+1:
                idx1 -= 1                      # We're to the left of a space or decimal point 
        idx = int(idx1)                        # Finally, we can determine which digit it is
        #print('idx=',idx,ndig)
        if self.signed and idx>=ndig-1:
            idx-=1

        # Adjust step size based on digit 
        self.step = pow(10,idx-self.nfrac)
        if event.num == 5:
            delta = -1
        if event.num == 4:
            delta = 1

        # Display new value
        xx = self.val + self.step*delta
        #print(self.val,self.step,event.num,event.delta)
        #print '---',idx1,idx,xx,self.max_val
        self.set(xx)

        # Do additional work if necessary
        if self.wheelCB:
            self.wheelCB(xx)


    # Function to set LCD display value
    def set(self,f):
        if f!=None:
            self.val=min(max(f,self.min_val),self.max_val)
            #self.display(format(self.val,self.fmt))
            #self.label['text'] = self.val
            self.label['text'] = format(self.val,self.fmt)


    # Function to get LCD display value
    def get(self):
        return self.val

################################################################################

class StatusBar(tk.Frame):
    def __init__(self, master, fg_color='Black',bg_color=None,relief=tk.RIDGE):
        tk.Frame.__init__(self, master, background = bg_color,relief=relief,borderwidth=2)

        self.root=master
         
        self.label = tk.Label(self, text = "", fg = fg_color, bg = bg_color)
        self.label.pack(side = tk.LEFT)
        #self.pack(fill=tk.X, side = tk.BOTTOM)
     
    def setText(self, newText):
        self.label.config(text = newText)
        #self.root.update_idletasks()
        self.root.update()
 
    def clearText(self):
        self.label.config(text = "")
        #self.root.update_idletasks()

################################################################################

# Test program
if __name__ == '__main__':
    
    # Original more or less - uses "pack" geo mgr
    class Window:   
        def __init__(self, master):
            self.frame = tk.Frame(master)
            b1 = tk.Button(self.frame, text="Button 1", command=self.handleButtonOne)
            b1.pack(padx=30, pady=20)
         
            b2 = tk.Button(self.frame, text="Button 2", command=self.handleButtonTwo)
            b2.pack(padx=30, pady=20)
            
            #self.status_bar = StatusBar(self.frame, 'white',"blue")
            self.status_bar = StatusBar(self.frame)
            self.status_bar.pack(fill=tk.X, side = tk.BOTTOM)
            self.frame.pack(expand = True, fill = tk.BOTH)
 
        def handleButtonOne(self):
            self.status_bar.setText("Button 1 was Clicked")
 
        def handleButtonTwo(self):
            self.status_bar.setText("Button 2 was Clicked")


    # Simpler - no frame and uses grid geo mgr
    class Window2:   
        def __init__(self, master):
            b1 = tk.Button(master, text="Button 1", command=self.handleButtonOne)
            b1.grid(row=1,column=0)
         
            b2 = tk.Button(master, text="Button 2", command=self.handleButtonTwo)
            b2.grid(row=2,column=0)
 
            #self.status_bar = StatusBar(self.frame, 'white',"blue")
            self.status_bar = StatusBar(master)
            self.status_bar.grid(row=3,column=0)
 
        def handleButtonOne(self):
            self.status_bar.setText("Button 1 was Clicked")
 
        def handleButtonTwo(self):
            self.status_bar.setText("Button 2 was Clicked")
 
    # Main
    root = tk.Tk()
    root.title('turn mouse wheel')
    root['bg'] = 'darkgreen'

    if 0:
        # LCD demo
        lcd=MyLCDNumber(root)
        lcd.label.pack()
    elif 1:
        # Status Bar demo
        #window = Window(root)
        window = Window2(root)
    else:
        # Clock demo
        lcd=DigitalClock(root)
        lcd.label.pack()
        now = datetime.now().strftime("%H:%M:%S")
        print('now=',now)
        lcd.set(now)
    
    root.mainloop()

    
