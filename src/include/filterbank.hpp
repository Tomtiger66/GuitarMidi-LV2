#pragma once
#include <vector>
#include <filter.hpp>
#include <map>
#include <memory>
#include <common.hpp>
using namespace std;
namespace GuitarMidi{


    class FilterBank{

        private:
            map<int,shared_ptr<Filter>> m_filters;
            AudioBuffer2D m_filterbankbuffer; //number of filters x buffersize
      
            public:
            FilterBank();
            ~FilterBank();

            void setup(map<uint,FilterRepresentation> filterreps,int samplerate);

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
