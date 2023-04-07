#! /usr/bin/python3
################################################################################
#
# tcp_server.py - Rev 1.0
# Copyright (C) 2021-3 by Joseph B. Attili, aa2il AT arrl DOT net
#
#    Simple tcp server to allow clients to communicate to keyer app.
#
# THIS OBJECT NOW ALSO INCLUDES THE CLIENT OBJECT!
# Use tcp_server instead with Server=False - see test program below.
# This was done to lessen the amount of duplicate codes that has to be
# maintaned since the client and server codes are very similar.
#
################################################################################
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
################################################################################

import sys
import socket 
from threading import Thread,Event
import time
import select
import zlib

################################################################################

VERBOSITY=0
SDR_UDP_PORT     = 7373
KEYER_UDP_PORT   = 7474
BANDMAP_UDP_PORT = 7575

################################################################################

# Prototype message handler
def dummy_msg_handler(self,sock,msg):
    id=sock.getpeername()
    print('TCP_SERVER->DUMMY MSG HANDLER: id=',id,'\tmsg=',msg.rstrip())

# Function to open UDP client
def open_udp_client(P,port,msg_handler,BUFFER_SIZE=1024):

    if not port:
        port = KEYER_UDP_PORT
    
    try:
        
        print('Opening UDP client ...')
        udp_client = TCP_Server(P,None,port,Server=False,
                                  BUFFER_SIZE=BUFFER_SIZE,Handler=msg_handler)
        worker = Thread(target=udp_client.Listener,args=(), kwargs={},
                        name='UDP Client' )
        worker.setDaemon(True)
        worker.start()
        P.threads.append(worker)
        return udp_client
    
    except Exception as e:
        
        print('OPEN UDP CLIENT: Exception Raised:\n',e)
        print('--- Unable to connect to UDP socket ---')
        return None
    
    
# TCP Server class
class TCP_Server(Thread):
    
    def __init__(self,P,host,port,Server=False,BUFFER_SIZE=1024,Handler=None): 
        Thread.__init__(self)

        self.P=P
        if not host:
            host='127.0.0.1'
        self.host=host
        self.port=port
        self.Server=Server
        self.BUFFER_SIZE = BUFFER_SIZE
        self.running=False
        if Handler:
            self.msg_handler=Handler
        else:
            self.msg_handler=dummy_msg_handler
        if P and hasattr(P,'Stopper'):
            self.Stopper = P.Stopper
        else:
            self.Stopper = Event()
            
        print('TCP Server: host=',host,'\tport=',port,'\tBuf Size=',self.BUFFER_SIZE,
              '\tHandler=',self.msg_handler)

        # Start the server
        self.StartServer()

################################################################################

    def StartServer(self):
        print('TCP_SERVER->StartServer: Starting ...')
        if self.running:
            self.tcpServer.close()
            #self.socks.remove(self.tcpServer)
        self.tcpServer = socket.socket(socket.AF_INET, socket.SOCK_STREAM) 
        self.tcpServer.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1) # Not sure why we need these?
        if self.Server:
            self.tcpServer.bind((self.host,self.port))                       # Server binds socket to server address
        else:
            self.tcpServer.connect((self.host, self.port))                   # Client connects to server
        self.socks = [self.tcpServer]        
        self.running=True

    def Connect(self,host,port):
        if not host:
            host='127.0.0.1'
        print('TCP_SERVER->Connect: Connecting to',host,port,'\tfrom',self.host,self.port)
        self.tcpServer.connect((host, port))                       # Connect to server
        
    # Function to listener for new connections and/or data from clients
    def Listener(self): 
        print('TCP_SERVER->Listener: Waiting for connections from TCP clients...')
        if self.Server:
            self.tcpServer.listen(4)                                          # Server listens for clients

        # Run until stopper is set
        while not self.Stopper.is_set():
            if VERBOSITY>0:
                print('TCP_SERVER - Listener - Hey 1')
            time.sleep(1)

            # Get list of sockets 
            #print('Getting list ...')
            #readable,writeable,inerror = select.select(self.socks,self.socks,self.socks,0)
            readable,writeable,inerror = select.select(self.socks,[],[],0)
            if VERBOSITY>0:
                print('TCP_SERVER - Listener - readable=',readable,  \
                      '\twriteable=',writeable,'\tinerror=',inerror)
            
            # iterate through readable sockets
            for sock in readable:
                if VERBOSITY>0:
                    print('TCP_SERVER - Listener - Hey 2')

                # Any new connections?
                if self.Server and sock is self.tcpServer:

                    # Server has a new client
                    if VERBOSITY>0:
                        print('TCP_SERVER - Listener - Hey 3')
                    
                    # Accept new connection
                    conn, addr = self.tcpServer.accept()
                    #conn.settimeout(2)
                    conn.setblocking(0)
                    print('LISTENER:\r{}:'.format(addr),'connected')
                    readable.append(conn)
                    self.socks.append(conn)

                    print('LISTENER: New socket:',conn,addr)
                    print('\tSock Name=',conn.getsockname())
                    print('\tPeer Name=',conn.getpeername())
                    #print('\tName Info=',conn.getnameinfo())

                    # Send my name & query name of this client
                    if self.port==SDR_UDP_PORT:
                        name='pySDR'
                    elif self.port==KEYER_UDP_PORT:
                        name='pyKeyer'
                    elif self.port==BANDMAP_UDP_PORT:
                        name='bandmap'
                    else:
                        name='NoName'
                    msg='Name:'+name+'\nName:?\n'
                    conn.send(msg.encode())

                else:

                    # Server and clients read from a client
                    try:
                        
                        if VERBOSITY>0:
                            print('TCP_SERVER - Listener - Hey 4a')
                        ready = select.select([sock], [], [], 1)
                        if ready[0]:
                            data = sock.recv(self.BUFFER_SIZE)
                        else:
                            data=None
                        if VERBOSITY>0:
                            print('TCP_SERVER - Listener - Hey 4b - ready=',ready)
                            
                    except Exception as e:
                        
                        print('Listener: Problem with socket - closing')
                        print( str(e) )
                        print(sock)
                        data=None

                    # Pass data onto message handler
                    if data:
                        
                        # We received a message from a client
                        print('\r{}:'.format(sock.getpeername()),data)
                        try:
                            # Some messages are compressed
                            #print('DATA TYPE:',type(data))
                            data=zlib.decompress(data)
                        except:
                            pass
                        if self.msg_handler:
                            self.msg_handler(self,sock,data.decode())

                    elif ready[0]:
                        
                        # The client seemed to send a msg but we didn't get it
                        try:
                            print('LISTENER:\r{}:'.format(sock.getpeername()),'disconnected')
                            sock.close()
                        except:
                            pass
                        readable.remove(sock)
                        self.socks.remove(sock)
                        
                    else:
                        
                        # Nothing to see here
                        pass
        
        # Close socket
        self.Close()
        
    # Function to close socket
    def Close(self):
        
        self.tcpServer.close()
        print('Listerner: Bye bye!')

################################################################################

    # Function to send a message to all writeable peers
    # Need to modify this to send to only one peer?
    def Send(self,msg):
        self.Broadcast(msg)

    # Function to broadcast a message to all connected clients
    def Broadcast(self,msg):

        # Get list of sockets
        try:
            readable,writeable,inerror = select.select([],self.socks,[],0)
        except:
            writeable=[]
        if len(writeable)==0:
            print('TCP_SERVER->Broadcast: No open sockets')
            return
                
        msg=msg+'\n'
        for sock in writeable:
            #print(sock)
            addr = sock.getsockname()
            print('BROADCASTing',msg.strip(),'to',addr,'...')
            #print('\tSock Name=',sock.getsockname())
            #print('\tPeer Name=',sock.getpeername())
            try:
                sock.send(msg.encode())
            except:
                print('Broadcast: Problem with socket')
                print(sock)

################################################################################

# Test program                
if __name__ == '__main__':
    TCP_HOST = '127.0.0.1'
    TCP_PORT = 2004 

    mode=''
    while not mode in ['S','C']:
        mode = input("Server or Client? (S/C) ").upper()
    
    print('mode=',mode)
    if mode=='S':
        # Server mode
        server = TCP_Server(None,TCP_HOST,TCP_PORT,Server=True)
    else:
        # Client mode
        server = TCP_Server(None,TCP_HOST,TCP_PORT,Server=False)

    worker = Thread(target=server.Listener, args=(), name='TCP Server' )
    worker.daemon=True
    worker.start()

    MESSAGE=''
    while MESSAGE.lower()!='exit':
        time.sleep(1)
        server.Broadcast(mode+' Heartbeat')
        MESSAGE = input("Enter Response or exit:")
        server.Broadcast(MESSAGE)

    server.Stopper.set()
    print('Joining ...')
    worker.join()
    print('Done.')

    sys.exit(0)

"""

# This is some code to explore address resolution
hostname = socket.gethostname()
dns_resolved_addr = socket.gethostbyname(hostname)
port = 2004
print('hostname=',hostname)
print('dns_resolved_addr',dns_resolved_addr)
if dns_resolved_addr=='127.0.1.1':                        # Not sure why it gets resolved this way!
    #host='127.0.0.1'
    host='localhost'
else:
    host=dns_resolved_addr
print('host=',host)
 
"""
