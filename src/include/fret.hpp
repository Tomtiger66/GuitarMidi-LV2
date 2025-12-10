#pragma once

#include <harmonicgroup.hpp>
using namespace std;

namespace GuitarMidi
{
    class Fret
    {
        vector<HarmonicGroup> m_strings;

    public:
        Fret(int fret, float fund_s0, float fund_s1, float fund_s2, float fund_s3, float fund_s4, float fund_s5);
        void get_filterrepresentations(map<uint,FilterRepresentation>& filterreps)
        {
        
            for (auto s : m_strings)
            {
                 s.get_filterrepresentations(filterreps);
                
            }
            return;
        }
    };
}
