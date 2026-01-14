################################################################################
#
# Spot Processing - J.B.Attili - ?
#
# Functions for processing spot from the dx cluster
#
# I think the original for this came from
#        https://github.com/dh1tw/DX-Cluster-Parser
# This is the sme gentleman that provides pyhamtools - TU!
# If you recognize this code, please email me so I can give proper attribution.
#
# Notes:
#    The cty.plist file is large (~14 Mb) and takes time to load
#    Its better to convert this file to binary after downloading it.
#    See comments in cty.py as to how to do this.
#
################################################################################

import sys
import os
import re
import pytz
from pytz import timezone
from datetime import datetime, time, date, tzinfo
from .cty import load_cty
import logging
from pprint import pprint
import xlrd
from unidecode import unidecode
from utilities import find_resource_file, error_trap,stack_trace
import pandas as pd

################################################################################

#------------------CONSTANTS --------------------
UTC = pytz.utc
root_logger_name = "dxcsucker"

# Download this file from http://www.country-files.com/cty/
#cty_dir = os.path.expanduser('~/Python/data/')

################################################################################

class ChallengeData:
    def __init__(self,fname,DATA_DIR=None):

        # Init
        self.dxccs=[]
        self.bands=[]
        self.slots=[]
        self.nrows1=0
        self.nrows2=0
        self.cwops_worked=[]
        self.cwops_nums=[]

        fname=os.path.expanduser(fname)
        if DATA_DIR==None:
            DATA_DIR='~/Python/data'
        DATA_DIR=os.path.expanduser(DATA_DIR)

        # Read XLS format spreadsheet and pull out sheets we want
        # There are newer modules for this - look into them sometime
        print('CHALLENGE DATA: Opening ',fname,' ...')
        book  = xlrd.open_workbook(fname,formatting_info=True)
        self.sheet1 = book.sheet_by_name('Challenge')
        self.nrows1 = self.sheet1.nrows
        self.sheet2 = book.sheet_by_name('Modes')
        self.nrows2 = self.sheet2.nrows

        # Read sheet with CWops members we've worked
        print('CHALLENGE DATA: Reading CWops member list ..')
        """
        # No longer stored in a separate sheet
        self.sheet3 = book.sheet_by_name('CWops')
        for i in range(1,self.sheet3.nrows):
            try:
                call = self.sheet3.cell(i,12).value
                if len(call)>0:
                    self.cwops_worked.append(call)
                    num = int( self.sheet3.cell(i,11).value )
                    self.cwops_nums.append(num)
            except:
                error_trap('Problem reading CWOPS member data - giving up')
                print(i,self.sheet3.nrows)
                break
        """

        data = pd.read_csv(DATA_DIR+'/aca.csv')
        self.cwops_aca  = data['Call'].tolist()
        self.cwops_nums = data['CWops'].tolist()
        
        data = pd.read_csv(DATA_DIR+'/acma.csv')
        self.cwops_acma  = data['Call'].tolist()
        
        data = pd.read_csv(DATA_DIR+'/dxcc.csv')
        DXCCs = data['DXCC'].tolist()
        self.cwops_dxccs = []
        for dxcc in DXCCs:
            idx=dxcc.find(' (')
            if idx>0:
                dxcc=dxcc[:idx]
            dxcc=dxcc.replace('I.','ISLAND')   \
                     .replace('IS.','ISLANDS') \
                     .replace('ST.','SAINT')   \
                     .replace('SABA & SAINT','SABA & ST') 
            self.cwops_dxccs.append(dxcc)

        self.cwops_worked = self.cwops_aca       # Backward compatability
        
        if False:
            print('CHALLENGE DATA: CWops members worked so far this year:')
            print(self.cwops_worked,len(self.cwops_worked))
            print(self.cwops_nums,len(self.cwops_nums))
            print('\n',self.cwops_dxccs,len(self.cwops_dxccs))
            sys.exit(0)

        # Read in spreadsheet with band slots - much faster this way
        for i in range(1, self.sheet1.nrows):
            self.dxccs.append( self.sheet1.cell(i, 0).value )
        #print 'DXCCs:',self.dxccs
        
        NCOLS=20
        for j in range(1, NCOLS):
            #self.bands.append( str( self.sheet1.cell(0, j).value ) )
            val = self.sheet1.cell(0, j).value 
            if isinstance(val, float):
                val=int(val)
            val = str( val )
            self.bands.append(val)
        print('CHALLENGE DATA - BANDS=',self.bands)

        self.slots=[]
        for i in range(1, self.sheet1.nrows):
            calls = []
            for j in range(1,NCOLS):
                #calls.append( unidecode( self.sheet1.cell(i, j).value ) )
                #print('i,j=',i,j,'\tval=',self.sheet1.cell(i, j).value)
                val = self.sheet1.cell(i, j).value
                if isinstance(val,float):
                    if val==0.0:
                        val=''
                    else:
                        val = str(int(val))
                try:
                    calls.append( unidecode( val ) )
                except:
                    error_trap('SPOT PROCESSING - Challenge Data: Problem unpacking cell')
                    print('i=',i,'\tj=',j)
            self.slots.append(calls)
            #print('CHALLENGE DATA - i=',i,'\tcalls=',calls)
            
        # JBA - MEM??? - Try this
        del book

    # Work through Challenge sheet
    def needed_challenge(self,dxcc,band,verbosity):

        if self.nrows1==0:
            return False
        
        band=str(band)
        if dxcc is None or band=='60M' or band=='Unknown':
            return False
        else:
            dxcc=dxcc.upper().replace('ST.','SAINT')
            if dxcc=='UNITED STATES':           # This helps to speed things up
                return False

        # Its probably better to fix the names rather than have this
        # special treatment.  The problem with St. Martin is that
        # MARTIN is also in Martinique.  Try fixing these as they come up.
        # The "St."'s should be easy but I left it like this for now to
        # minimize potential issues.
        special = ['VIET','GERMANY','NEVIS','EUSTATIUS','FIJI',    \
                   'SOUTH AFRICA','PIERRE','CHATHAM','BARTHELEMY', \
                   'PAUL ISLAND','VINCENT','SAN ANDRES','ROTUMA',  \
                   'BRUNEI','MAURITIUS','KEELING','LESTE','JARVIS']
        needed=True

        #print('NEEDED_CHALLENGE:',dxcc,band)
        #print self.dxccs
        #print dxcc in self.dxccs
        #ii=self.dxccs.index(dxcc)

        try:
            jj=self.bands.index(band)
        except:
            jj=-1
            if band!='ALL':
                print('CHALLENGE_NEEDED: Band',band,'not in band list')
                print('BANDS:',self.bands)
        #print('NEEDED_CHALLENGE: dxcc=',dxcc,'\tattribute=',band,'\tjj=',jj)

        for i in range(1, self.nrows1):
            cell = self.dxccs[i-1]

            found = dxcc==cell
            for s in special:
                found = found or (s in dxcc and s in cell)

            if found:
                if verbosity>0:
                    print('CHALLENGE_NEEDED: dxcc=',dxcc,'\ti=',i,'\tjj=',jj)

                if jj>0:
                    #print 'jj=',jj
                    call = str(self.slots[i-1][jj]).strip()
                    #if isinstance(call,float):
                    #    call = str(call)
                    if verbosity>0:
                        print('CHALLENGE_NEEDED: dxcc=',dxcc,'\ti=',i,'\tjj=',jj,'\tcall=',call,
                              '\tval=',self.slots[i-1][jj])
                        print('slots=',self.slots[i-1])
                    needed= call=='' or call=='PAPER'
                    if verbosity>0 or band=='Phone99':
                        print('CHALLENGE_NEEDED: band=',band,'\tdxcc=',dxcc,\
                              '\tfound=',found,'\ti=',i,'\tjj=',jj,\
                              '\tcall=',call,'\tneeded=',needed)
                    return needed
                
                for j in range(10):
                    b2 = self.bands[j]
                    
                    if band=='ALL' or band==b2:
                        call = self.slots[i-1][j].strip()

                        if call=='':
                            NEEDED='*** NEEDED ***'
                        elif call=='PAPER' and True:
                            NEEDED='*** NEEDED ***'
                        else:
                            NEEDED=' '
                            needed=False
                        if verbosity>0 or NEEDED!=' ':
                            print(("DXCC: %s : %-8s -   %-10s     %-20s" % (dxcc,b2,call,NEEDED) ))
                break
        else:
            if verbosity>0:
                print('NEEDED_CHALLENGE: ',dxcc,' not found - *** NEEDED ***')

        #sys.exit(0)
        return needed

    # Work through Modes sheet
    def needed_mode(self,dxcc,band):
        
        if self.nrows2==0:
            return False
        
        for i in range(1, self.nrows2):
            cell =self.sheet2.cell(i, 0).value 
            #if sheet2.cell(i, 0).value==dxcc:
            if dxcc==cell or ('GERMANY' in dxcc and 'GERMANY' in cell):
                for j in range(1, 5):
                    if band=='ALL':
                        b2 = self.sheet2.cell(0, j).value
                        call = unidecode(self.sheet2.cell(i, j).value).strip()
                        if call=='':
                            NEEDED='*** NEEDED ***'
                        else:
                            NEEDED=' '
                        print(("%s: %-8s -   %-10s     %-20s" % (dxcc,b2,call,NEEDED) ))
                

            
def get_configured_logger(name):
        #print('GET_CONFIGURED_LOGGER 1: name=',name)
        logger = logging.getLogger(name)
        #print('logger=',logger)
        #print('handlers=',logger.handlers)
        if (len(logger.handlers) == 0):
                # This logger has no handlers, so we can assume it hasn't yet been configured
                # (Configure logger)
                #print('GET_CONFIGURED_LOGGER 2: name=',name)
                
                #Define Formatters
                formatter_simple="[%(levelname)s] [%(module)s]: %(message)s"
                #formatter_verbose=("[%(levelname)s] [%(asctime)s] [%(module)s]: %(message)s","%d/%m/%Y %H:%M:%S")
                formatter_verbose=("[%(levelname)s] [%(asctime)s] [%(module)s]: %(message)s","%d/%m/%Y %H:%M:%S")

                #Define & Configure Handlers
                console_handler = logging.StreamHandler() #outputs to the console
                console_handler.setLevel(logging.DEBUG) #adjust level to your needs
                file_handler = logging.FileHandler("spot_processing.log") #outputs into this file
                file_handler.setLevel(logging.ERROR) #adjust logging level to your needs
                file_handler.setLevel(logging.DEBUG) #adjust logging level to your needs

                # Instanciate Root logger
                #logger = logging.getLogger()
                logger = logging.getLogger(name)

                # Assign Formatter to Handler
                console_handler.setFormatter(logging.Formatter(formatter_simple))
                #print('GET_CONFIGURED_LOGGER: fmt verbose=',formatter_verbose)
                #file_handler.setFormatter(logging.Formatter(formatter_verbose))
                file_handler.setFormatter(logging.Formatter(None))
                
                # Assign Handler to Logger
                logger.addHandler(console_handler)
                logger.addHandler(file_handler)
                
                return logger
                
        else: #return root logger
                return logger
                

####################################################################################################

# This is convoluted and I need to find a better solution!
CTY_INFO=None
def load_cty_info(DIR=None):
        global CTY_INFO
        
        # Load Country File
        print('LOADing CTY INFO ... DIR=',DIR)
        if CTY_INFO!=None:
            error_trap('CTY INFO already loaded!')
            #sys.exit(0)
            return
        
        CTY_INFO = ""
        if DIR==None:
            DIR='~/Python/data'
        cty_dir = os.path.expanduser(DIR+'/')
        #CTY_FILE='cty.plist'
        CTY_FILE='cty.bin'
        try:
            print('fname=',cty_dir+CTY_FILE)
            if os.path.isfile(cty_dir+CTY_FILE):

                if False:
                    import asyncio
                    loop = asyncio.get_event_loop()
                    loop.run_until_complete(load_cty(cty_dir+CTY_FILE))
                    print(CTY_INFO)
                    sys.exit(0)
                else:
                    CTY_INFO = load_cty(cty_dir+CTY_FILE)

                if False:
                    print(CTY_INFO)
                    print(CTY_INFO.keys())
                    sys.exit(0)
            else:
                fname=find_resource_file(CTY_FILE)
                print('Cty fname=',fname)
                if os.path.isfile(fname):
                    CTY_INFO = load_cty(fname)              # Load Country File
                else:
                    #self._logger.critical(CTY_FILE+" could not be loaded!")
                    raise Exception(CTY_FILE+" not found!")
        except:
            error_trap('SPOT PROCESSING - Station: '+CTY_FILE+' could not be loaded!',1)
            #self._logger.exception("CTY.PLIST could not be loaded!")
            print('cty_dir=',cty_dir)
            sys.exit(0)

            
class Station(object):
        #------------------Constructor --------------------
        def __init__(self, call):
        #       super(Station, self).__init__()
                #print('\nSPOT PROC: STATION INIT call=',call)
                self._logger = get_configured_logger(root_logger_name)
                self._logger.propagate = True #send all log events to higher logger which has a handler
                
                self.valid = None
                self.call = None
                self.prefix = None
                self.homecall = None
                self.appendix = None
                self.country = None
                self.latitude = None
                self.longitude = None
                self.cqz = None
                self.ituz = None
                self.continent = None
                self.offset = None
                self.mm = False                 # Marine mobile
                self.am = False                 # Aero mobile
                self.beacon = False             # Beacon
                
                self.call_prefix=None
                self.call_number=None
                self.call_suffix=None

                #self.DEBUG = True
                self.DEBUG = False
                
                self.call = call.rstrip().lstrip().upper()
                self.homecall = self.obtain_homecall(self.call)

                if self.DEBUG :
                    print('SPOT PROCESSING->Station: call=',self.call,'\thomecall=',self.homecall)

                if CTY_INFO==None:
                    print('\nSPOT PROCESSING->Station: call=',call)
                    stack_trace('*** Need to load cty info !!! ***')
                    sys.exit(0)

                if not self.homecall:
                    self.valid = False
                    self._logger.warning("Busted Homecall: '"+ str(self.homecall) \
                                         + "' of " + self.call + " could not be decoded")
                else:
                    self.prefix = self.obtain_prefix(self.call)
                    if self.DEBUG:
                        print('SPOT PROCESSING->Station: call=',call,'\tprefix=',self.prefix)
                    if not self.prefix:
                        
                        self.valid = False
                        if not self.mm and not self.am and self.appendix=='':
                            self._logger.warning("STATION: Busted Prefix: '"+ str(self.prefix) \
                                                 + "' of " + self.call + " could not be decoded")
                            print('STATION: Busted prefix - call=',call)
                            if self.DEBUG:
                                sys.exit(0)
                                
                    else:
                        
                        if self.call in CTY_INFO:
                            cty_info = self.lookup_cty_info(self.call)
                        else:
                            cty_info = self.lookup_cty_info(self.prefix)
                        if self.DEBUG:
                            print('\tcall=',self.call,'\tprefix=',self.prefix,'\tcty_info=',cty_info)
                        if not cty_info:
                            self.valid = False
                            print("Busted: No Country Info found for " + self.call )
                            self._logger.warning("Busted: No Country Info found for " + self.call )
                                        
                        else:
                            self.country = cty_info['country']
                            self.latitude = cty_info['latitude']
                            self.longitude = cty_info['longitude']
                            self.cqz = cty_info['cqz']
                            self.ituz = cty_info['ituz']
                            self.continent = cty_info['continent']
                            self.offset = cty_info['offset']
                            self.valid = True

                    # Disect the homecall
                    parts = self.obtain_parts(self.homecall)
                    self.call_prefix=parts[0]
                    self.call_number=parts[1]
                    self.call_suffix=parts[2]

                    # Fix-up quirks
                    # Calls from Club Gitmo are 2x2, rest are from the U.S.
                    # Scicily and African Itally are not separate DXCCs
                    # European and Asiatic Turkey are not separate DXCCs
                    if self.country:
                        if self.country=='Guantanamo Bay' and len(self.call_suffix)!=2:
                            self.country='United States'
                        elif 'Sicily' in self.country or 'Italy' in self.country:
                            self.country='Italy'
                        elif 'Germany' in self.country:
                            self.country='Germany'
                        elif 'Turkey' in self.country:
                            self.country='Turkey'
                                        
        #------------------Class Methods --------------------           
        def __iterate_prefix(self, call):
            """truncate call until it corresponds to a Prefix in the database"""

            prefix = call
            if self.DEBUG:
                print('SPOT PROCESSING->Iterate ENTRY: call=',call)
                a=(prefix in CTY_INFO)
                if a:
                    b=CTY_INFO[prefix]['ExactCallsign']
                else:
                    b=None
                print('\tin=',a,'\texact=',b)
            Done=False
            #Done=(prefix in CTY_INFO) and not CTY_INFO[prefix]['ExactCallsign']
            while not Done:
                #print('\tprefix1=',prefix)
                if len(prefix) == 0:
                    break
                else:
                    prefix = prefix.replace(' ','')[:-1]
                #print('\tprefix2=',prefix)
                if self.DEBUG:
                    print('SPOT PROCESSING->Iterate Prefix: prefix=',prefix,'\tlen=',len(prefix))
                    a=(prefix in CTY_INFO)
                    if a:
                        b=CTY_INFO[prefix]['ExactCallsign']
                    else:
                        b=None
                    print('\t',a,b)
                Done=(prefix in CTY_INFO) and not CTY_INFO[prefix]['ExactCallsign']

            if self.DEBUG:
                print('SPOT PROCESSING->Iterate Prefix: call=',call,'\tprefix=',prefix)
                #if len(prefix)>0:
                print('\tCTY_INFO for',prefix,'=',CTY_INFO[prefix])
                if call in CTY_INFO:
                    print('\tCTY_INFO for',call,'=',CTY_INFO[call])

            return(prefix)
                
            # Nice try but the doesnt work right, e.g. if call is in cty.plist - JBA - THIS HAS BEEN FIXED ABOVE!!!
            #print prefix
            if len(prefix)>0 and prefix!='E5' and prefix[0:4]!='4U1U' and False:
                #print prefix
                #print CTY_INFO[prefix]
                return CTY_INFO[prefix]['Prefix']
            else:
                #print(prefix)
                return(prefix)

        def obtain_parts(self,homecall):
            #print 'HC=',homecall

            # Look for prefix
            i1=0
            for i in range(len(homecall)):
                if homecall[i].isdigit():
                    i1=i
                    #break
            #print i1,homecall[0:i1]

            # Look for suffix
            i2=i1
            for i in range(i1,len(homecall)):
                if not homecall[i].isdigit():
                    i2=i
                    break
            #print i2,homecall[i1:i2]
            #print homecall[i2:]

            return [homecall[0:i1],homecall[i1:i2],homecall[i2:]]

        def obtain_homecall(self, raw_call):
                """verify call and strip off any /ea1 vp5/ /qrp etc"""
                try:
                        raw_call = raw_call.upper()
                        #--------identify Homecall in case the callsign has an appendix (e.g. call: DH1TW/VP5, homecall: DH1TW) ------------
                        homecall = re.search(r'[\d]{0,1}[A-Z]{1,2}\d([A-Z]{1,4}|\d{3,3}|\d{1,3}[A-Z])[A-Z]{0,5}', raw_call, re.I)
                        if homecall:
                            homecall = homecall.group(0)
                        else:
                            homecall = False
                            #appendix = ''
                        return(homecall)     # ,appendix)
                except Exception as e:
                        self._logger.debug(str(e))
                        return(False)
        
        
        def obtain_prefix(self, call):
            if self.DEBUG :
                print('OBTAIN_PREFIX: call=',call)
            
            try:
                entire_call = call.upper()
                self.appendix=''
                self._logger.debug("obtain_prefix(): call " + call)
                if re.search(r'[/A-Z0-9\-]{3,15}', entire_call, re.I):  #make sure the call has at least 3 characters
                                
                    if re.search(r'\-\d{1,3}$', entire_call, re.I): #cut off any -10 / -02 appendixes
                        call = re.sub(r'\-\d{1,3}$', '', entire_call)
                                
                    if re.search(r'/[A-Z0-9]{2,4}/[A-Z0-9]{1,4}$', call):
                        call = re.sub('/[A-Z0-9]{1,4}$', '', call) # cut off 2. appendix DH1TW/HC2/P -> DH1TW/HC2

                    if self.DEBUG :
                        print('\tcall2=',call)
                    if re.search(r'/[A-Z0-9]{2,4}$', call):  # case call/xxx, but ignoring /p and /m or /5
                        appendix = re.search(r'/[A-Z0-9]{1,4}$', call)
                        appendix = re.sub('/', '', appendix.group(0))
                        self._logger.debug("obtain_prefix(): appendix: " + appendix)
                        self.appendix=appendix
                                        
                        if appendix == 'MM':                            # special case Martime Mobile
                            self.mm = True
                            self._logger.debug("obtain_prefix(): return False (case /MM)")
                            return(False)
                        elif appendix == 'AM':                          # special case Aeronautic Mobile
                            self._logger.debug("obtain_prefix(): return False (case /AM)")
                            self.am = True
                            return(False)
                        elif appendix == 'QRP':                 # special case QRP
                            call = re.sub('/QRP', '', call)
                            prefix = self.__iterate_prefix(call)
                            self._logger.debug("obtain_prefix(): prefix: "+ str(prefix) + " (case /QRP)")
                        elif appendix == 'QRPP':                        # special case QRPP
                            call = re.sub('/QRPP', '', call)
                            prefix = self.__iterate_prefix(call)
                            self._logger.debug("obtain_prefix(): prefix: "+ str(prefix) + " (case /QRPP)")
                        elif appendix == 'BCN': #filter all beacons
                            call = re.sub('/BCN', '', call)
                            prefix = self.__iterate_prefix(call)
                            self.beacon = True
                            self._logger.debug("obtain_prefix(): prefix: "+ str(prefix) + " (case /BCN)")
                        elif appendix == "LH": #Filter all Lighthouses
                            call = re.sub('/LH', '', call)
                            prefix = self.__iterate_prefix(call)
                            self._logger.debug("obtain_prefix(): prefix: "+ str(prefix) + " (case /LH)")
                        else:
                            
                            # Look for "bogus" appendices that are often used in state QPs
                            has_digit=False
                            for i in range(len(appendix)):
                                has_digit = has_digit or appendix[i].isdigit()
                            bogus = len(appendix)>1 and (appendix.isdigit() or not has_digit)
                            if self.DEBUG :
                                print('\tbogus=',bogus)

                            if not bogus:
                                # It looks like a valid appendix
                                prefix = self.__iterate_prefix(re.sub('/', '', appendix))   #check if the appendix is a valid country prefix
                                #print('===== Valid - prefix=',prefix)
                            else:
                                # Its probably bogus
                                #prefix = self.homecall
                                call = re.sub('/'+appendix, '', call)
                                prefix = self.__iterate_prefix(call)
                                #print('===== Bogux - prefix=',prefix,'\tcall=',call)
                            #print("OBTAIN_PREFIX: call=",call,"\tprefix: " + str(prefix) + " using appendix: " + appendix )
                            self._logger.debug("obtain_prefix(): prefix: " + str(prefix) + " using appendix: " + appendix )
                        
                    elif re.search('/[A-Z0-9]$', call):  # case call/p or /b /m or /5 etc.
                        appendix = re.search('/[A-Z0-9]$', call)
                        appendix = re.sub('/', '', appendix.group(0))
                        self.appendix=appendix
                        if appendix == 'B':                     #special case Beacon
                            call = re.sub('/B', '', call)
                            prefix = self.__iterate_prefix(call)
                            self.beacon = True
                            self._logger.debug("obtain_prefix(): prefix: "+ str(prefix) + " (case /B)")
                        elif re.search(r'\d$', appendix):
                            area_nr = re.search(r'\d$', appendix).group(0)
                            call = re.sub(r'/\d$', '', call)
                            call = re.sub(r'[\d]+',area_nr, call)
                            prefix = self.__iterate_prefix(call)
                        else:
                            if self.DEBUG :
                                print('\tcall3=',call)
                            prefix = self.__iterate_prefix(call)
                            self._logger.debug("obtain_prefix(): appendix: " + appendix)
                        
                    elif re.match(r'^[\d]{0,1}[A-Z]{1,2}\d([A-Z]{1,4}|\d{3,3}|\d{1,3}[A-Z])[A-Z]{0,5}$', call, re.I):  # normal callsigns
                        if self.DEBUG :
                            print('\tcall4a=',call)
                        prefix = self.__iterate_prefix(call)
                        if self.DEBUG :
                            print('\tcall4b=',call,'\tprefix=',prefix)
                        self._logger.debug("obtain_prefix(): Prefix found: " + str(prefix) )
                    
                    else:
                        if re.search('^[A-Z0-9]{1,4}/', entire_call):  # case xxxx/call
                            pfx = re.search('^[A-Z0-9]{1,4}/', entire_call)
                            pfx = re.sub('/', '', pfx.group(0))
                            #print pfx
                            prefix = self.__iterate_prefix(pfx)
                            self._logger.debug("obtain_prefix(): country prefix " + pfx)
                        else:
                            self._logger.debug("obtain_prefix(): returning False; Invalid callsign " + call )
                            return(False)
                    
                    #--------identify Prefix of Callsign ------------
                    
                    if self.DEBUG :
                        print('\tcall5=',call)
                    if re.search('^[A-Z0-9]{1,4}/', entire_call):  # case xxxx/call
                        if re.search('^[A-Z0-9]{4}/', entire_call) and len(entire_call) < 8:
                            if self.DEBUG :
                                print('\tcall6=',call)
                            pass
                        else:
                            pfx = re.search('^[A-Z0-9]{1,4}/', entire_call)
                            #pfx = re.sub('/', '', pfx.group(0))
                            pfx = pfx.group(0)
                            if self.DEBUG :
                                print('OBTAIN_PREFIX: entire call=',entire_call,'\tpfx=',pfx)
                            prefix = self.__iterate_prefix(pfx)
                            self._logger.debug("obtain_prefix(): country prefix " + pfx)
                            
                    if  prefix == '': #in 
                        self._logger.debug("obtain_prefix(): return False; No Prefix found for " + call )
                        return(False)
                    
                    if self.DEBUG :
                        print('\tcall7=',call,'\tprefix=',prefix)
                    return(prefix) #everything went well - return prefix
                
                else:
                    self._logger.debug("obtain_prefix(): return False; No Prefix found for " + call )
                    return(False)
                   
            except:
                error_trap('OBTAIN_PREFIX: Exception',1)
                #sys.exit(0)
                #self._logger.warning(str(e))
                self._logger.warning("obtain_prefix(): Exception with call:" +call )
                return(False)
            
        def lookup_cty_info(self, prefix):
            #--------Lookup Prefix in Country Database / File and the variables ------------
            if prefix:  # if Country information found, fill the variables
                try:
                    #print prefix,CTY_INFO[prefix]
                    info = {
                        'latitude': CTY_INFO[prefix]['Latitude'],
                        'longitude': CTY_INFO[prefix]['Longitude'],
                        'cqz': CTY_INFO[prefix]['CQZone'],
                        'ituz': CTY_INFO[prefix]['ITUZone'],
                        'country': CTY_INFO[prefix]['Country'],
                        'continent': CTY_INFO[prefix]['Continent'],
                        'offset': CTY_INFO[prefix]['GMTOffset']
                    }
                    return(info)

                except KeyError as e: #catching remaining invalid prefixes like call/023 or call/1C0 
                    print("LookUpCall() - Could not identify prefix of " + prefix + "; "+ str(e))
                    self._logger.debug("LookUpCall() - Could not identify prefix of " + prefix + "; "+ str(e))
                    #self._logger.debug(call_info)
                    return(False)
                
                except Exception as e:
                    self._logger.debug("LookUpCall() exception"+ str(e))
                    #self._logger.debug(call_info)
                    return(False)

                else:   # busted call
                    return(False)

####################################################################################################

class Spot(object):
        """Split up a DXCluster line and return the individual fields"""
        def __init__(self, raw_spot):
                #super(Spot, self).__init__()
                self._logger = get_configured_logger(root_logger_name)
                self._logger.propagate = True #send all log events to higher logger which has a handler
                self.raw_spot = raw_spot
                self.valid = None
                self.dx_call = None
                self.spotter_call = None
                self.spotter_station = None
                self.frequency = None
                self.time = None
                self.utc  = ""
                self.comment = ""
                self.mode = None
                self.snr = ''
                self.wpm = ''
                self.band = None
                self.locator = None
                if self.__process_spot(raw_spot):
                    self.dx_station = Station(self.dx_call)
                    self.spotter_station = Station(self.spotter_call)
                    self.spot_fixup()
                    if self.dx_station.valid & self.spotter_station.valid:
                        self.valid = True
                    else:
                        self.valid = False
                else:
                    self.dx_station = None
                    self.valid = False


        def spot_fixup(self):
                comment=self.comment
                mode=self.mode
                snr=''
                df=''
                wpm=''
                cc=comment.split()
                #if len(cc)==0:
                #        pass
                if 'CW' in comment.upper():
                        mode="CW"
                        if len(cc)>2 and cc[2]=='dB':
                            snr=cc[1]
                        if len(cc)>4 and cc[4]=='WPM':
                            wpm=cc[3]
                else:
                    FT_MODES=["FT8","FT4"]
                    OTHER_MODES=["RTTY","PSK31","PSK63","PSK125",
                                  "JT9","JT65","SIM31","OPERA",
                                  "SSB","LSB","USB"]
                    for m in FT_MODES+OTHER_MODES:
                        if m in comment.upper():
                            mode=m
                            if m in FT_MODES:
                                idx1 = comment.find('dB')
                                if idx1>0:
                                    snr = comment[4:(idx1-1)]
                                idx2 = comment.find('Hz')
                                if idx2>0:
                                    df = comment[(idx1+2):(idx2-1)]
                            break
                        
                if mode!='FT8' and mode!='FT4' and False:
                    freqx=self.frequency
                    if int(float(freqx))==144489 or int(float(freqx))==70091 or \
                       int(float(freqx))== 50276 or int(float(freqx))==28076 or \
                       int(float(freqx))== 24917 or int(float(freqx))==21076 or \
                       int(float(freqx))== 18102 or int(float(freqx))==14076 or \
                       int(float(freqx))== 10138 or int(float(freqx))== 7076 or \
                       int(float(freqx))==  5357 or int(float(freqx))== 3576 or \
                       int(float(freqx))==  1838 or int(float(freqx))==  474 or \
                       int(float(freqx))==   136:
                        mode="JT65"
                
                self.mode=mode
                #                print "mode=",mode
                self.snr = snr
                self.wpm = wpm
                self.df  = df


        def convert_freq_to_band(self, freq):
                """converts a frequency into the band and looks up the mode"""
                band = 0
                mode = "unknown"
                if ((freq >=135) and (freq <=138)): 
                        band = 2190
                        mode = "CW"
                elif ((freq >=1800) and (freq <=2000)): 
                        band = 160
                        if ((freq >=1800) and (freq <=1838)):
                                mode = "CW"
                        elif ((freq >1838) and (freq <=1840)):
                                mode = "DIGITAL"
                        elif ((freq >1840) and (freq <=2000)):
                                mode = "LSB"
                elif ((freq >=3500) and (freq <=4000)): 
                        band = 80
                        if ((freq >=3500) and (freq <=3580)):
                                mode = "CW"
                        elif ((freq >3580) and (freq <=3600)):
                                mode = "DIGITAL"
                        elif ((freq >3600) and (freq <=4000)):
                                mode = "LSB"
                elif ((freq >=5000) and (freq <=5500)): 
                        band = 60
                elif ((freq >=7000) and (freq <=7300)): 
                        band = 40
                        if ((freq >=7000) and (freq <=7040)):
                                mode = "CW"
                        elif ((freq >7040) and (freq <=7050)):
                                mode = "DIGITAL"
                        elif ((freq >7050) and (freq <=7300)):
                                mode = "LSB"
                elif ((freq >=10100) and (freq <=10150)): 
                        band = 30
                        if ((freq >=10100) and (freq <=10140)):
                                mode = "CW"
                        elif ((freq >10140) and (freq <=10150)):
                                mode = "DIGITAL"
                elif ((freq >=14000) and (freq <=14350)): 
                        band = 20
                        if ((freq >=14000) and (freq <=14070)):
                                mode = "CW"
                        elif ((freq >14070) and (freq <=14099)):
                                mode = "DIGITAL"
                        elif ((freq >14100) and (freq <=14350)):
                                mode = "USB"
                elif ((freq >=18068) and (freq <=18268)): 
                        band = 17
                        if ((freq >=18068) and (freq <=18095)):
                                mode = "CW"
                        elif ((freq >18095) and (freq <=18110)):
                                mode = "DIGITAL"
                        elif ((freq >18110) and (freq <=18268)):
                                mode = "USB"
                elif ((freq >=21000) and (freq <=21450)): 
                        band = 15
                        if ((freq >=21000) and (freq <=21070)):
                                mode = "CW"
                        elif ((freq >21070) and (freq <=21150)):
                                mode = "DIGITAL"
                        elif ((freq >21150) and (freq <=21450)):
                                mode = "USB"
                elif ((freq >=24890) and (freq <=24990)): 
                        band = 12
                        if ((freq >=24890) and (freq <=24915)):
                                mode = "CW"
                        elif ((freq >24915) and (freq <=24930)):
                                mode = "DIGITAL"
                        elif ((freq >24930) and (freq <=24990)):
                                mode = "USB"
                elif ((freq >=28000) and (freq <=29700)): 
                        band = 10
                        if ((freq >=28000) and (freq <=28070)):
                                mode = "CW"
                        elif ((freq >28070) and (freq <=28190)):
                                mode = "DIGITAL"
                        elif ((freq >28300) and (freq <=29700)):
                                mode = "USB"
                elif ((freq >=50000) and (freq <=54000)): 
                        band = 6
                        if ((freq >=50000) and (freq <=50100)):
                                mode = "CW"
                        elif ((freq >50100) and (freq <=50500)):
                                mode = "USB"
                        elif ((freq >50500) and (freq <=51000)):
                                mode = "DIGITAL"
                elif ((freq >=70000) and (freq <=71000)): 
                        band = 4
                        mode = "unknown"
                elif ((freq >=144000) and (freq <=148000)): 
                        band = 2
                        if ((freq >=144000) and (freq <=144150)):
                                mode = "CW"
                        elif ((freq >144150) and (freq <=144400)):
                                mode = "USB"
                        elif ((freq >144400) and (freq <=148000)):
                                mode = "unknown"
                elif ((freq >=220000) and (freq <=226000)): 
                        band = 1.25 #1.25m
                        mode = "unknown"
                elif ((freq >=420000) and (freq <=470000)): 
                        band = 0.7 #70cm
                        mode = "unknown"
                elif ((freq >=902000) and (freq <=928000)): 
                        band = 0.33 #33cm US
                        mode = "unknown"
                elif ((freq >=1200000) and (freq <=1300000)): 
                        band = 0.23 #23cm
                        mode = "unknown"
                elif ((freq >=2390000) and (freq <=2450000)): 
                        band = 0.13 #13cm
                        mode = "unknown"
                elif ((freq >=3300000) and (freq <=3500000)): 
                        band = 0.09 #9cm
                        mode = "unknown"
                elif ((freq >=5650000) and (freq <=5850000)): 
                        band = 0.053 #5.3cm
                        mode = "unknown"
                elif ((freq >=10000000) and (freq <=10500000)): 
                        band = 0.03 #3cm
                        mode = "unknown"
                elif ((freq >=24000000) and (freq <=24050000)): 
                        band = 0.0125 #1,25cm
                        mode = "unknown"
                elif ((freq >=47000000) and (freq <=47200000)): 
                        band = 0.0063 #6,3mm
                        mode = "unknown"
                else:
                        band = 0
                        mode = "unknown"
                return(band, mode)
                
        def __process_spot(self, raw_string):
                # Fix-up history spots so they can be parsed also
                if raw_string.strip()[0:5]!='DX de':
                    try:
                        a=raw_string.strip().split(' ')
                        #print('a=',a)
                        self.frequency = float(a[0])

                        self.spotter_call = a[-1].replace('<','').replace('>','')
                                
                        self.dx_call = a[2]
                        self.comment = a[12]
                        time_temp = a[10]
                        #print('time_temp=',time_temp)
                        self.utc=time_temp
                        self.time = datetime.utcnow().replace(hour=int(time_temp[0:2]), \
                                                              minute=int(time_temp[2:4]), second=0, \
                                                              microsecond = 0, tzinfo=UTC)
                        self.locator = ''
                        self.band, self.mode = self.convert_freq_to_band(self.frequency)
                        
                        #print('Pre-pending ...')
                        #raw_string='DX de HISTO:'+raw_string
                        return(True)
                    except:
                        pass
                    
                """Chop Line from DX-Cluster into pieces and return a dict with the spot data"""
                try:
                        spotter_call_temp = re.match(r'[A-Za-z0-9\/]+[:$]', raw_string[6:15])
                        if spotter_call_temp:
                                self.spotter_call = re.sub(':', '', spotter_call_temp.group(0))
                        else:
                                self._logger.debug("Missing Semicolon ?!")

                                # JBA - fix problem with some rbn nodes named AC0C-1 or JH7CSU1
                                #self.spotter_call = re.sub(r'[^A-Za-z0-9\/]+', '', raw_string[6:15])
                                #self.spotter_call = re.sub(r'[^A-Za-z0-9\/]+-', '', raw_string[6:15])
                                tmp = re.sub(r'[^A-Za-z0-9\/]+-', '', raw_string[6:15])
                                self.spotter_call = tmp.split('-')[0]
                                if self.spotter_call[-2]!='/' and ord(self.spotter_call[-1])<ord('A'):
                                    self.spotter_call=self.spotter_call[:-1]

                        # JBA - fix since some spots are longer than normal
                        raw_string = raw_string.strip()
                        n=len(raw_string)-75
                        if n>0:
                            raw_string=raw_string[n:]
                                                            
                        frequency_temp = re.search(r'[0-9\.]{5,12}', raw_string[10:25])
                        if frequency_temp: 
                                self.frequency = float(frequency_temp.group(0))
                        else:
                                self._logger.debug("RegEx for Frequency didn't work")
                                self.frequency = float(re.sub(r'[^0-9\.]+', '', raw_string[16:25]))
                                self._logger.error("__process_spot(): Frequency incorrect; "+frequency_temp)
                                raise Exception("Could not decode frequency")

                        self.dx_call = re.sub(r'[^A-Za-z0-9\/]+', '', raw_string[26:38])

                        # For debugging problems with specific calls
                        #if self.frequency>7000 and self.frequency<7020:
                        #    self.dx_call = 'CE0YHO'

                        self.comment = re.sub(r'[^\sA-Za-z0-9\.,;\#\+\-!\?\$\(\)@\/]+', ' ', raw_string[39:69])
                        time_temp = re.sub(r'[^0-9]+', '', raw_string[70:74])
                        self.utc=time_temp
                        self.time = datetime.utcnow().replace(hour=int(time_temp[0:2]), \
                                                              minute=int(time_temp[2:4]), second=0, \
                                                              microsecond = 0, tzinfo=UTC)
                        self.locator = re.sub(r'[^A-Za-z0-9]+', '', raw_string[75:80])
                        self.band, self.mode = self.convert_freq_to_band(self.frequency)
                        return(True)
                except Exception as e:
                        if False:
                                print("Problem in Spot Proc")
                                print("e=",str(e))
                                pprint(vars(self))
                        self._logger.error(str(e)) 
                        self._logger.exception("Problem in Spot Processing")
                        return(False)
                        
####################################################################################################

class WWV(object):
        
        #------------------Constructor --------------------
        def __init__(self, raw_wwv):
        #       super(Station, self).__init__()
                self._logger = get_configured_logger(root_logger_name)
                self._logger.propagate = True #send all log events to higher logger which has a handler
                self.station = None
                self.time = None
                self.a = None
                self.sfi = None
                self.k = None
                self.expk = None
                self.r = None
                self.aurora = False
                self.valid = False
                self.counter = 0
                if self.__process_wwv(raw_wwv):
                        self.valid = True
                
        def __process_wwv(self, wwv):
                """Chop Line from DX-Cluster into pieces and return WWV data"""
                try:
                        if re.match('^WWV', wwv) or re.search('^WCY', wwv):
                                if re.search(r'\s[\-A-Z0-9/]{3,10}\s', wwv[6:20], re.I):
                                        station =  re.search(r'\s[\-A-Z0-9/]{3,10}\s', wwv[6:20], re.I).group(0)
                                        station = station.lstrip().rstrip()
                                        station = Station(station)
                                        if station:
                                                self.station = station
                                        else:
                                                raise Exception("Callsign wrong")
                                                
                                if re.search(r'<[\d]{2}>', wwv):
                                        time_temp = re.search(r'<[\d]{2}>', wwv).group(0)
                                        time_temp = re.search(r'[\d]{2}', time_temp).group(0)
                                        time_temp = int(time_temp)
                                        self.time = datetime.utcnow().replace(hour=time_temp, minute=0, second=0, microsecond=0, tzinfo=UTC)

                                if re.search(r'A=\d{1,3}', wwv):
                                        temp = re.search(r'A=\d{1,3}', wwv).group(0)
                                        temp = re.sub('A=', '', temp)
                                        self.a = int(temp)
                                else:
                                        raise Exception("could not decode A")
                                        
                                if re.search(r'SFI=\d{1,3}', wwv):
                                        temp = re.search(r'SFI=\d{1,3}', wwv).group(0)
                                        temp = re.sub('SFI=', '', temp)
                                        self.sfi = int(temp)
                                else:
                                        raise Exception("could not decode SFI")
                                        
                                if re.search(r'\sK=\d{1,3}', wwv):
                                        temp = re.search(r'\sK=\d{1,3}', wwv).group(0)
                                        temp = re.sub(r'\sK=', '', temp)
                                        self.k = int(temp)
                                else:
                                        raise Exception("could not decode K")

                                if re.search(r'expK=\d{1,3}', wwv):
                                        temp = re.search(r'expK=\d{1,3}', wwv).group(0)
                                        temp = re.sub('expK=', '', temp)
                                        self.expk = int(temp)
                                        
                                if re.search(r'R=\d{1,3}', wwv):
                                        temp = re.search(r'R=\d{1,3}', wwv).group(0)
                                        temp = re.sub('R=', '', temp)
                                        self.r = int(temp)
                                        
                                if re.search(r'Au=\S{2,3}', wwv):
                                        temp = re.search(r'Au=\S{2,3}', wwv).group(0)
                                        temp = re.sub('Au=', '', temp)
                                        if temp == "no":
                                                self.aurora = False
                                        elif temp == "yes":
                                                self.aurora = True
                                
                                self._logger.info("Stored WWV successfully")
                                self._logger.info(self.station.call + " " + self.time.strftime("%d.%m.%Y %H:%M:%S") + " A:" + str(self.a) + " SFI:" + str(self.sfi) + " K:" + str(self.k) + " expK:" + str(self.expk) + " R:" + str(self.r) + " Aurora:" + str(self.aurora))
                                return(True)
                        else:
                                raise Exception("missing starting letters 'WWV'")
                except Exception as e:
                        self._logger.error(str(e)) 
                        self._logger.error("Problem in WWV Processing")
                        return(False)



class Comment(object):
        #------------------Constructor --------------------
        def __init__(self, raw_comment):
        #       super(Station, self).__init__()
                self._logger = get_configured_logger(root_logger_name)
                self._logger.propagate = True #send all log events to higher logger which has a handler

                self.station = None
                self.time = None
                self.text = None
                self.valid = False
                if self.__process_comment(raw_comment):
                        self.valid = True
        
        def __process_comment(self, comment):
                """Chop Line from DX-Cluster into pieces and return Comment data"""
                try:
                        if re.match('^To ALL de', comment, re.I):
                                if re.search(r'de [\-A-Z0-9/]{4,15}', comment[6:20], re.I):
                                        station = re.search(r'de [\-A-Z0-9/]{4,15}', comment[6:20], re.I).group(0)
                                        station = re.sub(r'de ','', station)
                                        station = station.upper()
                                        self.station = Station(station)
                                        if not self.station.valid:
                                                raise Exception("Callsign invalid")
                                else:
                                        raise Exception("Callsign invalid")

                                self.time = datetime.utcnow().replace(tzinfo = UTC)
                                self.text = "hi"
                                if re.search(r':[\S\s]+', comment):
                                        text = re.search(r':[\S\s]+', comment).group(0)
                                        text = re.sub(': ', '', text)
                                        text = re.sub(r'[^A-Za-z0-9\.,@&\?;\-\#\+!\$\(\)\/]+', ' ', text) #sanitize input
                                        text = text.rstrip() #chop off tailing whitespaces
                                        self.text = text
                                else:
                                        raise Exception("Comment text not processible; Missing semicolon?")
                                
                                self._logger.debug("Comment successfully processed")
                                self._logger.debug(self.station.call + " " + self.time.strftime("%d.%m.%Y %H:%M:%S") + " " + self.text)
                                return(True)
                                
                        else:
                                raise Exception("missing starting letters 'TO ALL'")
                
                except Exception as e:
                        self._logger.error(str(e))
                        self._logger.error("Problem in Comment Processing")
                        return(False)
