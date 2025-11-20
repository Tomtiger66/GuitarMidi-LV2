#pragma once
#include <DspFilters/Dsp.h>
#include <config.hpp>
#define MAXORDER 10   // the real order is 2*MAXORDER
#define FILTERORDER 2 // the real order is 2*MAXORDER
#define NUM_HARMONICS 4
#define NUM_STRINGS 6
#define NUM_FRETS 12

namespace GuitarMidi
{
    class Filter
    {
    private:
        int m_filter_id;
        /**
         * @brief m_centerfreq: The center frequency of the bandpass filters
         *
         */
        float m_centerfreq;

        /**
         * @brief m_bandwidth: The bandwidth frequency of the bandpass filters
         *
         */
        float m_bandwidth;

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

        void setFilterParameters(float bandwidth = 20, float passbandatten = 2, int order = FILTERORDER);

    public:
        Filter(int fret, int string, int harmonic, float samplerate, float center = 110.0, float bandwidth = 20, float passbandatten = 2);
        ~Filter();
        void initialize();

        int get_filter_id()
        {
            return m_filter_id;
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