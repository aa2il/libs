#! /usr/bin/python3
############################################################################################
#
# audio_io.py - Rev 1.0 - Joseph B. Attili, joe DOT aa2il AT gmail DOT com
#
# Wave recorder class.
# Originally inspired by code snippent found at https://gist.github.com/sloria/5693955.
#
############################################################################################

import pyaudio
import wave
import sys
import time
import numpy as np
from sig_proc import ring_buffer2
if sys.platform == "linux" or sys.platform == "linux2":
    from pyudev import Context

############################################################################################

SCALE=32767
#SCALE=16384
#SCALE=1

############################################################################################

# A recorder class for recording audio to a WAV file.
# Records in mono @ 48KHz by default.
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
            left  = self.GAIN[0]*data1[idx]
            
            self.rb.push(left)
            
            return in_data, pyaudio.paContinue
        return callback

    

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



    # Function to assemble & write-out data to disk
    def write_data(self,in_data):

        DEBUG=0
            
        # Left channel is audio from RX
        # Direct decimation of the data
        #data1 = np.fromstring(in_data,dtype=np.int16);
        left  = self.GAIN[0]*in_data.astype(np.int16)
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
            right = self.GAIN[1]*data3.astype(np.int16)   
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
    
