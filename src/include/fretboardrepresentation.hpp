#pragma once
#include <vector>
#include <guitarstring.hpp>
using namespace std;

namespace GuitarMidi
{

    class FretBoardRepresentation
    {
        vector<GuitarString> m_strings;

        public:
        FretBoardRepresentation();

        map<uint,FilterRepresentation> get_filterrepresentations(){
            map<uint,FilterRepresentation> res;
            for (auto f: m_strings)
                f.get_filterrepresentations(res);

            return res;
        }
    };
}