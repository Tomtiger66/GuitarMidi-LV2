#include <noteinferencer.hpp>
namespace GuitarMidi{
    NoteInferencer::NoteInferencer()
    {
    }
    void NoteInferencer::initialize()
    {
    }
    void NoteInferencer::setMidiOutput(shared_ptr<MidiOutput> output)
    {
        m_midioutput=output;
    }
    void NoteInferencer::setAudioInputBuffer(AudioBuffer2D input)
    {
        m_audiobuffer=input;
    }
    void NoteInferencer::process(int nsamples)
    {
    }
}
