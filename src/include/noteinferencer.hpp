#pragma once
#include <memory>
#include <midioutput.hpp>
#include <common.hpp>
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
using namespace tflite;
namespace GuitarMidi{
    class NoteInferencer{
        unique_ptr<FlatBufferModel> m_model;
        unique_ptr<Interpreter> m_interpreter;
        GuitarMidi::MidiOutput m_midioutput;
        AudioBuffer2D m_audiobuffer;
        float* m_onset_threshold;
        float* m_offset_threshold;
        float* m_smoothing;
        float smoothed_output[OUTPUT_DIM]={0};
        // std::unique_ptr<tflite::FlatBufferModel> model;
        int64_t m_frames;
        bool m_note_on[OUTPUT_DIM]={false};
        public:
        NoteInferencer(LV2_URID_Map *map);

        void initialize();
        void setMidiOutput(LV2_Atom_Sequence *output);

        void setAudioInputBuffer(AudioBuffer2D input);

        void setOnsetThreshold(float* threshold){
            m_onset_threshold=threshold;
        }

        void setOffsetThreshold(float* threshold){
            m_offset_threshold=threshold;
        }

        void setSmoothing(float* smoothing){
            m_smoothing=smoothing;
        }

        void process(int nsamples);

    };
}