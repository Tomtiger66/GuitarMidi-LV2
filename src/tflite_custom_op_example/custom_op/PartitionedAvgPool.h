#pragma once
#include "tensorflow/lite/c/c_api_types.h"
#include "tensorflow/lite/core/c/c_api_types.h"
#include "tensorflow/lite/kernels/internal/types.h"

// Define the name used in the Keras model Lambda layer and the TFLite file
constexpr char kPartitionedAveragePoolingName[] = "PartitionedAveragePooling";

// Function to register the custom operation with the TFLite runtime
TfLiteRegistration* Register_Partitioned_Average_Pooling();