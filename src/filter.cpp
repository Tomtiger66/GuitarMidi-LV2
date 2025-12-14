#include <filter.hpp>
namespace GuitarMidi
{
    Filter::Filter(FilterRepresentation filter_rep, float samplerate, float bandwidth, float passbandatten)
    {
        m_filter_rep=filter_rep;
        m_passbandatten = passbandatten;
        m_bandwidth = bandwidth;
        m_samplerate = samplerate;

        m_bufferSize = BUFFER_SIZE;
        m_buffer = nullptr;
        m_output = nullptr;
        initialize();
    }

    void Filter::setFilterParameters(float bandwidth, float passbandatten, int order)
    {
        m_bandwidth = bandwidth;
        m_passbandatten = passbandatten;
        m_order = order;

        m_filter.reset();

#ifdef USE_ELLIPTIC_FILTERS
        m_filter.setup(m_order, m_samplerate, m_filter_rep.center_freq, m_bandwidth, m_passbandatten, 18.0);
#else
        m_filter.setup(m_order, m_samplerate, m_centerfreq, m_bandwidth);
#endif
    }

    Filter::~Filter()
    {
        m_filter.reset();
        if (m_buffer)
            delete[] m_buffer;
    }

    void Filter::initialize()
    {
        // Setup FILTERORDER 1st order filters. Currently Elliptic::BandPass crashes when running setup() with orders higher than 1
        // When we solve this we can run sharper filters with narrower bandwidth and maybe drop the pitch validation below in process()
        setFilterParameters(m_bandwidth, m_passbandatten);

        if (m_bufferSize)
            m_buffer = new float[m_bufferSize];
    }

    void Filter::process(int nsamples)
    {
        memcpy(m_buffer, m_input, nsamples * sizeof(float));

        m_filter.process(nsamples, &m_buffer);
        for (int b=0;b<m_bufferSize;b++)
            m_buffer[b]=fabs(m_buffer[b]);

        if (m_output != nullptr)
        {
            memcpy(m_output, m_buffer, nsamples * sizeof(float));
        }
    }
}