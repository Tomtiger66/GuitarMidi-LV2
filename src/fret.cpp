#include <fret.hpp>

namespace GuitarMidi
{
    Fret::Fret(int fret, float fund_s0, float fund_s1, float fund_s2, float fund_s3, float fund_s4, float fund_s5)
    {
        m_strings.push_back(HarmonicGroup(fret, 0, fund_s0));
        m_strings.push_back(HarmonicGroup(fret, 1,  fund_s1));
        m_strings.push_back(HarmonicGroup(fret, 2,  fund_s2));
        m_strings.push_back(HarmonicGroup(fret, 3,  fund_s3));
        m_strings.push_back(HarmonicGroup(fret, 4,  fund_s4));
        m_strings.push_back(HarmonicGroup(fret, 5,  fund_s5));
    }
}