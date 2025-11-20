#include <fret.hpp>

namespace GuitarMidi
{
    Fret::Fret(int fret, float fund_s0, float fund_s1, float fund_s2, float fund_s3, float fund_s4, float fund_s5, float samplerate, float bandwidth, float passbandatten)
    {
        m_strings.push_back(HarmonicGroup(fret, 0, samplerate, fund_s0, bandwidth, passbandatten));
        m_strings.push_back(HarmonicGroup(fret, 1, samplerate, fund_s1, bandwidth, passbandatten));
        m_strings.push_back(HarmonicGroup(fret, 2, samplerate, fund_s2, bandwidth, passbandatten));
        m_strings.push_back(HarmonicGroup(fret, 3, samplerate, fund_s3, bandwidth, passbandatten));
        m_strings.push_back(HarmonicGroup(fret, 4, samplerate, fund_s4, bandwidth, passbandatten));
        m_strings.push_back(HarmonicGroup(fret, 5, samplerate, fund_s5, bandwidth, passbandatten));
    }
}