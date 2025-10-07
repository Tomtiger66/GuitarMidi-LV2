#include <fdeep/fdeep.hpp>
#include <iostream>
#include <vector>
#include <string>
#include <chrono>

// Include Eigen to set the number of threads for parallel execution
// Note: Eigen is a dependency of fdeep, so this should usually be available.
#include <Eigen/Core> 

// Define the expected input shape for the model
// Based on the previous CNN discussion (128 time steps, 43 mel bins, 1 channel)
// constexpr size_t INPUT_HEIGHT = 256; 
constexpr size_t INPUT_WIDTH = 312;
constexpr size_t INPUT_CHANNELS = 1;
using namespace std;
/**
 * @brief Demonstrates loading a Frugally-Deep JSON model and running inference.
 * * @param model_file_path The path to the JSON file containing the model.
 */
void run_inference(const std::string& model_file_path) {
    std::cout << "Attempting to load model from: " << model_file_path << std::endl;

    // 1. Load the model
    // fdeep::load_model performs all necessary parsing and validation.
    // NOTE: Model loading is slow. Do this only ONCE at application start.
    const fdeep::model model = fdeep::load_model(model_file_path);
    
    std::cout << "Model loaded successfully." << std::endl;

    // 2. Prepare the input tensor
    
    // Create the input data in a flat std::vector (size = H * W * C)
    const size_t input_size = /*INPUT_HEIGHT * */INPUT_WIDTH * INPUT_CHANNELS;
    
    // For demonstration, we fill the input with dummy data (e.g., 0.5)
    std::vector<float> input_data(input_size, 0.5f); 
    
    // Create the tensor shape, including the batch size of 1
    const fdeep::tensor_shape shape(/*INPUT_HEIGHT,*/ INPUT_WIDTH, INPUT_CHANNELS);

    // Create the final input tensor wrapped in a vector for the predict function
    const fdeep::tensor input_tensor(shape, input_data);
    const fdeep::tensors input_vec = {input_tensor};

    std::cout << "Input tensor created with shape: " 
              << fdeep::show_tensor_shape(input_tensor.shape())<< " (Total elements: " << input_size << ")" 
              << std::endl;
    
    // 3. Run Prediction (Warm-up)
    // The first prediction can be slower due to caching, so run it once to "warm up"
    std::cout << "Running warm-up prediction..." << std::endl;
    model.predict(input_vec);
    std::cout << "Warm-up complete. Starting timed loop." << std::endl;


    // 4. Run Timed Loop for Steady-State Measurement
    // We use microseconds for better resolution to target the 5ms goal.
    int count = 0;
    while(true)
    {
        auto begin = std::chrono::high_resolution_clock::now();
        fdeep::tensors result_vec = model.predict(input_vec);
        auto end = std::chrono::high_resolution_clock::now();

        auto duration_us = std::chrono::duration_cast<std::chrono::microseconds>(end - begin);
        double duration_ms = static_cast<double>(duration_us.count()) / 1000.0;
        
        std::cout << "Prediction " << ++count << ": Duration " << duration_ms << "ms" << std::endl;
        
        // Simple break condition to avoid infinite loop in testing environments
        if (count > 50) break; 
    }

    // 5. Process the Output (from the last prediction)
    const fdeep::tensors& result_vec = model.predict(input_vec); // Re-run one last time for result
    if (result_vec.empty()) {
        std::cerr << "Prediction failed: Result vector is empty." << std::endl;
        return;
    }

    // The output for our binary classification CNN model is likely a single tensor
    const fdeep::tensor& output_tensor = result_vec[0];
    
    // Get the scalar result (e.g., the probability of the positive class)
    // We assume the output is flattened (size 1) for a simple binary classification.
    const float prediction_value = output_tensor.get(0,0,0,0,0);
    
    std::cout << "\n--- Inference Result ---" << std::endl;
    std::cout << "Output Shape: " << fdeep::show_tensor_shape(output_tensor.shape()) << std::endl;
    std::cout << "Predicted Value (Probability): " << prediction_value << std::endl;
    std::cout << "------------------------\n" << std::endl;

}

int main(int argc, char* argv[]) {
    try {
        // --- CRITICAL SPEED UP STEP 1: Enable Multi-threading (Parallelization) ---
        // Eigen (FDeep's dependency) uses multi-threading. Set the number of threads
        // to match your CPU cores for maximum speed. You must ensure your CMake
        // enables OpenMP for this to be effective.
        const int num_threads = 4; // Adjust this to your core count for maximum throughput.
        Eigen::setNbThreads(num_threads);
        std::cout << "Set Eigen threads to: " << Eigen::nbThreads() << std::endl;
        
        // Specify the path to your converted JSON model file
        const std::string MODEL_PATH = "/home/gmwangi/workspace/src/GuitarMidi-LV2/python/neuralnetmodelling/model_dir/guitarmidi-model-and-weights.json";
        
        // This is the main function call
        run_inference(MODEL_PATH);

    } catch (const std::exception& e) {
        std::cerr << "Caught exception: " << e.what() << std::endl;
        return 1;
    }
    return 0;
}
