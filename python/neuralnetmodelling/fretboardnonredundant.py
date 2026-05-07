# GuitarMidi-LV2 Library
 # Copyright (C) 2026 Gerald Mwangi
 #
 # This program is free software; you can redistribute it and/or
 # modify it under the terms of the GNU Lesser General Public
 # License as published by the Free Software Foundation; either
 # version 2 of the License, or (at your option) any later version.
 #
 # This program is distributed in the hope that it will be useful,
 # but WITHOUT ANY WARRANTY; without even the implied warranty of
 # MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
 # Lesser General Public License for more details.
 #
 # You should have received a copy of the GNU Lesser General
 # Public License along with this program; if not, write to the
 # Free Software Foundation, Inc., 51 Franklin Street, Fifth Floor,
 # Boston, MA  02110-1301  USA
num_harmonics=4 
num_frets=13
num_strings=6
from scipy import signal 
import numpy as np
from joblib import Parallel, delayed
class Filter:
    def __init__(self, filterid,center_freq, q,sample_rate):
        self.id=filterid
        self.sample_rate=sample_rate
        bw=center_freq/q 
        # create the filter
        N = 2
        low = (center_freq-bw/2) 
        high = (center_freq+bw/2) 
        #self.b, self.a = signal.ellip(N,0.5,40,[low, high], btype='band',fs=sampleRate)
        self.b, self.a =signal.butter(N, [low, high], btype='band',fs=sample_rate)
        self.zi=signal.lfilter_zi(self.b,self.a)
        self.zi_initial=self.zi.copy()
        
    def process(self,input_audio,filterbank_out: np.array):
        out, self.zi = signal.lfilter(self.b, self.a, input_audio, zi=self.zi)
        filterbank_out[self.id] = np.abs(out)
    def reset(self):
        self.zi=self.zi_initial


class GuitarNote:
    def __init__(self,noteid ,center_freq, q,sample_rate):
        self.harmonics=[]
        
        for h in range(1,num_harmonics+1):
            filterid=noteid*num_harmonics+h-1
            self.harmonics.append(Filter(filterid,center_freq*h,q,sample_rate))
    
            
    def process(self, input_audio, filterbank_out: np.array):
        # def process_harmonic(h):
        #     h.process(input_audio,filterbank_out)
        # Parallel(n_jobs=1,backend="threading")(delayed(process_harmonic)(h) for h in self.harmonics)
        
        for h in self.harmonics:
            #filterbank_out.append(h.process(input_audio))
            h.process(input_audio,filterbank_out)
    def reset(self):
        for h in self.harmonics:
            h.reset()
            
  
    def get_num_filters(self):
        return len(self.harmonics)
          
            
class GuitarString:
    def __init__(self,frets: dict, q,sample_rate):
        assert len(frets)<=num_frets
        #print("Frets: ",type(frets)," values: ",frets)
        self.frets=[]
        for noteid,notefreq in frets.items():
            
            self.frets.append(GuitarNote(noteid,notefreq,q,sample_rate))
    def process(self, input_audio, filterbank_out: np.array):        
        for fret in self.frets:
            #filterbank_out.append(h.process(input_audio))
            fret.process(input_audio,filterbank_out)
    def reset(self):
        for fret in self.frets:
            fret.reset()
            
  
    def get_num_filters(self):
        res=0
        for fret in self.frets:
            res+=fret.get_num_filters()
        return res
            
            
class FretBoard:
    def __init__(self,q,sample_rate):
        self.strings=[]
        # add the e string
        self.strings.append(GuitarString({0:82,1:87,2:92,3:98,4:104},q,sample_rate))
        self.strings.append(GuitarString({5:110,6:117,7:123,8:131,9:139},q,sample_rate))
        self.strings.append(GuitarString({10:147,11:156,12:165,13:175,14:185},q,sample_rate))
        self.strings.append(GuitarString({15:196,16:208,17:220,18:233},q,sample_rate))
        self.strings.append(GuitarString({19:247,20:262,21:277,22:294,23:311},q,sample_rate))
        self.strings.append(GuitarString({24:329,25:349,26:370,27:392,28:415,29:440,30:466,31:494,32:523,33:554,34:587,35:622,36:659},q,sample_rate))


   #Parallel(n_jobs=5)(delayed(prepare_audio_midi_data)(f) for f in all_jams_files)      
    def process(self, input_audio, filterbank_out: np.array):
      
        # def process_fret(h):
        #     h.process(input_audio,filterbank_out)
        # Parallel(n_jobs=12,backend="threading")(delayed(process_fret)(h) for h in self.frets)
        for h in self.strings:
            # filterbank_out.append(h.process(input_audio,filterbank_out))    
            res=h.process(input_audio,filterbank_out)
    def reset(self):
        for s in self.strings:
            s.reset()
       
    def get_num_filters(self):
        res=0
        for h in self.strings:
            res=res+h.get_num_filters()
            
        return res
    # def get_harmonic_group(self,fret,string):
    #     return self.frets[fret].strings[string]
    

import math
# Get the highest and  the lowest delay of a guitarnote
def get_guitarnote_delays(midi_note: int, q: float, sample_rate: int):
    highest_harmonic=get_butterworth_group_delay(midi_note,num_harmonics,q,sample_rate)
    fundamental=get_butterworth_group_delay(midi_note,1,q,sample_rate)
    return (highest_harmonic,fundamental)
def get_butterworth_group_delay(
    midi_note: int,
    harmonic: int,
    q: float,
    sample_rate: int
) -> int:
    """
    Calculates the group delay of a 2nd-order Butterworth BANDPASS filter
    at the center frequency, for a given harmonic of a MIDI note.

    Args:
        midi_note (int):   The MIDI note number (0-127).
        harmonic (int):    The harmonic number (1 = fundamental, 2 = 2nd, etc.).
        q (float):         The Q factor (controls bandwidth: BW = f_c / Q).
        sample_rate (int): The sample rate in Hz (e.g. 44100, 48000).

    Returns:
        float: The group delay in samples at the center frequency.

    Raises:
        ValueError: If inputs are out of valid range or exceed Nyquist.
    """
    # --- Input validation ---
    if not (0 <= midi_note <= 127):
        raise ValueError(f"midi_note must be 0-127, got {midi_note}")
    if harmonic < 1:
        raise ValueError(f"harmonic must be >= 1, got {harmonic}")
    if q <= 0:
        raise ValueError(f"Q factor must be positive, got {q}")
    if sample_rate <= 0:
        raise ValueError(f"sample_rate must be positive, got {sample_rate}")

    # --- Step 1: MIDI note → fundamental frequency (Hz) ---
    # Standard formula: f = 440 * 2^((n - 69) / 12)
    # MIDI note 69 = A4 = 440 Hz
    fundamental = 440.0 * (2.0 ** ((midi_note - 69) / 12.0))

    # --- Step 2: Scale by harmonic number ---
    frequency = harmonic * fundamental

    # --- Step 3: Frequency → normalized digital angular frequency ---
    # w_c = 2π * f / fs  (radians per sample)
    w_c = 2.0 * math.pi * frequency / sample_rate

    # Guard against Nyquist aliasing
    if w_c >= math.pi:
        raise ValueError(
            f"Harmonic {harmonic} frequency {frequency:.1f} Hz exceeds "
            f"Nyquist ({sample_rate / 2:.0f} Hz). "
            f"Max harmonic for this note: "
            f"{int((sample_rate / 2) / fundamental)}"  # helpful hint
        )

    # --- Step 4: Bandpass group delay at center frequency ---
    # For a 2nd-order bandpass transfer function:
    #   H(s) = (w_c/Q)s / (s^2 + (w_c/Q)s + w_c^2)
    #
    # Group delay τ(ω) = -d(phase)/dω
    # At ω = w_c this simplifies to:
    #   τ(w_c) = Q / w_c
    delay_samples = 2*q / w_c

    return int(delay_samples)