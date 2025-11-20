#pragma once

#include <harmonicgroup.hpp>
using namespace std;

namespace GuitarMidi{
    class Fret{
        vector<HarmonicGroup> m_strings;

        public:
        Fret(int fret,float fund_s0,float fund_s1,float fund_s2,float fund_s3,float fund_s4,float fund_s5,  float samplerate, float bandwidth = 20, float passbandatten = 2);


    };
}

