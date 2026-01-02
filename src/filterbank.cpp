#include <filterbank.hpp>

GuitarMidi::FilterBank::FilterBank()
{


}

GuitarMidi::FilterBank::~FilterBank()
{
    delete [] m_filterbankbuffer.audio_buffer_2D;
}

void GuitarMidi::FilterBank::setup(map<uint, FilterRepresentation> filterreps, int samplerate)
{
    lv2_log_note(&g_logger,"Setting up filterbank\n");
    if (filterreps.size()==0)
        throw std::runtime_error("No filter representations");
    

    m_filterbankbuffer.num_filters=filterreps.size();
    m_filterbankbuffer.window_size=BUFFER_SIZE;
    
    lv2_log_note(&g_logger,"Setting up filterbank with %d filters and windowsize %d\n",m_filterbankbuffer.num_filters,m_filterbankbuffer.window_size);

    m_filterbankbuffer.audio_buffer_2D=new float[m_filterbankbuffer.num_filters*m_filterbankbuffer.window_size];
    for(auto f:filterreps){
        shared_ptr<Filter>  filter=make_shared<Filter>(f.second,samplerate);

        filter->setOutput((m_filterbankbuffer.audio_buffer_2D+f.first*m_filterbankbuffer.window_size));
        m_filters.insert(make_pair(f.first,filter));

    }
}
