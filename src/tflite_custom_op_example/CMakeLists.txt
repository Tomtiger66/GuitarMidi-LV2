# cmake_minimum_required(VERSION 3.10)
# project(TFLiteCustomOpExample CXX)

# --- TENSORFLOW LITE CONFIGURATION ---
# IMPORTANT: You need to set the path to your TFLite source or installation.
# This variable should point to the directory containing the TFLite libraries 
# and the include directories (e.g., where 'tensorflow/lite/interpreter.h' resides).
# Example: set(TFLITE_DIR "/path/to/your/tflite/install")
# A simple way for many is to use the TFLite CMake configuration if available.
# We'll rely on finding the TFLite dependency.

find_package(TFLite REQUIRED)
# If TFLite is installed via a package manager or built with install targets, 
# this should find the necessary headers and libraries.

# If TFLite is NOT found via find_package, you will need manual configuration:
# include_directories(
#     /path/to/tflite/src/
#     /path/to/tflite/src/tensorflow/lite/
# )
# link_libraries(
#     /path/to/libtensorflow-lite.a
#     /path/to/libtensorflow-lite_custom_op.a # Or similar libs
# )

# --- CUSTOM OPERATOR LIBRARY ---
add_library(custom_op STATIC
    custom_op/PartitionedAvgPool.cc
)

# Link against TFLite includes for custom op development
target_include_directories(custom_op PUBLIC ${TFLite_INCLUDE_DIRS} custom_op /home/gerald/workspace/src/tensorflow-op70/tensorflow /home/gerald/workspace/src/tensorflow-op70/tensorflow/tensorflow/lite/kernels /home/gerald/workspace/src/tensorflow-op70/tensorflow/tensorflow/lite  )

# --- EXECUTABLE TARGET ---
add_executable(tflite_runner src/main.cc)

# Link the executable with the custom op library and the TFLite libraries
target_link_libraries(tflite_runner
    custom_op
    ${TFLite_LIBRARIES} 
    /home/gerald/workspace/src/tensorflow-op70/tensorflow/bazel-bin/tensorflow/lite/libtensorflowlite.so

)