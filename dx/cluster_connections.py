################################################################################

# Cluster Connections - J.B.Attili - ?

# Functions related to connections to dx cluster.
#
# I'm not completely sure where the original for this came from.
# If you recognize this code, please email me so I can give proper attribution.

################################################################################

import time
import sys
import telnetlib
import logging
from logging import StreamHandler

READ_ALL_TXT=False
if READ_ALL_TXT:
    from .wsjt_helper import *
else:
    #import pywsjtx
    from pywsjtx.simple_server import SimpleServer 

################################################################################

# Function to define a root logger which is needed for spot_processing Classes
def get_logger(name):
    logger = logging.getLogger(name)
    console_handler = StreamHandler()
    default_formatter = logging.Formatter("[%(levelname)s] [%(asctime)s] [%(module)s]: %(message)s",\
                                          "%d/%m/%Y %H:%M:%S")
    console_handler.setFormatter(default_formatter)
    logger.addHandler(console_handler)
    logger.setLevel(logging.CRITICAL) #adjust to the level of information you want to see
    return(logger)

# Function to open telnet connection
def connection(TEST_MODE,CLUSTER,MY_CALL,fname=None,ip_addr=None,port=None):
    
    if TEST_MODE:
        #tn = open('/tmp/ALL_SPOTS.DAT', 'r')
        tn = open(fname, 'r')
    
    elif CLUSTER=='WSJT':
        if READ_ALL_TXT:
            print('Opening WSJT LOG FILE',fname,'...')
            tn = wsjt_helper(fname,10)
            tn.find_recent_spots(5.)
        else:
            print('Opening WSJT UDP Server ...')
            #tn = pywsjtx.simple_server.SimpleServer(ip_addr,port,timeout=1.0)
            tn = SimpleServer(ip_addr,port,timeout=1.0)
            
    else:
        while True:
            if CLUSTER.find(":")>0:
                host,port = CLUSTER.split(":")
            else:
                host=CLUSTER
                port=0
            print("Opening telnet connection to ",host," on port ",port)

            try:
                tn = telnetlib.Telnet(host,port,timeout=10)
            except Exception as e: 
                print(e)
                print("Cluster Connect Failed for ",CLUSTER)
                return None

            Done=False
            line=''
            ready=False
            while not Done:
                try:
                    if len(line)==0:
                        txt = tn.read_some()
                    else:
                        txt = tn.read_eager()
                except Exception as e: 
                    print(e)
                    print("Cluster Connect Failed for ",CLUSTER)
                    return None
                txt=txt.decode("utf-8") 
                #print( '===>',txt.rstrip(),txt=='')
                if txt=='':
                    if line.find("Please enter your call:")>=0 or \
                       line.find("login:")>=0:
                        Done=True
                else:
                    #print('txt=',txt)
                    for ch in txt:
                        #print('ch=',ch)
                        if ord(ch)==10 or ord(ch)==13:
                            if line:
                                print('>>>',line)
                            if line.find("All connections to this system are recorded")>=0:
                                ready=True
                                #print 'READY or not, here I come!'
                            if line.find("Please enter your call:")>=0 or \
                               line.find("login:")>=0 or \
                               (line.find("===")>=0 and ready):
                                Done=True
                                break
                            else:
                                line=''
                        else:
                            line=line+ch

            tn.write( bytes(MY_CALL+"\n",'utf-8'))              # send the callsign
            print("--- Connected to DXCluster ---")
            time.sleep(.1)
            #print("Default Settings:\n")
            tn.write( bytes("Show DX Options\n",'utf-8'))   
            time.sleep(.1)
            tn.write(bytes("Set DX Filter Skimmer AND SpotterCont = NA\n",'utf-8'))            # Enable CW Skimmer & only spots from north america
            time.sleep(.1)
            tn.write( bytes("Set DX Mode Open\n",'utf-8'))   
            time.sleep(.1)
            #print("Current Settings:\n")
            tn.write( bytes("Show DX Options\n",'utf-8'))   
            #time.sleep(.1)
            if False:
                tn.write(b"SET/DX/FILTER/SKIMMER\n")            # Enable CW Skimmer
                time.sleep(.1)
                tn.write(b"SET/FT8\n")            # Enable ft8 spots - there are a bunch of other things we can do also
                time.sleep(.1)
                tn.write(b"SET/FT4\n")            # Enable ft4 spots also
                time.sleep(.1)
                tn.write(b"SHOW/DX\n")            # Get last N spots to start populating the map
            break

    return tn

