#pragma once
#include <thread>
#include <mutex>
#include <condition_variable>
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
#define RING_BUFFER_SIZE 20 // Number of frames to store in the ring buffer
/*
    * ModelInferencer class for handling model inference tasks. This class contains two ringbuffers for storing the last N frames of the audio input and model output.
        The audio input ringbuffer is used to store the last N frames of the audio input, which are then fed into the model for inference.
         The model output ringbuffer is used to store the last N frames of the model output, which are then used to in noteinferencer.cpp to trigger MIDI messages based on the confidence of the detected notes.
         The inferencing is performed in a separate thread to avoid blocking the audio processing thread, and the results are communicated back to the main thread using the output ringbuffer.
 */
namespace GuitarMidi{
    class RingBuffer{
        int size;
        int stride;
        int write_index;
        int read_index;
        float* buffer;
    public:
        RingBuffer(int size, int stride);
        ~RingBuffer();
        void add_data(const float* data, int num_frames);
        bool has_new_data() const;
        float* get_latest_data();
        void get_latest_data(float* output, int num_frames);

    };
class ModelInferencer {
    private:
        unique_ptr<FlatBufferModel> m_model;
        unique_ptr<Interpreter> m_interpreter;
        RingBuffer audio_input_buffer;
        RingBuffer model_output_buffer;
        std::thread inferencing_thread;
        std::mutex buffer_mutex;
        std::condition_variable buffer_cv;
        bool stop_thread;
        void inferencing_loop();
        
    public:
        ModelInferencer();
        ~ModelInferencer();
        void initialize();
        void add_audio_input(const float* input, int num_frames);
        bool get_model_output(float* output, int num_frames);
};
} // namespace GuitarMidi