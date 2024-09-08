############################################################################
#
# widgets_qt.py - Rev 1.0
# Copyright (C) 2021-4 by Joseph B. Attili, aa2il AT arrl DOT net
#
# Modified/augmented gui qt widgets
#
############################################################################
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
############################################################################

try:
    from PySide6.QtWidgets import QLCDNumber,QLabel,QSplashScreen,QRadioButton
    from PySide6.QtCore import * 
    from PySide6.QtGui import QPixmap
except ImportError:
    # use Qt5
    from PyQt5.QtWidgets import QLCDNumber,QLabel,QSplashScreen,QRadioButton
    from PyQt5.QtCore import * 
    from PyQt5.QtGui import QPixmap

################################################################################

# LCD which responds to mouse wheel & has a call back
class MyLCDNumber(QLCDNumber):
 
    def __init__(self,parent=None,ndigits=7,nfrac=1,signed=False,leading=False,ival=0,wheelCB=None):
        QLCDNumber.__init__(self,parent)
        self.wheelCB = wheelCB

        # Init
        self.setSegmentStyle(QLCDNumber.Filled)    
        #self.setSegmentStyle(QLCDNumber.Flat)        # Bolder
        self.setStyleSheet("""QLCDNumber { 
        color: black; }""")

        # Determine total number of display "digits" including spaced and decimal point
        self.signed  = signed
        self.nfrac   = nfrac                                  # No. fractional position to right of decima
        self.nspaces = int( (ndigits-1)/3 )                   # No. spaces
        if self.nfrac>0:
            self.nspaces += 1
        ntot    = ndigits + self.nspaces + self.nfrac         # Total no. display digits
        if signed:
            ntot+=1
            
        #self.fmt = '0'+str(ntot-1)+',.1f'                    # Format spec for displaying value w/ leading zeros
        #self.fmt = str(ntot-1)+',.1f'                        # Format spec for displaying value - hardwired for nfrac=1
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
        self.sc   = 1./120.                                   # Wheel scaling factor
        #print ndigits,self.nfrac,self.nspaces,ntot
        #print('fmt=',self.fmt)
        
        self.setDigitCount(ntot)                              # Set no. of digits
        self.set(ival)                                        # Display starting value
        self.setFocusPolicy(Qt.StrongFocus)

    # Override some of the event handlers - see docs for QWidget to see what's available
    
    # Callback for mouse wheel event
    def wheelEvent(self,event):
        #print("wheelEvent:",self.val,event.pos())

        # If no callback is defined, don't allow user to adjust the digitis
        if not self.wheelCB:
            return

        # Determine which digit the mouse was over when the wheel was spun
        x = event.x()                    # Width of lcd widget
        ndig = self.digitCount()         # Includes spaces & dec point
        w    = self.width()              # Width of the display
        edge = .028*w                    # Offset of border
        idx1  = (w-x-edge)*float(ndig) / (w-2*edge)        # Indicator of digit with mouse but...

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
        self.step = pow(10,idx-self.nfrac)*self.sc

        # Display new value
        xx = self.val + self.step*event.angleDelta().y()
        #print '---',idx1,idx,xx,self.max_val
        self.set(xx)

        # Do additional work if necessary
        if self.wheelCB:
            self.wheelCB(xx)

    # Function to set LCD display value
    def set(self,f):
        if f!=None:
            self.val=min(max(f,self.min_val),self.max_val)
            self.display(format(self.val,self.fmt))

    # Function to get LCD display value
    def get(self):
        return self.val

################################################################################

# Splash screen
class SPLASH_SCREEN():
    def __init__(self,app,fname):

        self.splash = QSplashScreen(QPixmap(fname))
        self.splash.show()
        self.status_bar = StatusBar(self.splash,-1)
        #time.sleep(.1)
        app.processEvents()

    def destroy(self):
        self.splash.destroy()
        
################################################################################

# Status Bar
class StatusBar():
    def __init__(self,root,nrows):

        if nrows<0:
            # For a splash screen
            self.label = root
            self.splish_splash = True
            self.setText("Howdy Ho!")
        else:
            # Normal QT gui
            print('Normal satus bar ...')
            self.label = QLabel("Howdy Ho!")
            root.grid.addWidget(self.label,nrows,0)
            self.splish_splash = False
     
    def setText(self, newText):
        if self.splish_splash:
            self.label.showMessage(newText,alignment=Qt.AlignBottom)
        else:
            self.label.setText(newText)
        #self.root.update()
 
    def clearText(self):
        self.label.setText("")
        #self.label.config(text = "")
        #self.root.update()
        pass

################################################################################

# LED-like indicator
class LED(QRadioButton):
    def __init__(self,txt='',color=None,parent=None):
        QRadioButton.__init__(self,txt,parent)
        if color:
            self.setColor(color)
        
    def setColor(self,color):
        self.setStyleSheet("QRadioButton::indicator:unchecked {"
                           "background-color: "+color+";"  
                           "border: 2px solid gray; "
                           "border-radius: 10px; "
                           "}")

        
