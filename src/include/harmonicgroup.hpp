#pragma once
#include <filter.hpp>
#include <iostream>
#include <vector>
#include <memory>
using namespace std;
#define NUM_HARMONICS 4
namespace GuitarMidi
{
    class HarmonicGroup
    {
    private:
        vector<shared_ptr<Filter>> m_filters;
        bool m_oldState;
        float *m_buffer;
        int m_bufferSize;

    public:
        float *audioBuffer;
        HarmonicGroup(float samplerate, float centerfreq, float bandwidth = 20, float passbandatten = 2);
        ~HarmonicGroup();
    };
}
