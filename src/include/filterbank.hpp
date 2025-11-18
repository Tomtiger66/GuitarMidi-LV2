#pragma once
#include <vector>
#include <filter.hpp>
#include <memory>
using namespace std;
namespace GuitarMidi{
    class FilterBank{

        private:
            std::vector<std::shared_ptr<Filter> > m_filters;
            public:
            FilterBank(){}
            void addFilter(shared_ptr<Filter> filter){
                m_filters.push_back(filter);
            }

            void process(int nsamples){
                for(auto filter:m_filters){
                    filter->process(nsamples);
                }
            }

    };
}
