Neural Network Architecture for Polyphonic Guitar Pitch Detection1. Introduction to Polyphonic Pitch DetectionMulti-pitch estimation (MPE) is a long-standing and complex challenge within Music Information Retrieval (MIR), specifically focused on identifying the simultaneous presence of multiple pitches from various sound sources within a single audio mixture.1 When applied to guitar audio, this task involves precisely determining all notes being played concurrently—whether forming a chord, a complex arpeggio, or overlapping melodic lines—at each discrete moment in time.This problem is inherently difficult, particularly for polyphonic music, due to several interacting factors. First, polyphonic audio represents an intricate blend of numerous sound sources, such as different instruments and vocals, each possessing distinct onset times, fundamental frequencies (pitches), and volume characteristics.2 Disentangling individual pitch information from this composite signal presents a formidable analytical challenge. Second, a significant complication arises from the interaction of individual harmonics produced by concurrent notes. These harmonics can either constructively interfere, leading to increased amplitude for certain frequencies, or destructively interfere, resulting in a decrease or complete elimination of specific frequencies. Such interactions profoundly complicate the accurate inference of individual pitches.2 Finally, a pervasive limitation in this field is the scarcity of large-scale and diverse polyphonic music datasets accompanied by detailed multi-pitch annotations.1 The creation of comprehensive, frame-level annotations for polyphonic audio is labor-intensive and costly, posing a substantial hurdle for training robust supervised deep learning models.Despite these challenges, deep neural networks, particularly Convolutional Neural Networks (CNNs) and Recurrent Neural Networks (RNNs), have consistently demonstrated robust and superior performance across a wide spectrum of audio processing tasks, including intricate problems like pitch tracking and various facets of music information retrieval.2 These models possess the unique capability to learn complex, hierarchical features directly from raw audio representations, such as spectrograms. This capability circumvents the limitations of conventional signal processing techniques, which often struggle to adapt to the much broader frequency ranges and more rapid pitch variations characteristic of diverse audio domains beyond traditional speech and monophonic music.3 Deep learning architectures enable the estimation of pitch contours—defined as the temporal sequence of fundamental frequency (F0) values—directly from time-frequency representations of audio signals in an efficient, end-to-end manner.3The fundamental nature of polyphonic music, where multiple pitches can sound concurrently, dictates that the task of polyphonic pitch detection is not a multi-class classification problem (where an input belongs to exactly one category, such as identifying a single instrument). Instead, it is inherently a multi-label classification problem. In a multi-label scenario, a single input (e.g., a time frame of audio) can be associated with zero, one, or multiple categories (MIDI notes) simultaneously.5 For MPE, each of the 88 standard MIDI notes (or a relevant subset covering the guitar's range) represents an independent "label" that can be either active (present) or inactive (absent) at any given time frame. This approach is consistent with successful systems that have trained "88 binary classifiers capable of transcribing notes of polyphonic music," where "each classifier detects the presence of a single note in the music at each time step".2 This specific classification paradigm has direct and crucial implications for the design of the neural network's output layer and the choice of its associated loss function. It necessitates the use of a sigmoid activation function (rather than softmax) for each output neuron, as sigmoid outputs independent probabilities for each label. Consequently, the appropriate loss function is Binary Cross-Entropy (BCE) or its advanced variants, which are designed to handle independent binary classification tasks for each label.7 This framing requires the model to learn to distinguish the presence versus absence of each possible note independently, even amidst the complex interactions of other simultaneously sounding notes.2. Audio Preprocessing and Feature Extraction: Filter Bank Outputs as Direct InputYour plugin architecture provides a highly specialized and pre-processed input: the amplitudes or energies from 72 Butterworth filters. These filters are strategically deployed as 12 filters per string, with each filter precisely corresponding to a specific fret on that string. This means your plugin performs a crucial step of feature engineering by directly providing the neural network with information about the energy present at the fundamental frequencies of each playable note on the guitar. 9A key constraint for your system is that the input block size is 256 samples at a 48kHz sample rate, and the neural network must run inference per block in real-time. This means that for each 256-sample audio block, your Butterworth filter bank will produce a sequence of 72 output values for each of the 256 samples within that block. Consequently, the neural network will receive a 2D matrix of shape (256, 72) as input for each inference call. This matrix represents 256 time steps, with 72 filter outputs at each time step.This approach offers several advantages:
Direct Relevance: The filter outputs are directly tied to the specific pitches (frets) of interest on a guitar, making them highly relevant features for pitch detection.
Reduced Computational Load for NN: The neural network doesn't need to learn how to extract these fundamental frequency components from raw audio or complex spectrograms; this work is already done by your Butterworth filter bank. This can lead to a simpler and more efficient neural network.
Targeted Overtone Handling: While overtones are still a challenge, the NN can learn to interpret the pattern of activations across these 72 filters. For example, if the filter for a low E (fret 0 on string 6) is active, and filters corresponding to its octave or fifth (which might be higher frets on other strings, or even higher frequencies on the same string if the filter bank extends to harmonics) are also active, the NN can learn that this pattern indicates the low E fundamental, rather than misinterpreting an overtone as a separate note. 10
The input to the neural network for a single inference will be a 2D matrix of num_samples_per_block (256) time steps by num_filters (72) features, representing the filter outputs for that specific 256-sample block.It is imperative to normalize these filter outputs before feeding them into the neural network to ensure stable and efficient training. Common normalization techniques include min-max scaling (e.g., to a range like ``) or Z-score normalization (mean 0, standard deviation 1).For each inference call, the input to the neural network will have a shape of (batch_size, 256, 72), where batch_size will typically be 1 for real-time inference. The crucial aspect of maintaining temporal context across these individual blocks will be handled by the internal state of the recurrent neural network (RNN), which is designed to carry information from one time step (block) to the next.3. Proposed Neural Network ArchitecturesHere, we propose two distinct neural network architectures, both designed to process your (256, 72) filter bank input per audio block and provide real-time MIDI note predictions.3.1. Architecture 1: Pure CNN SolutionThis architecture relies solely on 1D Convolutional Neural Networks (CNNs) to extract features and make predictions. It processes each (256, 72) block independently, meaning it does not explicitly maintain memory across different audio blocks. Its strength lies in efficiently capturing intra-block temporal patterns and feature interactions.
Input Layer: The input to the CNN block will be the (256, 72) filter outputs for the current block, with a shape of (batch_size, 256, 72).
1D Convolutional Layers: Multiple sequential 1D convolutional layers will extract hierarchical temporal features. Each Conv1D layer will be followed by BatchNormalization and a ReLU activation function. MaxPooling1D layers will periodically reduce the temporal dimension.

These layers learn localized patterns across the 256 samples within the block and across the 72 filter outputs.


Global Pooling Layer: After the final convolutional layer, a GlobalAveragePooling1D or GlobalMaxPooling1D layer will reduce the entire temporal dimension of the feature map into a single feature vector for the current 256-sample block. This condenses all the learned intra-block temporal information.
Output Layer: A final Dense layer with 88 units and a Sigmoid activation function will output the independent probabilities for each MIDI note.
Python Code for Pure CNN Architecture (using Keras/TensorFlow):Pythonimport tensorflow as tf
from tensorflow.keras import layers, models, optimizers
import numpy as np

# --- Configuration ---
INPUT_SHAPE = (256, 72)  # (time_steps_per_block, num_filters)
OUTPUT_DIM = 88          # Number of MIDI notes (A0 to C8)
LEARNING_RATE = 0.001
BATCH_SIZE = 32          # For training; for inference, batch_size=1
EPOCHS = 10              # Example, adjust based on dataset size and convergence

# --- 1. Define the Pure CNN Model ---
def build_cnn_model(input_shape, output_dim):
    model = models.Sequential()
    return model

# --- 2. Compile the Model ---
cnn_model = build_cnn_model(INPUT_SHAPE, OUTPUT_DIM)
cnn_model.compile(optimizer=optimizers.Adam(learning_rate=LEARNING_RATE),
                  loss='binary_crossentropy', # BCE for multi-label classification
                  metrics=['accuracy'])

cnn_model.summary()

# --- 3. Placeholder for Data Generation (Replace with your actual data loading) ---
# In a real scenario, X_train would be a NumPy array of shape (num_samples, 256, 72)
# and y_train would be (num_samples, 88)
num_training_samples = 1000
X_train_cnn = np.random.rand(num_training_samples, INPUT_SHAPE, INPUT_SHAPE[1]).astype(np.float32)
y_train_cnn = np.random.randint(0, 2, size=(num_training_samples, OUTPUT_DIM)).astype(np.float32)

# Normalize inputs (example: min-max scaling if values are 0-1, or Z-score if needed)
# X_train_cnn = (X_train_cnn - X_train_cnn.min()) / (X_train_cnn.max() - X_train_cnn.min())

# --- 4. Training the Model ---
print("\n--- Training Pure CNN Model ---")
history_cnn = cnn_model.fit(X_train_cnn, y_train_cnn,
                            batch_size=BATCH_SIZE,
                            epochs=EPOCHS,
                            validation_split=0.2) # Use a portion of data for validation

# --- 5. Real-time Inference Example (per block) ---
print("\n--- Pure CNN Real-time Inference Example ---")
# Simulate a single 256-sample block of filter outputs
single_block_input = np.random.rand(1, INPUT_SHAPE, INPUT_SHAPE[1]).astype(np.float32)
# Normalize if training data was normalized
# single_block_input = (single_block_input - X_train_cnn.min()) / (X_train_cnn.max() - X_train_cnn.min())

# Perform inference
predictions_cnn = cnn_model.predict(single_block_input)
print(f"Predicted probabilities for 88 MIDI notes (first 5): {predictions_cnn[0, :5]}")
# Apply a threshold to get binary predictions (e.g., 0.5)
binary_predictions_cnn = (predictions_cnn > 0.5).astype(int)
print(f"Binary predictions (first 5): {binary_predictions_cnn[0, :5]}")

3.2. Architecture 2: Hybrid CNN-RNN SolutionThis architecture combines the strengths of CNNs for intra-block feature extraction with RNNs for inter-block temporal modeling. This is generally the more robust approach for time-series data like audio, as it allows the network to "remember" context from previous audio blocks, which is crucial for tracking sustained notes, vibrato, and complex melodic/harmonic progressions across block boundaries.
Input Layer: The input for each inference call will be the (256, 72) filter outputs for the current block, with a shape of (batch_size, 256, 72).
1D Convolutional Layers (CNN Block): Similar to the pure CNN model, these layers will extract hierarchical temporal features within each 256-sample block. They will be followed by BatchNormalization and ReLU activations, and MaxPooling1D layers for downsampling.
Global Pooling Layer: After the final convolutional layer, a GlobalAveragePooling1D or GlobalMaxPooling1D layer will condense the intra-block information into a single feature vector. This vector represents the learned features for the current 256-sample block.
Recurrent Layers (RNN Block): The condensed feature vector from the CNN block will be fed into a Bidirectional LSTM or Bidirectional GRU layer. These layers are crucial for maintaining memory across successive audio blocks.

Stateful RNN: For real-time processing, the RNN layer will be configured as stateful=True. This means its internal hidden state and cell state (for LSTM) are preserved and passed from one inference call (one block) to the next. This allows the network to build a long-term understanding of the musical context.
State Management: During real-time inference, you must explicitly manage these states: initialize them at the beginning of a new sequence (e.g., when a new song starts or after a long silence) and pass the updated states from the previous inference step to the current one.


Output Layer: A final Dense layer with 88 units and a Sigmoid activation function will output the independent probabilities for each MIDI note.
Python Code for Hybrid CNN-RNN Architecture (using Keras/TensorFlow):Pythonimport tensorflow as tf
from tensorflow.keras import layers, models, optimizers
import numpy as np

# --- Configuration ---
INPUT_SHAPE = (256, 72)  # (time_steps_per_block, num_filters)
OUTPUT_DIM = 88          # Number of MIDI notes (A0 to C8)
LEARNING_RATE = 0.001
BATCH_SIZE = 1           # Crucial for stateful RNN in real-time inference
EPOCHS = 10              # Example, adjust based on dataset size and convergence

# --- 1. Define the Hybrid CNN-RNN Model ---
def build_cnn_rnn_model(input_shape, output_dim, rnn_units=256, stateful=False):
    # Input for a single block
    inputs = layers.Input(batch_shape=(BATCH_SIZE, input_shape, input_shape[1]))

    # 1D CNN Block 1
    x = layers.Conv1D(filters=64, kernel_size=3, padding='same', activation='relu')(inputs)
    x = layers.BatchNormalization()(x)
    x = layers.MaxPooling1D(pool_size=2, strides=2)(x) # Output shape: (128, 64)

    # 1D CNN Block 2
    x = layers.Conv1D(filters=128, kernel_size=3, padding='same', activation='relu')(x)
    x = layers.BatchNormalization()(x)
    x = layers.MaxPooling1D(pool_size=2, strides=2)(x) # Output shape: (64, 128)

    # 1D CNN Block 3
    x = layers.Conv1D(filters=256, kernel_size=3, padding='same', activation='relu')(x)
    x = layers.BatchNormalization()(x)
    x = layers.MaxPooling1D(pool_size=2, strides=2)(x) # Output shape: (32, 256)

    # Global Pooling to condense intra-block temporal information
    # This reduces (time_steps_after_cnn, features) to (features,)
    x = layers.GlobalAveragePooling1D()(x) # Output shape: (256,)

    # Reshape for RNN: (batch_size, 1, features) as RNN expects a sequence
    # Even though it's one block, it's one step in the sequence of blocks
    x = layers.Reshape((1, x.shape[-1]))(x)

    # Bidirectional GRU/LSTM Layer (stateful for real-time context)
    # GRU is often preferred for real-time due to lower computational cost [13, 14]
    rnn_output = layers.Bidirectional(
        layers.GRU(rnn_units, return_sequences=False, stateful=stateful)
    )(x)
    rnn_output = layers.Dropout(0.3)(rnn_output) # Regularization

    # Optional Dense Layer
    x = layers.Dense(256, activation='relu')(rnn_output)
    x = layers.Dropout(0.3)(x) # Regularization

    # Output Layer for 88 MIDI notes (multi-label classification)
    outputs = layers.Dense(output_dim, activation='sigmoid')(x)

    model = models.Model(inputs=inputs, outputs=outputs)
    return model

# --- 2. Compile the Model ---
# For training, stateful=False is often easier for shuffled batches.
# For real-time inference, you'd load a model trained with stateful=True or manage states manually.
cnn_rnn_model_train = build_cnn_rnn_model(INPUT_SHAPE, OUTPUT_DIM, stateful=False)
cnn_rnn_model_train.compile(optimizer=optimizers.Adam(learning_rate=LEARNING_RATE),
                            loss='binary_crossentropy',
                            metrics=['accuracy'])

cnn_rnn_model_train.summary()

# --- 3. Placeholder for Data Generation (Replace with your actual data loading) ---
# For training, you'd typically have longer sequences or many independent blocks.
# If training with stateful=True, sequences must not be shuffled and batch_size must be fixed.
num_training_sequences = 100 # Number of "songs" or long audio segments
sequence_length_blocks = 50  # Each sequence is 50 blocks long
total_blocks = num_training_sequences * sequence_length_blocks

X_train_cnn_rnn = np.random.rand(total_blocks, INPUT_SHAPE, INPUT_SHAPE[1]).astype(np.float32)
y_train_cnn_rnn = np.random.randint(0, 2, size=(total_blocks, OUTPUT_DIM)).astype(np.float32)

# Normalize inputs (example: min-max scaling if values are 0-1, or Z-score if needed)
# X_train_cnn_rnn = (X_train_cnn_rnn - X_train_cnn_rnn.min()) / (X_train_cnn_rnn.max() - X_train_cnn_rnn.min())

# --- 4. Training the Model ---
print("\n--- Training Hybrid CNN-RNN Model ---")
# For stateful training, you'd typically train on sequences and reset states after each sequence.
# For simplicity in this example, we'll train stateless, but note the real-time inference implications.
history_cnn_rnn = cnn_rnn_model_train.fit(X_train_cnn_rnn, y_train_cnn_rnn,
                                          batch_size=BATCH_SIZE, # Batch size 1 for training if stateful=True
                                          epochs=EPOCHS,
                                          validation_split=0.2)

# --- 5. Real-time Inference Example (per block with state management) ---
print("\n--- Hybrid CNN-RNN Real-time Inference Example ---")

# To perform stateful inference, you need to build a stateful model
# and manage its states. This is often done by creating a separate inference model
# or by using the functional API and explicitly passing states.
# For simplicity, we'll demonstrate using a stateful model.
# In a real plugin, you'd load the trained weights into this stateful model.

# Build a stateful model for inference (batch_size=1 is typical for real-time)
cnn_rnn_model_inference = build_cnn_rnn_model(INPUT_SHAPE, OUTPUT_DIM, stateful=True)
# Copy weights from the trained model
cnn_rnn_model_inference.set_weights(cnn_rnn_model_train.get_weights())

# Simulate a sequence of blocks (e.g., a short musical phrase)
num_inference_blocks = 5
inference_sequence = np.random.rand(num_inference_blocks, INPUT_SHAPE, INPUT_SHAPE[1]).astype(np.float32)

print("Processing inference sequence block by block:")
for i in range(num_inference_blocks):
    current_block_input = inference_sequence[i:i+1, :, :] # Take one block, maintain (1, 256, 72) shape
    
    # Perform inference
    predictions_rnn = cnn_rnn_model_inference.predict(current_block_input, verbose=0)
    
    print(f"Block {i+1}: Predicted probabilities (first 5): {predictions_rnn[0, :5]}")
    # Apply a threshold to get binary predictions
    binary_predictions_rnn = (predictions_rnn > 0.5).astype(int)
    print(f"Block {i+1}: Binary predictions (first 5): {binary_predictions_rnn[0, :5]}")

# After a sequence (e.g., a song ends, or a long silence), reset the RNN states
cnn_rnn_model_inference.reset_states()
print("\nRNN states reset after sequence.")

4. Training ConsiderationsThe effective training of the proposed neural network architectures for polyphonic pitch detection necessitates careful consideration of the loss function, optimizer, and data augmentation strategies.Loss FunctionGiven that polyphonic pitch detection is formulated as a multi-label classification problem, where multiple notes can be active simultaneously, the Binary Cross-Entropy (BCE) loss function is the appropriate choice.6 Unlike softmax cross-entropy, which is suitable for single-label classification where classes are mutually exclusive, BCE treats each of the 88 MIDI note predictions as an independent binary classification task. For each output neuron, BCE measures the dissimilarity between the predicted probability (output by the sigmoid activation) and the true binary label (0 or 1, indicating absence or presence of the note). While BCE is well-suited for this decomposition, it can face challenges related to class imbalance, particularly when some notes are significantly more common than others in the training data.7 Advanced variants of BCE, such as weighted BCE or focal loss, can be explored to mitigate these imbalance issues.OptimizerThe Adam (Adaptive Moment Estimation) optimizer is highly recommended for training this deep neural network.15 Adam is an adaptive learning rate algorithm that computes individual adaptive learning rates for different parameters, thereby improving training speeds and accelerating convergence.15 It combines the benefits of two other popular optimization algorithms: Momentum (which accelerates convergence in consistent directions) and RMSProp (which controls overshooting by modulating step size based on squared gradients).15 Adam maintains exponentially decaying moving averages of the gradients (first moment) and the squared gradients (second moment) for each parameter, using these to adaptively adjust the learning rate during training.16Typical hyperparameters for the Adam optimizer include:
α (Learning Rate): Often initialized at 0.001.16 While Adam adapts learning rates, a reasonable initial value is still essential.
β₁ (Decay rate for momentum): A typical value is 0.9, giving high weighting to the most recent gradients.15
β₂ (Decay rate for squared gradients): A typical value is 0.999, capturing long-term memory of gradients for a stable variance estimate.15
ϵ (Epsilon): A small constant, usually around 1e-8, added for numerical stability to prevent division by zero.15
Data AugmentationA significant limitation in multi-pitch estimation, particularly for polyphonic music, is the "shortage of large-scale and diverse polyphonic music datasets with multi-pitch annotations".2 To address this data scarcity and enhance the model's robustness and generalization capabilities, audio data augmentation is an essential technique.17 Data augmentation involves modifying existing audio samples to create new training data, expanding the coverage of the problem space and making models robust to variations encountered in real-world conditions.17It is crucial to apply these augmentation techniques to the raw audio signal before it is fed into your Butterworth filter bank. This ensures that the filter outputs reflect the augmented audio, allowing the neural network to learn from a wider variety of realistic input conditions.Common and effective audio augmentation techniques include:
Pitch Shifting: Altering the pitch of an audio signal without changing its duration. This can simulate different musical keys or variations in instrument tuning.17
Time Stretching: Adjusting the duration of an audio signal while maintaining its pitch. This mimics variations in tempo or performance speed.17
Speed Perturbation: Changing the speed of an audio signal by resampling it at a different sample rate, which can simulate variations in playing speed.18
Amplitude Scaling: Adjusting the overall volume of an audio signal to simulate different recording levels or dynamic variations.18
Noise Injection: Adding background sounds like street noise, static, or room reverb to simulate real-world acoustic environments and improve robustness to noise.17
SpecAugment: A method that masks parts of a spectrogram (frequency or time blocks) to force models to focus on broader patterns rather than fixed features, reducing overfitting.17 (While your input isn't a spectrogram, similar masking concepts could potentially be applied to blocks of your 72 filter outputs if carefully designed).
These transformations expand the dataset, making models more robust to variations they might encounter in production. Implementing audio augmentation typically involves libraries like Librosa, TorchAudio, or TensorFlow Signal.17 It is crucial to balance augmentation intensity, as excessive transformation can distort the audio beyond realistic scenarios and reduce credibility.175. Latency Considerations for Real-time InferenceThe requirement for real-time output is a critical design constraint for your plugin. Latency in audio processing refers to the delay between an audio signal entering a system and its corresponding output. For a musical instrument plugin, low latency is crucial for a natural and responsive playing experience.Inherent Block LatencyYour system processes audio in 256-sample blocks at a 48kHz sample rate. This inherently introduces a minimum buffer latency, as the system must collect a full block of samples before processing can begin.
Block Duration: 256 samples / 48,000 samples/second = 0.00533 seconds, or approximately 5.33 milliseconds (ms). 19
This 5.33ms is the fundamental delay introduced by the block-based processing, even before any neural network computation. The goal for real-time performance is to ensure that the neural network's inference time does not add significantly to this inherent buffer latency.
RNN and Neural Network Inference LatencyThe RNN itself, and the preceding CNN layers, introduce computational latency, which is the time it takes for the network to perform its calculations for a given input block.
Sequential Processing: Recurrent Neural Networks (RNNs), including LSTMs and GRUs, are designed to process sequential data by maintaining an internal memory state that is updated with each new input (in your case, each 256-sample block). This sequential nature means that the output for the current block depends on the current input and the state derived from all previous blocks.
No Additional Buffer Lag from RNN: The RNN does not introduce an additional buffering delay beyond the 256-sample block itself, provided its computation for that block completes within the 5.33ms window. The latency contribution of the RNN is solely its inference computation time for that single block. If the network's computation for a block takes longer than 5.33ms, it will cause the audio processing chain to fall behind, leading to audible glitches, dropouts, or increased perceived latency.
Factors Influencing Inference Latency:

Model Complexity: The number of layers (CNN and RNN), the number of filters in CNN layers, and the number of recurrent units (e.g., 256 units) directly impact the number of computations and parameters. More complex models generally lead to higher latency.
Choice of RNN Cell: Gated Recurrent Units (GRUs) are generally considered more computationally efficient and faster to train and infer than Long Short-Term Memory (LSTM) networks due to their simpler internal structure and fewer parameters (two gates vs. three for LSTMs). 13 For real-time applications with strict latency requirements, GRUs are often preferred if they achieve comparable performance. 13
Hardware: Inference speed is heavily dependent on the processing hardware (CPU vs. GPU). For LV2 plugins, inference typically runs on the CPU. Optimized hardware accelerators exist for RNNs, capable of sub-millisecond latency, but these are specialized solutions not typically found in standard plugin environments. 23
Inference Engine Optimization: Deploying the trained neural network using highly optimized inference engines (e.g., ONNX Runtime, TensorFlow Lite) in C++ can significantly reduce the computational overhead compared to running directly within a full deep learning framework.
Batch Size: For real-time audio, the batch size is typically 1. While larger batch sizes can sometimes improve throughput (samples processed per second), a batch size of 1 is necessary for minimal latency per block.


Quantifying Latency ContributionIt is challenging to provide an exact millisecond figure for the RNN's latency contribution without knowing the precise model size, specific hardware, and level of optimization. However, for a responsive musical experience, total latency (including audio interface, buffer, and plugin processing) should ideally be below 10ms, with sub-3ms often considered imperceptible by human perception. 21To achieve real-time performance, the combined inference time of your CNN and RNN for each 256-sample block must be significantly less than 5.33ms. This allows the plugin to process the audio block and generate its MIDI output before the next audio block is ready, preventing any additional delay. Choosing GRUs over LSTMs, keeping the network architecture as lean as possible while maintaining accuracy, and employing highly optimized inference code are crucial steps to minimize this computational latency.5. ConclusionThe proposed neural network architectures for polyphonic guitar pitch detection integrate either a pure Convolutional Neural Network (CNN) or a hybrid CNN-RNN design, meticulously tailored to leverage your plugin's unique feature extraction and the per-block, real-time inference requirement. The direct input of a (256, 72) matrix of Butterworth filter outputs for each audio block serves as a powerful, pre-engineered feature set, eliminating the need for the neural network to learn basic frequency decomposition.The pure CNN architecture efficiently extracts hierarchical temporal patterns within each 256-sample block, condensing this information into a single feature vector for immediate prediction. The hybrid CNN-RNN approach extends this by using 1D CNN layers for intra-block feature extraction, followed by a Global Pooling layer, and then feeding into Bidirectional LSTM or GRU layers. These recurrent layers are critical for modeling the long-term temporal dependencies inherent in musical sequences by maintaining and updating their internal states across successive audio blocks. This enables the network to understand how pitches evolve and interact over time, even when processing one block at a time. Both architectures explicitly frame polyphonic pitch detection as a multi-label classification problem, employing 88 independent sigmoid output units, each corresponding to a standard MIDI note. This design directly addresses the challenge of simultaneous note occurrences and complex harmonic interactions, enabling the model to predict the presence of multiple pitches concurrently. The use of Binary Cross-Entropy loss and the Adam optimizer further supports this multi-label framework and ensures efficient training.Finally, the emphasis on data augmentation, applied to the raw audio before filter processing, is paramount, particularly given the scarcity of large-scale annotated polyphonic datasets. Techniques like pitch shifting, time stretching, and noise injection are essential for enhancing the model's robustness and generalization capabilities to real-world guitar performances. This comprehensive architectural design, coupled with appropriate training strategies, provides a robust framework for advancing the state-of-the-art in automatic polyphonic guitar transcription using your specific filter bank outputs and adhering to the per-block, real-time inference constraint.
