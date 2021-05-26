#! /usr/bin/python
##############################################################################################################

# Hamlib Server - J.B.Attili - 2019

# Functions that implement a minimal subset of the hamlib protocal.
# Just enough to make WSJTX & FLDIGI happy (with a few additions).
#
# Based on code by James C. Ahlstrom 2012
#
# Port scheme:
#     Port       SDR RX     Rig VFO
#     4532         0          A              This is the default for hamlib
#     4575         0          A              This is what we often use as something else to avoid confusion
#     4576         1          A
#     4577         2          A
#     4578         3          A
#     4579         4          A
#     4580         5          A
#
#     4675         0          B
#     4676         1          B
#     4677         2          B
#     4678         3          B

# This module creates a Hamlib TCP server that implements the rigctl protocol.  To start the server,
# run "python hamlibserver.py" from a command line.  To exit the server, type control-C.  Connect a
# client to the server using localhost and port 4575.  The TCP server will imitate a software defined
# radio, and you can get and set the frequency, etc.

# You can test it with "rigctl -m 2 -r localhost:4575".

# To Do:
# Test stand alone under python 3

##############################################################################################################

# !!!!!!!!!!! BIG NOTE !!!!!!!!!!!!!!
# As used right now, this seems sluggish.  It is probably bx I'm using threading instead of multiprocessing
# libraries to spawn various threads.  According to the Python Docs:
#
# CPython implementation detail: In CPython, due to the Global Interpreter Lock, only one thread can execute
# Python code at once (even though certain performance-oriented libraries might overcome this limitation).
# If you want your application to make better use of the computational resources of multi-core machines,
# you are advised to use multiprocessing. However, threading is still an appropriate model if you want
# to run multiple I/O-bound tasks simultaneously.
#
# So at some point, let's try to multiprocessing instead.  Although the APIs are very similar, there is
# the issue of sharing data.  For threading, this is trivial but for multiprocessing, it looks a bit
# tricky.  STUDY UP B4 TRYING THIS!!!!!!!!

############################################################################################

import sys, time, socket, string
from pprint import pprint
import threading

DEFAULT_VERBOSITY=0     # 0=quiet, 1=enough to see hand-shaking, 2=detailed

##############################################################################################################

# A possible response to the "dump_state" request
dump1 = """ 2
2
2
150000.000000 1500000000.000000 0x1ff -1 -1 0x10000003 0x3
0 0 0 0 0 0 0
0 0 0 0 0 0 0
0x1ff 1
0x1ff 0
0 0
0x1e 2400
0x2 500
0x1 8000
0x1 2400
0x20 15000
0x20 8000
0x40 230000
0 0
9990
9990
10000
0
10 
10 20 30 
0x3effffff
0x3effffff
0x7fffffff
0x7fffffff
0x7fffffff
0x7fffffff
"""

# Another possible response to the "dump_state" request
dump2 = """ 0
2
2
150000.000000 30000000.000000  0x900af -1 -1 0x10 000003 0x3
0 0 0 0 0 0 0
150000.000000 30000000.000000  0x900af -1 -1 0x10 000003 0x3
0 0 0 0 0 0 0
0 0
0 0
0
0
0
0


0x0
0x0
0x0
0x0
0x0
0
"""


RIG_MODEL_NETRIGCTL = 2
RIG_ITU_REGION2 = 2

# See dump_state in rigctl_parse.c for what this means.
dump3 = "".join([
  "0\n", # protocol version
  "%d\n" % RIG_MODEL_NETRIGCTL,
  "%d\n" % RIG_ITU_REGION2,
  "0 0 0 0 0 0 0\n",
  "0 0 0 0 0 0 0\n",
  "0 0\n",
  "0 0\n",
  "0\n",
  "0\n",
  "0\n",
  "0\n",
  "\n",
  "\n",
  "0x0\n",
  "0x0\n",
  "0x0\n",
  "0x0\n",
"0x0\n",
  "0\n",
])


# This class is created for each connection to the server.  It services requests from each client
class HamlibHandler:
  
  SingleLetters = {		# convert single-letter commands to long commands
    'f':'freq',
    'm':'mode',
    't':'ptt',
    'v':'vfo',
    's':'split',
    #'w':'command',
    'y':'ant',
    '_':'info',
    '1':'caps',
    'q':'quit',
  }
  
  def __init__(self, app, sock, address):
    self.app = app		# Reference back to the "hardware"
    self.sock = sock
    sock.settimeout(0.5)
    self.address = address
    self.received = ''
    self.P = self.app.P
    self.modeB = None
    self.VERBOSITY = DEFAULT_VERBOSITY
    
    h = self.Handlers = {}
    h[''] = self.ErrProtocol
    h['dump_state']	= self.DumpState
    h['get_caps']	= self.GetCaps
    h['get_freq']	= self.GetFreq
    h['set_freq']	= self.SetFreq
    h['get_mode']	= self.GetMode
    h['set_mode']	= self.SetMode
    h['chk_vfo']	= self.ChkVfo
    h['get_vfo']	= self.GetVfo
    h['set_vfo']	= self.SetVfo
    h['get_split']	= self.GetSplit
    h['get_ptt']	= self.GetPtt
    h['set_ptt']	= self.SetPtt
    h['get_ant']	= self.GetAnt
    h['set_ant']	= self.SetAnt
    #h['get_command']	= self.SendCommand
    #h['set_command']	= self.SendCommand
    h['get_info']	= self.GetInfo
    h['set_info']	= self.GetInfo
    h['get_quit']	= self.Quit
    h['set_quit']	= self.Quit

    if self.app.port==4675 and False:
      self.VERBOSITY = 2
      
    
  # Send text back to the client
  def Send(self, text):
    try:
      if type(text) is list:
        text='\n'.join(text)
      self.sock.sendall(text.encode())
    except socket.error:
      print('HAMLIB_SERVER: SEND: Socket error - closing socket')
      self.sock.close()
      self.sock = None
      
  # Create a string reply of name, value pairs, and an ending integer code.
  def Reply(self, *args):	        # args is name, value, name, value, ..., int
    if self.extended:
      # Use extended format
      t = "%s:" % self.cmd		# Extended format echoes the command and parameters
      for param in self.params:
        t = "%s %s" % (t, param)
      t += self.extended
      for i in range(0, len(args) - 1, 2):
        t = "%s%s: %s%c" % (t, args[i], args[i+1], self.extended)
      t += "RPRT %d\n" % args[-1]
      
    elif len(args) > 1:
      # Use simple format
      t = ''
      for i in range(1, len(args) - 1, 2):
        t = "%s%s\n" % (t, args[i])
        
    else:
      # No names; just the required integer code
      t = "RPRT %d\n" % args[0]
      
    if self.VERBOSITY>=1:
      print('HAMLIB_SERVER: REPLY:',t.rstrip(),'on port',self.app.port)
    self.Send(t)
    
  # Invalid parameter
  def ErrParam(self):
    if self.VERBOSITY>0:
      print('HAMLIB_SERVER: Invalid Param on port',self.app.port)
      #sys.exit(0)
    self.Reply(-1)
    
  # Command not implemented
  def UnImplemented(self):
    self.cmd2=''
    if self.VERBOSITY>0 or True:
      print('*** ERROR *** HAMLIB_SERVER: Unimplemented command:',self.cmd,'on port',self.app.port)
      #sys.exit(0)
    self.Reply(-4)
    
  # Protocol error
  def ErrProtocol(self):
    if self.VERBOSITY>0:
      print('HAMLIB_SERVER: Invalid protocal on port',self.app.port)
      #sys.exit(0)
    self.Reply(-8)
    
  # main processing loop that reads and satisfies requests.
  def Process(self):
    if not self.sock:
      if self.VERBOSITY>=2:
        print('HAMLIB_SERVER: Process: NULL SOCKET on port',self.app.port)
      return 0
    
    # Read any data from the socket
    try:
      text = self.sock.recv(1024).decode("utf-8") 
    except socket.timeout:	# This does not work
      if self.VERBOSITY>=2:
        print('HAMLIB_SERVER: Process: Socket timeout on port',self.app.port)
    except socket.error:	# Nothing to read
      if self.VERBOSITY>=2:
        print('HAMLIB_SERVER: Process: Socket error on port',self.app.port)
    else:					# We got some characters
      self.received += text
      if self.VERBOSITY>=2:
        print('HAMLIB_SERVER: Process: text=',text.rstrip(),' on port',self.app.port)
      
    if '\n' in self.received:	# A complete command ending with newline is available
      cmd, self.received = self.received.split('\n', 1)	# Split off the command, save any further characters
    else:
      return 1
    cmd = cmd.strip()		# Here is our command
    self.cmd=cmd
    if self.VERBOSITY>=1:
      print('HAMLIB_SERVER: Got command', cmd,'on port',self.app.port)
    
    # ??? Indicates a closed connection?
    if not cmd:
      print('HAMLIB_SERVER: Empty command :-(')
      self.sock.close()
      self.sock = None
      return 0
    
    # Parse the command and call the appropriate handler
    if cmd[0] == '+':			# rigctld Extended Response Protocol
      self.extended = '\n'
      cmd = cmd[1:].strip()
    elif cmd[0] in ';|,':		# rigctld Extended Response Protocol
      self.extended = cmd[0]
      cmd = cmd[1:].strip()
    else:
      self.extended = None

    if cmd[0:1] == '\\':		# long form command starting with backslash
      args = cmd[1:].split()
      self.cmd = args[0]
      self.params = args[1:]
      self.Handlers.get(self.cmd, self.UnImplemented)()
    else:

      #### Handle compound commands, e.g.  M USB 0 X USB 0 #####
      # Need to flush out how individual command strip off args - see SetMode
      # Also need to add handlers for 'X' and 'I'
      self.cmd2=''
      Done=False
      while not Done:
      
        # single-letter command
        self.params = cmd[1:].strip()
        cmd = cmd[0:1]
        if self.VERBOSITY>=1:
          print('HAMLIB_SERVER: Process: cmd=',cmd)
        try:
          t = self.SingleLetters[cmd.lower()]
        except KeyError:
          print('HAMLIB_SERVER: KeyError')
          Done=True
          self.cmd=cmd
          self.UnImplemented()
        else:
          #if cmd in string.uppercase:
          if cmd.isupper():
            self.cmd = 'set_' + t
          else:
            self.cmd = 'get_' + t
          if self.VERBOSITY>=1:
            print('HAMLIB_SERVER: Process: cmd1=',self.cmd)
          self.Handlers.get(self.cmd, self.UnImplemented)()
          if self.VERBOSITY>=1:
            print('HAMLIB_SERVER: Process: cmd2=',self.cmd2)

          if len(self.cmd2)==0:
            Done=True
          else:
            # Done=True
            cmd = self.cmd2
            if self.VERBOSITY>=1:
              print('HAMLIB_SERVER: Process: Try again, cmd=',cmd)

    return 1
  
  # These are the handlers for each request
  def DumpState(self):
    if self.VERBOSITY>=1:
      print('HAMLIB_SERVER: Dump State on port',self.app.port)
    self.Send(dump2)

  def GetCaps(self):
    if self.VERBOSITY>=1:
      print('HAMLIB_SERVER: Get Caps on port',self.app.port)
    caps=['Model name:\tFT-2000', 'Mfg name:\tYaesu']
    self.Send(caps)

  # Routine to associate SDR RX number and RIG VFO with a prot number
  def port2rx(self):
      port = self.app.port
      if port==4532 or port==4632 or port==4732:
        irx = 0
        vfo='A'
      elif port==4533 or port==4633 or port==4733:
        irx = 0
        vfo='B'
      elif port>=4675:
        irx = port - 4675
        vfo='B'
      else:
        irx = port - 4575
        vfo='A'

      return [irx,vfo]

  # Return current freq
  def GetFreq(self):
    if self.P:
      [irx,vfo] = self.port2rx()
      #print('HAMLIB_SERVER: GetFreq:',self.app.port,irx,vfo)
      if self.P.SO2V:
        frq=self.P.sock.get_freq(vfo)
        self.Reply('Frequency', int(frq+0.5) , 0)
      elif self.P.NUM_RX==0:
        frq=self.P.sock.freq    # *1e3
        self.Reply('Frequency', int(frq+0.5) , 0)
      else:
        self.app.freq = int( self.P.FC[irx] + 0.5)
        #print(self.P.FC)
        #print(self.P.FC[irx])
        self.Reply('Frequency', self.app.freq, 0)
    else:
      #print('HAMLIB_SERVER: GetFreq', self.app.freq)
      self.Reply('Frequency', self.app.freq, 0)

  # Set freq
  def SetFreq(self):
    if self.VERBOSITY>=1:
      print('HAMLIB_SERVER: SetFreq',self.params,'on port',self.app.port)
    try:
      x = float(self.params)
      self.Reply(0)
    except:
      self.ErrParam()
    else:
      x = int(x + 0.5)
      self.app.freq = x

    if self.P:
      [irx,vfo] = self.port2rx()
      #print('HAMLIB_SERVER:.SetFreq: ============================ port=',self.app.port,'/t rx=',irx,'/t frq=',x)
      if self.P.SO2V or self.P.NUM_RX==0:
        print('HAMLIB_SERVER: SetFreq:',irx,vfo,x)
        self.P.sock.set_freq(x*1e-3,vfo)
      else:
        self.P.NEW_FREQ[irx] = x
        self.P.VFO[irx]      = vfo
        self.P.FREQ_CHANGE   = True

  # Return current mode
  def GetMode(self):
    #print('HAMLIB_SERVER: GetMode on port',self.app.port,self.P.SO2V)
    if self.P.SO2V:
      [irx,vfo] = self.port2rx()
      #print('HAMLIB_SERVER: GetMode:',irx,vfo)
      if vfo=='A':
        rig_mode = self.P.sock.get_mode(vfo)
      else:
        if not self.modeB:
          rig_mode   = self.P.sock.get_mode(vfo)
          self.modeB = rig_mode
        rig_mode = self.modeB
      #print('HAMLIB_SERVER: GetMode:',irx,vfo,rig_mode)
      self.Reply('Mode', rig_mode, 'Passband', self.app.bandwidth, 0)
    elif self.P.NUM_RX==0:
      rig_mode = self.P.sock.mode
      self.Reply('Mode', rig_mode, 'Passband', self.app.bandwidth, 0)
    else:
      self.Reply('Mode', self.app.mode, 'Passband', self.app.bandwidth, 0)
    
  # Set mode
  def SetMode(self):
    if self.VERBOSITY>=1:
      print('HAMLIB_SERVER: SetMode',self.params,'on port',self.app.port)
    try:
      #mode, bw = self.params.split()
      a=self.params.split()
      if len(a)==1:
        # NONE mode from FLDIGI is mapped to IQ
        mode = 'IQ'
        bw   = a[0]
      else:
        mode = a[0]
        bw   = a[1]
        if len(a)>2:
          self.cmd2=' '.join(a[2:])
        
      bw = int(float(bw) + 0.5)
      self.Reply(0)
    except:
      self.ErrParam()
    else:
      self.app.mode = mode
      self.app.bandwidth = bw

    if self.P:
      [irx,vfo] = self.port2rx()
      #print('HAMLIB_SERVER:.SetMode: ============================ port=',self.app.port,'/t mode/bw=',mode,bw)
      if self.P.SO2V or self.P.NUM_RX==0:
        print('HAMLIB_SERVER: SetMode:  mode/irx/vfo=',mode,irx,vfo)
        self.P.sock.set_mode(mode,vfo)
        if vfo=='B':
          self.modeB=mode
      else:
        self.P.NEW_MODE    = mode
        self.P.MODE_CHANGE = True
      #print('^^^^^^^^^^^^^^^^^^^^^^^^^^^^^ NEED to ADD CODE to SET BANDWIDTH **********************\n')

  # Check VFO
  def ChkVfo(self):
    print('HAMLIB_SERVER: Chk VFO on port',self.app.port)
    self.Reply('CHKVFO', 0, 0)
    
  # Return current VFO
  def GetVfo(self):
    if self.VERBOSITY>=1:
      print('HAMLIB_SERVER: Get VFO on port',self.app.port)
    [irx,vfo] = self.port2rx()
    self.app.vfo = "VFO"+vfo
    self.Reply('VFO', self.app.vfo, 0)
    
  # Set current VFO
  def SetVfo(self):
    if self.VERBOSITY>=1:
      print('HAMLIB_SERVER: Set VFO on port',self.app.port)
    try:
      x = self.params
      self.Reply(0)
    except:
      self.ErrParam()
    else:
      self.app.vfo = "VFO"+x

    if self.P:
      [irx,vfo] = self.port2rx()
      print('HAMLIB_SERVER:.SetVfo: ============================ port=',self.app.port,'/t rx=',irx,'/t vfo=',vfo)
      if self.P.SO2V or self.P.NUM_RX==0:
        print('HAMLIB_SERVER: SetVfo:',irx,vfo,x)
        self.P.sock.set_vfo(x)
      else:
        self.P.VFO[irx] = x
    
  # Return split state
  def GetSplit(self):
    if self.VERBOSITY>=1:
      print('HAMLIB_SERVER: Get SPLIT on port',self.app.port)
      print('*** Get Split is NOT FULLY IMPLEMENTED ***')
    [irx,vfo] = self.port2rx()
    self.app.tx_vfo = "VFO"+vfo
    self.Reply('Split', self.app.split, 'TX VFO',self.app.tx_vfo,0)

  # Send a command directly to the rig
  def SendCommand(self):
    print('HAMLIB_SERVER: SEND COMMAND:',self.cmd,self.params)
    print('This is not fully implemented yet')
    
  # Return rig info
  def GetInfo(self):
    if self.VERBOSITY>=1:
      print('HAMLIB_SERVER: Get Info on port',self.app.port)
    if self.P and hasattr(self.P,'sock'):
      info=self.P.sock.get_info()
      self.Reply('Info', info, 0)
      print('HAMLIB_SERVER: Get Info info=',info)
    else:
      self.Reply('Info', self.app.info, 0)
    
  # Return current antenna
  def GetAnt(self):
    if self.VERBOSITY>=1:
      print('HAMLIB_SERVER: Get Ant on port',self.app.port)
    if self.P:
      ant=self.P.sock.get_ant()
      self.Reply('Ant', ant, 0)
    else:
      self.Reply('Ant', self.app.ant, 0)
    
  # Set antenna port
  def SetAnt(self):
    if self.VERBOSITY>=1:
      print('HAMLIB_SERVER: Set Ant',self.params,'on port',self.app.port)
      print('HAMLIB_SERVER: Set Ant:',self.P.sock.connection)
    if self.P:
      ant=int(self.params)
      print('HAMLIB_SERVER: Set Ant:',ant)
      #if P.sock.connection=='DIRECT':
      self.P.sock.set_ant(ant+1)
    self.Reply(0)
    
  # Return current PTT state
  def GetPtt(self):
    if self.VERBOSITY>=1:
      print('HAMLIB_SERVER: Get PTT on port',self.app.port)
    self.Reply('PTT', self.app.ptt, 0)
    
  # Set PPT
  def SetPtt(self):
    if self.VERBOSITY>=1:
      print('HAMLIB_SERVER: Set PTT',self.params,'on port',self.app.port)
      
    try:
      x = int(self.params)
      self.Reply(0)
    except:
      self.ErrParam()
    else:
      print('x=',x)
      if x:
        self.app.ptt = 1
      else:
        self.app.ptt = 0
      if self.P:
        [irx,vfo] = self.port2rx()
        print('irx/vfo=',irx,vfo)
        self.P.sock.ptt(self.app.ptt,vfo)
      else:
        print('No P!')

  # No-op - ignore command
  def NoOp(self):
    if self.VERBOSITY>=1:
      print('HAMLIB_SERVER: No-op on port',self.app.port)

  def set_verbosity(self,verbosity):
    self.VERBOSITY=verbosity
    print('HAMLIB_SERVER: Setting verbosity to',self.VERBOSITY,'on port',self.app.port)

  def Quit(self):
    print('HAMLIB_SERVER: Quitting on port',self.app.port)
    self.sock.close()
    self.sock = None
  
  def Exit(self):
    print('HAMLIB_SERVER: Exitting on port',self.app.port)
    sys.exit(0)

    
# This is the main application class.  It listens for connectons from clients and creates a server for each one.
class HamlibServer:
  
  def __init__(self,P=None,port=4575,verbosity=DEFAULT_VERBOSITY):
    print('@@@@@@@@@@@@@@ HAMLIB_SERVER:SERVER Init',port)
    self.port = port
    self.P=P
    self.hamlib_clients = []
    self.VERBOSITY=verbosity
    
    # This is the state of the "hardware"
    self.freq   = 29999999
    self.mode   = 'CW'
    self.bandwidth = 2400
    self.vfo    = "VFOA"
    self.ptt    = 0
    self.split  = 0
    self.tx_vfo = 'VFOA'
    self.ant    = 0
    self.info   = 'UNKNOWN'

    self.hamlib_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    self.hamlib_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    self.hamlib_socket.bind(('localhost', port))
    self.hamlib_socket.settimeout(0.1)
    self.hamlib_socket.listen(5)
    #self.hamlib_socket.setblocking(False)

    # Spawn thread to look for new connection
    print('@@@@@@@@@@@@@@@@@@@@@@@ Spawning accepter',port)
    self.worker = threading.Thread(target=self.Accepter, args=(),name='Accepter '+str(port))
    self.worker.setDaemon(True)
    self.worker.start()
    self.accepter_running = True
    
  def Accepter(self):
    print('@!@!@!@!@!@!@! Acceptor started on port',self.port)

    while not self.P.Stopper.isSet():
      time.sleep(1.)
      self.check_connections()

    print('@!@!@!@!@!@!@! Acceptor ended on port',self.port)
    self.accepter_running = False

  def Run(self):
    self.connected=False

    print('HAMLIB_SERVER:SERVER Running on port',self.port)

    while not self.P.Stopper.isSet():
      #print('HAMLIB_SERVER: Running on port',self.port)
 
      while not self.connected and not self.P.Stopper.isSet():
        #print('HAMLIB_SERVER: Waiting for connection on port',self.port)
        time.sleep(1.)
        #self.check_connections()

      n=0
      while self.connected and not self.P.Stopper.isSet():
        time.sleep(.05)

        # Check for any new connections
        #n+=1
        #if n>=20:
        #  n=0
        #  self.check_connections()
            
        # Check if connections are still alive
        for client in self.hamlib_clients:
          ret = client.Process()
          if self.VERBOSITY>=2:
            print('\nHAMLIB_SERVER: Checking client',client,ret,self.port)

	  # False return indicates a closed connection; remove the server
          if not ret:
            self.hamlib_clients.remove(client)
            print('HAMLIB_SERVER: Removed', client.address)
            self.connected=False

    print('HAMLIB_SERVER: waiting for accepeter to stop on port',self.port,' ...')
    while self.accepter_running:
        time.sleep(0.1)
    print('HAMLIB_SERVER: waiting for clients to stop on port',self.port,' ...')
    for client in self.hamlib_clients:
      client.Quit()
    print('HAMLIB_SERVER: Exited on port',self.port)


  # Function to check for new connections
  def check_connections(self):
    P=self.P
    #print('!@#$%^&*()*&^%$#@$%^&*()*&^%$ HAMLIB_SERVER:SERVER: Checking for new connections ...',self.port)

    # Update freq & mode info
    if not P.SO2V or self.P.NUM_RX==0:
      #print("P=",pprint(vars(self.P)))
      port = self.port
      if port==4532 or port==4533 or port==4632 or port==4633 or port==4732 or port==4733:
        irx = 0
      elif port>=4675:
        irx = port - 4675
      else:
        irx = port - 4575
      if irx>=0 and irx<P.NUM_RX:
        self.freq = self.P.FC[irx]
        self.mode = self.P.MODE
      elif irx==0 and P.NUM_RX==0:
        vfo='A'
        self.freq = self.P.sock.freq   # *1e3
        self.mode = self.P.sock.mode
      else:
        print('HAMLIB_SERVER: ERROR - Unknown port',self.port)
        #sys.exit(0)
      #print('\nHAMLIB_SERVER: ============================ port=',self.port,'     frq=',self.freq)

    # Check for new connections
    #print('Checking ...')
    try:
      conn, address = self.hamlib_socket.accept()
    except socket.error:
      # Nothing to see here (i.e. no new connections)
      pass 
    else:
      print('HAMLIB_SERVER: New Connection from', address,'on port',self.port)
      self.hamlib_clients.append(HamlibHandler(self, conn, address))
      self.connected=True

##############################################################################################################      

if __name__ == "__main__":
  print('HAMLIB_SERVER: Starting Hamkib emulator ...',PORT)

  try:
    HamlibServer().Run()
  except KeyboardInterrupt:
    sys.exit(0)
