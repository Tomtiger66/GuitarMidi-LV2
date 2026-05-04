#include <modelinferencer.hpp>
#include <iostream>
#include <tensorflow/lite/logger.h>
    // TFlite C++ API reference: https://ai.google.dev/edge/api/tflite/cc?hl=en
#define TFLITE_MINIMAL_CHECK(x)                                  \
    if (!(x))                                                    \
    {                                                            \
        fprintf(stderr, "Error at %s:%d\n", __FILE__, __LINE__); \
        exit(1);                                                 \
    }
void GuitarMidi::ModelInferencer::inferencing_loop()
{
    while (!stop_thread) {
        std::unique_lock<std::mutex> lock(buffer_mutex);
        buffer_cv.wait(lock, [this] { return stop_thread || audio_input_buffer.has_new_data(); });
        if (stop_thread) break;

        // Get the latest audio input data from the ring buffer
        float* audio_input_data = audio_input_buffer.get_latest_data();
      

    if (audio_input_data) {
            float* input_buffer=m_interpreter->typed_input_tensor<float>(0);
            memcpy(input_buffer,audio_input_data,NUM_NOTES*NUM_HARMONICS*BUFFER_SIZE*sizeof(float));
            TFLITE_MINIMAL_CHECK(m_interpreter->Invoke() == kTfLiteOk);

            TfLiteTensor *output = m_interpreter->output_tensor(0);
            float* output_data=m_interpreter->typed_output_tensor<float>(0);
            // print the output dims
            TfLiteIntArray* output_dims = output->dims;
    
                // Add the model output to the model output ring buffer
                model_output_buffer.add_data(output_data, 1); // Assuming 1 frame of output
            }


    }
}

void GuitarMidi::ModelInferencer::initialize()
{
            // Load model
        m_model = FlatBufferModel::BuildFromFile("/home/gerald/workspace/src/GuitarMidi-LV2/python/neuralnetmodelling/guitarmidi.tflite");
        TFLITE_MINIMAL_CHECK(m_model != nullptr);
        ops::builtin::BuiltinOpResolver resolver;
        InterpreterBuilder builder(*m_model, resolver);

        builder(&m_interpreter);
        TfLiteXNNPackDelegateOptions xnnpack_options =
            TfLiteXNNPackDelegateOptionsDefault();
        xnnpack_options.num_threads = 4; // Set number of threads as appropriate for your
                                         // platform and application needs.
        xnnpack_options.weight_cache_file_path = TfLiteXNNPackDelegateInMemoryFilePath();
        // xnnpack_options.logging_level = TFLITE_XNNPACK_LOGGING_LEVEL_ERROR;

        if (m_interpreter->ModifyGraphWithDelegate(
                TfLiteXNNPackDelegateCreate(&xnnpack_options)) != kTfLiteOk)
        {
            // Handle error, but usually optional
            fprintf(stderr, "Warning: Failed to apply XNNPACK delegate.\n");
        }
        // Allocate tensor buffers.
        TFLITE_MINIMAL_CHECK(m_interpreter->AllocateTensors() == kTfLiteOk);
        printf("=== Pre-invoke Interpreter State ===\n");
        // tflite::PrintInterpreterState(m_interpreter.get());
        tflite::LoggerOptions::SetMinimumLogSeverity(tflite::TFLITE_LOG_ERROR);
}

GuitarMidi::ModelInferencer::ModelInferencer():audio_input_buffer(RING_BUFFER_SIZE, NUM_NOTES*NUM_HARMONICS*BUFFER_SIZE), model_output_buffer(RING_BUFFER_SIZE, NUM_NOTES)
{

    stop_thread = false;
    inferencing_thread = std::thread(&ModelInferencer::inferencing_loop, this);
}

GuitarMidi::ModelInferencer::~ModelInferencer()
{
    {
        std::lock_guard<std::mutex> lock(buffer_mutex);
        stop_thread = true;
    }
    buffer_cv.notify_all();
    if (inferencing_thread.joinable()) {
        inferencing_thread.join();
    }
}

void GuitarMidi::ModelInferencer::add_audio_input(const float *input, int num_frames)
{
    std::lock_guard<std::mutex> lock(buffer_mutex);
    audio_input_buffer.add_data(input, num_frames);
    buffer_cv.notify_all();
}

bool GuitarMidi::ModelInferencer::get_model_output(float *output, int num_frames)
{
    std::lock_guard<std::mutex> lock(buffer_mutex);
    if (model_output_buffer.has_new_data()) {
        model_output_buffer.get_latest_data(output, num_frames);
        return true;
    }
    return false;
}

GuitarMidi::RingBuffer::RingBuffer(int size, int stride)
{
    this->size = size;
    this->stride = stride;
    this->write_index = 0;
    this->read_index = 0;
    buffer = new float[size * stride];
}

GuitarMidi::RingBuffer::~RingBuffer()
{
    delete[] buffer;
}

void GuitarMidi::RingBuffer::add_data(const float *data, int num_frames)
{
    int frames_to_write = std::min(num_frames, size);
    for (int i = 0; i < frames_to_write; ++i) {
        std::copy(data + i * stride, data + (i + 1) * stride, buffer + write_index * stride);
        write_index = (write_index + 1) % size;
        if (write_index == read_index) {
            read_index = (read_index + 1) % size; // Overwrite oldest data
        }
    }
}

bool GuitarMidi::RingBuffer::has_new_data() const
{
    return write_index != read_index;
}

float *GuitarMidi::RingBuffer::get_latest_data()
{
    if (!has_new_data()) {
        return nullptr; // No new data available
    }
     // Return the latest data from the read index and move the read index forward
    float* latest_data = buffer + read_index * stride;
    read_index = (read_index + 1) % size;
    return latest_data;
}

void GuitarMidi::RingBuffer::get_latest_data(float *output, int num_frames)
{
    if (!has_new_data()) {
        return; // No new data available
    }
    int frames_to_read = std::min(num_frames, size);
    for (int i = 0; i < frames_to_read; ++i) {
        std::copy(buffer + read_index * stride, buffer + (read_index + 1) * stride, output + i * stride);
        read_index = (read_index + 1) % size;
        if (read_index == write_index) {
            break; // No more new data available
        }
    }
}
