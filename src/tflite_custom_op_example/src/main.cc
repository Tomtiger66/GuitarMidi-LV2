#include <iostream>
#include <vector>
#include <memory>

#include "tensorflow/lite/interpreter.h"
#include "tensorflow/lite/kernels/register.h"
#include "tensorflow/lite/model.h"
#include "tensorflow/lite/optional_debug_tools.h"

#include "../custom_op/PartitionedAvgPool.h"

// Define the path to your TFLite model file
#define TFLITE_MODEL_PATH "cnn_partitioned.tflite"

void RunInference(const std::string& model_path) {
    // 1. Load the model
    std::unique_ptr<tflite::FlatBufferModel> model =
        tflite::FlatBufferModel::BuildFromFile(model_path.c_str());
    if (!model) {
        std::cerr << "Failed to load model: " << model_path << std::endl;
        return;
    }

    // 2. Build the interpreter resolver and register the custom op
    tflite::ops::builtin::BuiltinOpResolver resolver;
    // CRUCIAL STEP: Add the custom op to the resolver
    resolver.AddCustom(kPartitionedAveragePoolingName, Register_Partitioned_Average_Pooling());

    // 3. Build the interpreter
    std::unique_ptr<tflite::Interpreter> interpreter;
    tflite::InterpreterBuilder(*model, resolver)(&interpreter);

    if (!interpreter) {
        std::cerr << "Failed to build interpreter." << std::endl;
        return;
    }

    // Allocate tensors
    if (interpreter->AllocateTensors() != kTfLiteOk) {
        std::cerr << "Failed to allocate tensors." << std::endl;
        return;
    }

    // 4. Set up input tensor (Assuming a batch size of 1)
    int input_tensor_idx = interpreter->inputs()[0];
    TfLiteTensor* input_tensor = interpreter->tensor(input_tensor_idx);
    
    // Check input dimensions (e.g., [1, 39, W, C])
    if (input_tensor->dims->size != 4) {
        std::cerr << "Input tensor dimension mismatch." << std::endl;
        return;
    }

    // Fill the input tensor with dummy data (e.g., all 1.0)
    int input_size = 1;
    for (int i = 0; i < input_tensor->dims->size; ++i) {
        input_size *= input_tensor->dims->data[i];
    }
    std::fill(interpreter->typed_input_tensor<float>(0), 
              interpreter->typed_input_tensor<float>(0) + input_size, 
              1.0f);

    std::cout << "Successfully initialized model and input data." << std::endl;

    // 5. Run inference
    if (interpreter->Invoke() != kTfLiteOk) {
        std::cerr << "Failed to invoke interpreter." << std::endl;
        return;
    }

    // 6. Get output tensor
    int output_tensor_idx = interpreter->outputs()[0];
    const TfLiteTensor* output_tensor = interpreter->tensor(output_tensor_idx);
    const float* output_data = interpreter->typed_output_tensor<float>(0);

    // Display output (assuming a small output_dim for demonstration)
    int output_dim = output_tensor->dims->data[1];
    std::cout << "Inference successful. Output vector (first 5 elements):" << std::endl;
    for (int i = 0; i < std::min(5, output_dim); ++i) {
        std::cout << "Output[" << i << "]: " << output_data[i] << std::endl;
    }
}

int main(int argc, char* argv[]) {
    // Note: You must first generate the cnn_partitioned.tflite file using the Python script.
    std::cout << "Starting TFLite inference with custom PartitionedAveragePooling Op." << std::endl;
    RunInference(TFLITE_MODEL_PATH);
    return 0;
}