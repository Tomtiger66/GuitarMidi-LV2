#pragma once
/* GuitarMidi-LV2 Library
 * Copyright (C) 2022 Gerald Mwangi
 *
 * This program is free software; you can redistribute it and/or
 * modify it under the terms of the GNU Lesser General Public
 * License as published by the Free Software Foundation; either
 * version 2 of the License, or (at your option) any later version.
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
 * Lesser General Public License for more details.
 *
 * You should have received a copy of the GNU Lesser General
 * Public License along with this program; if not, write to the
 * Free Software Foundation, Inc., 51 Franklin Street, Fifth Floor,
 * Boston, MA  02110-1301  USA
 */
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
