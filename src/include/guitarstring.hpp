#pragma once

#include <guitarnote.hpp>
using namespace std;

namespace GuitarMidi
{
    class GuitarString
    {
        vector<GuitarNote> m_notes;

    public:
        GuitarString(map<int,int> note_freqs);
        void get_filterrepresentations(map<uint,FilterRepresentation>& filterreps)
        {
        
            for (auto note : m_notes)
            {
                 note.get_filterrepresentations(filterreps);
                
            }
            return;
        }
    };
}
