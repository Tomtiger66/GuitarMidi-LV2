#pragma once
#include <vector>
#include <fret.hpp>
using namespace std;

namespace GuitarMidi
{

    class FretBoardRepresentation
    {
        vector<Fret> m_frets;

        public:
        FretBoardRepresentation();

        map<uint,FilterRepresentation> get_filterrepresentations(){
            map<uint,FilterRepresentation> res;
            for (auto f: m_frets)
                f.get_filterrepresentations(res);

            return res;
        }
    };
}