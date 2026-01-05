#pragma once
#include <DspFilters/Dsp.h>
#include <config.hpp>
#include <harmonicgroup.hpp>
#define MAXORDER 10   // the real order is 2*MAXORDER
#define FILTERORDER 2 // the real order is 2*MAXORDER
#define NUM_HARMONICS 4
#define NUM_STRINGS 6
#define NUM_FRETS 12
#define BUFFER_SIZE 256
namespace GuitarMidi
{

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

        void setFilterParameters(float q = 17.5, float passbandatten = 2, int order = FILTERORDER);

    public:
        Filter(FilterRepresentation filter_rep, float samplerate,  float q = 17.5, float passbandatten = 2);
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