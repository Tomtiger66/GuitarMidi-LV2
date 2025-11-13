/* Copyright 2018 The TensorFlow Authors. All Rights Reserved.

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
==============================================================================*/

#define TF_MAJOR_VERSION 2
#define TF_MINOR_VERSION 20
#define TF_PATCH_VERSION 0
#include <cstdio>
#include <cstdlib>
#include <memory>
#include <chrono>
#include <iostream>
#include "tensorflow/core/public/version.h"
#include "tensorflow/lite/version.h"
#include "tensorflow/lite/core/interpreter_builder.h"
#include "tensorflow/lite/interpreter.h"
#include "tensorflow/lite/kernels/register.h"
#include "tensorflow/lite/model_builder.h"
#include "tensorflow/lite/optional_debug_tools.h"
#include "tensorflow/lite/delegates/xnnpack/xnnpack_delegate.h"
// This is an example that is minimal to read a model
// from disk and perform inference. There is no data being loaded
// that is up to you to add as a user.
//
// NOTE: Do not add any dependencies to this that cannot be built with
// the minimal makefile. This example must remain trivial to build with
// the minimal build tool.
//
// Usage: minimal <tflite model>

#define TFLITE_MINIMAL_CHECK(x)                              \
  if (!(x)) {                                                \
    fprintf(stderr, "Error at %s:%d\n", __FILE__, __LINE__); \
    exit(1);                                                 \
  }

int main(int argc, char* argv[]) {
  if (argc != 2) {
    fprintf(stderr, "minimal <tflite model>\n");
    return 1;
  }
  const char* filename = argv[1];

  // Load model
  std::unique_ptr<tflite::FlatBufferModel> model =
      tflite::FlatBufferModel::BuildFromFile(filename);
  TFLITE_MINIMAL_CHECK(model != nullptr);

  // Build the interpreter with the InterpreterBuilder.
  // Note: all Interpreters should be built with the InterpreterBuilder,
  // which allocates memory for the Interpreter and does various set up
  // tasks so that the Interpreter can read the provided model.
  tflite::ops::builtin::BuiltinOpResolver resolver;
  tflite::InterpreterBuilder builder(*model, resolver);
  std::unique_ptr<tflite::Interpreter> interpreter;
  builder(&interpreter);
  TFLITE_MINIMAL_CHECK(interpreter != nullptr);
  
  TfLiteXNNPackDelegateOptions xnnpack_options =
      TfLiteXNNPackDelegateOptionsDefault();
  xnnpack_options.num_threads = 16;  // Set number of threads as appropriate for your
                                    // platform and application needs.  
//  tflite::gpu::GpuDelegateOptions gpu_options = 
//       tflite::gpu::GpuDelegateOptionsDefault();
//   gpu_options.inference_preference = TFLITE_GPU_INFERENCE_PREFERENCE_FAST_SINGLE_ANSWER;
//   gpu_options.inference_priority1 = TFLITE_GPU_INFERENCE_PRIORITY_MIN_LATENCY;
//   gpu_options.inference_priority2 = TFLITE_GPU_INFERENCE_PRIORITY_AUTO;
//   gpu_options.inference_priority3 = TFLITE_GPU_INFERENCE_PRIORITY_AUTO;
//   std::unique_ptr<tflite::GpuDelegate, decltype(&tflite::GpuDelegateDelete)> gpu_delegate(
//       tflite::GpuDelegateCreate(&gpu_options), tflite::GpuDelegateDelete);
//   TFLITE_MINIMAL_CHECK(interpreter->ModifyGraphWithDelegate(gpu_delegate.get()) == kTfLiteOk);
    if (interpreter->ModifyGraphWithDelegate(
        TfLiteXNNPackDelegateCreate(&xnnpack_options)) != kTfLiteOk) {
    // Handle error, but usually optional
    fprintf(stderr, "Warning: Failed to apply XNNPACK delegate.\n");
}
  // Allocate tensor buffers.
  TFLITE_MINIMAL_CHECK(interpreter->AllocateTensors() == kTfLiteOk);
  printf("=== Pre-invoke Interpreter State ===\n");
  tflite::PrintInterpreterState(interpreter.get());

  // Fill input buffers
  // TODO(user): Insert code to fill input tensors.
  // Note: The buffer of the input tensor with index `i` of type T can
  // be accessed with `T* input = interpreter->typed_input_tensor<T>(i);`

  // Run inference
  while (true){
    // char c;
    // std::cin >>c;
    // if(c=='q'){
    //   break;
    // }
    auto timer_start=std::chrono::high_resolution_clock::now();
    TFLITE_MINIMAL_CHECK(interpreter->Invoke()==kTfLiteOk);
    auto timer_end=std::chrono::high_resolution_clock::now();
    std::chrono::duration<double,std::milli> duration=timer_end-timer_start;
    std::cout<<"Inference time: "<<duration.count()<<"ms"<<std::endl;
  }
  TFLITE_MINIMAL_CHECK(interpreter->Invoke() == kTfLiteOk);
  printf("\n\n=== Post-invoke Interpreter State ===\n");
  tflite::PrintInterpreterState(interpreter.get());

  // Read output buffers
  // TODO(user): Insert getting data out code.
  // Note: The buffer of the output tensor with index `i` of type T can
  // be accessed with `T* output = interpreter->typed_output_tensor<T>(i);`

  return 0;
}