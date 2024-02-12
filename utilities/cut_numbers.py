############################################################################
#
# cut_numbers.py - Rev 1.0
# Copyright (C) 2021-4 by Joseph B. Attili, aa2il AT arrl DOT net
#
# Functions related to cut numbers.
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

import sys
import os
import numpy as np
import time

from subprocess import check_output, CalledProcessError
import platform
import socket

import serial.tools.list_ports as lp
from pprint import pprint
import platform

############################################################################

VERBOSITY=0

############################################################################

def cut_numbers(n,ndigits=-3,ALL=False):

    if VERBOSITY>0:
        print('CUT_NUMBERS:',n,ndigits,ALL)

    n=int(n)

    if n<0:
        print('CUT_NUMBERS - ERROR - Positive number only duffess',n)
        return str(n)

    if False:
    
        if n<10:
            txt = 'TT'+'{:,d}'.format(n)
        elif n<100:
            txt = 'T'+'{:,d}'.format(n)
        else:
            txt = '{:,d}'.format(n)

    elif ALL:

        nn=str(n)
        txt=''
        for i in range(len(nn)):
            d=nn[i]
            if d=='0':
                d='T'
            elif d=='1':
                d='A'
            elif d=='9':
                d='N'
            txt=txt+d

        while len(txt)<ndigits:
            txt = 'T'+txt
            
        return txt

    else:
        #if ndigits<0:
        #    ndigits=-ndigits
        if True:
            if n>9 and n<100 and n!=73 and n!=88:
                ndigits=2
        
        txt = '{:d}'.format(n)
        if VERBOSITY>0:
            print('CUT NUMBERS B4: n=',n,'\tndigits=',ndigits,'\ttxt=',txt,'\tlen=',len(txt))
        while len(txt)<ndigits:
            txt = 'T'+txt
        if VERBOSITY>0:
            print('CUT NUMBERS AFTER: n=',n,'\tndigits=',ndigits,'\ttxt=',txt,'\tlen=',len(txt))
        
    return txt
    

# Routine to replace cut numbers with their numerical equivalents
def reverse_cut_numbers(x,n=0):
    x=x.upper()
    x=x.replace('T','0')
    x=x.replace('O','0')
    x=x.replace('A','1')
    x=x.replace('E','5')
    x=x.replace('N','9')

    # Strip leading 0's
    #print(n,int(x),str(int(x)).zfill(n))
    try:
        if n:
            out = str(int(x)).zfill(n)
        else:
            out = str(int(x))
    except:
        out = x

    return out


