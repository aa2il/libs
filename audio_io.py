#! /usr/bin/python3
############################################################################################
#
# audio_io.py - Rev 1.0 - Joseph B. Attili, aa2il AT arrl DOT net
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

############################################################################################

# A recorder class for recording audio to a WAV file.
# Records in mono @ 48KHz by default.
class WaveRecorder(object):
    def __init__(self, fname, mode='wb', channels=1, rate=48000, frames_per_buffer=1024, wav_rate=48000,rb2=None,GAIN=[1,1]):
        self.channels = channels
        self.rate = rate
        self.wav_rate = wav_rate
        self.frames_per_buffer = frames_per_buffer
        self.fname = fname
        self.mode = mode
        self._pa = pyaudio.PyAudio()
        self._stream = None
        self.rb2 = rb2
        self.GAIN=GAIN
        
        self.down   = int( rate/wav_rate )
        self.istart = 0

        self.wavefile = self._prepare_file(self.fname, self.mode)
        
    def __enter__(self):
        print('@@@@@@@ ENTER @@@@@@@@@@@@@@')
        return self

    def __exit__(self, exception, value, traceback):
        self.close()

    # Use a stream with no callback function in blocking mode
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
              '\tfs=',self.rate,'\tframes/buf=',self.frames_per_buffer)
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
        print('... Recording stopped.')
        return self

    # Wrapper to pass callback to gui
    def get_callback_orig(self):

        # Callback when samples are ready, writes out data to wave file
        def callback(in_data, frame_count, time_info, status):
            self.wavefile.writeframes(in_data)
            return in_data, pyaudio.paContinue
        return callback

    # Wrapper to pass callback to gui
    def get_callback(self):
        
        # Callback when samples are ready, writes out data to wave file
        # This version includes decimation (no filtering)
        def callback(in_data, frame_count, time_info, status):

            # Generate indecies into the array
            # Keep track of starting point for next time around
            N=self.frames_per_buffer
            idx = list(range(self.istart,N,self.down))
            self.istart = idx[-1]+self.down-N
            #print 'AUDIO callback:',N,self.down,self.istart,idx[-1],self.channels,len(data1),len(data2)

            # Left channel is audio from RX
            # Direct decimation of the data
            #data1 = np.fromstring(in_data, 'Int16');    # Doesn't work anymore
            data1 = np.fromstring(in_data,dtype=np.int16);
            left  = self.GAIN[0]*data1[idx]

            # Right channel contains sidetone
            if self.rb2:
                nsamps = self.rb2.nsamps
                #print(nsamps,N)
                if nsamps>=N:
                    data3 = 32767*self.rb2.pull(N)
                elif nsamps>0:
                    x = 32767*self.rb2.pull(nsamps)
                    z = np.array((N-nsamps)*[0])
                    data3 = np.concatenate( (x,z) )
                else:
                    data3 = np.array(N*[0])
                right = self.GAIN[1]*data3[idx].astype(np.int16)

            # Write out to file
            if self.rb2:
                data = np.column_stack((left,right)) 
            else:
                data = left  
            self.wavefile.writeframes(data)

            self.nframes+=1
            if self.nframes==1:
                print('First frame of wave data (left chan):',left)

            return in_data, pyaudio.paContinue
        
        return callback

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
        return wavefile

    def list_input_devices(self,dev_name):
        print("\n---------------------- Record devices -----------------------")

        p = self._pa
        info = p.get_host_api_info_by_index(0)
        numdevices = info.get('deviceCount')
        index=None
        for i in range(0, numdevices):
            if (p.get_device_info_by_host_api_device_index(0, i).get('maxInputChannels')) > 0:
                dev = p.get_device_info_by_host_api_device_index(0, i).get('name')
                print("Input Device id ", i, " - ",dev)

                if dev.find(dev_name)>=0:
                    print('*** There it is ***',i)
                    index = i

        print("-------------------------------------------------------------")
        return index

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
    
