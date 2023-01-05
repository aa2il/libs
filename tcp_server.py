#! /usr/bin/python3
################################################################################
#
# tcp_server.py - Rev 1.0
# Copyright (C) 2021-3 by Joseph B. Attili, aa2il AT arrl DOT net
#
#    Simple tcp server to allow clients to communicate to keyer app.
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

################################################################################

VERBOSITY=0
KEYER_UDP_PORT   = 7474
BANDMAP_UDP_PORT = 7575

################################################################################

# Prototype message handler
def dummy_msg_handler(self,sock,msg):
    id=sock.getpeername()
    print('TCP_SERVER->MSG HANDLER: id=',id,'\tmsg=',msg.rstrip())
        
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
            self.tcpServer.bind((self.host,self.port))                           # Bind socket to server address
        else:
            self.tcpClient.connect((self.host, self.port))                       # Connect to server
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
            self.tcpServer.listen(4)                                              # Listen for clients

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
                    msg='Name:pyKeyer\nName:?\n'
                    conn.send(msg.encode())

                else:

                    # Read from a client
                    #timeout=False
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
                
                    if data:
                        
                        # We received a message from a client
                        print('\r{}:'.format(sock.getpeername()),data)
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

    # These two function do similar things - perhaps we need a version that only
    # send to one peer?

    # Function to send a message to all writeable peers
    def Send(self,msg):
        self.Broadcast(msg)

    """
        # Get list of sockets
        readable,writeable,inerror = select.select([],self.socks,[],0)
        if len(writeable)==0:
            print('TCP_CLIENT->SEND: No open sockets')                
                
        msg=msg+'\n'
        for sock in writeable:
            addr = sock.getsockname()
            print('TCP_CLIENT->SEND: Sending msg',msg,'to addr',addr,'...')
            sock.send(msg.encode())

        return
            
        sock = self.tcpClient
        try:
            addr = sock.getsockname()
            sock.send(msg.encode())
        except:
            print('Send: Problem with socket')
            print(sock)
    """
    
    # Function to broadcast a message to all connected clients
    def Broadcast(self,msg):

        # Get list of sockets
        readable,writeable,inerror = select.select([],self.socks,[],0)
        if len(writeable)==0:
            print('TCP_SERVER->Broadcast: No open sockets')                
                
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
    if 0:
        TCP_PORT = 2004 
        TCP_PORT2 = None
    else:
        TCP_PORT  = 2135
        TCP_PORT2 = 2004

    server = TCP_Server(None,TCP_HOST,TCP_PORT)
    worker = Thread(target=server.Listener, args=(), name='TCP Server' )
    worker.daemon=True
    worker.start()

    if TCP_PORT2:
        time.sleep(1)
        print('Connecting to ',TCP_HOST,TCP_PORT2)
        try:
            server.Connect(TCP_HOST,TCP_PORT2)
            print('Connected.')
        except Exception as e:
            print('Excpetion Raised:',e)        

    while True:
        server.Broadcast('Heartbeat')
        MESSAGE = input("Enter Response or exit:")
        if MESSAGE == 'exit':
            server.Stopper.set()
            print('Main exiting')
            break
        else:
            server.Broadcast(MESSAGE)
        time.sleep(1)

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
