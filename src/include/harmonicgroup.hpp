#pragma once
#include <filter.hpp>
#include <iostream>
#include <vector>
#include <memory>
using namespace std;

namespace GuitarMidi
{
    struct FilterRepresentation{
        int filter_id;
        float center_freq;

    };
    class HarmonicGroup
    {
    private:
        vector<FilterRepresentation> m_filters;


    public:
   
        HarmonicGroup(int fret,int string_id, float centerfreq);
        ~HarmonicGroup();
    };
}
