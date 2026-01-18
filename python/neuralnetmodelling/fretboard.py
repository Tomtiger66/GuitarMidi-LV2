num_harmonics=4 
num_frets=13
num_strings=6
from scipy import signal 
import numpy as np
from joblib import Parallel, delayed
class Filter:
    def __init__(self, fret,stringid,harmonic,center_freq, q,sample_rate):
        self.id=fret*num_strings*num_harmonics+stringid*num_harmonics+harmonic
        self.sample_rate=sample_rate
        bw=center_freq/q 
        # create the filter
        N = 2
        low = (center_freq-bw/2) 
        high = (center_freq+bw/2) 
        #self.b, self.a = signal.ellip(N,0.5,40,[low, high], btype='band',fs=sampleRate)
        self.b, self.a =signal.butter(N, [low, high], btype='band',fs=sample_rate)
        
    def process(self,input_audio,filterbank_out: np.array):
        filterbank_out[self.id]=np.abs(signal.filtfilt(self.b, self.a, input_audio))


class HarmonicGroup:
    def __init__(self,fret,stringid ,center_freq, bw,sample_rate):
        self.harmonics=[]
        
        for h in range(1,num_harmonics+1):
            self.harmonics.append(Filter(fret,stringid,h-1,center_freq*h,bw,sample_rate))
    
            
    def process(self, input_audio, filterbank_out: np.array):
        def process_harmonic(h):
            h.process(input_audio,filterbank_out)
        Parallel(n_jobs=num_harmonics,backend="threading")(delayed(process_harmonic)(h) for h in self.harmonics)
        
        # for h in self.harmonics:
        #     #filterbank_out.append(h.process(input_audio))
        #     h.process(input_audio,filterbank_out)
            
  
    def get_num_filters(self):
        return len(self.harmonics)
          
            
class Fret:
    def __init__(self,fret,s0,s1,s2,s3,s4,s5, q,sample_rate):
        
        self.strings=[]
        self.strings.append(HarmonicGroup(fret,0,s0,q,sample_rate))
   
        self.strings.append(HarmonicGroup(fret,1,s1,q,sample_rate))

        self.strings.append(HarmonicGroup(fret,2,s2,q,sample_rate))

        self.strings.append(HarmonicGroup(fret,3,s3,q,sample_rate))

        self.strings.append(HarmonicGroup(fret,4,s4,q,sample_rate))

        self.strings.append(HarmonicGroup(fret,5,s5,q,sample_rate))

        
    def process(self, input_audio, filterbank_out: np.array):
        def process_string(h):
            h.process(input_audio,filterbank_out)
        Parallel(n_jobs=6,backend="threading")(delayed(process_string)(h) for h in self.strings)
        # for h in self.strings:
        #     #filterbank_out.append(h.process(input_audio,filterbank_out))
        #     h.process(input_audio,filterbank_out)
      
    def get_num_filters(self):
        res=0
        for h in self.strings:
            res=res+h.get_num_filters()
            
        return res
            
class FretBoard:
    def __init__(self,q,sample_rate):
        self.frets=[]
       
        self.frets.append(Fret(0,82,11,147,196,247,329,q,sample_rate))
        self.frets.append(Fret(1,87,117,156,208,262,349,q,sample_rate))
        self.frets.append(Fret(2,92,123,165,220,277,370,q,sample_rate))
        self.frets.append(Fret(3,98,131,175,233,294,392,q,sample_rate))
        self.frets.append(Fret(4,104,139,185,247,311,415,q,sample_rate))
        self.frets.append(Fret(5,110,147,196,262,329,440,q,sample_rate))
        self.frets.append(Fret(6,117,156,208,277,349,466,q,sample_rate))
        self.frets.append(Fret(7,123,165,220,294,370,494,q,sample_rate))
        self.frets.append(Fret(8,131,175,233,311,392,523,q,sample_rate))
        self.frets.append(Fret(9,139,185,247,329,415,554,q,sample_rate))
        self.frets.append(Fret(10,147,196,262,349,440,587,q,sample_rate))
        self.frets.append(Fret(11,156,208,277,370,466,622,q,sample_rate))
        self.frets.append(Fret(12,165,220,294,392,494,659,q,sample_rate))
   #Parallel(n_jobs=5)(delayed(prepare_audio_midi_data)(f) for f in all_jams_files)      
    def process(self, input_audio, filterbank_out: np.array):
      
        def process_fret(h):
            h.process(input_audio,filterbank_out)
        Parallel(n_jobs=12,backend="threading")(delayed(process_fret)(h) for h in self.frets)
        # for h in self.frets:
        #     # filterbank_out.append(h.process(input_audio,filterbank_out))    
        #     res=h.process(input_audio,filterbank_out)
       
    def get_num_filters(self):
        res=0
        for h in self.frets:
            res=res+h.get_num_filters()
            
        return res