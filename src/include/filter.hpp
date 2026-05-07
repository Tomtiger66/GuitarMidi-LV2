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
#include <DspFilters/Dsp.h>
#include <config.hpp>
#include <guitarnote.hpp>
#include <common.hpp>
#define MAXORDER 10   // the real order is 2*MAXORDER
#define FILTERORDER 4 // the real order is 2*MAXORDER
#define NUM_HARMONICS 4
#define NUM_STRINGS 6
#define NUM_FRETS 12

#define Q_FACTOR 6
namespace GuitarMidi
{

    /**
 * @brief The Filter class represents a digital filter that can be applied to audio data. It encapsulates the parameters and functionality needed to process audio samples using a bandpass filter. 
 * The class is designed  allowing for the creation of either Butterworth or Elliptic bandpass filters based on the defined preprocessor directive. 
 * The Filter class manages the filter's parameters, such as bandwidth and attenuation, and provides methods for initializing the filter and processing audio samples.
 */
    class Filter
    {
    private:
        GuitarMidi::FilterRepresentation m_filter_rep;

        /**
         * @brief m_bandwidth: The bandwidth frequency of the bandpass filters
         *
         */
        float m_q;

        /**
         * @brief m_passbandatten: The attenuation in db of amplitude of the ripple in the pass and stopband of the elliptic filters
         *
         */
        float m_passbandatten;
        int m_order;

        /**
         * @brief m_samplerate: The samplerate of the audio
         *
         */
        float m_samplerate;

        /**
         * @brief m_bufferSize: audio buffersize set by the host
         *
         */
        int m_bufferSize;
        /**
         * @brief pointer to output audio buffer
         *
         */
        float *m_buffer;

        float *m_output;

        /**
         * @brief pointer to input audio buffer
         *
         */
        const float *m_input;
#ifndef USE_ELLIPTIC_FILTERS
        Dsp::SimpleFilter<Dsp::Butterworth::BandPass<MAXORDER>, 1> m_filter;
#else
        Dsp::SimpleFilter<Dsp::Elliptic::BandPass<MAXORDER>, 1> m_filter;
#endif

        void setFilterParameters(float q = Q_FACTOR, float passbandatten = 2, int order = FILTERORDER);

    public:
        Filter(FilterRepresentation filter_rep, float samplerate,  float q = Q_FACTOR, float passbandatten = 2);
        ~Filter();
        void initialize();

        FilterRepresentation get_filter_id()
        {
            return m_filter_rep;//TODO replace with filter rep
        }

        void setOutput(float *output)
        {
            m_output = output;
        }

        void process(int nsamples);

        void setInput(const float *input)
        {
            m_input = input;
        }
    };
}