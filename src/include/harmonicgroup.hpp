#pragma once
#include <noteclassifier.hpp>
#include <iostream>
using namespace std;
#define NUM_HARMONICS 4 //f
class HarmonicGroup
{
    private:
    vector<NoteClassifier > m_noteClassifiers;
    double m_fundamentalfreq;
    public:

 
    HarmonicGroup(LV2_URID_Map *map, float samplerate, float center = 110.0, float bandwidth = 20, float passbandatten = 2);
    ~HarmonicGroup();

    void setAudioInput(const float *input){
        for (int n=0;n<m_noteClassifiers.size();n++)
        {
            m_noteClassifiers[n].input=input;
        }

    }

    void setOutput(int harmonic,float * buffer){
        
    }






};
