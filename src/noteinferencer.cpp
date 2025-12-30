#include <noteinferencer.hpp>
#include <iostream>
namespace GuitarMidi
{

    // TFlite C++ API reference: https://ai.google.dev/edge/api/tflite/cc?hl=en
#define TFLITE_MINIMAL_CHECK(x)                                  \
    if (!(x))                                                    \
    {                                                            \
        fprintf(stderr, "Error at %s:%d\n", __FILE__, __LINE__); \
        exit(1);                                                 \
    }

    NoteInferencer::NoteInferencer()
    {
    }
    void NoteInferencer::initialize()
    {
        // Load model
        m_model = FlatBufferModel::BuildFromFile("/home/gerald/workspace/src/GuitarMidi-LV2/python/neuralnetmodelling/guitarmidi.tflite");
        TFLITE_MINIMAL_CHECK(m_model != nullptr);
        ops::builtin::BuiltinOpResolver resolver;
        InterpreterBuilder builder(*m_model, resolver);

        builder(&m_interpreter);
        TfLiteXNNPackDelegateOptions xnnpack_options =
            TfLiteXNNPackDelegateOptionsDefault();
        xnnpack_options.num_threads = 8; // Set number of threads as appropriate for your
                                         // platform and application needs.
        xnnpack_options.weight_cache_file_path = TfLiteXNNPackDelegateInMemoryFilePath();

        if (m_interpreter->ModifyGraphWithDelegate(
                TfLiteXNNPackDelegateCreate(&xnnpack_options)) != kTfLiteOk)
        {
            // Handle error, but usually optional
            fprintf(stderr, "Warning: Failed to apply XNNPACK delegate.\n");
        }
        // Allocate tensor buffers.
        TFLITE_MINIMAL_CHECK(m_interpreter->AllocateTensors() == kTfLiteOk);
        printf("=== Pre-invoke Interpreter State ===\n");
        tflite::PrintInterpreterState(m_interpreter.get());
    }
    void NoteInferencer::setMidiOutput(shared_ptr<MidiOutput> output)
    {
        m_midioutput = output;
    }
    void NoteInferencer::setAudioInputBuffer(AudioBuffer2D input)
    {
        m_audiobuffer = input;
    }
    void NoteInferencer::process(int nsamples)
    {
        cout<<"Input tensor dims:";
        TfLiteTensor *input = m_interpreter->input_tensor(0);
        TfLiteIntArray* dims = input->dims;
        cout<<"Input tensor dims:";
        for(int i=0;i<dims->size;i++){
            cout<<" "<<dims->data[i];
        }
        TFLITE_MINIMAL_CHECK(m_interpreter->Invoke() == kTfLiteOk);
    }
}
