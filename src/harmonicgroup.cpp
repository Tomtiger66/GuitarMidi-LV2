#include <harmonicgroup.hpp>

HarmonicGroup::HarmonicGroup( float samplerate, float fund, float bandwidth, float passbandatten)
{
    //Add the fundamental
    m_noteClassifiers.push_back(Filter(samplerate,fund,bandwidth,passbandatten));
    m_fundamentalfreq=fund;
    //Add the overtones
    for(int n=1;n<NUM_HARMONICS;n++)
    {
        m_noteClassifiers.push_back(Filter(samplerate,fund*(n+1),bandwidth,passbandatten));
    }

}

HarmonicGroup::~HarmonicGroup()
{

}




