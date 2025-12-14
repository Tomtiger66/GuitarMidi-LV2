#pragma once
#include <vector>
#include <filter.hpp>
#include <map>
#include <memory>
using namespace std;
namespace GuitarMidi{

    struct AudioBuffer2D{
        int num_filters;
        int window_size;
        float* audio_buffer_2D;
    };
    class FilterBank{

        private:
            map<int,shared_ptr<Filter>> m_filters;
            AudioBuffer2D m_filterbankbuffer; //number of filters x buffersize
      
            public:
            FilterBank(map<uint,FilterRepresentation> filterreps,int samplerate);
            ~FilterBank();

            void setInput(const float *input)
            {
                for(auto f:m_filters){
                    f.second->setInput(input);
                }
                
            }

            void process(int nsamples){
                for(auto f:m_filters){
                    f.second->process(nsamples);
                }
            }

            AudioBuffer2D get_buffer(){
                return m_filterbankbuffer;
            }



    };
}
