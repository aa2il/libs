#######################################################################################
#
# Signal Processing - Rev 1.0
# Copyright (C) 2021 by Joseph B. Attili, aa2il AT arrl DOT net
#
# Various routines/objects related to sig processing, demodulation and digital receivers
#
#######################################################################################
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
#######################################################################################

import numpy as np
import scipy.signal as signal
import pyaudio
import sys
#from fractions import gcd            # No longer available on RPi?
from math import gcd
import time
if sys.version_info[0]==3:
    import queue
else:
    import Queue
import multiprocessing as mp

#######################################################################################

# A phase locked loop
class PLL(object):
    def __init__(self, fs, bandwidth,damping):
        self.fs       = fs
        self.phz      = 0.0
        self.frq      = 0.0
        self.vco      = np.exp(-1j*self.phz)
        self.phz_diff = 0.0
        self.alpha    = (2*np.pi*bandwidth/float(fs))**2
        self.beta     = 2*damping*np.sqrt(self.alpha)
        print(self.alpha,self.beta)

    def reset(self):
        #print 'PLL Reset'
        self.phz      = 0.0
        self.frq      = 0.0
        self.phz_diff = 0.0

    # Need to work on these routines to make them more computationally efficient
    def step(self, sig):
        if True:
            self.phz_diff = np.angle(sig*self.vco)
        else:
            # Small angle approx - only a problem if phz diff is large
            phase_det = sig*self.vco
            self.phz_diff = np.imag(phase_det) / np.real(phase_det) 
            if np.real(phase_det)<0:
                self.phz_diff -= np.pi
            #print phase_det,np.angle(phase_det),self.phz_diff

        self.frq += self.alpha * self.phz_diff
        self.phz += self.beta * self.phz_diff + self.frq
        self.vco  = np.exp(-1j*self.phz)   # This is probably the CPU hog!

        #print self.frq/(2*np.pi)*self.fs
        
    def fm_block(self,ref):
        N=len(ref)
        sc = self.fs / (2.*np.pi) * 1e-8
        fm = np.zeros( N, np.float32 )
        for i in range(N):
            self.step( ref[i] )
            fm[i] = sc*self.frq
            
        return fm

    def am_block(self,ref):
        N=len(ref)
        sc = self.fs / (2.*np.pi) * 1e-8
        vco = np.zeros( N, np.complex64 )
        for i in range(N):
            self.step( ref[i] )
            vco[i] = self.vco
            
        return vco

###################################################################

# Spectral analysis 
class spectrum:
    def __init__(self,fs,chunk_size,NFFT,overlap=0.,demean=False,foffset=0):
        self.fs   = fs
        self.fold = fs/2.
        self.chunk_size = chunk_size
        self.NFFT = NFFT
        self.df = float(fs*1e3)/NFFT
        self.frq1 = np.fft.rfftfreq(NFFT, d=1./fs) + foffset
        self.frq2 = np.fft.fftshift( np.fft.fftfreq(NFFT, d=1./fs) ) + foffset
        self.first_time = True
        self.demean = demean

        # From the numpy docs, here is how the shape parameter of the Kaiser window affects its performance
        # beta	Window shape
        #  0	Rectangular
        #  5	Similar to a Hamming
        #  6	Similar to a Hanning
        beta = 8.6	# Similar to a Blackman
        # 14    Probably a good starting point
        #self.win  = np.kaiser(chunk_size,2*np.pi)
        self.win  = np.kaiser(chunk_size,beta)

        self.overlap = overlap
        self.old_samps = int( chunk_size*overlap )
        self.new_samps = chunk_size - self.old_samps
        self.prev = np.zeros(self.old_samps)

    def periodogram(self,x,FORCE_COMPLEX=False):

        # Take care of overlap between periodograms
        #print 'PERIODOGRAM 1',len(x)
        if self.old_samps>0:
            #print 'PERIODOGRAM:',len(x),len(self.prev)
            xx = np.concatenate( (-self.prev, x) )
            self.prev = -xx[-self.old_samps:]
        else:
            xx = x

        # Demean data
        #print 'PERIODOGRAM 2',len(xx)
        if self.demean:
            xx = xx - np.mean(xx)
            
        #print 'PERIODOGRAM 3',len(x),len(self.win),self.NFFT
        if np.iscomplexobj(x) or FORCE_COMPLEX:
            #print 'PERIODOGRAM 3a - complex FFT'
            PSD = np.fft.fftshift( np.fft.fft(xx * self.win , self.NFFT) )
            self.frq = self.frq2
        else:
            PSD = np.fft.rfft(xx*self.win , self.NFFT) 
            self.frq = self.frq1
            #print 'PERIODOGRAM 3b - real FFT',len(xx),self.NFFT,len(PSD)
        #print 'PERIODOGRAM 4',len(x)
        PSD = 10*np.log10( np.square(PSD.real) + np.square(PSD.imag) )

        #print 'PERIODOGRAM 5',len(x)
        return PSD


# Quick & dirty PSD
def PSD1d(x,fs,iplot):

    PSD=np.fft.fftshift( np.fft.fft(x) )
    PSD = 10*np.log10( np.square(PSD.real) + np.square(PSD.imag) )
    NFFT=len(PSD)
    frq=( np.arange(NFFT)/float(NFFT) - 0.5 )*fs

    if iplot:
        plt.plot(frq,PSD, 'b')
        plt.xlabel('f [kHz]')
        plt.ylabel('PSD')

        fold=fs/2.
        rm=np.max(PSD)
        plt.axis((-fold,fold,rm-60,rm))
        plt.grid()
        plt.show(block=True)
        sys.exit()

    return (frq,PSD)

###################################################################

# Bandpass filter design
def bpf(flow,fhigh,fs,n):
    f1=flow  / (fs/2.)    # Normalized BPF cutoff freqs - Nyquist is 1
    f2=fhigh / (fs/2.)    # Normalized BPF cutoff freqs - Nyquist is 1
    h = signal.firwin(n, [f1,f2], window=('chebwin',80), pass_zero=False)
    return h

# Lowpass filter design
def lpf(bw,fs,n):
    #print('LPF: bw=',bw,'\tfs=',fs,'\tn=',n)

    fn=bw/float(fs/2.)                  # Normalized LPF cutoff freq - Nyquist is 1
    #    h = signal.firwin(n, fn)       # Default window is hamming
    #    h = signal.firwin(n, fn, window='blackmanharris')
    
    # From the numpy docs, here is how the shape parameter of the Kaiser window affects its performance
    # beta	Window shape
    #  0	Rectangular
    #  5	Similar to a Hamming
    #  6	Similar to a Hanning
    beta=2*np.pi     # Has traditionally been my favorite - sidelobes down 90+ dB
    # 8.6	Similar to a Blackman
    # 14    Probably a good starting point
    #h = signal.firwin(n, fn, window=('kaiser',beta))

    h = signal.firwin(n, fn, window=('chebwin',80))

    # Doesn't seem to work
    #h = signal.remez(n, [0, bw, 1.1*bw, fs/2.], [1, 0], fs=fs)
    
    return h

# Bank of low pass filter - just a wrapper for the more general BPF banker
def lpf_bank(bws,fs,n,cmplx,Other_BW=0,Scaling=1.):
    bank = bpf_bank(0,bws,fs,n,cmplx,Other_BW,Scaling)
    return bank
    
# Bank of band pass filter
def bpf_bank(flo,bws,fs,n,cmplx,Other_BW=0,Scaling=1.):

    filter_bank=[]
    bws2=[]
    for bw in bws:
        if bw=='Max':
            bw2 = fs/2
        elif bw=='Other':
            if Other_BW==0:
                bw2 = fs
            else:
                bw2 = Other_BW
        else:
            a=bw.split(" ")
            bw2 = int(a[0])
            if a[1]=="KHz":
                bw2 *= 1e3 
            elif a[1]=="MHz":
                bw2 *= 1e6

        if cmplx:
            bw2 = min( bw2, fs-10 )
            bw2 /= 2.
        else:
            bw2 = min( bw2, fs/2-10 )
        #print 'Designing ',bw,bw2,fs,n,cmplx
        if flo==0 or bw2<=flo:
            h = lpf(bw2,fs,n)
        else:
            h = bpf(flo,bw2,fs,n)
        filter_bank.append( Scaling * h )
        bws2.append( bw2 )
        
    return (filter_bank,bws2)
        
# Hilbert transform filter design (aka 90-deg phase shifter)
def hilbert(n,iPlot=False):
    n2=int(n/2)
#    print n2

    H = [0] + [1j]*n2 + [-1j]*n2
    h = np.fft.fftshift( np.fft.ifft(H) )

    if iPlot:
        plt.plot(np.imag(h))
        plt.plot(np.real(h))
        plt.show()

    return -np.real(h)

# Plot the filter response
def plot_filter_response(h,fs):

    w, H = signal.freqz(h)

    twopi=2*np.pi
    f=fs*w/twopi

    plt.title('Digital filter frequency response')
    plt.plot(f, 20*np.log10(np.abs(H)), 'b')
    plt.ylabel('Amplitude Response (dB)')
    plt.xlabel('Frequency (Hz)')
    plt.grid()
    plt.show(block=False)
    
    z = plt.axis()
    plt.axis((0,fs/2.,z[2],z[3]))
    
    plt.show(block=True)


###################################################################

# Ring buffers for data buffering 

# Defines a stripped-down ring buffer object used for multiprocessing
class ring_buffer3:
    def __init__(self,tag,n):

        # Allocate the buffer & init
        self.tag    = tag
        self.buf    = mp.Queue(maxsize=n)
        self.size   = n       # Size of the buffer
        self.prev   = np.array([])      # Overlap from pervious call

    # Routine to pull data out
    # Bx of multi-processing, data must be pushed using the queue.put method directly
    def pull(self,n,flush=False):

        # Pull data from queue until we get enough samples or the queue is empty
        xx = -self.prev
        while len(xx)<n and not self.buf.empty():
            xxx = self.buf.get()
            xx = np.concatenate( (xx, xxx) )

        # Did we get enough samples?
        if len(xx)>=n:

            # Yes - copy them to output buffer
            # Check if we're to flush the queue
            x = xx[0:n]
            if not flush:
                self.prev    = -xx[n:]
            else:
                # Flush the queue
                while self.buf.qsize()>1:
                    xxx = self.buf.get()
                self.prev = np.array([])             
            
        else:

            # No - save what we got for next time
            x = np.array([])
            self.prev = -xx

        #print 'Ringbuffer3 PULL:',n,len(x),self.buf.qsize()
        return x


                
# Defines a ring buffer object - this works fine for a threaded pragma but not for multiprocessing
class ring_buffer2:
    def __init__(self,tag,n,block=False):

        # data_type can be np.float32,np.complex64, etc.

        # Allocate the buffer & init pointers
        self.tag    = tag
        if sys.version_info[0]==3:
            self.buf    = queue.Queue(maxsize=n)
        else:
            self.buf    = Queue.Queue(maxsize=n)
        self.size   = n       # Size of the buffer
        self.nsamps = 0       # Counter of no. samples aailable
        self.block  = block   # If true, block on over/underflows
        self.prev   = np.array([])      # Overlap from pervious call

    # Data write & read functions with robust index checking
    # These allow arbirtrary chunk sizes to be accessed
    def push(self,x):

        if self.tag=='Audio1' and False:
            print(self.tag,'- Push',len(x),x.dtype)
        if self.tag!='Audio1' and False:
            print( self.tag,'- Push',x)
            print( self.tag,'- Push',len(x),x.dtype)
            
        self.nsamps += len(x)
        self.buf.put(x)

        if self.nsamps>self.size and False:
            print('Ringbuffer2: Push overflow',self.tag,self.nsamps,self.size)

    def pull(self,n,flush=False):

        if self.tag=='Audio1' and False:
            print(self.tag,'- Pull',n,flush)
            
        if flush:

            xx = self.prev
            while self.buf.qsize()>1 or len(xx)<n:
                xxx = self.buf.get()
                #print 'Pull:',len(xx),len(xxx),self.buf.qsize()
                xx = np.concatenate( (xx, xxx) )
                self.buf.task_done()
                self.nsamps -= len(xxx)
            x = xx[0:n]
            self.prev = []

        else:
            
            xx = self.prev
            while len(xx)<n:
                #xx = np.concatenate( (xx, self.buf.get()) )
                xxx = self.buf.get()
                xx = np.concatenate( (xx, xxx) )
                self.buf.task_done()
            x = xx[0:n]
            self.prev = xx[n:]
            self.nsamps -= n

        if len(x)!=n:
            print(self.tag,'Ringbuffer Queue error - expected',n,' samples, got',len(x))
            sys,exit(1)
        #if self.tag=='RF':
            #print self.tag,self.buf.qsize()

        if self.tag!='Audio1' and False:
            print( self.tag,'- Pull',x,np.iscomplexobj(x))
            print( self.tag,'- Pull',len(x),x.dtype)
            print( self.tag,'- Pull',len(xx),xx.dtype)
            #print( self.tag,'- Pull',len(self.prev),self.prev.dtype)
        #return x                                   # Old
        #return x.astype(np.float32)               # New but messes up IQ PSD
        if np.iscomplexobj(x):
            return x.astype(np.complex64)
        else:
            return x.astype(np.float32)

    def ready(self,n):
        if self.nsamps < n:
            if n>self.size:
                print('RING BUFFER READY - looking for too many samples!',n,self.size)
                sys,exit(1)
            return False
        else:
            return True

###################################################################

# convolver object - should be arbitrary
class convolver:
    def __init__(self,h,data_type):

        self.h    = h                # filter
        self.K    = len(h)           # Length of filter
        self.prev = np.zeros(self.K-1, data_type)     # Last part of previous chunk
        self.dtype=data_type

    # Function to do convolution in time domain, chunk by chunk
    def convolve_fast(self,x):
        K1=self.K-1                  # Length of overlap region
        h=self.h

        y1 = signal.convolve(x, self.h, mode='full')
        N  = len(y1)
        y2 = -self.prev + y1[ 0:K1 ]
        y3 = np.concatenate(( y2, y1[K1:(N-K1)] ))

        self.prev = -y1[(N-K1):]

        return y3
        
    # Function to do convolution in time domain, chunk by chunk
    def convolve(self,x):
        K=self.K                     # Length of filter
        N=len(x)                     # Chunk length
        h=self.h
        y = np.zeros(N, self.dtype)     # Allocate array

        # Pre-pend enough data from previous chunk to do filtering
        xx=np.concatenate((-self.prev, x))
#        print 'concat:',len(-self.prev),len(x),len(xx)
        NN=len(xx)

        # Compute output points
        noff=len(self.prev)           # Offset between original and pre-pended chunks
        n2=noff +1                    # Pointer into pre-pended chunk.xx
        nn=0                          # Pointer into decimated chunk, y
        n1=0
        while n2<=NN:
            xxx  = xx[(n2-K):n2]
#            print n2,K,len(x),NN,len(xxx)
            y[nn] = np.dot( xxx,h )

            n2 +=1
            nn +=1
            n1 +=1

        # Save tail end of input sequence for the next go round
        #        self.prev = -x[N-K+1:];
        self.prev = -xx[NN-K+1:];
#        print "CONVO:",len(x),len(y[0:nn]),len(self.prev)
#        print "CONVO:",n1,n2,self.first
#        print "noff=",noff

        return y[0:nn]


###################################################################

# Delay line object - should be arbitrary
class delay_line:
    def __init__(self,K,data_type):

        self.K    = K                                   # Delay
        self.prev = np.zeros(K, data_type)         # Last part of previous chunk
        self.nchunks = 0;
        self.dtype=data_type

    # Function to do the delay
    def delay(self,x):
        K=self.K        
        N=len(x)                     # Chunk length
        self.nchunks += 1;

        # The delay is simply the previous left-over part + the most of the current chunk
        n2 = N-K
        y  = np.concatenate((-self.prev, x[0:n2]))

        # Save tail end of input sequence for the next go round
        self.prev  = -x[n2:];

        return y


    # Function to do the delay - loop version used to diagnos python bug
    def delay0(self,x):
        K=self.K        
        self.nchunks += 1;
        prev=self.prev
        if self.nchunks<=3:
            print("prev=",prev)

        # The delay is simply the previous left-over part + the most of the current chunk
        y=0*x
        n=0
        while n<len(prev):
            y[n]=prev[n]
            n += 1

        n1=0
        while n<len(x):
            y[n]=x[n1]
            n += 1
            n1 += 1

        n11=n1
        n2=0
        while n1<len(x):
            self.prev[n2]=x[n1]
            n1 += 1
            n2 += 1

        # Save tail end of input sequence for the next go round
        if self.nchunks<=3:
            print("DELAY:",len(x),len(y),len(self.prev))
            print("x=",x)
            print("y=",y)
            print("prev=",prev)
            print(" ")

#        self.prev  = x[n11:];           # This doesn't work but
#        self.prev  = -x[n11:];          # THis does!  What a mess!

        return y


###################################################################

# Decimator object - should be arbitrary
class decimator:
    def __init__(self,h,ndec,nin,data_type):

        # data_type can be np.float32,np.complex64, etc.

        self.h    = h                # anti-aliasing filter
        self.K    = len(h)
        self.ndec = int(ndec)        # Decimation factor
        self.N    = nin              # Length of input chunk
        self.prev = np.zeros(self.K-1, data_type)     # Last part of previous chunk
        self.zero = np.zeros(self.N/self.ndec+1, data_type)
        self.first = 0
        self.dtype=data_type

    # Function to actually do the decimation
    def decim(self,x):
        K=self.K                     # Length of anti-aliasing filter
        N=self.N                     # Chunk length
        h=self.h
        y=self.zero                  # Allocate output array

        # Pre-pend enough data from previous chunk to do filtering
        xx=np.concatenate((-self.prev, x))
        NN=len(xx)

        # Compute decimated output points
#        n1=self.first                 # Pointer into current chunk, x
        noff=len(self.prev)           # Offset between original and pre-pended chunks
        n2=noff + self.first+1        # Pointer into pre-pended chunk.xx
        nn=0                          # Pointer into decimated chunk, y
        while n2<=NN:
            xxx  = xx[(n2-K):n2]
            y[nn] = np.dot( xxx,h )

#            n1 += self.ndec
            n2 += self.ndec
            nn +=1

        # Save tail end of input sequence for the next go round
#        self.first = n1 - self.N
        self.first = n2-noff-1 - self.N
        self.prev = -x[N-K+1 + self.first:N];

        return y[0:nn]


# A stand alone decimation function - not as robust
def decimate(x,h,ndec):
    N=x.size
    K=len(h)
    try:
        xprev = decimate.xprev
    except AttributeError:
        xprev = 0*x[N-K+1:N];

    idx=list(range(0,N,ndec))
    y=np.zeros(len(idx), np.float32)
    xx=np.concatenate((xprev, x))
    nn=0
    for n in idx:
        xxx  = xx[n : n+K]
        y[nn] = np.dot( xxx,h )
        nn +=1

    decimate.xprev=x[N-K+1:N];

    return y


###################################################################

# Signal generator object
class signal_generator:
    def __init__(self,fo,N,fs,force_fast=False):

        self.N     = N
        self.fs    = fs

        f2 = self.adjust_freq(fo,N,fs)
        if force_fast:
            fo = f2
            self.fast_mode = True
        else:
            self.fast_mode = ( abs(f2-fo) < 1e-5 )

        # Phase diff between samples due to carrier at fo
        self.fo    = fo
        self.dphi  = 2. * np.pi * fo / float(fs)

        # Phases over a block of N-samples
        self.phi   = self.dphi*np.arange(N)
        self.dphi2 = self.dphi*N
        self.phi0  = 0.

        # Determine if we need to recompute sines/cosines for each block
        #        M=round(fo/fs*N)
        #        f2 = M*fs/N
        if self.fast_mode:
            print('Sig gen using fast mode for fo=',fo)
            self.c = np.cos(self.phi)
            self.s = np.sin(self.phi)

            lo = self.c + 1j*self.s
            self.lo1 = np.concatenate( (lo,lo) )
            self.lo2 = np.conj( self.lo1 )
        else:
            print('\n***** Sig gen NOT using fast mode for fo=',fo, \
                ' - consider changing fo to',f2,' *****\n')

    # Routine to change LO freq
    def change_freq(self,fo):
        N  = self.N
        fs = float(self.fs)
        M  = round(fo/fs*N)
        f2 = M*fs/N
        
        self.fo    = f2
        self.dphi  = 2. * np.pi * f2 / fs
        self.phi   = self.dphi*np.arange(self.N)
        self.c = np.cos(self.phi)
        self.s = np.sin(self.phi)

        lo = self.c + 1j*self.s
        self.lo1 = np.concatenate( (lo,lo) )
        self.lo2 = np.conj( self.lo1 )

        return f2

    # Routine to adjust LO frequency, fo, so that we only need to compute
    # sines/cosines once.  This is accomplished by making sure there
    # are an integer number of full cycles in the a block of N-samples
    def adjust_freq(self,fo,N,fs):
        M=round(fo/float(fs)*N)
        f2 = M*float(fs)/N
        return f2

    # Change lo freq, forcing fast mode & re-init
    def force_fast_mode(self,fo):
        N = self.N
        fs = float( self.fs )
        f2             = self.adjust_freq(fo,N,fs)

        self.fo        = f2
        self.dphi      = 2. * np.pi * f2 / fs
        self.phi       = self.dphi*np.arange(N)
        self.fast_mode = True
        self.c         = np.cos(self.phi)
        self.s         = np.sin(self.phi)

        lo = self.c + 1j*self.s
        self.lo1 = np.concatenate( (lo,lo) )
        self.lo2 = np.conj( self.lo1 )

        print('Sig gen using fast mode for fo=',fo,' ---> ',f2)
        return f2

    # Real Sinusoid using a phase accumulator
    def tone_block(self):

        if self.fast_mode:
            x = self.c 
        else:
            x = np.cos(self.phi)
            self.phi += self.dphi2

        return x

    # Complex Sinusoid using a phase accumulator 
    def quad_osc_block(self):

        if self.fast_mode:
            x = self.c + 1j*self.s
        else:
            x = np.cos(self.phi) + 1j*np.sin(self.phi)
            self.phi += self.dphi2

        return x

    # Quadrature mixers - fastest - must use fast mode and constant block size
    def quad_mix_up(self,x):
        #lo = self.c + 1j*self.s
        n = len(x)
        y = x * self.lo1[0:n]
        self.lo1 = np.roll( self.lo1, -n )
        return y

    def quad_mix_down(self,x):
        #lo = self.c - 1j*self.s
        n = len(x)
        y = x * self.lo2[0:n]
        self.lo2 = np.roll( self.lo2, -n )
        return y

    # Quadrature mixer - arbitrary/variable chunk size
    def quad_mixer(self,x):

        N = len(x)
        if self.fast_mode and N==self.N:
            lo = self.c + 1j*self.s
        else:
            #if self.fast_mode:
            #print 'QUAD_MIXER - Warning - expected fast mode',N,self.N
            phi = self.phi0 + self.dphi*np.arange(N)
            self.phi0 += N*self.dphi
            lo = np.cos(phi) + 1j*np.sin(phi)

        y = x * lo
        return y

    # Real mixer - arbitrary/variable chunk size
    def real_mixer(self,x):

        N = len(x)
        if self.fast_mode and N==self.N:
            lo = self.c 
        else:
            phi = self.phi0 + self.dphi*np.arange(N)
            self.phi0 += N*self.dphi
            lo = np.cos(phi) 

        y = x * lo
        return y


# Tone generator - depricated
def tone_gen(fo,N,fs,nchunk):

    t = (N*nchunk + np.arange(N)) / float(fs)
    x = np.sin(2 * np.pi * fo * t)

    return x


###################################################################

# Here is the audio player.  PortAudio is apperently very finiky about
# the callback deadline which can lead to underruns.  These in turn peg
# the CPU, causing the SDR app to fall way behind.  To avoid this,
#       sudo emacs /etc/pulse/daemon.conf
# and uncomment the line
#       default-fragments = 4
# Then restart Pulse Audio:    pulseaudio --kill
#
# These websites are helpful in this regard:
# https://bbs.archlinux.org/viewtopic.php?id=185736
# https://wiki.archlinux.org/index.php/PulseAudio#Setting_the_default_fragment_number_and_buffer_size_in_PulseAudio

class AudioIO():
    def __init__(self,P,fs,rb,device=None,Chan='B',ZeroFill=False,Tag=None):
        print('AUDIO_IO: Init audio player @',fs,' Hz',
              '\trequested device=',device,'\tTag=',Tag,' ...')
        self.device = device
        self.fs = fs
        self.rb = rb
        self.p  = pyaudio.PyAudio()
        self.rb.Chan = Chan           # B,L or R for Both, Left or Right
        self.P = P
        self.stream=None
        self.last=None
        self.ZeroFill=ZeroFill

        if self.device==None:
            loopbacks = self.find_loopback_devices(True)
            default_device = self.p.get_default_output_device_info()
            print('Default device=',default_device)
        else:
            loopbacks = self.find_loopback_devices()
            print('AUDIO_IO: loopback device ids=',loopbacks)
            self.device = loopbacks[device-1]
            print('device=',device,'\t Using Device id=',self.device,'\n')
            #sys,exit(0)

        self.idle =True
        self.Start_Time = 0
        self.active=False
        self.nchan = 2

        # This can eventually be smplified since I now know how to do this with an object method
        self.FirstTime = True
        self.callback = self.AudioPlayCB
        print('Player Init')

    # Function to create a list of loopback devices
    def find_loopback_devices(self,INFO_ONLY=False):

        p=self.p
        info = p.get_host_api_info_by_index(0)
        numdev = info.get('deviceCount')
        print('\nFIND_LOOPBACK_DEVICES: info=',info,numdev)

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

            if "Loopback:" in name and srate==48000:
            #if "Loopback:" in name:
                #print dev_info
                loopback_devs.append(i)
                print('***')

        if len(loopback_devs)==0 and not INFO_ONLY:
            print('\n*** FIND_LOOP_BACKS - WARNING - None found ***\n')
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

        print("\nStarting audio play back @",self.fs," Hz ... tag=",
              self.rb.tag,'\tnsamps=',self.rb.nsamps,'\tdevice=',self.device)

        self.stream = self.p.open(output_device_index=self.device,
                                  format=pyaudio.paFloat32,
                                  channels=self.nchan,
                                  rate=self.fs,
                                  output=True,
                                  stream_callback=self.callback)

        self.stream.start_stream()
        self.Start_Time = time.time()
        self.active=True
        self.idle = False
        print("Audio playback started ...",self.rb.tag)
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

    # Callback to retrieve data for a hungry sound card.
    # Finally know how to do this without an external function!!!!
    def AudioPlayCB(self,in_data, frame_count, time_info, status):
        #print('HEY!!!!')

        rb=self.rb
        N=int(frame_count)

        ##################################################################
        # Handle problems - See comments just above AudioIO class def    #
        # on how to fix underruns                                        #
        ##################################################################

        if self.ZeroFill:
            Stopper=True
            if status!=0:
                print('Warning - AudioPlayCB Non-zero Status')
        else:
            Stopper = (self.P.Stopper and self.P.Stopper.isSet())
        if status!=0 and not Stopper:
            print("AudioPlayCB:",rb.tag,frame_count,time_info,status)
            if status == pyaudio.paOutputUnderflow:
                print("Houston, we have an underflow problem ...")
                print("Stalling until recharge",
                      rb.tag,rb.nsamps,self.last,self.nchan,rb.Chan)
                #print("See comments in sig_proc.py on how to fix if this persists")
                
                # Wait for ring buffer to fill half way again
                delay=self.P.RB_SIZE/self.P.FS_OUT/4
                #print(self.P.RB_SIZE,self.P.FS_OUT,delay)
                while not rb.ready( rb.size/2 ) and not self.P.REPLAY_MODE and not Stopper:
                    #print('Hey')
                    time.sleep(delay)
                    Stopper = (self.P.Stopper and self.P.Stopper.isSet())
                #print("Recharged on ",rb.tag,rb.nsamps,rb.size/2,self.P.RB_SIZE,N)
            
        # First time through, wait for ring buffer to start to fill
        if self.FirstTime and False:
            while rb.nsamps <= 4*N:
                time.sleep(.01)
                #pass
        self.FirstTime = False

        # Pull next chunk from the ring buffer
        if self.ZeroFill:
            nready = rb.nsamps
            #print('Available:',nready,N)
            if nready>=N:
                x=rb.pull(N)
            else:
                #x=rb.pull(nready)
                #print('Need padding')
                #x=np.array(N*[0]*self.nchan)
                x=np.array(N*[0])
        else:
            x=rb.pull(N)
            #print('Pulled',rb.tag,x.dtype,self.nchan,rb.Chan)
    
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
            data = x.astype(np.complex64).tostring()
        else:
            data = x.astype(np.float32).tostring()
        
        self.last=len(data)
        #print('Pushed',N,self.last)
        return (data, pyaudio.paContinue)

###################################################################

# Various demodulators

class Demodulator:
    def __init__(self,P,AF_BWs,FAST_SCHEME):
        self.P = P
        if FAST_SCHEME:
            fs = P.FS_OUT/float(P.UP)
        else:
            fs = P.FS_OUT

        # Design all the audio filters
        n=501                # 501 - This needs to be large for narrow filters
                             # Might want to re-think this later on
        flow=300.
        self.filter_bank_real,junk      = bpf_bank(1*flow,AF_BWs,fs,n,False)
        self.filter_bank_cmpx,self.dfrq = lpf_bank(AF_BWs,fs,n,True)           # These have to be LPFs for Weaver SSB

        # Create a filtering object for post-det filtering
        self.last_type = False
        self.filt_num = 0
        h=self.filter_bank_real[self.filt_num]
        self.lpf_post  = convolver(h,np.complex64)
        self.lpf_post2 = convolver(h,np.float32)          # Can be used to put a notch near DC - not fully implemented

        # For SSB phase method - no longer used
        if False:
            n=21
            self.h=hilbert(n)
            #print "Hilbert filter=",self.h
            self.hilbert = convolver(self.h,np.float32)

            #self.delay_line   = delay_line(int(n/2),np.float32)
            self.delay_line = delay_line(10,np.float32)

        # For SSB Weaver method - 2nd lo is for CW
        df = self.dfrq[self.filt_num] 
        print('LO Weaver:',df,P.OUT_CHUNK_SIZE,fs)
        self.lo_weaver  = signal_generator( df,     P.OUT_CHUNK_SIZE,fs,True)
        print('LO CW:   ',P.BFO,P.OUT_CHUNK_SIZE,fs)
        self.lo_cw      = signal_generator( P.BFO,P.OUT_CHUNK_SIZE,fs,True)

        # Wideband (broadcast) FM - needs works
        print('LO WFM:  ',-38e3,P.IN_CHUNK_SIZE,P.SRATE)
        self.lo_wfm = signal_generator(-38e3,P.IN_CHUNK_SIZE,P.SRATE,True)
        self.delays = np.zeros(2, np.complex64)      # 2 delay elements
        self.fm_scaling = P.FS_OUT/100

        # PLL-based demod
        self.fm_pll = PLL(fs,1000.,0.707)
        self.am_pll = PLL(fs,50.,0.707)

    # Envelope AM = sqrt( I^2 + Q^2 )
    def am_envelope(self,iq):
        x = np.sqrt( np.square(iq.real) + np.square(iq.imag) )
        y = self.post_det(x)
        return y.real
    
    # Synchrounous AM det
    # Note - further option would be to select sideband, i.e. follow with weaver SSB
    def am_synch(self,iq):
        carrier = self.am_pll.am_block(iq)
        x = iq*carrier
        y = self.post_det(x.real)
        return y.real

    # Beat Freq Osc style ssb - doesn't distinguish U/L sidebands
    def ssb(self,iq):
        # am  = y.real
        # am = y.imag
        # am  = y.real + y.imag
        # am  = y.real - y.imag
        return iq.real + iq.imag

    # Phase method USB
    def usb_phase(self,iq):
        ii = self.delay_line.delay(iq.real)
        qq = self.hilbert.convolve(iq.imag)
        return ii + qq

    # Phase method LSB
    def lsb_phase(self,iq):
        ii = self.delay_line.delay(iq.real)
        qq = self.hilbert.convolve(iq.imag)
        return ii - qq

    # Weaver method USB 
    def usb_weaver(self,iq):
        self.check_filter(True)
        y1 = self.lo_weaver.quad_mix_down(iq)
        y2 = self.lpf_post.convolve_fast(y1)
        y3 = self.lo_weaver.quad_mix_up(y2)
        if True:
            y4 = y3.real + y3.imag
        else:
            # This allow us to put a notch near DC - not fully implemented yet
            y4 = self.lpf_post2.convolve_fast(y3.real + y3.imag)
        return y4

    # Weaver method LSB
    def lsb_weaver(self,iq):
        self.check_filter(True)
        y1 = self.lo_weaver.quad_mix_up(iq)
        y2 = self.lpf_post.convolve_fast(y1)
        y3 = self.lo_weaver.quad_mix_down(y2)
        return y3.real + y3.imag

    # Plain vanilla CW - SDR is centered on desired signal so
    # we just filter around DC and shift up to effect 700 Hz pitch
    def cw(self,iq):
        self.check_filter(True)
        y2 = self.lpf_post.convolve_fast(iq)
        y3 = self.lo_cw.quad_mix_up(y2)
        return y3

    # FM ~ I*dQ/dt - Q*dI/dt
    # Derivatives are approximated by a 2nd-order difference
    def fm(self,iq):

        N  = len(iq)
        y  = np.concatenate((-self.delays, iq))

        d  = iq - y[0:N];
        y1 = y[1:(N+1)]

        fm = y1.real*d.imag - y1.imag*d.real
#        print 'FM type=',type(fm),fm.dtype

        self.delays = -iq[(N-2):N]

        return fm*self.fm_scaling

    # Narrowband FM
    def nfm(self,iq):
        if True:
            # Conventional demod - seems CPU efficient
            fm = self.fm(iq)
        else:
            # Use a PLL - this seems to be CPU intensive
            fm = self.fm_pll.fm_block(iq)
            #print np.mean(fm)*1e8
        am = self.post_det(fm.real).real
        return am

    # Narrowband FM
    def nfm_OLD(self,iq):

        # This is depricated - it uses wideband data
        y = self.lpf5.convolve_fast(iq)
        fm = self.fm(y)
        y = self.P.dec.resample_fast(fm).real
        nfm = self.post_det(y)

        return nfm

    
    # Function to handle filter changes
    def check_filter(self,CMPLX):
        #print('CHECK_FITLER in: filt_num=',
        #      self.filt_num,self.P.AF_FILTER_NUM,
        #      '\tCMPLX=',CMPLX,self.last_type)

        # Check that we have the proper filter in place
        #if self.filt_num and  \
        if ( (self.filt_num != self.P.AF_FILTER_NUM) or \
             (CMPLX != self.last_type)):
            self.filt_num = self.P.AF_FILTER_NUM
            if CMPLX:
                self.lpf_post.h = self.filter_bank_cmpx[self.filt_num]
            else:
                self.lpf_post.h = self.filter_bank_real[self.filt_num]

            df = self.dfrq[self.filt_num]
            self.lo_weaver.force_fast_mode(df)
            print("\n############## Check Filter:",CMPLX,self.filt_num,df,self.P.BFO,'\n')

            self.last_type = CMPLX

        

    # Post-detection filtering
    def post_det(self,x):
        if self.P.AF_FILTER_NUM<=0:
            return x
        elif False:
            # Check that we have the proper filter in place
            this_type = np.iscomplexobj(x)
            if (self.filt_num != self.P.AF_FILTER_NUM) or \
               (this_type != self.last_type):
                self.filt_num = self.P.AF_FILTER_NUM
                if this_type:
                    self.lpf_post.h = self.filter_bank_cmpx[self.filt_num]
                else:
                    self.lpf_post.h = self.filter_bank_real[self.filt_num]
                self.last_type = this_type

        else:
            self.check_filter(np.iscomplexobj(x))

        #print('POST_DET: Calling fast convolver - filt num=',
        #      self.filt_num,self.P.AF_FILTER_NUM)
        y = self.lpf_post.convolve_fast( x )
        #print 'TYPES:',x.dtype,y.dtype,this_type
        return y

###################################################################

# Resampling

# Function to compute re-sampling interpolation and decimation params 
def up_dn(fs1,fs2):
    g  = gcd(int(fs1),int(fs2))
    up = int( fs2/g )
    dn = int( fs1/g )

    return up,dn

# Resampler object - interp, filter and down-sample by dn
class resampler:
    def __init__(self,h,up,dn,data_type):

        self.h    = h                # filter
        self.K    = len(h)           # Length of filter
        self.up   = up               # Interpolation factor
        self.dn   = dn               # Decimation factor
        self.prev = []               # Overlap from pervious call
        self.dtype=data_type         # Data type
        self.nadd  = 0               # No. of zeros to pre-pend on next call

    # Function to do convolution in time domain, chunk by chunk
    # This function wraps the scipy upfirdn function so that it
    # can be successively called with continuity preserved
    def resample_fast(self,x):
        h=self.h
        K=self.K
        up = self.up
        dn = self.dn

        # If there is no dat, just flush the buffer
        if len(x)==0:
            y = -self.prev
            self.prev=[]
            self.nadd  = 0
            return y

        # Resample this chunk
        # upfirdn supposedly is an efficient polyuphase implementation
        # but does not given any obvious method for preserving the
        # "phasing" of the data sampling.  To overcome this, we
        # pre-pend some zeros so that continutity is preserved from the previous call
        x = np.concatenate( (np.zeros(self.nadd), x) )
        nx = len(x)
        y = signal.upfirdn(self.h, x, up, dn)

        # Stich in residual from previous chunk
        N=len(self.prev)
        if N>0:
            yy = -self.prev + y[0:N]
            y = np.concatenate((yy, y[N:] ))

        # Phasing for next go round
        # the first sample out of upfirdn is the first sample as if
        # the filter were applied to the first input sample followed
        # by dn-1 zeros, e.g. for up=5 and dn=3:
        #
        #         x:      x0         x1         x2         x3
        #         x up5:  x0 0 0 0 0 x1 0 0 0 0 x2 0 0 0 0 x3
        #         y:      y0     y1     y2    y3     y4    y5
        #
        # Here, x0 has a sampling phase of 0, x1 has a phase of 2, x2 has 1 and x3 has 0
        # with respect to the down-sampling.
        # So the next time we come in, we want to preserve the relative phasing of
        # the input data wrt to down-sampling.  We will do this by pre-pending
        # the correct amount of zeros to effect this.
        #
        # Compute required phasing for next sample (e.g. x4 above)
        m1=(nx*up) % dn
        #print "Phasing:",m1

        # Determine how many zeros we'll need to pre-pend next time to make this happend
        m2=-99
        nadd=-1
        while m2!=m1:
            nadd=nadd+1
            m2 = (nadd*up) % dn
        self.nadd  = nadd

        # This pre-pending results in extra output data at the beginning of the next
        # call so we need to figure out how to align the two output chunks.
        # n0 is output sample number of the current data
        # n1 how many samples we need to back-up because of the pre-pending
        # n2 is output sample number of the first output point in the next chunk
        # due to the pre-pending
        n0 = 1 + ( nx*up-1 ) / dn 
        n1 = 1 + (nadd*up-1) / dn
        n2 = int( n0-n1 )
        #print "nadd n0 n1 n2=",nadd,n0,n1,n2

        # Save points at tail end that will overlap with next chunk
        self.prev = -y[n2:]

        # Return only the valid part of current chunk
        return y[0:n2]
        
    # Wrapper for decimation only
    def decim9(self,x):
        if self.up==1:
            return self.resample_fast(x)
        else:
            print('\n **** ERROR in resampler.decim - up-sampling needed ***\n')
            print('up,dn=',self.up,self.dn)
            sys.exit(1)

############################################################################

# CIC resampler object - interp, filter and down-sample 
class CIC_Filter:
    def __init__(self,N,up,dn,ibits):
        self.N    = N                # filter order
        self.up   = up
        self.dn   = dn
        self.ibits = ibits
        self.dtype = np.int64
        #self.dtype = np.float32
        self.reset()

        # Scale data to ibits bits
        self.sc = 2.**ibits
        R1 = self.up
        self.scup = 1./float(self.sc * (R1**(N-1)))
        R2=self.dn
        self.scdn = 1./float(self.sc * (R2**N))
        R=R1*R2

        # Calculate the total number of bits used internally, 
        # and the output shift and mask required.
        bit_growth = N * int(round(np.log2(R)))
        numbits = ibits + bit_growth
        #outshift = numbits - obits
        #outmask  = (1 << obits) - 1
        print('\nCIC Bit Growth=',bit_growth)
        #print 'N=',N
        #print 'R=',R,np.log2(R)

        # If we need more than 64 bits, we can't do it...
        #assert numbits <= 64
        if numbits > 64:
            print('\n*** ERROR *** CIC Filter will overflow')
            print('up/dn=',self.up,self.dn)
            print('ibits=',ibits)
            #sys.exit(0)

    # Function to reset CIC resampler
    def reset(self):
        N = self.N
        dtype = self.dtype
        
        self.prev1r = np.zeros(N,dtype)
        self.prev2r = np.zeros(N,dtype)
        self.prev1i = np.zeros(N,dtype)
        self.prev2i = np.zeros(N,dtype)

        self.prev3r = np.zeros(N,dtype)
        self.prev4r = np.zeros(N,dtype)
        self.prev3i = np.zeros(N,dtype)
        self.prev4i = np.zeros(N,dtype)
        self.istartr = 0
        self.istarti = 0

        self.last_was_complex = False

    # CIC Decimator for real sigs
    def cic_decim(self,x,ichan=0):

        N = self.N
        R = self.dn

        # If length of input buffer is zero, flush the filter
        if len(x)==0:
            y=np.zeros(N*(R-1), self.dtype)
        else:
            #y=np.array(self.sc*x , self.dtype)
            y=(self.sc*x).astype(self.dtype)

        # Select channel - this allows us to call it twice to handle complex sigs
        if ichan==0:
            prev1 = self.prev1r
            prev2 = self.prev2r
            istart = self.istartr
        elif ichan==1:
            prev1 = self.prev1i
            prev2 = self.prev2i
            istart = self.istarti
        else:
            print('CIC_DECIM - Only two channels available')
            sys.exit(1)
            
        # Cascaded integrators
        for i in range(N):
            y[0] += prev1[i]
            y     = np.cumsum(y)
            prev1[i] = y[-1]
            
        # Decimate
        yy = y[istart : : R]

        # Determine phasing for next go round
        n=len(y)
        ilast = (istart + (n/R)*R)
        while ilast>=n:
            ilast -= R
        istart = ilast + R - n

        # Cascaded comb stages - work backwards to preserve data
        Ny=len(yy)
        prev2new = np.zeros(N,self.dtype)
        for i in range(N):
            prev2new[i] = yy[-1]
            yy[Ny-1 : 0 : -1] -= yy[Ny-2 : : -1]
            yy[0] -= prev2[i]

        # Save state for next go round
        if ichan==0:
            self.prev1r = prev1
            self.prev2r = prev2new
            self.istartr = istart
        else:
            self.prev1i = prev1
            self.prev2i = prev2new
            self.istarti = istart
            
        return self.scdn*yy

    # CIC Decimator for complex sigs
    def cic_decim_cmplx(self,x):

        y1 = self.cic_decim(np.real(x),0)
        if np.iscomplexobj(x) or  (len(x)==0 and self.last_was_complex):
            y2 = self.cic_decim(np.imag(x),1)
            self.last_was_complex = True
            return y1 + 1j*y2
        else:
            self.last_was_complex = False
            return y1

    
    # CIC Interpolator for real sigs
    def cic_interp(self,x,ichan=0):

        N = self.N
        R = self.up

        # If length of input buffer is zero, flush the filter
        if len(x)==0:
            yy = np.zeros(N*(R-1), self.dtype)
        else:
            yy = np.array(self.sc*x , self.dtype)
            
        # Select channel - this allows us to call it twice to handle complex sigs
        if ichan==0:
            prev3 = self.prev3r
            prev4 = self.prev4r
        elif ichan==1:
            prev3 = self.prev3i
            prev4 = self.prev4i
        else:
            print('CIC_DECIM - Only two channels available')
            sys.exit(1)
            
        # Cascaded comb stages - work backwards to preserve data
        Ny=len(yy)
        prev3new = np.zeros(N,self.dtype)
        for i in range(N):
            prev3new[i] = yy[-1]
            yy[Ny-1 : 0 : -1] -= yy[Ny-2 : : -1]
            yy[0] -= prev3[i]
        
        # Insert zeros
        y = np.zeros( R*Ny , self.dtype)
        y[::R] = yy

        # Don't need to worry about phasing bx we insert R-1 trailing zeros above

        # Cascaded integrators
        for i in range(N):
            y[0] += prev4[i]
            y     = np.cumsum(y)
            prev4[i] = y[-1]

        # Save state for next go round
        if ichan==0:
            self.prev4r = prev4
            self.prev3r = prev3new
        else:
            self.prev4i = prev4
            self.prev3i = prev3new
            
        return self.scup*y

    # CIC Decimator for complex sigs
    def cic_interp_cmplx(self,x):

        y1 = self.cic_interp(np.real(x),0)
        if np.iscomplexobj(x) or (len(x)==0 and self.last_was_complex):
            y2 = self.cic_interp(np.imag(x),1)
            self.last_was_complex = True
            return y1 + 1j*y2
        else:
            self.last_was_complex = False
            return y1

    # CIC Interpolator/Decimator for complex sigs
    def cic_updn(self,x):

        up=self.up
        dn=self.dn

        if up>1 and dn>1:
            y1 = self.cic_interp_cmplx(x)
            y2 = self.cic_decim_cmplx(y1)
            return y2
        elif up>1:
            y1 = self.cic_interp_cmplx(x)
            return y1
        elif dn>1:
            y2 = self.cic_decim_cmplx(x)
            return y2
        else:
            print('WARNING - CIC_UPDN  is a No-op')
            return x

    # Compatability wrapper 
    def resample_fast(self,x):
        return self.cic_updn(x)

############################################################################

# AGC loop - needs some work
class Gain_Control:
    def __init__(self,P):

        self.P      = P
        self.N      = 10
        self.ref    = 0.1
        self.buf    = np.zeros(self.N, np.float32)
        self.maxbuf = 0
        self.err    = 0
        self.reset()

    def reset(self):

        print('AGC RESET')
        self.gain = 1
        self.agc  = 0
        self.ptr  = 0
        self.buf  = 0.*self.buf

    def agc_loop(self,am):

        P   = self.P
        agc = self.agc
        err = 0

        if False:
        
            # No AGC
            if P.MODE=='WFM' or P.MODE=='WFM2':
                gain=4
            elif P.MODE=='NFM':
                gain=20
            else:
                gain=250
            
        elif False:

            # Linear agc with FIFO
            beta=0.1
            if agc==0.:
                agc=1.
            gain=self.gain

            # Keep the max from the last N chunks
            #self.buf[self.ptr] = gain*max(abs(am))
            #m = max( self.buf )
            m = gain*max(abs(am))
            if self.ptr>=self.N-1:
                self.ptr=0
            else:
                self.ptr += 1

            if m>0.:
                if agc==1:
                    agc = self.ref/m
                    gain = (agc-1)*gain
                    print('AGC JAMMED1',agc)
                else:
                    agc = (1.-beta)*agc + beta*self.ref/m
            err=agc-1
            if abs(err)>0.2:
                gain = gain + 0.01*err*gain
            print('AGC_LOOP:',m,self.ref,ref/m,err,agc,gain)

        elif True:

            # Log agc with FIFO 
            beta=0.01          # 0.1
            gain=self.gain

            # Keep the max from the last N chunks
            #self.buf[self.ptr] = gain*max(abs(am))
            #m = max( self.buf )
            m = gain*max(abs(am))
            if self.ptr>=self.N-1:
                self.ptr=0
            else:
                self.ptr += 1

            if m>0. or True:
                err = np.log(self.ref / m)
                if agc==0:
                    agc = err
                    print('AGC JAMMED2',agc,self.ref,m)
                else:
                    agc = agc + beta*err*agc
            gain = abs(agc)
            #print 'AGC_LOOP:',m,self.ref,self.ref/m,err,gain

        elif False:

            # Log agc with FIFO - seems to work - used for quite some time
            beta=0.1 # 0.01
            gain=np.exp(agc)

            # Keep the max from the last N chunks
            self.buf[self.ptr] = gain*max(abs(am))
            m = max( self.buf )
            if self.ptr>=self.N-1:
                self.ptr=0
            else:
                self.ptr += 1

            if m>0.:
                if agc==0. :
                    agc=np.log(self.ref/m)
                else:
                    #agc = agc + beta*np.log(self.ref/m)
                    err = np.log(self.ref/m)
                    agc = (1.-beta)*agc + beta*err
                #print 'AGC_LOOP:',np.log(m),self.ref,err,agc,gain

        self.agc    = agc
        self.gain   = gain
        self.maxbuf = m
        self.err    = err

############################################################################

# Digitial receiver
class Receiver:
    def __init__(self,P,foffset,irx,tag,VIDEO_BWs,AF_BWs):
        print("Receiver: Init",foffset)
        self.P = P
        self.tag=tag
        self.FAST_SCHEME=True
        self.FAST_SCHEME=False
        self.iq=[]
        self.irx = irx
        #self.player=None

        self.USE_CIC = False
        #self.USE_CIC = True

        if P.SOURCE[irx]<0 or P.SOURCE[irx]==irx:
            # Data source for this rx is the SDR
            self.fs = P.SRATE
            self.chunk_size = P.IN_CHUNK_SIZE
            self.SOURCE = -1
            print('\nData source for rx',irx,'is the SDR',self.fs,self.chunk_size)
        else:
            # Data source is IQ of one of the other rx's
            self.fs = P.FS_OUT
            self.chunk_size = P.OUT_CHUNK_SIZE
            self.SOURCE = P.SOURCE[irx]
            print('\nData source for rx',irx,'is IQ from RX',self.SOURCE,self.fs,self.chunk_size,foffset)

        # Local osc
        # For computational efficiency, the LO freq is likely changed in
        # the following call.  We compenstate for this by adjusting the
        # tuning offset.
        print('LO:      ',-foffset,self.chunk_size,self.fs)
        self.lo = signal_generator(-foffset,self.chunk_size,self.fs,True)
        if self.SOURCE<0:
            # Not quite sure why this is here??
            P.FOFFSET += self.lo.fo + foffset
        print(self.lo.fo,P.FOFFSET)

        # Decimator and anti-aliasing filter
        if self.USE_CIC:
            print('RECEIVER INIT: Using CIC')
            Ncic = 5
            ibits =  12
            self.dec               = CIC_Filter(Ncic,P.UP,P.DOWN,ibits)
            video_filter_bank,junk = lpf_bank(VIDEO_BWs,P.UP*self.fs,P.FILT_LEN,True,P.VIDEO_BW,P.UP)
        elif not self.FAST_SCHEME:
            if True:
                print('RECEIVER INIT: Using slow scheme',P.UP,P.DOWN,VIDEO_BWs)
                video_filter_bank,junk = lpf_bank(VIDEO_BWs,P.UP*self.fs,P.FILT_LEN,True,P.VIDEO_BW,P.UP)
                self.dec               = resampler(video_filter_bank[2],P.UP,P.DOWN,np.complex64)
            else:
                print('RECEIVER INIT: Using slow scheme',P.UP,P.DOWN,AF_BWs)
                video_filter_bank,junk = lpf_bank(AF_BWs,P.UP*self.fs,P.FILT_LEN,True,P.AF_BW,P.UP)
                self.dec               = resampler(video_filter_bank[2],P.UP,P.DOWN,np.complex64)
        else:
            print('RECEIVER INIT: Using fast scheme')
            video_filter_bank,junk = lpf_bank(VIDEO_BWs,self.fs,P.FILT_LEN,True,P.VIDEO_BW,P.UP)
            self.dec               = resampler(video_filter_bank[2],1   ,P.DOWN,np.complex64)
        #sys.exit(0)
        self.dec.filter_bank   = video_filter_bank

        # Demodulators
        self.demod = Demodulator(P, AF_BWs, self.FAST_SCHEME)
        if self.FAST_SCHEME:
            # *** Need to take out hard wired params here!!!!!!
            nf=101   #501
            fb,junk                = lpf_bank(AF_BWs,P.FS_OUT,nf,True)
            self.dec2              = resampler(fb[10],P.UP,1,np.complex64)

        video_filter_bank2,junk    = lpf_bank(VIDEO_BWs,self.fs,P.FILT_LEN,True,P.VIDEO_BW,1.)
        self.demod.wfm_video       = convolver(video_filter_bank2[6],np.complex64)
        self.demod.wfm_filter_bank = video_filter_bank2

        # Gain control
        self.agc = Gain_Control(P)
        

    def demod_data(self,x):

        P     = self.P
        lo    = self.lo
        dec   = self.dec
        demod = self.demod
        agc   = self.agc

        # Shift by tuning offset
        if self.SOURCE<0 and lo.fo!=0:
            x1 = lo.quad_mixer(x)
        else:
            x1=x

        if False:
            print('LO fo=',lo.fo)
            print('UP/DOWN=',P.UP,P.DOWN)

        # Down-sample shifted input data.
        # Broadcast FM is a wideband signal so we need to demod before reducing the sample rate
        if P.MODE!='WFM' and P.MODE!='WFM2':
            if self.SOURCE>=0:
                yy = P.rx[self.SOURCE].iq
                y  = lo.quad_mixer(yy)
                #print 'RX',self.irx,self.tag,'taking IQ from RX',self.SOURCE,lo.fo,lo.fs,len(yy),lo.N,len(y)
            elif P.UP!=1 or P.DOWN!=1 or True:
                # Need to always do this so that video filter is applied
                y = dec.resample_fast(x1)
            else:
                y=x1
            self.iq = y
        
        # Select demodulator
        if P.MODE=='IQ' or P.MODE=='RTTY':
            #am = y
            if P.BFO==0:
                am = demod.post_det(y)
            else:
                am = demod.cw(y)
                
        elif P.MODE=='AM-Synch':
            am = demod.am_synch(y)

        elif P.MODE=='AM':
            am = demod.am_envelope(y)

            # DC Removal
            if P.nchunks<=2:
                dc = np.mean(am)
            else:
                dc=0
            alpha=max(0.01,1./P.nchunks)
            #print 'AM TYPES:',y.dtype,am.dtype,dc.dtype

            if True:
                am = am-dc
            dc = dc + alpha*np.mean(am)
            #print 'DC:',dc,np.mean(am)
        
        elif P.MODE=='SSB':
            am = demod.ssb(y)
        elif P.MODE=='CW':
            am = demod.cw(y)
        elif P.MODE=='USB':
            #am = demod.usb_phase(y)
            am = demod.usb_weaver(y)
        elif P.MODE=='LSB':
#            am = demod.lsb_phase(y)
            am = demod.lsb_weaver(y)
        elif P.MODE=='WFM':

            y1 = demod.wfm_video.convolve_fast(x1)
            self.iq = y1
            fm = demod.fm(y1)

            # The de-emphasis filter
            # Given a signal 'x5' (in a numpy array) with sampling rate Fs_y
            #d = Fs_y * 75e-6   # Calculate the # of samples to hit the -3dB point  
            #x = np.exp(-1/d)   # Calculate the decay between each sample  
            #b = [1-x]          # Create the filter coefficients  
            #a = [1,-x]  
            #x6 = signal.lfilter(b,a,x5)  
            
            y = dec.resample_fast(fm).real
            if True:
                am = demod.post_det(y)
            else:
                am = y

        elif P.MODE=='WFM2':
            # Stereo FM - not sure if levels are correct
            y1 = demod.wfm_video.convolve_fast(x)
            fm = demod.fm(y1)

            y2 = demod.lo_wfm.real_mixer(fm)    # Spectrum shift to get at L-R
            bb = fm + 1j*y2                     # Put L+R on I and L-R on Q

            y3 = dec.resample_fast(bb)          # Down-sample both channels
            #y4 = demod.post_det(y3)
            y4 = y3
            
            L  = y4.real + y4.imag
            R  = y4.real - y4.imag
            #am = y3.real     # L+R - mono 
            #am = y3.imag     # L-R
            am = L + 1j*R
            
        elif P.MODE=='NFM':
            am = demod.nfm(y)
            #am = demod.post_det(fm.real).real
            #print 'NFM:',fm.dtype,am.dtype
        else:
            print("Unknown MODE - ",P.MODE)
            sys.exit(1)

        # AGC loop 
        agc.agc_loop(am)
        am = agc.gain*am

        # Up sample rate to desired output rate
        if self.FAST_SCHEME and True:
            #print('DEMOD_DATA - Calling fast resampler ...')
            am2 = self.dec2.resample_fast(am)
            return am2

        self.am = am
        return am

