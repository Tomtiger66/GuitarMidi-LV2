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
    };
}