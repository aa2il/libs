############################################################################################

# Util.py - J.B.Attili - 2019

# This module contains utilities used to command the radio

from subprocess import check_output, CalledProcessError
#import sys

############################################################################################

# Function to convert a freq in KHz to a ham band
def convert_freq2band(freqs,STRING=False):

    if not isinstance(freqs, list):
        freqs=[freqs]
        bands=0
    else:
        bands=[]
        
    for frq in freqs:
        if frq<3000:
            band=160
        elif frq<5000:
            band=80
        elif frq<6000:
            band=60
        elif frq<9000:
            band=40
        elif frq<12000:
            band=30
        elif frq<16000:
            band=20
        elif frq<20000:
            band=17
        elif frq<23000:
            band=15
        elif frq<27000:
            band=12
        elif frq<40000:
            band=10
        elif frq<100000:
            band=6
        else:
            band=2

        if STRING:
            band = str(band)+'m'
            
        if isinstance(bands, list):
            bands.append( band )
        else:
            bands=band

    return bands


# Routine to get PID of a process by name
def get_PIDs(name):
    try:
        pidlist = list(map(int, check_output(["pidof", name]).split()))
    except  CalledProcessError:
        pidlist = []

    #print 'list of PIDs = ' + ', '.join(str(e) for e in pidlist)
    return pidlist

