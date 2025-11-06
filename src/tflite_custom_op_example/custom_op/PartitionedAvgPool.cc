#include <PartitionedAvgPool.h>
#include <tensorflow/lite/kernels/kernel_util.h>
#include <tensorflow/lite/kernels/register.h>
#include <tensorflow/lite/c/common.h>
#include <vector>
#include <iostream>

// The sizes for the height splits (7, 7, 7, 6, 6, 6)
const std::vector<int> split_sizes = {7, 7, 7, 6, 6, 6};

TfLiteStatus PartitionedAveragePoolingPrepare(TfLiteContext* context, TfLiteNode* node) {
    // Check I/O counts
    TF_LITE_ENSURE_EQ(context, tflite::NumInputs(node), 1);
    TF_LITE_ENSURE_EQ(context, tflite::NumOutputs(node), 1);

    const TfLiteTensor* input = tflite::GetInput(context, node, 0);
    // Ensure input is 4D: [Batch, Height, Width, Channels]
    TF_LITE_ENSURE_EQ(context, tflite::NumDimensions(input), 4);

    TfLiteTensor* output = tflite::GetOutput(context, node, 0);

    // Output shape: [Batch, Number_of_Splits * Channels] (2D tensor)
    TfLiteIntArray* output_dims = TfLiteIntArrayCreate(2);
    output_dims->data[0] = input->dims->data[0];
    // Output size is 6 (splits) * Channels
    output_dims->data[1] = split_sizes.size() * input->dims->data[3]; 

    return context->ResizeTensor(context, output, output_dims);
}

TfLiteStatus PartitionedAveragePoolingEval(TfLiteContext* context, TfLiteNode* node) {
    const TfLiteTensor* input = tflite::GetInput(context, node, 0);
    TfLiteTensor* output = tflite::GetOutput(context, node, 0);

    const float* input_data = tflite::GetTensorData<float>(input);
    float* output_data = tflite::GetTensorData<float>(output);

    int batch = input->dims->data[0];
    int height = input->dims->data[1]; // Should be 39
    int width = input->dims->data[2];
    int channels = input->dims->data[3];
    int output_features = output->dims->data[1]; // 6 * Channels

    // Iterate over batches
    for (int b = 0; b < batch; ++b) {
        int current_h_offset = 0;
        
        // Iterate over each partition
        for (size_t split_idx = 0; split_idx < split_sizes.size(); ++split_idx) {
            int split_size = split_sizes[split_idx];
            
            // For each channel, calculate the average over the partition
            for (int c = 0; c < channels; ++c) {
                float sum = 0.0f;
                int count = split_size * width;

                // Sum over the height and width of the partition
                for (int h = 0; h < split_size; ++h) {
                    for (int w = 0; w < width; ++w) {
                        // Index calculation: (b * H * W * C) + ((current_h_offset + h) * W * C) + (w * C) + c
                        int input_index = b * height * width * channels +
                                          (current_h_offset + h) * width * channels +
                                          w * channels + c;
                        sum += input_data[input_index];
                    }
                }

                // Output index: (b * OutputFeatures) + (split_idx * C) + c
                int output_index = b * output_features + split_idx * channels + c;
                output_data[output_index] = sum / (float)count;
            }
            current_h_offset += split_size;
        }
    }

    return kTfLiteOk;
}

// Function to create a custom op registration object
TfLiteRegistration* Register_Partitioned_Average_Pooling() {
    static TfLiteRegistration r = {
        .init = nullptr, 
        .free = nullptr, 
        .prepare = PartitionedAveragePoolingPrepare,
        .invoke = PartitionedAveragePoolingEval,
        .profiling_string = nullptr,
        .builtin_code = tflite::BuiltinOperator_CUSTOM,
        .custom_name = kPartitionedAveragePoolingName,
        .version = 1,
    };
    return &r;
}