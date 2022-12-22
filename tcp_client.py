#! /usr/bin/python3
################################################################################
#
# tcp_client.py - Rev 1.0
# Copyright (C) 2021-2 by Joseph B. Attili, aa2il AT arrl DOT net
#
#    Simple tcp server to effect allow clients to communicate to app.
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
import select
from threading import Thread,Event
import time

################################################################################

# TCP Client object
class TCP_Client(Thread):
    
    def __init__(self,P,host,port,BUFFER_SIZE=1024,handler=None): 
        Thread.__init__(self)

        self.P=P
        if not host:
            host='127.0.0.1'
        self.host=host
        self.port=port
        self.BUFFER_SIZE = BUFFER_SIZE
        self.running=False
        if handler:
            self.handler=handler
        else:
            self.handler=self.simple_msg_handler
            
        print('TCP Client: host=',host,'\tport=',port,'\tBuf Size=',self.BUFFER_SIZE,
              '\tHandler=',self.handler)

        self.Stopper = Event()
        self.StartClient()

    def StartClient(self):
        print('TCP_CLIENT StartClient Starting ...')
        if self.running:
            self.tcpClient.close()
            #self.socks.remove(self.tcpClient)
        self.tcpClient = socket.socket(socket.AF_INET, socket.SOCK_STREAM) 
        self.tcpClient.connect((self.host, self.port))
        self.socks = [self.tcpClient]
        self.running=True
        
    # Function to listener for new connections and/or data from clients
    def Listener(self): 
        print('Listener Client ...')

        # Run until stopper is set
        while not self.Stopper.isSet():
            time.sleep(1)

            # Get list of sockets 
            #print('Getting list ...')
            #readable,writeable,inerror = select.select(self.socks,self.socks,self.socks,0)
            readable,writeable,inerror = select.select(self.socks,[],[],0)
            #print('TCP_CLIENT->LISTENER: readable=',readable,
            #       '\twriteable=',writeable,'\tinerror=',inerror)
            if len(readable)==0 and False:
                print('TCP_CLIENT->LISTENER: No open sockets')
            
            # iterate through readable sockets
            for sock in readable:
                # read from server
                data = sock.recv(self.BUFFER_SIZE)
                if not data:
                    print('\r{}:'.format(sock.getpeername()),'disconnected')
                    readable.remove(sock)
                    self.socks.remove(sock)
                    sock.close()
                else:
                    #print('\rLISTENER:{}:'.format(sock.getpeername()),data)
                    if self.handler:
                        self.handler(self,sock,data.decode("utf-8") )

        self.Close()
        
    def Close(self):
        
        # Close socket
        self.tcpClient.close()
        print('Listerner: Bye bye!')

    def Send(self,msg):

        readable,writeable,inerror = select.select([],self.socks,[],0)
        #print('TCP_CLIENT->SEND: readable=',readable,
        #      '\twriteable=',writeable,'\tinerror=',inerror)
        if len(writeable)==0:
            print('TCP_CLIENT->SEND: No open sockets')                
                
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

    def simple_msg_handler(self,sock,msg):
        id=sock.getpeername()
        print('TCP_CLIENT->MSG HANDLER: id=',id,'\tmsg=',msg)
        
################################################################################

if __name__ == '__main__':
    TCP_IP = '127.0.0.1' 
    TCP_PORT = 2004 

    client = TCP_Client(None,TCP_IP,TCP_PORT)
    worker = Thread(target=client.Listener, args=(), name='TCP Client' )
    worker.setDaemon(True)
    worker.start()

    while True:
        #print('zzzzzzzzzzzzzzzzz....')
        MESSAGE = input("Enter Response or exit:")
        if MESSAGE == 'exit':
            client.Stopper.set()
            print('Main exiting')
            break
        else:
            client.Send(MESSAGE)
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
