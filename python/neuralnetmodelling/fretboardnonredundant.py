num_harmonics=16 
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
        
    def process(self,input_audio,filterbank_out: np.array):
        filterbank_out[self.id]=np.abs(signal.lfilter(self.b, self.a, input_audio))


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
       
    def get_num_filters(self):
        res=0
        for h in self.strings:
            res=res+h.get_num_filters()
            
        return res
    # def get_harmonic_group(self,fret,string):
    #     return self.frets[fret].strings[string]
    

