#include <harmonicgroup.hpp>
#include <memory>
namespace GuitarMidi
{
    HarmonicGroup::HarmonicGroup(float samplerate, float centerfreq, float bandwidth, float passbandatten)
    {
        for (int i=1;i<=NUM_HARMONICS;i++){
            float f_mult=centerfreq*i;
            auto filter=std::make_shared<Filter>(samplerate,f_mult, bandwidth,passbandatten);
        }
    }
}
