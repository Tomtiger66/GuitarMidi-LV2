#pragma once
#include <memory>
#include <midioutput.hpp>
#include <common.hpp>
#define TF_MAJOR_VERSION 2
#define TF_MINOR_VERSION 20
#define TF_PATCH_VERSION 0
#define TF_VERSION_SUFFIX ""
#include <tensorflow/lite/version.h>
#include "tensorflow/core/public/release_version.h"
#include "tensorflow/core/public/version.h"
#include "tensorflow/lite/version.h"
#include "tensorflow/lite/core/interpreter_builder.h"
#include "tensorflow/lite/interpreter.h"
#include "tensorflow/lite/kernels/register.h"
#include "tensorflow/lite/model_builder.h"
#include "tensorflow/lite/optional_debug_tools.h"
#include "tensorflow/lite/delegates/xnnpack/xnnpack_delegate.h"
using namespace std;
namespace GuitarMidi{
    class NoteInferencer{
        shared_ptr<GuitarMidi::MidiOutput> m_midioutput;
        AudioBuffer2D m_audiobuffer;
        std::unique_ptr<tflite::FlatBufferModel> model;
        public:
        NoteInferencer();

        void initialize();
        void setMidiOutput(shared_ptr<MidiOutput> output);

        void setAudioInputBuffer(AudioBuffer2D input);

        void process(int nsamples);

    };
}