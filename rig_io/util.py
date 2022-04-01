############################################################################################

# Util.py - J.B.Attili - 2019

# This module contains utilities used to command the radio

from subprocess import check_output, CalledProcessError
import sys
import platform

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
    if platform.system()=='Linux':
        try:
            pidlist = list(map(int, check_output(["pidof", name]).split()))
        except  CalledProcessError:
            pidlist = []
    elif platform.system()=='Windows':
        #name='chrome'
        name=name+'.exe'
        #print('GET_PIDs: Windoz')
        cmd='tasklist /fi "imagename eq '+name
        #print('GET_PIDs: cmd=',cmd)
        result = check_output(cmd).decode()
        #print('GET_PIDs: result=',result)
        result2=result.strip().split('\r\n')
        #print('GET_PIDs: result2=',result2)
        #print(len(result2))
        pidlist = []
        for line in result2:
            if name in line:
                #print(line)
                a=line.split()
                #print(a)
                pidlist.append(int(a[1]))
        #sys.exit(0)
    else:
        print('GET_PIDs: Unknown OS',platform.system())
        sys.exit(0)

    #print('GET_PISD: List of PIDs = ',pidlist)
    #sys.exit(0)
    return pidlist

"""
 In windoz, use wmic:
 C:\>wmic process where "name='chrome.exe'" get ProcessID, ExecutablePath

 In Linux, can also use    pgrep flrig

def process_exists(process_name):
    call="TASKLIST", '/FI', 'imagename eq %s' % process_name
    # use buildin check_output right away
    output = subprocess.check_output(call).decode()
    # check in last line for process name
    last_line = output.strip().split('\r\n')[-1]
    # because Fail message could be translated
    return last_line.lower().startswith(process_name.lower())

>>> import platform
>>> platform.system()
'Linux'
'Windows' or
'Darwin'   (Mac)

"""
