#include <harmonicgroup.hpp>

HarmonicGroup::HarmonicGroup(LV2_URID_Map *map, float samplerate, float center, float bandwidth, float passbandatten)
{
    //Add the fundamental
    m_noteClassifiers.push_back(NoteClassifier(map,samplerate,center,bandwidth,passbandatten));

    //Add the overtones
    for(int n=1;n<=NUMOVERTONES;n++)
    {
        m_noteClassifiers.push_back(NoteClassifier(map,samplerate,center*(n+1),bandwidth,passbandatten));
    }

}

HarmonicGroup::~HarmonicGroup()
{

}




