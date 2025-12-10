#pragma once
#include <iostream>
#include <vector>
#include <map>
#include <memory>
using namespace std;
#define NUM_HARMONICS 4
#define NUM_STRINGS 6
namespace GuitarMidi
{
    struct FilterRepresentation{
        int filter_id;
        float center_freq;

    };

    //The harmonic group represents the fundamental note frequency and its overtones
    class HarmonicGroup
    {
    private:
        vector<FilterRepresentation> m_filters;


    public:
   
        HarmonicGroup(int fret,int string_id, float centerfreq);
        ~HarmonicGroup();

        void get_filterrepresentations(map<uint,FilterRepresentation>& filterreps){
            for (auto f:m_filters){
                filterreps[f.filter_id]=f;
            }
        }
    };
}
