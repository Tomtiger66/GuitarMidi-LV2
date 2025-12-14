#pragma once
#include <memory>
#include <midioutput.hpp>
#include <common.hpp>
using namespace std;
namespace GuitarMidi{
    class NoteInferencer{
        shared_ptr<GuitarMidi::MidiOutput> m_midioutput;
        AudioBuffer2D m_audiobuffer;
        public:
        NoteInferencer();

        void initialize();
        void setMidiOutput(shared_ptr<MidiOutput> output);

        void setAudioInputBuffer(AudioBuffer2D input);

        void process(int nsamples);

    };
}