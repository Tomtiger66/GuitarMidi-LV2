#pragma once
#include <filter.hpp>
#include <iostream>
using namespace std;
#define NUM_HARMONICS 4 //fundamental+Overtones
class HarmonicGroup
{
    private:
    vector<Filter > m_noteClassifiers;
    double m_fundamentalfreq;
    public:

 
    HarmonicGroup( float samplerate, float center = 110.0, float bandwidth = 20, float passbandatten = 2);
    ~HarmonicGroup();

    void setAudioInput(const float *input){
        for (int n=0;n<m_noteClassifiers.size();n++)
        {
            m_noteClassifiers[n].setInput(input);
        }

    }

    void setOutput(int harmonic, float * buffer){
        if(m_noteClassifiers.size()>harmonic){
            m_noteClassifiers[harmonic].setOutput(buffer);
        }
        
    }






};
