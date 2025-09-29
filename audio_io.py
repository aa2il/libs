#! /usr/bin/python3
###################################################################
#
# audio_io.py - Rev 1.1 
#
# Copyright (C) 2021-5 by Joseph B. Attili, joe DOT aa2il AT gmail DOT com
#
# Various routines/objects related to audio recording and play
#
###################################################################
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
###################################################################

import pyaudio
import pygame
import pygame._sdl2.audio as sdl2_audio
import wave
import sys
import time
import numpy as np
from sig_proc import ring_buffer2
if sys.platform == "linux" or sys.platform == "linux2":
    from pyudev import Context

###################################################################

# User params
#SCALE=32767
#SCALE=16384
#SCALE=8192
#SCALE=4096
SCALE=1

###################################################################

# An audio player which uses pygame instead of pyaudio.
# This is interesting since pygame seems to
#    1) find bluetooth devices but pyaudio does not,
#    2) be supported on android and pyaudio is not - TBD

class pgPLAYER:
    def __init__(self,fs):

        print('pgPLAYER init ... fs=',fs)
        self.fs     = int(fs)
        self.vol    = 1.
        self.active = False

        # Get list of available playback (and recording devices)
        self.playback_devices=self.get_devices()
        print('\tPlayback Devices:  ',self.playback_devices)
        self.device_name = self.playback_devices[0]         # Default is first device
        
        #self.recording_devices=self.get_devices(True)
        #print('Recording Devices: ',self.recording_devices)
        
    def get_devices(self,capture_devices: bool = False):
        init_by_me = not pygame.mixer.get_init()
        if init_by_me:
            pygame.mixer.init()
        devices = tuple(sdl2_audio.get_audio_device_names(capture_devices))
        if init_by_me:
            pygame.mixer.quit()
        return devices

    def set_device(self,name):
        self.device_name = name
        init_by_me = not pygame.mixer.get_init()
        print('\tSet Device: name=',name,'\tinit=',init_by_me,'\tactive=',self.active)
        if self.active or True:
            self.quit()
            self.start_playback()

    def start_playback(self,nwait=0,block=False):
        print('pgPLAYER Start Playback: dev=',self.device_name)

        # Open the mixer and create a channel to play sounds
        pygame.mixer.pre_init(self.fs, size=-16, channels=1,devicename = self.device_name)
        pygame.mixer.init()
        self.chan=pygame.mixer.Channel(0)
        self.active = True

        return

    def set_volume(self,a):
        #if self.active:
            #self.pause()
        self.vol = a
        if self.active:
            self.chan.set_volume(self.vol)
            #self.resume()

    def push(self,x):
        #print('push: x=',x,len(x))
        print('push: ',len(x))
        xx  = (x*16383).astype(np.int16)
        sound = pygame.sndarray.make_sound(xx)
        sound.set_volume(self.vol)
        self.chan.queue(sound)

        # It looks like we can only queue-up one sound bite in advance
        # That's too bad - I was hoping pygame did the ring-buffering for us
        #print('s=',sound)
        #q = self.chan.get_queue()
        #print('q=',q)

    def wait(self):
        while self.chan.get_busy():
            time.sleep(.1)

    def pause(self):
        pygame.mixer.pause()
        return
    
    def resume(self):
        pygame.mixer.unpause()
        return

    def stop(self):
        self.chan.stop()
        #pygame.mixer.quit()
        self.active=False
    
    def quit(self):
        pygame.mixer.quit()
        self.active=False
    
###################################################################

# Here is the audio player.  PortAudio is apperently very finiky about
# the callback deadline which can lead to underruns.  These in turn pegs
# the CPU, causing the SDR app to fall way behind.  To avoid this,
#       sudo emacs /etc/pulse/daemon.conf
# and un-comment the line
#       default-fragments = 4
# Then restart Pulse Audio:
#       pulseaudio --kill
#
# These websites are helpful in this regard:
# https://bbs.archlinux.org/viewtopic.php?id=185736
# https://wiki.archlinux.org/index.php/PulseAudio#Setting_the_default_fragment_number_and_buffer_size_in_PulseAudio

class AudioIO():
    def __init__(self,P,fs,rb,device=None,Chan='B',ZeroFill=False,Tag=None):
        print('AUDIO_IO: Init audio player @',fs,' Hz',
              '\trequested device=',device,'\tTag=',Tag,' ...')
        self.device = device               # Device index
        self.playback_devices=[]           # Available playback devices
        self.fs = fs
        self.rb = rb
        self.p  = pyaudio.PyAudio()
        self.rb.Chan = Chan                # B,L or R for Both, Left or Right
        self.P = P
        self.stream=None
        self.last=None
        self.ZeroFill=ZeroFill
        self.push = self.rb.push           # Link to ringbuf push function
        self.vol = 1.0

        if self.device==None:
            loopbacks = self.find_loopback_devices(True)
            default_device = self.p.get_default_output_device_info()
            print('Default device=',default_device)
            self.device=default_device.get('index')
            self.device_name = default_device.get('name')
        else:
            loopbacks = self.find_loopback_devices()
            print('AUDIO_IO: loopback device ids=',loopbacks)
            self.device = loopbacks[device-1]
            print('device=',device,'\t Using Device id=',self.device,'\n')
            # TODO: Will need to add device_name when we use this again

        self.idle =True
        self.Start_Time = 0
        self.active=False
        self.nchan = 2

        # This can eventually be smplified since I now know how to do this with an object method
        self.FirstTime = True
        self.callback = self.AudioPlayCB
        print('Player Init')

    # Function to push a chunk of data into the ring buffer
    # See link above instead
    #def push(x):
    #    self.rb.push(x)

    # Function to create a list of loopback devices
    def find_loopback_devices(self,INFO_ONLY=False):

        p=self.p
        info = p.get_host_api_info_by_index(0)
        numdev = info.get('deviceCount')
        print('\nAUDIO - FIND_LOOPBACK_DEVICES: info=',info,numdev)

        # Look at all audio devices 
        loopback_devs=[]
        for i in range(0,numdev):
            dev_info = p.get_device_info_by_host_api_device_index(0,i)
            #print dev_info

            name = dev_info.get('name')
            srate = dev_info.get('defaultSampleRate')
            if dev_info.get('maxInputChannels')>0:
                print("Input  Device id ", i, " - ",name,srate)

            if dev_info.get('maxOutputChannels')>0:
                print("Output Device id ", i, " - ",name,srate)
                self.playback_devices.append(name)

            if "Loopback:" in name and srate==48000:
            #if "Loopback:" in name:
                #print dev_info
                loopback_devs.append(i)
                print('***')

        if len(loopback_devs)==0 and not INFO_ONLY:
            print('\nFIND_LOOP_BACKS: *** WARNING *** None found ***\n')
            print('This might be becuase the default sample rate is not 48k')
            print('To fix this, run start_loopback\n')
            print('If that doesnt work, try eliminating the "and srate" above')
            print('ed ~/Python/pySDR/pySDR/sig_proc.py')
            print('Note, however, that 48K is needed for WSJT to function correctly')
            print('so this is NOT a good solution!!!!\n')
            print('Quitting')
            sys.exit(1)
        
        return loopback_devs


    def start_playback(self,nwait,block):

        # Need to delay start of playback until there are enough samples
        if not self.idle:
            #print "Playback already running"
            return True
        elif block:
            # Blocking
            #print "Playback blocking..."
            while self.rb.nsamps<nwait:
                print('waiting for ring buffer to fill ....',self.rb.nsamps)
                #                time.sleep(self.rb.size/(2.*self.fs))
                time.sleep(.1)
        else:
            # Non-blocking
            if self.rb.nsamps<nwait:
                print("Too few samples to start Playback...")
                return False

        print('\n##############################################################################')
        print("\nStarting audio play back @",self.fs,"Hz\ttag=",self.rb.tag,
              '\n\tnsamps=',self.rb.nsamps,'\trb_size=',self.rb.size,
              '\tdevice=',self.device)
        msec = 20                            # Set buffer size to about 20ms
        ifr = int( .001*msec*self.fs )
        self.stream = self.p.open(output_device_index=self.device,
                                  format=pyaudio.paFloat32,
                                  channels=self.nchan,
                                  rate=self.fs,
                                  frames_per_buffer=ifr,
                                  output=True,
                                  stream_callback=self.callback)

        self.stream.start_stream()
        self.Start_Time = time.time()
        self.active=True
        self.idle = False
        print("Audio playback started ... tag=",self.rb.tag)
        return True

    def restart(self,dfs=0):
        fsold=self.fs
        self.fs += max( min(dfs,1000) ,-1000)
        print('Changing audio playback rate from',fsold,' to',self.fs,'         ',dfs)
        self.stop()
        self.start_playback(self.rb.size/2,True)
        print("Audio playback restarted ...")

    def stop(self):
        self.active=False
        if self.stream:
            print('\tStopping audio:',self.rb.tag)
            self.stream.stop_stream()
            print('\tStream stopped:',self.rb.tag)
            self.stream.close()
        self.stream=None
        self.idle =True
        print("\tAudio playback stopped ...",self.rb.tag)
        self.rb.clear()

    def quit(self):
        print('Quitting audio',self.rb.tag,self.active,self.idle)
        self.stream.stop_stream()
        self.stream.close()
        self.p.terminate()
        self.idle =True

    def pause(self):
        self.idle =True
        self.stream.stop_stream()
        print('### Audio Stream Paused ###')

    def resume(self):
        if self.active:
            self.idle =False
            self.stream.start_stream()
            print('### Audio Stream Resumed ###')
        else:
            self.start_playback(0,False)

    def set_volume(self,a):
        #if self.active:
            #self.pause()
        self.vol = a
        #if self.active:
            #self.chan.set_volume(self.vol)
            #self.resume()
            
    # Callback to retrieve data for a hungry sound card.
    # Finally know how to do this without an external function!!!!
    def AudioPlayCB(self,in_data, frame_count, time_info, status):

        DEBUG=0
        rb=self.rb
        N=int(frame_count)
        if DEBUG>=2:
            print('\nAUDIO PLAY CallBack: status=',status,'\tN=',N,
                  '\ttag=',rb.tag,'ZeroFill=',self.ZeroFill)

        ##################################################################
        #                                                                #
        # Handle problems - See comments just above AudioIO class def    #
        # on how to fix some underruns.                                  #
        #                                                                #
        # Here are the error codes from the pyAudio manual:              #
        #   PortAudio Callback Flags                                     #
        #        paInputUnderflow  = 1                                   #
        #        paInputOverflow   = 2                                   #
        #        paOutputUnderflow = 4                                   #
        #        paOutputOverflow  = 8                                   #
        #        paPrimingOutput   = 16                                  #
        #                                                                #
        ##################################################################

        if status!=0 and True:
            if status == pyaudio.paInputUnderflow:
                err='Input Under Flow'
            elif status == pyaudio.paInputOverflow:
                err='Input Over Flow'
            if status == pyaudio.paOutputUnderflow:
                err='Output Under Flow'
            elif status == pyaudio.paOutputOverflow:
                err='Output Over Flow'
            elif status == pyaudio.paPrimingOutput:
                err='Priming Output'
            print("AudioPlayCB: err=",err,'\ttag=',rb.tag,
                  '\tframe cnt=',frame_count,'\n\ttime=',time_info,'\tstatus=',status)
        
        if self.ZeroFill:
            Stopper=True
            if status!=0:
                print('AudioPlayCB: *** WARNING *** Non-zero Status')
        elif self.P.Stopper:
            Stopper = (self.P.Stopper and self.P.Stopper.isSet())
        else:
            Stopper=False
            
        if status!=0 and not Stopper:
            print("AudioPlayCB: tag=",rb.tag,'\tframe count=',frame_count,
                  '\ttime=',time_info,'\tstauts=',status)
            if status == pyaudio.paOutputUnderflow:
                delay=self.P.RB_SIZE/self.P.FS_OUT/4
                print("Houston, we have an underflow problem ...")
                print("Stalling until recharge - tag=",rb.tag,
                      '\tnsamps=',rb.nsamps,'\tlast=',self.last,
                      '\n\tnchan=',self.nchan,'\tChan=',rb.Chan,'\tZeroFill=',self.ZeroFill,
                      '\n\tP.DELAY=',self.P.DELAY,'\tdelay=',delay)
                #print("See comments in sig_proc.py on how to fix if this persists")
                
                # Wait for ring buffer to fill again
                while not rb.ready( self.P.DELAY ) and not self.P.REPLAY_MODE and not Stopper:
                    time.sleep(delay)
                    Stopper = (self.P.Stopper and self.P.Stopper.isSet())
                print("Recharged tag=",rb.tag,'\tnsamps=',rb.nsamps,'\tN=',N)
            
        # First time through, wait for ring buffer to start to fill
        if self.FirstTime:
            if False:
                while rb.nsamps <= 4*N:
                    time.sleep(.01)
                    #pass
            if False:
                N=4*N
        self.FirstTime = False

        # Pull next chunk from the ring buffer
        if self.ZeroFill:
            nready = rb.nsamps
            if DEBUG>=2:
                print('Available:',nready,N)

            if nready<1024:
                N2=1024
                x2=np.array(N2*[0],dtype=np.float32)
                rb.push(x2)
                nready = rb.nsamps
                if DEBUG>=1:
                    print('Zero Pushed:',rb.tag,N2,x2.dtype,len(x2))
                    print('Available:',nready,N)
                    
            if nready>0:
                N1=min(N,nready)
                x=rb.pull(N1)
                if DEBUG>=2:
                    print('Pulled:',rb.tag,N1,x.dtype)
                    
            if nready<N:
                N2=N-nready
                x2=np.array(N2*[0.],dtype=x.dtype)
                x = np.concatenate( (x, x2) )
                if DEBUG>=1:
                    print('Zeroed:',rb.tag,N2,x.dtype,len(x))
                    
        else:
            x=rb.pull(N)
            if DEBUG>=2:
                print('Pulled',rb.tag,x.dtype,self.nchan,rb.Chan)
    
        if self.nchan==2:
            #print(x.dtype==np.float32,x.dtype==np.float64)
            if x.dtype==np.float32 or x.dtype==np.float64:
                if rb.Chan=='B':
                    x = x + 1j*x                      # Copy mono data to both L&R channels
                elif rb.Chan=='L':
                    x = x + 1j*0                       # Copy mono data to L channel
                    #print rb.tag,x.dtype,nchan,rb.Chan
                else:
                    x = 0 + 1j*x                       # Copy mono data to R channel
                    #print rb.tag,x.dtype,nchan,rb.Chan
            #data = x.astype(np.complex64).tostring()
            data = x.astype(np.complex64).tobytes()
        else:
            #data = x.astype(np.float32).tostring()
            data = x.astype(np.float32).tobytes()
        
        self.last=len(data)
        if DEBUG>=2 or status!=0:
            print('Final Push: N=',N,'\tlast=',self.last,x.dtype,
                  '\tnsamps=',rb.nsamps)
        return (data, pyaudio.paContinue)

###################################################################
#
# A recorder class for recording audio to a WAV file.
# Records in mono @ 48KHz by default.
# Originally inspired by code snippent found at https://gist.github.com/sloria/5693955.
#
###################################################################

class WaveRecorder(object):
    def __init__(self, fname, mode='wb', channels=1, rate=48000, frames_per_buffer=None,
                 wav_rate=48000,rb2=None,GAIN=[1,1]):
        
        self.channels = channels
        self.rate = rate
        self.wav_rate = wav_rate
        if frames_per_buffer==None:
            msec = 20                            # Set buffer size to about 20ms
            frames_per_buffer=int( .001*msec*self.rate )
        self.frames_per_buffer = frames_per_buffer
        self.fname = fname
        self.mode = mode
        self._pa = pyaudio.PyAudio()
        self._stream = None
        self.rb2 = rb2
        self.GAIN=GAIN
        self.rb     = ring_buffer2('WaveRec0',32*1024)
        
        self.down   = int( rate/wav_rate )
        self.istart = 0

        self.wavefile = self._prepare_file(self.fname, self.mode)
                
        print('WAVE RECORDER Init: fname=',fname,
              '\n\trates=',self.rate,self.wav_rate,
              '\n\tnchan=',self.channels,
              '\n\tgain=',self.GAIN,
              '\n\tframes_per_buf=',self.frames_per_buffer)

        width = self.wavefile.getsampwidth()
        fmt   = self._pa.get_format_from_width(width)
        print('WAVE RECORDER Init: width=',width,'\tfmt=',fmt)

    def __enter__(self):
        print('@@@@@@@ ENTER @@@@@@@@@@@@@@')
        return self

    def __exit__(self, exception, value, traceback):
        self.close()

    # Use a stream in blocking mode (no callback)
    def record(self, duration):
        self._stream = self._pa.open(format=pyaudio.paInt16,
                                     channels=self.channels,
                                     rate=self.rate,
                                     input=True,
                                     frames_per_buffer=self.frames_per_buffer)
        for _ in range(int(self.rate / self.frames_per_buffer * duration)):
            audio = self._stream.read(self.frames_per_buffer)
            self.wavefile.writeframes(audio)
        return None

    # Use a stream with a callback in non-blocking mode
    def start_recording(self,index=0):
        print('WaveRecorder - START_RECORDING - Recording started ...' \
              '\n\tDevice index=',index,'\tnchan=',self.channels,\
              '\tfs=',self.rate,'\twave rate=',self.wav_rate,'\tdown=',self.down,
              '\tframes/buf=',self.frames_per_buffer)
        self._stream = self._pa.open(format=pyaudio.paInt16,
                                     channels=self.channels,
                                     rate=self.rate,
                                     input=True,
                                     input_device_index = index,
                                     frames_per_buffer=self.frames_per_buffer,
                                     stream_callback=self.get_callback())
        self._stream.start_stream()
        self.nframes=0
        return self

    def stop_recording(self):
        self._stream.stop_stream()
        print('WaveRecorder - ... Recording stopped.')
        return self

    def resume_recording(self):
        self._stream.start_stream()
        print('... Recording restarted.')
        return self

    # Wrapper to pass callback to gui
    def get_callback(self):

        # Callback when samples are ready and copies them to a ring buffer
        def callback(in_data, frame_count, time_info, status):
            #self.wavefile.writeframes(in_data)

            DEBUG=0

            # Generate indecies into the array
            # Keep track of starting point for next time around
            N=self.frames_per_buffer
            idx = list(range(self.istart,N,self.down))
            self.istart = idx[-1]+self.down-N
            if DEBUG>0:
                print('WAVE RECORDER CB: frame_count=',frame_count,'\tN=',N,'\tdown=',self.down,
                      '\n\tistart=',self.istart,'\tidx=',idx[-1],
                      '\tnchan=',self.channels,'\tnamp=',self.rb.nsamps)  

            # Left channel is audio from RX
            # Direct decimation of the data
            data1 = np.fromstring(in_data,dtype=np.int16);
            left  = np.int16( self.GAIN[0]*data1[idx] )
            
            self.rb.push(left)
            
            return in_data, pyaudio.paContinue
        return callback

    
    """
    # Wrapper to pass callback to gui
    # This works but is not good since it writes data to disk & can cause lost chunks
    def get_callback_old(self):
        
        # Callback when samples are ready, writes out data to wave file
        # This version includes decimation (no filtering)
        def callback(in_data, frame_count, time_info, status):

            DEBUG=0
            
            # Generate indecies into the array
            # Keep track of starting point for next time around
            N=self.frames_per_buffer
            idx = list(range(self.istart,N,self.down))
            self.istart = idx[-1]+self.down-N
            if DEBUG>0:
                print('WAVE RECORDER CB: N=',N,'\tdown=',self.down,'\tistart=',self.istart,'\tidx=',idx[-1],
                      '\tnchan=',self.channels)     # ,'\tndata1=',len(data1),'\tndata2=',len(data2))

            # Left channel is audio from RX
            # Direct decimation of the data
            #data1 = np.fromstring(in_data, 'Int16');    # Doesn't work anymore
            data1 = np.fromstring(in_data,dtype=np.int16);
            left  = self.GAIN[0]*data1[idx]

            # Right channel contains sidetone
            if self.rb2:
                #N2=N                                      # Decimate sidetone also
                N2=len(left)                               # Don't need to decimate anymore
                nsamps = self.rb2.nsamps
                if nsamps>=N2:
                    data3 = SCALE*self.rb2.pull(N2)
                elif nsamps>0:
                    x = SCALE*self.rb2.pull(nsamps)
                    z = np.array((N2-nsamps)*[0])
                    data3 = np.concatenate( (x,z) )
                else:
                    data3 = np.array(N2*[0])
                right = self.GAIN[1]*data3.astype(np.int16)
                if DEBUG>0:
                    print('RB2: Pulled nsamps=',nsamps,N2,'\tLen=',len(left),len(right))

            # Write out to file
            if self.rb2:
                data = np.column_stack((left,right)) 
            else:
                data = left  
            self.wavefile.writeframes(data)

            self.nframes+=1
            if self.nframes==1 and False:
                print('First frame of wave data (left chan):',left)

            return in_data, pyaudio.paContinue
        
        return callback
    """


    # Function to assemble & write-out data to disk
    def write_data(self,in_data):

        DEBUG=0
            
        # Left channel is audio from RX
        # Direct decimation of the data
        #data1 = np.fromstring(in_data,dtype=np.int16);
        #left  = np.int16( self.GAIN[0]*in_data ) # .astype(np.int16)
        left  = in_data.astype(np.int16)
        if DEBUG>0 and False:
            print('WAVE RECORDER - WRITE_DATA: Left has nsamps=',len(left))

        # Right channel contains sidetone
        if self.rb2:
            N2=len(left)                               # Don't need to decimate sidetone data
            nsamps = self.rb2.nsamps
            if nsamps>=N2:
                data3 = SCALE*self.rb2.pull(N2)
            elif nsamps>0:
                x = SCALE*self.rb2.pull(nsamps)
                z = np.array((N2-nsamps)*[0])
                data3 = np.concatenate( (x,z) )
            else:
                data3 = np.array(N2*[0])
            #right = np.int16( self.GAIN[1]*data3 ) #.astype(np.int16)   
            right = data3.astype(np.int16)   
            if DEBUG>0:
                print('WAVE RECORDER - WRITE_DATA: Pulled nsamps=',nsamps,'\tN2=',N2,'\tLen=',len(left),len(right))

        # Write out to file
        if self.rb2:
            data = np.column_stack((left,right)) 
        else:
            data = left  
        self.wavefile.writeframes(data)


    def close(self):
        self._stream.close()
        self._pa.terminate()
        self.wavefile.close()

    def _prepare_file(self, fname, mode='wb'):
        wavefile = wave.open(fname, mode)
        nchan = self.channels
        if self.rb2:
            nchan+=1
        wavefile.setnchannels(nchan)
        wavefile.setsampwidth(self._pa.get_sample_size(pyaudio.paInt16))
        wavefile.setframerate(self.wav_rate)
        print('WAVE RECORDER: Open Wave file: name=',fname,'\tnchan=',nchan,'\trate=',self.wav_rate)
        return wavefile

    def list_input_devices(self,dev_name):
        print("\n---------------------- Recording devices -----------------------")
        print('\tLooking for',dev_name,'...')

        p = self._pa
        info = p.get_host_api_info_by_index(0)
        numdevices = info.get('deviceCount')
        index=None
        for i in range(0, numdevices):
            if (p.get_device_info_by_host_api_device_index(0, i).get('maxInputChannels')) > 0:
                dev = p.get_device_info_by_host_api_device_index(0, i)
                name = dev.get('name')
                print("Input Device id ", i, " - ",name)

                if name.find(dev_name)>=0:
                    print('*** There it is ***',i)
                    if sys.platform == "linux" or sys.platform == "linux2":
                        self.get_detailed_usb_info(dev_name.replace(' ','_'))
                    else:
                        print(dev)
                    index = i

        print("-------------------------------------------------------------")
        #sys.exit(0)
        return index

    def get_detailed_usb_info(self,dev_name):

        #context = pyudev.Context()
        context = Context()
        devices = context.list_devices(subsystem='usb')

        for device in devices:
            if device.get('ID_MODEL')==dev_name:
                print(f'\tDevice Name: {device.get("ID_VENDOR")} {device.get("ID_MODEL")}')
                print(f'\tDevice Serial Number: {device.get("ID_SERIAL_SHORT")}')
                print(f'\tDevice Bus: {device.get("ID_BUS")}')
                print(f'\tDevice Device: {device.get("ID_PATH")}')
                print('')

    
############################################################################################

# Main program to demo non-blocking usage
if __name__ == "__main__":

    print('\n****************************************************************************')
    print('\n   Recorder beginning ...\n')

    rec = WaveRecorder('junk.wav', 'wb')
    idx=rec.list_input_devices('USB Audio CODEC')
    rec.start_recording(idx)
    time.sleep(5.0)
    #rec.stop_recording()
    
    sys.exit(0)
    
