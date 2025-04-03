############################################################################
#
# conversions.py - Rev 1.0
# Copyright (C) 2021-5 by Joseph B. Attili, joe DOT aa2il AT gmail DOT com
#
# Number and format conversions.
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

# Function to convert frequency (MHz) to nominald band
def freq2band(frq):

    if frq<0:
        band=None
    elif frq<1.7:
        band='MW'
    elif frq<3:
        band='160m'
    elif frq<5:
        band='80m'
    elif frq<6:
        band='60m'
    elif frq<9:
        band='40m'
    elif frq<12:
        band='30m'
    elif frq<16:
        band='20m'
    elif frq<20:
        band='17m'
    elif frq<23:
        band='15m'
    elif frq<27:
        band='12m'
    elif frq<40:
        band='10m'
    elif frq<60:
        band='6m'
    elif frq<144:
        band='AIR'
    elif frq<200:
        band='2m'
    elif frq<300:
        band='1.25m'
    elif frq<500:
        band='70cm'
    elif frq<1000:
        band='33cm'
    elif frq<1500:
        band='23cgm'
    else:
        band='70cm'
        print('FREQ2BAND: frq=',frq,'\tband=',band)
            
    return band

############################################################################

# Function to convert a list of BCD hex values to an integer
def bcd2int(x,ireverse=0):

    mult= 1
    val = 0
    if ireverse:
        #x.reverse()
        x=x[::-1];
    for xx in x:
        xxx = xx.replace('0x','')
        val  += mult*int(xxx)
        mult *= 100

    return val

############################################################################

# Function to convert an integer to a list of BCD hex values
def int2bcd(x,n,ireverse=0):

    y=str(int(x)).zfill(2*n)
    if ireverse==0:
        #y.reverse()
        y=y[::-1];
    bcd=[]
    for i in range(n):
        i2 = 2*i
        yy = y[i2:(i2+2)]
        bcd.append(int(yy,16))

    return bcd

############################################################################

# Function to return hex values of a list of bytes
def show_hex(x):
    if isinstance(x, str):
        return [hex(ord(c)) for c in x]
    else:
        return [hex(c) for c in x]            

# Function to return ascii values of a list of bytes
def show_ascii(x):
    return [ord(c) for c in x]


