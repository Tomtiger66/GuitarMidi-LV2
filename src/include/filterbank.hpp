#pragma once
#include <vector>
#include <filter.hpp>
#include <map>
#include <memory>
using namespace std;
namespace GuitarMidi{
    class FilterBank{

        private:
            std::vector<Filter > m_filters;
            public:
            FilterBank(map<uint,FilterRepresentation> filterreps){}
            

            // void process(int nsamples){
            //     for(auto filter:m_filters){
            //         filter->process(nsamples);
            //     }
            // }

    };
}
