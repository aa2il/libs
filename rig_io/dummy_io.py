############################################################################################

# Dummy IO - J.B.Attili - 2019

# Dummied-up socket I/O routines so codes will work if no rig connection.

############################################################################################

VERBOSITY=0

############################################################################################

# Object with dummy connection
class no_connect:
    def __init__(self,host=0,port=0):
        self.s          = None
        self.active     = False
        self.connection = 'NONE'
        self.wpm        = 0
        self.freq       = 0
        self.band       = ''
        self.mode       = ''
        self.pl_tone    = 0
        self.fldigi_active=False
        self.flrig_active=False
        self.host=host
        self.port=port
        self.rig_type   = None
        self.rig_type2  = None
        self.tlast      = None

    def get_band(self,frq=None):
        return 0
        
    def get_ant(self):
        return 0
        
    def set_ant(self,a):
        return 0
        
    def get_fldigi_mode(self):
        return '0'

    def get_mode(self):
        return 'CW'
        
    def set_mode(self,mode):
        return '0'
        
    def get_freq(self,VFO='A'):
        return 0

    def set_freq(self,f,VFO='A'):
        if VERBOSITY>0:
            print('Ignoring call to SET_FREQ')
        return 0

    def set_vfo(self,rx=None,tx=None):
        return
    
    def send(self,cmd):
        return 0

    def set_log_fields(self,fields):
        return 0
        
    def set_call(self,call):
        return 0

    def get_serial_out(self):
        return 0
    
    def get_response(self,cmd):
        return ''

    def get_info(self):
        return ''
    
    def set_speed(self,wpm):
        return 0

    def get_PLtone(self):
        return 0
    
    def get_filters(self,VFO='A'):
        #return [None,None]
        return ['Wide','500 Hz']

    def tuner(self,opt):
        return 0
    
    def read_meter(self,meter):
        return 0

    def get_position(self):
        return [None,None]

    def split_mode(self,opt):
        return 0
    
    def set_position(self,pos):
        return 0
