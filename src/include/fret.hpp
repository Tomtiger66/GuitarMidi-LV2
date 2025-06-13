#pragma once

#include <harmonicgroup.hpp>
using namespace std;

class Fret{
    vector<HarmonicGroup> m_strings;

    public: 
    Fret(float fund_s0,float fund_s1,float fund_s2,float fund_s3,float fund_s4,float fund_s5,  float samplerate, float bandwidth = 20, float passbandatten = 2);

    void setAudioInput(const float *input){
        for (int n=0;n<m_strings.size();n++)
        {
            m_strings[n].setAudioInput(input);
        }
    }

    void setOutput(int stringid,int harmonic,float* output){
        if(stringid<m_strings.size()){
            m_strings[stringid].setOutput(harmonic,output);
        }
    

    }
};