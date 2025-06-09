#include <harmonicgroup.hpp>

HarmonicGroup::HarmonicGroup(LV2_URID_Map *map, float samplerate, float fund, float bandwidth, float passbandatten)
{
    //Add the fundamental
    m_noteClassifiers.push_back(NoteClassifier(map,samplerate,fund,bandwidth,passbandatten));
    m_fundamentalfreq=fund;
    //Add the overtones
    for(int n=1;n<=NUMOVERTONES;n++)
    {
        m_noteClassifiers.push_back(NoteClassifier(map,samplerate,fund*(n+1),bandwidth,passbandatten));
    }

}

HarmonicGroup::~HarmonicGroup()
{

}




