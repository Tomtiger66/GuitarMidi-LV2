#include <fret.hpp>



Fret::Fret(float fund_s0, float fund_s1, float fund_s2, float fund_s3, float fund_s4, float fund_s5,  float samplerate, float bandwidth, float passbandatten)
{
    m_strings.push_back(HarmonicGroup(samplerate,fund_s0,bandwidth,passbandatten));
    m_strings.push_back(HarmonicGroup(samplerate,fund_s1,bandwidth,passbandatten));
    m_strings.push_back(HarmonicGroup(samplerate,fund_s2,bandwidth,passbandatten));
    m_strings.push_back(HarmonicGroup(samplerate,fund_s3,bandwidth,passbandatten));
    m_strings.push_back(HarmonicGroup(samplerate,fund_s4,bandwidth,passbandatten));
    m_strings.push_back(HarmonicGroup(samplerate,fund_s5,bandwidth,passbandatten));
}
