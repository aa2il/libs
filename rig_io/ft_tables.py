############################################################################################
#
# FT Tables - Rev 1.0
# Copyright (C) 2021-5 by Joseph B. Attili, joe DOT aa2il AT gmail DOT com
#
# Tables defining various operating parameters and capabilities
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

from collections import OrderedDict
import os
import sys
import csv
import numpy as np
from counties import COUNTIES

############################################################################################

VERBOSITY=0

############################################################################################

#DATA_DIR = '~/Python/data'
#PRESETS_FNAME = os.path.expanduser(DATA_DIR + '/presets.xls')

# Local hardware/network etc.
# HOST = 'localhost'
HOST        = '127.0.0.1'       # Everything will run on localhost
KEYER_PORT  = 7389              # Arbitrary non-privileged port

# Ports for FTdx3000
SERIAL_PORT1 = '/dev/serial/by-id/usb-Silicon_Labs_CP2105_Dual_USB_to_UART_Bridge_Controller_AH046H3M120067-if00-port0'
SERIAL_PORT2 = '/dev/serial/by-id/usb-Silicon_Labs_CP2105_Dual_USB_to_UART_Bridge_Controller_AH046H3M120067-if01-port0'

# Ports for FT-991a
SERIAL_PORT3 = '/dev/serial/by-id/usb-Silicon_Labs_CP2105_Dual_USB_to_UART_Bridge_Controller_00A50791-if00-port0'
SERIAL_PORT4 = '/dev/serial/by-id/usb-Silicon_Labs_CP2105_Dual_USB_to_UART_Bridge_Controller_00A50791-if01-port0'

# Ports for TS850 - the serial number of the FTDI chip changes if we don't
# turn off auto gen serial number when programming the device
SERIAL_PORT5 = '/dev/serial/by-id/usb-FTDI_FT232R_USB_UART_TS850-if00-port0'
SERIAL_PORT6 = '/dev/serial/by-id/usb-RT_Systems_CT-69_Radio_Cable_RTWC054-if00-port0'

# Port for ICOM 706 MKII
SERIAL_PORT7 = '/dev/serial/by-id/usb-FTDI_FT232R_USB_UART_AK06USTH-if00-port0'

# Ports for ICOM 9700 - these are rig-dependent so eventually, we need to come up with a scheme to
# detect anything that satifies base description
SERIAL_PORT9  = '/dev/serial/by-id/usb-Silicon_Labs_CP2102N_USB_to_UART_Bridge_Controller_IC-9700_12007709_A-if00-port0'
SERIAL_PORT10 = '/dev/serial/by-id/usb-Silicon_Labs_CP2102N_USB_to_UART_Bridge_Controller_IC-9700_12007709_B-if00-port0'

# Port for Nano IO keyer interface
SERIAL_NANO_IO = '/dev/serial/by-id/usb-1a86_USB2.0-Ser_-if00-port0'

# Ports for Yaesu Rotor
SERIAL_ROTOR = '/dev/serial/by-id/usb-Arduino__www.arduino.cc__0043_55338343639351B042A1-if00'
SERIAL_ROTOR = '/dev/ttyACM0'

BAUD = 38400

HAMLIB_PORT = 4532         

FLDIGI_HOST = '127.0.0.1'
FLDIGI_PORT = 7362

DELAY=.1

DEFAULT_PORTS = OrderedDict()
DEFAULT_PORTS["HAMLIB"] = {'KEYER'   : 4540,
                           'ROTOR'   : 4533,
                           'BANDMAP' : 4532 }

CONNECTIONS = ['FLDIGI','FLRIG','DIRECT','HAMLIB','DUMMY','KCAT','ANY']
RIGS        = ['FTdx3000','FT991a','IC9700','IC7300','TS850','IC706','TYT9000d','KC505']
ACCESSORIES = ['nanoIO']
SAT_RIGS    = ['FT991a','IC9700','pySDR']

############################################################################################

HF_BANDS = ['160m','80m','60m','40m','30m','20m','17m','15m','12m','10m']
CONTEST_BANDS = ['160m','80m','40m','20m','15m','10m']
NON_CONTEST_BANDS = ['60m','30m','17m','12m']
VHF_BANDS = ['6m','2m','1.25m','70cm','33cm','23cm']
ALL_BANDS = CONTEST_BANDS + NON_CONTEST_BANDS + VHF_BANDS

LOWER48 = ['AL','AR','AZ','CA','CO','CT','DE','FL','GA', \
           'ID','IL','IN','IA','KS','KY','LA','ME','MA','MD','MI','MS', \
           'MN','MO','MT','NC','NE','NH','NV','NY','ND','NJ','NM', \
           'OH','OK','OR','PA','RI','SC','SD','TN','TX','UT','VT', \
           'VA','WA','WV','WI','WY']
STATES  = LOWER48 + ['AK','HI']

# 13 Colonies SE stations
THIRTEEN_COLONIES=['K2A','K2B','K2C','K2D','K2E','K2F','K2G','K2H','K2I','K2J','K2K',
                   'K2L','K2M','WM3PEN','GB13COL','TM13COL']

# Canadian provinces/territories: 
# NS ((VE1, VA1, CY9, CYØ),         QC (VE2 VA2),
# ON (VE3 VA3),    MB (VE4 VA4),    SK (VE5 VA5),
# AB (VE6 VA6),    BC (VE7 VA7),    NWT (VE8),
# NB (VE9),        NF & LB (VO1 and VO2),
# NU (VY0),        YT (VY1), PEI (VY2)

PROVINCES1 = ['NB', 'NS', 'BC','AB','SK','MB','ON', 'QC', 'NWT', 'NF', 'LB', 'NU', 'YT', 'PEI']
PROVINCES2 = ['NB', 'NS', 'BC','AB','SK','MB','ON', 'QC', 'NT', 'NL', 'NU', 'YT', 'PE']
PROVINCES3 = ['NB', 'NS', 'BC','AB','SK','MB','ON', 'QC', 'NT', 'NF', 'LB', 'NU', 'YT', 'PE']

# Mexican states
XE_STATES=['AGS','BAC','BCS','CAM','CHI','CHH','CMX','COA','COL','DGO','EMX','GTO','GRO','HGO', \
           'JAL','MIC','MOR','NAY','NLE','OAX','PUE','QRO','QUI','SLP','SIN','SON','TAB','TAM',	\
           'TLX','VER','YUC','ZAC']

NA_COUNTRIES=['AK','PR','ZF','VI','HI','XE','V3','TI','8P','DX','KP4','HR','CY9','HP','KP2','HH','DR','CM','J8','VP5','6Y','HI6']
NAQP_SECS = STATES + PROVINCES2 + NA_COUNTRIES + ['DC']
SST_SECS  = STATES + PROVINCES2  + ['CWA','DX','AUS','NT','DC','PR']
CQ_STATES = LOWER48 + PROVINCES2 + ['DC']

FTRU_SECS = LOWER48 + PROVINCES1 + ['DC']
RTTYRU_SECS = LOWER48 + PROVINCES2 + ['DC']
TEN_METER_SECS = STATES + PROVINCES3 + XE_STATES + ['DC']

ARRL_SECS = ['CT','EMA','ME','NH','RI','VT','WMA',  \
             'ENY','NLI','NNJ','NNY','SNJ','WNY',  \
             'DE','EPA','MDC','WPA', \
             'AL','GA','KY','NC','NFL','SC','SFL','WCF','TN','VA','PR','VI', \
             'AR','LA','MS','NM','NTX','OK','STX','WTX', \
             'EB','LAX','ORG','SB','SCV','SDG','SF','SJV','SV','PAC', \
             'AZ','EWA','ID','MT','NV','OR','UT','WWA','WY','AK', \
             'MI','OH','WV','IL','IN','WI', \
             'CO','IA','KS','MN','MO','NE','ND','SD', \
             'NS','NB','NL','QC','ONE','ONN','ONS','GH','MB','SK','AB','BC','TER','PE']  # As of 2023
#             'MAR','NL','QC','ONE','ONN','ONS','GTA','MB','SK','AB','BC','NT','PE']     # Prior to 2023

FD_SECS = ARRL_SECS + ['DX']

# Use COUNTIES['CA'] for this now
#CA_COUNTIES = ['ALAM', 'MARN', 'SMAT', 'ALPI', 'MARP', 'SBAR', 'AMAD', 'MEND', 'SCLA', 'BUTT', 'MERC', 'SCRU', \
#               'CALA', 'MODO', 'SHAS', 'COLU', 'MONO', 'SIER', 'CCOS', 'MONT', 'SISK', 'DELN', 'NAPA', 'SOLA', \
#               'ELDO', 'NEVA', 'SONO', 'FRES', 'ORAN', 'STAN', 'GLEN', 'PLAC', 'SUTT', 'HUMB', 'PLUM', 'TEHA', \
#               'IMPE', 'RIVE', 'TRIN', 'INYO', 'SACR', 'TULA', 'KERN', 'SBEN', 'TUOL', 'KING', 'SBER', 'VENT', \
#               'LAKE', 'SDIE', 'YOLO', 'LASS', 'SFRA', 'YUBA', 'LANG', 'SJOA', 'MADE', 'SLUI']

#CQP_VE_CALL_AREAS =   ['MR','QC','ON','MB','SK','AB','BC','NT']    # B4 2023
#CQP_MULTS  = STATES + CQP_VE_CALL_AREAS
#CQP_STATES = STATES + PROVINCES + CA_COUNTIES + ['MR','NT']
CQP_MULTS  = STATES + PROVINCES2
CQP_STATES = STATES + PROVINCES2 + COUNTIES['CA']
CQP_COUNTRIES=['United States','Canada','Alaska','Hawaii'] 

CQ_ZONES = {'CT' : 5 , \
            'ME' : 5 , \
            'MA' : 5 , \
            'NH' : 5 , \
            'RI' : 5 , \
            'VT' : 5 , \
            'NJ' : 5 , \
            'NY' : 5 , \
            'DE' : 5 , \
            'MD' : 5 , \
            'PA' : 5 , \
            'AL' : 4 , \
            'FL' : 5 , \
            'GA' : 5 , \
            'KY' : 4 , \
            'NC' : 5 , \
            'SC' : 5 , \
            'TN' : 4 , \
            'VA' : 5 , \
            'AR' : 4 , \
            'LA' : 4 , \
            'MS' : 4 , \
            'NM' : 4 , \
            'OK' : 4 , \
            'TX' : 4 , \
            'CA' : 3 , \
            'HI' : 31 , \
            'AK' : 1 , \
            'AZ' : 3 , \
            'ID' : 3 , \
            'MT' : 4 , \
            'NV' : 3 , \
            'OR' : 3 , \
            'UT' : 3 , \
            'WA' : 3 , \
            'WY' : 4 , \
            'MI' : 4 , \
            'OH' : 4 , \
            'WV' : 5 , \
            'IL' : 4 , \
            'IN' : 4 , \
            'WI' : 4 , \
            'CO' : 4 , \
            'IA' : 4 , \
            'KS' : 4 , \
            'MN' : 4 , \
            'MO' : 4 , \
            'NE' : 4 , \
            'ND' : 4 , \
            'SD' : 4 , \
            'NS' : 5 , \
            'QC' : [2,5] , \
            'ON' : [2,4,5] , \
            'MB' : 4 , \
            'SK' : 4 , \
            'AB' : 4 , \
            'BC' : 3 , \
            'NT' : 1 , \
            'NB' : 5 , \
            'NL' : 5 , \
            'NL' : 2 , \
            'YT' : 1 , \
            'PE' : 5 , \
            'NU' : 2 }

# This is here as both pySat and pyKeyer.py reference it.
# Need the 'None' entry for list box in pyKeyer
# IO-86 never gets above the horizon in our part of the world
SATELLITE_LIST = ['None','ISS','PO-101','SO-50', \
                  'AO-123','AO-73','AO-91','RS-44', \
                  'AO-7','JO-97','UVSQ-SAT', \
                  'MO-122','FO-29',\
                  'SO-124','SO-125']

# Celestial bodies of interest - i.e. Sun and Moon
CELESTIAL_BODY_LIST=['Sun','Moon']

# Major meteor showers thorughout the year
METEOR_SHOWER_LIST=['QUA','LYR','ETA','SDA','PER','ORI','LEO','GEM']

# Valid precidences for ARRL SS
PRECS='QSABUMS'

############################################################################################

OFF_ON=["OFF","ON"]
VFO_MEM=["VFO","MEM"]
CTCSS=["OFF","ENC/DEC","ENC"]
SHIFTS=["SIMPLEX","+",'-']

# TABLE OF COMMON PL TONES (in Hz)
PL_TONES=np.array( [ 67.0,    94.8,  131.8,   171.3,    203.5 ,
                     69.3,    97.4,  136.5,   173.8,    206.5 ,
                     71.9,   100.0,  141.3,   177.3,    210.7 ,
                     74.4,   103.5,  146.2,   179.9,    218.1 ,
                     77.0,   107.2,  151.4,   183.5,    225.7 ,
                     79.7,   110.9,  156.7,   186.2,    229.1 ,
                     82.5,   114.8,  159.8,   189.9,    233.6 ,
                     85.4,   118.8,  162.2,   192.8,    241.8 ,
                     88.5,   123.0,  165.5,   196.6,    250.3 ,
                     91.5,   127.3,  167.9,   199.5,    254.1] )
PL_TONES = np.sort( PL_TONES )    # Put in ascending order

FTDX_MODES=["","LSB","USB","CW","FM","AM","RTTY-LSB",
            "CW-R","PKT-L","RTTY-USB","PKT-FM","FM-N","PKT-U","AM-N" ]

FTDX_MODES2 = ["CW","RTTY","USB","LSB","AM","FM"]
FTDX_ANTENNAS = ['Ant1','Ant2','Ant3']
METERS   = ['Front 1','S','Front 2','Comp','ALC','PO','SWR','ID','Vdd']

# RTTY & FT8 contest freqs:

# Band      RTTY Contest Frequencies (MHz) Suggested FT8 Frequencies (MHz)
#  80         3.570 -  3.600                   3.590 -  3.600
#  40         7.025 -  7.100                   7.080 -  7.100
#  20        14.080 - 14.150                  14.130 - 14.150
#  15        21.080 - 21.150                  21.130 - 21.150
#  10        28.080 - 28.200                  28.160 - 28.200

# Table of bands, index, CW subbandm RTTY subands, ssb subbands, psk center, data mic gain
bands = OrderedDict()
bands["160m"]= {"Code" : 0, 
                "CW1"  : 1800, "CW2"    : 1850, 
                "RTTY1": 1800, "RTTY2"  : 1810, 
                "SSB1" : 1800, "SSB2"   : 2000,
                "FT8"  : 1840,
                "FT8C" : 0,
                "FT4"  : 1840,
                "PSK"  : 1807, "MicGain": 18,
                "CONTEST" : True}
bands["80m"] = {"Code" : 1, 
                "CW1"  : 3500, "CW2"    : 3600, 
                "RTTY1": 3550, "RTTY2"  : 3600, 
                "SSB1" : 3600, "SSB2"   : 4000, 
                "FT8"  : 3573,
                "FT8C" : 3590,
                "FT4"  : 3568,
                "PSK"  : 3580, "MicGain": 24,
                "CONTEST" : True}

#    ( "60m", 2, 5000, 5000, 5000, 5000, 5000, 5000, 5000,18),

# 60m USB:
#   Channel 1: 5330.5 kHz
#   Channel 2: 5346.5 kHz
#   Channel 3: 5357.0 kHz
#   Channel 4: 5371.5 kHz
#   Channel 5: 5403.5 kHz
#
# 60m CW & PSK31:
#   Channel 1: 5332.0 kHz
#   Channel 2: 5348.0 kHz
#   Channel 3: 5358.5 kHz
#   Channel 4: 5373.0 kHz
#   Channel 5: 5405.0 kHz

bands["60m"] = {"Code"  : 2, 
                "CW1"   : 5332, "CW2"   : 5405, 
                "RTTY1" : 5332, "RTTY2" : 5405, 
                "SSB1"  : 5330.5, "SSB2"  : 5403.5, 
                "FT8"   : 5357,
                "FT8C"  : 0,
                "FT4"   : 5357,
                "PSK"   : 5332, "MicGain": 0,
                "CONTEST" : False}

bands["40m"] = {"Code" : 3, 
                "CW1"  : 7000, "CW2"    : 7125, 
                "RTTY1": 7030, "RTTY2"  : 7125, 
                "SSB1" : 7125, "SSB2"   : 7300, 
                "FT8"  : 7074,
                "FT8C" : 7080,
                "FT4"  : 7047.5,
                "PSK"  : 7070, "MicGain": 25,
                "CONTEST" : True}
bands["30m"] = {"Code" : 4, 
                "CW1"  : 10100, "CW2"    : 10150, 
                "RTTY1": 10130, "RTTY2"  : 10150,
                "SSB1" : 10100, "SSB2"   : 10150, 
                "FT8"  : 10136,
                "FT8C"  : 0,
                "FT4"  : 10140,
                "PSK"  : 10130, "MicGain": 18,
                "CONTEST" : False}
bands["20m"] = {"Code" : 5, 
                "CW1"  : 14000, "CW2"    : 14150, 
                "RTTY1": 14075, "RTTY2"  : 14130, 
                "SSB1" : 14150, "SSB2"   : 14350, 
                "FT8"  : 14074,
                "FT8C" : 140130,
                "FT4"  : 14080,
                "PSK"  : 14070, "MicGain": 24,
                "CONTEST" : True}
bands["17m"] = {"Code" : 6, 
                "CW1"  : 18068, "CW2"    : 18110, 
                "RTTY1": 18100, "RTTY2"  : 18110,
                "SSB1" : 18110, "SSB2"   : 18168, 
                "FT8"  : 18100,
                "FT8C" : 0,
                "FT4"  : 18104,
                "PSK"  : 18100, "MicGain": 18,
                "CONTEST" : False}
bands["15m"] = {"Code" : 7, 
                "CW1"  : 21000, "CW2"    : 21200, 
                "RTTY1": 21075, "RTTY2"  : 21130, 
                "SSB1" : 21200, "SSB2"   : 21450, 
                "FT8"  : 21074,
                "FT8C" : 21130,
                "FT4"  : 21140,
                "PSK"  : 21070, "MicGain": 25,
                "CONTEST" : True}
bands["12m"] = {"Code" : 8, 
                "CW1"  : 24890, "CW2"    : 24930, 
                "RTTY1": 24920, "RTTY2"  : 24930,
                "SSB1" : 24930, "SSB2"   : 24990, 
                "FT8"  : 24915,
                "FT8C" : 0,
                "FT4"  : 24919,
                "PSK"  : 24920, "MicGain": 20,
                "CONTEST" : False}
bands["10m"] = {"Code" : 9, 
                "CW1"  : 28000, "CW2"    : 28300, 
                "RTTY1": 28070, "RTTY2"  : 28150, 
                "SSB1" : 28300, "SSB2"   : 29700, 
                "FT8"  : 28074,
                "FT8C" : 28160,
                "FT4"  : 28180,
                "MSK144"  : 28145,
                "PSK"  : 28120, "MicGain": 13,
                "CONTEST" : True}
bands["6m"] = {"Code" : 10, 
                "CW1"  : 50000, "CW2"    : 50100, 
                "RTTY1": 50100, "RTTY2"  : 54000, 
                "SSB1" : 50100, "SSB2"   : 54000, 
                "FT8"  : 50313,
                "FT8C" : 0,
                "FT4"  : 50318,
                "MSK144"  : 50260,
                "PSK"  : 50290, "MicGain": 13,
                "CONTEST" : False}
bands["2m"] = {"Code" : 15, 
                "CW1"  : 144000, "CW2"    : 144100, 
                "RTTY1": 144100, "RTTY2"  : 148000, 
                "SSB1" : 144100, "SSB2"   : 148000, 
                "FT8"  : 144174,
                "FT8C" : 0,
                "FT4"  : 144170,
                "MSK144"  : 144360,
                "PSK"  : 144290, "MicGain": 0,
                "CONTEST" : False}
bands["1.25m"] = {"Code" : -1, 
                  "CW1"  : 222000, "CW2"    : 225000, 
                  "RTTY1": 222000, "RTTY2"  : 225000, 
                  "SSB1" : 222000, "SSB2"   : 225000, 
                  "FT8"  : 0,
                  "FT8C" : 0,
                  "FT4"  : 0,
                  "PSK"  : 222000, "MicGain": 0,
                  "CONTEST" : False}
bands["70cm"] = {"Code" : 16, 
                 "CW1"  : 430000, "CW2"    : 450000, 
                 "RTTY1": 430000, "RTTY2"  : 450000, 
                 "SSB1" : 430000, "SSB2"   : 450000, 
                 "FT8"  : 0,
                 "FT8C" : 0,
                 "FT4"  : 0,
                 "MSK144"  : 432360,
                 "PSK"  : 430000, "MicGain": 0,
                 "CONTEST" : False}
bands["33cm"] = {"Code" : -1, 
                 "CW1"  : 902000, "CW2"    : 928000, 
                 "RTTY1": 902000, "RTTY2"  : 928000, 
                 "SSB1" : 902000, "SSB2"   : 928000, 
                 "FT8"  : 0,
                 "FT8C" : 0,
                 "FT4"  : 0,
                 "PSK"  : 902000, "MicGain": 0,
                 "CONTEST" : False}
bands["23cm"] = {"Code" : -1, 
                 "CW1"  : 1240000, "CW2"   : 1300000, 
                 "RTTY1": 1240000, "RTTY2"  :1300000, 
                 "SSB1" : 1240000, "SSB2"   :1300000, 
                 "FT8"  : 0,
                 "FT8C" : 0,
                 "FT4"  : 0,
                 "PSK"  : 1240000, "MicGain": 0,
                 "CONTEST" : False}
bands["GEN"] = {"Code" : 11, 
                 "CW1"  : 1, "CW2"   :30000, 
                 "RTTY1": 1, "RTTY2" :30000, 
                 "SSB1" : 1, "SSB2"  :30000, 
                 "FT8"  : 0,
                 "FT8C" : 0,
                 "FT4"  : 0,
                 "PSK"  : 0, "MicGain": 0,
                 "CONTEST" : False}
bands["MW"] = {"Code" : 12, 
                 "CW1"  : 540, "CW2"   :1700, 
                 "RTTY1": 540, "RTTY2" :1700, 
                 "SSB1" : 540, "SSB2"  :1700, 
                 "FT8"  : 0,
                 "FT8C" : 0,
                 "FT4"  : 0,
                 "PSK"  : 0, "MicGain": 0,
                 "CONTEST" : False}
bands["AIR"] = {"Code" : 14, 
                 "CW1"  : 108000, "CW2"   :144000, 
                 "RTTY1": 108000, "RTTY2" :144000, 
                 "SSB1" : 108000, "SSB2"  :144000, 
                 "FT8"  : 0,
                 "FT8C" : 0,
                 "FT4"  : 0,
                 "PSK"  : 0, "MicGain": 0,
                 "CONTEST" : False}

# Make a copy of phone band edges for AM
for b in list(bands.keys()):
    bands[b]["AM1"] = bands[b]["SSB1"]
    bands[b]["AM2"] = bands[b]["SSB2"]

# Table of modes, index, code (for MD;), regular & narrrow roofing filters  (for RF;)
modes = OrderedDict()
modes["None"]  = {"Index":0,  "Code":'03', "Filter1":'03', "Filter2":'04', 'Filter3':'000'}
modes["CW-N"]  = {"Index":0,  "Code":'03', "Filter1":'03', "Filter2":'04', 'Filter3':'010'}
modes["CW"]    = {"Index":0,  "Code":'03', "Filter1":'03', "Filter2":'04', 'Filter3':'009'}
modes["RTTY"]  = {"Index":1,  "Code":'0C', "Filter1":'03', "Filter2":'04', 'Filter3':'002'}
modes["PSK"]   = {"Index":2,  "Code":'0C', "Filter1":'03', "Filter2":'04', 'Filter3':'002'}
modes["SSB"]   = {"Index":3,  "Code":'02', "Filter1":'03', "Filter2":'03', 'Filter3':'007'}
modes["AM"]    = {"Index":4,  "Code":'05', "Filter1":'00', "Filter2":'00', 'Filter3':'005'}
modes["WSJT"]  = {"Index":5,  "Code":'02', "Filter1":'03', "Filter2":'03', 'Filter3':'002'}
modes["LSB"]   = {"Index":6,  "Code":'01', "Filter1":'03', "Filter2":'03', 'Filter3':'007'}
modes["USB"]   = {"Index":7,  "Code":'02', "Filter1":'03', "Filter2":'03', 'Filter3':'007'}
modes["FM"]    = {"Index":8,  "Code":'04', "Filter1":'00', "Filter2":'00', 'Filter3':'002'}
modes["FM-W"]  = {"Index":8,  "Code":'04', "Filter1":'00', "Filter2":'00', 'Filter3':'002'}
modes["FSK"]   = {"Index":9,  "Code":'06', "Filter1":'00', "Filter2":'00', 'Filter3':'002'}
modes["CW-R"]  = {"Index":10, "Code":'07', "Filter1":'03', "Filter2":'04', 'Filter3':'009'}
modes["PKT-L"] = {"Index":11, "Code":'08', "Filter1":'03', "Filter2":'04', 'Filter3':'007'}
modes["FSK-R"] = {"Index":12, "Code":'09', "Filter1":'00', "Filter2":'00', 'Filter3':'002'}
modes["PKT-FM"]= {"Index":13, "Code":'0A', "Filter1":'00', "Filter2":'00', 'Filter3':'002'}
modes["FM-N"]  = {"Index":14, "Code":'0B', "Filter1":'00', "Filter2":'00', 'Filter3':'003'}
modes["PKT-U"] = {"Index":15, "Code":'0C', "Filter1":'03', "Filter2":'04', 'Filter3':'002'}
modes["AM-N"]  = {"Index":16, "Code":'0D', "Filter1":'00', "Filter2":'00', 'Filter3':'007'}

modes["PKTUSB"] = modes["PKT-U"]


icom_modes = OrderedDict()
icom_modes["CW"]    = {"Index":0,  "Code":0x03, "Filter1":0x02, "Filter2":0x02}
icom_modes["RTTY"]  = {"Index":1,  "Code":0x04, "Filter1":0x01, "Filter2":0x02}
icom_modes["PSK"]   = {"Index":2,  "Code":0x12, "Filter1":0x01, "Filter2":0x02}
icom_modes["SSB"]   = {"Index":3,  "Code":0x01, "Filter1":0x01, "Filter2":0x02}
icom_modes["AM"]    = {"Index":4,  "Code":0x02, "Filter1":0x01, "Filter2":0x02}
icom_modes["WSJT"]  = {"Index":5,  "Code":0x12, "Filter1":0x01, "Filter2":0x02}
icom_modes["LSB"]   = {"Index":6,  "Code":0x00, "Filter1":0x01, "Filter2":0x02}
icom_modes["USB"]   = {"Index":7,  "Code":0x01, "Filter1":0x01, "Filter2":0x02}
icom_modes["FM"]    = {"Index":8,  "Code":0x05, "Filter1":0x01, "Filter2":0x02}
icom_modes["FSK"]   = {"Index":9,  "Code":0x04, "Filter1":0x01, "Filter2":0x02}
icom_modes["CW-R"]  = {"Index":10, "Code":0x07, "Filter1":0x01, "Filter2":0x02}
icom_modes["PKT-L"] = {"Index":11, "Code":0x12, "Filter1":0x01, "Filter2":0x02}
icom_modes["FSK-R"] = {"Index":12, "Code":0x04, "Filter1":0x01, "Filter2":0x02}
icom_modes["PKT-FM"]= {"Index":13, "Code":0x04, "Filter1":0x01, "Filter2":0x02}
icom_modes["FM-N"]  = {"Index":14, "Code":0x05, "Filter1":0x01, "Filter2":0x02}
icom_modes["PKT-U"] = {"Index":15, "Code":0x04, "Filter1":0x01, "Filter2":0x02}
icom_modes["AM-N"]  = {"Index":16, "Code":0x02, "Filter1":0x01, "Filter2":0x02}

icom_modes["PKTUSB"] = icom_modes["PKT-U"]


# Filters for FT991a - SH width command - use NA cmd to select wide/narrow:
FT991A_SSB_FILTERS1  = [1500,200,400,600,850,1100,1350,1500,1650,1800]
FT991A_SSB_FILTERS2  = [2400]+8*[0]+[1800,1950]+list( range(2100,3100,100) )+[3200] 
FT991A_CW_FILTERS1   = [500]+list( range(50,550,50) )
FT991A_CW_FILTERS2   = [2400]+9*[0]+[500,800,1200,1400,1700,2000,2400,3000]
FT991A_DATA_FILTERS1 = [300]+list( range(50,550,50) )
FT991A_DATA_FILTERS2 = [500]+9*[0]+[500,800,1200,1400,1700,2000,2400,3000]
FT991A_AM_FILTERS1    = [6000]
FT991A_AM_FILTERS2    = [9000]

#FTdx3000_SSB_FILTERS1  = FT991A_SSB_FILTERS1
#FTdx3000_SSB_FILTERS2  = [2400]+8*[0]+[1800,1950]+list( range(2100,3000,100) )+[3200] 
FTdx3000_SSB_FILTERS2  = [2400]+8*[0]+[1800,1950]+[range(2100,3100,100)]+[range(3200,4200,200)]
FTdx3000_CW_FILTERS2   = [2400]+9*[0]+[500,800,1200,1400,1700,2000,2400]
FTdx3000_DATA_FILTERS1 = [500]+[range(50,550,50)]
FTdx3000_DATA_FILTERS2 = [2400]+9*[0]+[500,800,1200,1400,1700,2000,2400]

# Filters for TS-850
TS850_FILTERS = ['FM-W','FM-N','AM','SSB','CW','CW-N']

# Menu numbers
YAESU_MIC_MENU_NUMBERS = OrderedDict()
YAESU_MIC_MENU_NUMBERS['FT991a']   = {'AM':[45,46,48],   'FM':[74,75,77],   'SSB':[106,107,109],'PKTUSB':[106,107,109],'RTTY':[106,107,109]}
YAESU_MIC_MENU_NUMBERS['FTdx3000'] = {'AM':[53,52,None], 'FM':[85,84,None], 'SSB':[103,None,None]}

# A list of preset AM stations
stations = OrderedDict([ ("KOGO",600),
                         ("KFMB",760),
                         ("KABC",790),
                         ("KCBQ",1170),
                         ("KFBK",1530) ])

############################################################################################

# Function to associate filter name with key returned by rig
def Decode_Filter_ft991a(m,wide,idx):
    #VERBOSITY=1
    if VERBOSITY>0:
        print('Decode_Filter_ft991a:',m,wide,idx)
    if m=='RTTY' or m=='PKTUSB':
        if wide=='Wide':
            filts=FT991A_DATA_FILTERS2
        else:
            filts=FT991A_DATA_FILTERS1
    elif m=='USB' or m=='LSB':
        if wide=='Wide':
            filts=FT991A_SSB_FILTERS2
        else:
            filts=FT991A_SSB_FILTERS1
    elif m=='CW':
        if wide=='Wide':
            filts=FT991A_CW_FILTERS2
        else:
            filts=FT991A_CW_FILTERS1
    elif m=='AM' or m=='AMN':
        idx=0
        if wide=='Wide':
            filts=FT991A_AM_FILTERS2
        else:
            filts=FT991A_AM_FILTERS1
    elif m=='FM':
        idx=0
        if wide=='Wide':
            filts=FT991A_AM_FILTERS2
        else:
            filts=FT991A_AM_FILTERS1
    else:
        print('\n\n ####### Decode Filter ft991a - Unknown mode',m,'\n\n')
        #sys,exit(0)

    if VERBOSITY>0:
        print(filts)
        print('Decode_Filter_ft991a:',m,wide,idx)

    try:
        ret = str(filts[int(idx)])+' Hz'
    except:
        print('Decode_Filter_ft991a - Problem at end: m=',m,'\twide=',wide,'\tidx=',idx)
        #print('filts=',filts)
        ret = '2400 Hz'
        
    return ret

# Function to associate filter name with key returned by rig
def Decode_Filter_ts850(f):

    if f=='000':
        filt='None'
    elif f=='002':
        filt='FM-W'
    elif f=='003':
        filt='FM-N'
    elif f=='005':
        filt='AM'
    elif f=='007':
        filt='SSB'
    elif f=='009':
        filt='CW'
    elif f=='010':
        filt='CW-N'
    else:
        print('########### DECODE_FILTER_TS850: Unknown filter???',f)
        filt=None
        #sys.exit(0)

    return filt

############################################################################################

# Function to associate mode name with key returned by rig
def Decode_Mode(m):

    #if m=='1' or m=='2':
    #    mode='SSB'
    if m=='1':
        mode='LSB'
    elif m=='2':
        mode='USB'
    elif m=='3' or m=='7':
        mode='CW'
    elif m=='4' or m=='B':
        mode='FM'
    elif m=='5' or m=='D':
        mode='AM'
    elif m=='6' or m=='9' or m=='8' or m=='C':
        mode='RTTY'
    else:
        print('########## DECODE_MODE: Unknown mode???',m)
        mode=None
        #sys.exit(0)

    #print 'DECODE_MODE:',m,mode
    return mode


# Function to associate mode name with key returned by rig
def Icom_Decode_Mode(m):

    #print m,m.replace('0x','')
    m=int(m.replace('0x',''))
    if m==0x00 or m==0x01:
        mode='SSB'
    elif m==0x03 or m==0x07:
        mode='CW'
    elif m==0x05 or m==0x06:
        mode='FM'
    elif m==0x02 or m==0x11:
        mode='AM'
    elif m==0x04 or m==0x08 or m==0x12:
        mode='RTTY'
    else:
        print('######### ICOM_DECODE_MODE: Unknown mode???',m)
        mode=None
        #sys.exit(0)

    #print 'DECODE_MODE:',m,mode
    return mode

############################################################################################

############################################################################################

def arrl_sec2state(sec):
    if len(sec)==2:
        # Section is same as state
        return sec
    elif len(sec)==3 and sec[1:] in SST_SECS:
        return sec[1:]
    elif sec=='NLI':
        return 'NY'
    elif sec=='WCF':
        return 'FL'
    elif sec in ['EB','LAX','ORG','SB','SCV','SDG','SF','SJV','SV']:
        return 'CA'
    elif sec in ['ONE','ONN','ONS','GTA']:
        return 'ON'
    else:
        return ''
    
    
