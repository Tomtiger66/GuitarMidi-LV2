

# **Neural Network Architecture for Polyphonic Guitar Pitch Detection**

## **1\. Introduction to Polyphonic Pitch Detection**

Multi-pitch estimation (MPE) is a long-standing and complex challenge within Music Information Retrieval (MIR), specifically focused on identifying the simultaneous presence of multiple pitches from various sound sources within a single audio mixture.1 When applied to guitar audio, this task involves precisely determining all notes being played concurrently—whether forming a chord, a complex arpeggio, or overlapping melodic lines—at each discrete moment in time.This problem is inherently difficult, particularly for polyphonic music, due to several interacting factors. First, polyphonic audio represents an intricate blend of numerous sound sources, such as different instruments and vocals, each possessing distinct onset times, fundamental frequencies (pitches), and volume characteristics.2 Disentangling individual pitch information from this composite signal presents a formidable analytical challenge. Second, a significant complication arises from the interaction of individual harmonics produced by concurrent notes. These harmonics can either constructively interfere, leading to increased amplitude for certain frequencies, or destructively interfere, resulting in a decrease or complete elimination of specific frequencies. Such interactions profoundly complicate the accurate inference of individual pitches.2 Finally, a pervasive limitation in this field is the scarcity of large-scale and diverse polyphonic music datasets accompanied by detailed multi-pitch annotations.1 The creation of comprehensive, frame-level annotations for polyphonic audio is labor-intensive and costly, posing a substantial hurdle for training robust supervised deep learning models.Despite these challenges, deep neural networks, particularly Convolutional Neural Networks (CNNs) and Recurrent Neural Networks (RNNs), have consistently demonstrated robust and superior performance across a wide spectrum of audio processing tasks, including intricate problems like pitch tracking and various facets of music information retrieval.2 These models possess the unique capability to learn complex, hierarchical features directly from raw audio representations, such as spectrograms. This capability circumvents the limitations of conventional signal processing techniques, which often struggle to adapt to the much broader frequency ranges and more rapid pitch variations characteristic of diverse audio domains beyond traditional speech and monophonic music.3 Deep learning architectures enable the estimation of pitch contours—defined as the temporal sequence of fundamental frequency (F0) values—directly from time-frequency representations of audio signals in an efficient, end-to-end manner.3The fundamental nature of polyphonic music, where multiple pitches can sound concurrently, dictates that the task of polyphonic pitch detection is not a multi-class classification problem (where an input belongs to exactly one category, such as identifying a single instrument). Instead, it is inherently a multi-label classification problem. In a multi-label scenario, a single input (e.g., a time frame of audio) can be associated with zero, one, or multiple categories (MIDI notes) simultaneously.5 For MPE, each of the 88 standard MIDI notes (or a relevant subset covering the guitar's range) represents an independent "label" that can be either active (present) or inactive (absent) at any given time frame. This approach is consistent with successful systems that have trained "88 binary classifiers capable of transcribing notes of polyphonic music," where "each classifier detects the presence of a single note in the music at each time step".2 This specific classification paradigm has direct and crucial implications for the design of the neural network's output layer and the choice of its associated loss function. It necessitates the use of a sigmoid activation function (rather than softmax) for each output neuron, as sigmoid outputs independent probabilities for each label. Consequently, the appropriate loss function is Binary Cross-Entropy (BCE) or its advanced variants, which are designed to handle independent binary classification tasks for each label.7 This framing requires the model to learn to distinguish the presence versus absence of  
*each* possible note independently, even amidst the complex interactions of other simultaneously sounding notes.

## **2\. Audio Preprocessing and Feature Extraction: Extended Filter Bank Outputs as Direct Input**

Your plugin architecture now provides an even richer, more specialized input by extending the Butterworth filter bank. Instead of just 12 filters per string for fundamentals, you will now have **four filters per fret per string**: one for the fundamental frequency (F0) and three additional filters for its corresponding overtones (e.g., 2nd harmonic (2*F0), 3rd harmonic (3*F0), and 4th harmonic (4\*F0)). 9  
This significantly expands your feature set:

* **Original Filters:** 12 frets/string \* 6 strings \= 72 fundamental filters.  
* **New Overtone Filters:** 72 fundamental filters \* 3 overtones/fundamental \= 216 overtone filters.  
* **Total Filters:** 72 \+ 216 \= **288 filters**.

For each 256-sample audio block, your extended Butterworth filter bank will produce a sequence of 288 output values for *each* of the 256 samples within that block. Consequently, the neural network will receive a **2D matrix of shape (256, 288\)** as input for each inference call. This matrix represents 256 time steps, with 288 filter outputs at each time step.  
**Organization of the 288 Filter Outputs (Fret-wise, with Harmonics Grouped):**  
To maximize the effectiveness of the 2D CNN layers for learning guitar-specific patterns (like chords and harmonic structures), the 288 filter outputs should be organized in a **fret-wise manner, with the harmonic group for each string's fret kept together**. This means for each fret, you would group the fundamental and its three overtone filters for each of the six strings.  
The input vector of 288 features for a single time step (or column in the (256, 288\) matrix) would be structured as follows:  
\`\` (4 filters for String 6, Fret 11\)  
This organization results in (6 strings \* 4 filters/string/fret) \= 24 features per fret. Since there are 12 frets, the total is 12 frets \* 24 features/fret \= 288 features.  
**Advantages of this Extended Filter Bank:**

* **Explicit Harmonic Information:** By providing explicit filter outputs for harmonics, the neural network can more effectively learn to distinguish between a fundamental note and its overtones. For example, if the filter for a fundamental (e.g., S1F5\_F0) is active, and its corresponding overtone filters (S1F5\_2F0, S1F5\_3F0, S1F5\_4F0) are also active, this pattern strongly indicates the presence of the S1F5 note. Conversely, if a higher-frequency filter is active without its corresponding fundamental, the NN can learn to suppress it as an isolated overtone or noise. Studies have shown that filter banks can allow deep neural networks to "more efficiently analyze the harmonic components". 13  
* **Improved Polyphonic Tracking:** This richer input helps the NN disentangle overlapping harmonics from different simultaneously played notes, a major challenge in polyphonic pitch detection.  
* **Direct Relevance:** The filter outputs remain directly tied to the specific pitches (frets) and their harmonic content, making them highly relevant features.  
* **Reduced Computational Load for NN (Feature Extraction):** The complex task of identifying harmonic components is handled by your filter bank, allowing the NN to focus on pattern recognition and temporal modeling.

The input to the neural network for a single inference will be a 2D matrix of **num\_samples\_per\_block (256) time steps by num\_filters (288) features**, representing the filter outputs for that specific 256-sample block.  
It is imperative to **normalize** these filter outputs before feeding them into the neural network to ensure stable and efficient training. Common normalization techniques include min-max scaling (e.g., to a range like \`\`) or Z-score normalization (mean 0, standard deviation 1).  
For each inference call, the input to the neural network will have a shape of (batch\_size, 256, 288, 1\) (adding a channel dimension for 2D CNNs), where batch\_size will typically be 1 for real-time inference. The crucial aspect of maintaining temporal context across these individual blocks will be handled by the internal state of the recurrent neural network (RNN), which is designed to carry information from one time step (block) to the next.

## **3\. Proposed Neural Network Architectures**

Here, we propose two distinct neural network architectures, both designed to process your (256, 288\) filter bank input per audio block and provide real-time MIDI note predictions.

### **Why 2D CNNs are Ideal for Your Input**

Given your input for each 256-sample block is a (256, 288\) matrix, where the first dimension represents time steps and the second represents your organized filter outputs (pitch/harmonic content), **2D Convolutional Neural Networks (CNNs) are highly suitable and advantageous** for processing this data.

* **Treating Input as a "Time-Frequency-like Image":** This (256, 288\) matrix can be effectively treated as a single-channel "image." The 2D CNN can then apply its kernels to learn patterns that span across *both* time (within the 256-sample block) and your specialized filter features simultaneously.  
* **Capturing Intra-Block Temporal Patterns:** Convolutions along the 256-sample (time) axis will effectively capture short-term temporal dynamics within the block, such as note onsets, rapid decays, or vibrato.  
* **Learning Spectral/Harmonic Relationships:** This is where 2D CNNs offer a significant advantage. Since your 288 filters are organized to group fundamentals with their overtones (e.g., S1F0\_F0, S1F0\_2F0, S1F0\_3F0, S1F0\_4F0), a 2D convolutional kernel can learn to recognize the **characteristic "vertical" patterns** of a fundamental and its active harmonics. This is vital for confirming a note's presence and suppressing spurious overtone detections. 13  
* **Hierarchical Feature Extraction:** By stacking multiple 2D convolutional layers, the network can learn increasingly abstract and complex features. Initial layers might detect simple harmonic patterns, while deeper layers could combine these to recognize full chords or complex polyphonic interactions.

### **3.1. Architecture 1: Pure CNN Solution**

This architecture relies solely on 2D Convolutional Neural Networks (CNNs) to extract features and make predictions. It processes each (256, 288\) block independently, meaning it does not explicitly maintain memory across different audio blocks. Its strength lies in efficiently capturing intra-block temporal patterns and feature interactions.

* **Input Layer:** The input to the CNN block will be the (256, 288\) filter outputs for the current block, with an added channel dimension, resulting in a shape of (batch\_size, 256, 288, 1).  
* **2D Convolutional Layers:** Multiple sequential 2D convolutional layers will extract hierarchical temporal and spectral features. Each Conv2D layer will be followed by BatchNormalization and a ReLU activation function. MaxPooling2D layers will periodically reduce both the temporal and filter dimensions.  
  * These layers learn localized patterns across the 256 samples within the block and across the 288 filter outputs.  
* **Global Pooling Layer:** After the final convolutional layer, a GlobalAveragePooling2D or GlobalMaxPooling2D layer will reduce the entire 2D feature map into a single feature vector for the current 256-sample block. This condenses all the learned intra-block temporal and spectral information.  
* **Output Layer:** A final Dense layer with 88 units and a Sigmoid activation function will output the independent probabilities for each MIDI note.

**Python Code for Pure CNN Architecture (using Keras/TensorFlow):**

Python

import tensorflow as tf  
from tensorflow.keras import layers, models, optimizers  
import numpy as np

\# \--- Configuration \---  
INPUT\_SHAPE \= (256, 288, 1\)  \# (time\_steps\_per\_block, num\_filters\_including\_overtones, channels)  
OUTPUT\_DIM \= 88              \# Number of MIDI notes (A0 to C8)  
LEARNING\_RATE \= 0.001  
BATCH\_SIZE \= 32              \# For training; for inference, batch\_size=1  
EPOCHS \= 10                  \# Example, adjust based on dataset size and convergence

\# \--- 1\. Define the Pure CNN Model \---  
def build\_cnn\_model(input\_shape, output\_dim):  
    model \= models.Sequential()  
      
    \# Input Layer  
    model.add(layers.Input(shape=input\_shape))

    \# 2D CNN Block 1  
    model.add(layers.Conv2D(filters=64, kernel\_size=(3, 3), padding='same', activation='relu'))  
    model.add(layers.BatchNormalization())  
    model.add(layers.MaxPooling2D(pool\_size=(2, 2), strides=(2, 2))) \# Output shape: (128, 144, 64\)

    \# 2D CNN Block 2  
    model.add(layers.Conv2D(filters=128, kernel\_size=(3, 3), padding='same', activation='relu'))  
    model.add(layers.BatchNormalization())  
    model.add(layers.MaxPooling2D(pool\_size=(2, 2), strides=(2, 2))) \# Output shape: (64, 72, 128\)

    \# 2D CNN Block 3  
    model.add(layers.Conv2D(filters=256, kernel\_size=(3, 3), padding='same', activation='relu'))  
    model.add(layers.BatchNormalization())  
    model.add(layers.MaxPooling2D(pool\_size=(2, 2), strides=(2, 2))) \# Output shape: (32, 36, 256\)

    \# Global Pooling to condense intra-block temporal and spectral information  
    model.add(layers.GlobalAveragePooling2D()) \# Output shape: (256,)

    \# Output Layer for 88 MIDI notes (multi-label classification)  
    model.add(layers.Dense(output\_dim, activation='sigmoid'))

    return model

\# \--- 2\. Compile the Model \---  
cnn\_model \= build\_cnn\_model(INPUT\_SHAPE, OUTPUT\_DIM)  
cnn\_model.compile(optimizer=optimizers.Adam(learning\_rate=LEARNING\_RATE),  
                  loss='binary\_crossentropy', \# BCE for multi-label classification  
                  metrics=\['accuracy'\])

cnn\_model.summary()

\# \--- 3\. Placeholder for Data Generation (Replace with your actual data loading) \---  
\# In a real scenario, X\_train would be a NumPy array of shape (num\_samples, 256, 288, 1\)  
\# and y\_train would be (num\_samples, 88\)  
num\_training\_samples \= 1000  
X\_train\_cnn \= np.random.rand(num\_training\_samples, \*INPUT\_SHAPE).astype(np.float32)  
y\_train\_cnn \= np.random.randint(0, 2, size=(num\_training\_samples, OUTPUT\_DIM)).astype(np.float32)

\# Normalize inputs (example: min-max scaling if values are 0-1, or Z-score if needed)  
\# X\_train\_cnn \= (X\_train\_cnn \- X\_train\_cnn.min()) / (X\_train\_cnn.max() \- X\_train\_cnn.min())

\# \--- 4\. Training the Model \---  
print("\\n--- Training Pure CNN Model \---")  
history\_cnn \= cnn\_model.fit(X\_train\_cnn, y\_train\_cnn,  
                            batch\_size=BATCH\_SIZE,  
                            epochs=EPOCHS,  
                            validation\_split=0.2, \# Use a portion of data for validation  
                            verbose=1)

\# \--- 5\. Real-time Inference Example (per block) \---  
print("\\n--- Pure CNN Real-time Inference Example \---")  
\# Simulate a single 256-sample block of filter outputs  
single\_block\_input \= np.random.rand(1, \*INPUT\_SHAPE).astype(np.float32)  
\# Normalize if training data was normalized  
\# single\_block\_input \= (single\_block\_input \- X\_train\_cnn.min()) / (X\_train\_cnn.max() \- X\_train\_cnn.min())

\# Perform inference  
predictions\_cnn \= cnn\_model.predict(single\_block\_input, verbose=0)  
print(f"Predicted probabilities for 88 MIDI notes (first 5): {predictions\_cnn\[0, :5\]}")  
\# Apply a threshold to get binary predictions (e.g., 0.5)  
binary\_predictions\_cnn \= (predictions\_cnn \> 0.5).astype(int)  
print(f"Binary predictions (first 5): {binary\_predictions\_cnn\[0, :5\]}")

### **3.2. Architecture 2: Hybrid CNN-RNN Solution**

This architecture combines the strengths of 2D CNNs for intra-block feature extraction with RNNs for inter-block temporal modeling. This is generally the more robust approach for time-series data like audio, as it allows the network to "remember" context from previous audio blocks, which is crucial for tracking sustained notes, vibrato, and complex melodic/harmonic progressions across block boundaries.

* **Input Layer:** The input for each inference call will be the (256, 288\) filter outputs for the current block, with an added channel dimension, resulting in a shape of (batch\_size, 256, 288, 1).  
* **2D Convolutional Layers (CNN Block):** Similar to the pure CNN model, these layers will extract hierarchical temporal and spectral features *within* each 256-sample block. They will be followed by BatchNormalization and ReLU activations, and MaxPooling2D layers for downsampling.  
* **Global Pooling Layer:** After the final convolutional layer, a GlobalAveragePooling2D or GlobalMaxPooling2D layer will condense the intra-block information into a single feature vector. This vector represents the learned features for the current 256-sample block.  
* **Recurrent Layers (RNN Block):** The condensed feature vector from the CNN block will be fed into a Bidirectional LSTM or Bidirectional GRU layer. These layers are crucial for maintaining memory across successive audio blocks.  
  * **Stateful RNN:** For real-time processing, the RNN layer will be configured as stateful=True. This means its internal hidden state and cell state (for LSTM) are preserved and passed from one inference call (one block) to the next. This allows the network to build a long-term understanding of the musical context.  
  * **State Management:** During real-time inference, you must explicitly manage these states: initialize them at the beginning of a new sequence (e.g., when a new song starts or after a long silence) and pass the updated states from the previous inference step to the current one.  
* **Output Layer:** A final Dense layer with 88 units and a Sigmoid activation function will output the independent probabilities for each MIDI note.

**Python Code for Hybrid CNN-RNN Architecture (using Keras/TensorFlow):**

Python

import tensorflow as tf  
from tensorflow.keras import layers, models, optimizers  
import numpy as np

\# \--- Configuration \---  
INPUT\_SHAPE \= (256, 288, 1\)  \# (time\_steps\_per\_block, num\_filters\_including\_overtones, channels)  
OUTPUT\_DIM \= 88              \# Number of MIDI notes (A0 to C8)  
LEARNING\_RATE \= 0.001  
BATCH\_SIZE \= 1               \# Crucial for stateful RNN in real-time inference  
EPOCHS \= 10                  \# Example, adjust based on dataset size and convergence

\# \--- 1\. Define the Hybrid CNN-RNN Model \---  
def build\_cnn\_rnn\_model(input\_shape, output\_dim, rnn\_units=256, stateful=False):  
    \# Input for a single block  
    inputs \= layers.Input(batch\_shape=(BATCH\_SIZE, \*input\_shape))

    \# 2D CNN Block 1  
    x \= layers.Conv2D(filters=64, kernel\_size=(3, 3), padding='same', activation='relu')(inputs)  
    x \= layers.BatchNormalization()(x)  
    x \= layers.MaxPooling2D(pool\_size=(2, 2), strides=(2, 2))(x) \# Output shape: (128, 144, 64\)

    \# 2D CNN Block 2  
    x \= layers.Conv2D(filters=128, kernel\_size=(3, 3), padding='same', activation='relu')(x)  
    x \= layers.BatchNormalization()(x)  
    x \= layers.MaxPooling2D(pool\_size=(2, 2), strides=(2, 2))(x) \# Output shape: (64, 72, 128\)

    \# 2D CNN Block 3  
    x \= layers.Conv2D(filters=256, kernel\_size=(3, 3), padding='same', activation='relu')(x)  
    x \= layers.BatchNormalization()(x)  
    x \= layers.MaxPooling2D(pool\_size=(2, 2), strides=(2, 2))(x) \# Output shape: (32, 36, 256\)

    \# Global Pooling to condense intra-block temporal and spectral information  
    x \= layers.GlobalAveragePooling2D()(x) \# Output shape: (256,)

    \# Reshape for RNN: (batch\_size, 1, features) as RNN expects a sequence  
    \# Even though it's one block, it's one step in the sequence of blocks  
    x \= layers.Reshape((1, x.shape\[-1\]))(x)

    \# Bidirectional GRU/LSTM Layer (stateful for real-time context)  
    \# GRU is often preferred for real-time due to lower computational cost \[15, 16\]  
    rnn\_output \= layers.Bidirectional(  
        layers.GRU(rnn\_units, return\_sequences=False, stateful=stateful)  
    )(x)  
    rnn\_output \= layers.Dropout(0.3)(rnn\_output) \# Regularization

    \# Optional Dense Layer  
    x \= layers.Dense(256, activation='relu')(rnn\_output)  
    x \= layers.Dropout(0.3)(x) \# Regularization

    \# Output Layer for 88 MIDI notes (multi-label classification)  
    outputs \= layers.Dense(output\_dim, activation='sigmoid')(x)

    model \= models.Model(inputs=inputs, outputs=outputs)  
    return model

\# \--- 2\. Compile the Model \---  
\# For training, stateful=False is often easier for shuffled batches.  
\# For real-time inference, you'd load a model trained with stateful=True or manage states manually.  
cnn\_rnn\_model\_train \= build\_cnn\_rnn\_model(INPUT\_SHAPE, OUTPUT\_DIM, stateful=False)  
cnn\_rnn\_model\_train.compile(optimizer=optimizers.Adam(learning\_rate=LEARNING\_RATE),  
                            loss='binary\_crossentropy',  
                            metrics=\['accuracy'\])

cnn\_rnn\_model\_train.summary()

\# \--- 3\. Placeholder for Data Generation (Replace with your actual data loading) \---  
\# For training, you'd typically have longer sequences or many independent blocks.  
\# If training with stateful=True, sequences must not be shuffled and batch\_size must be fixed.  
num\_training\_sequences \= 100 \# Number of "songs" or long audio segments  
sequence\_length\_blocks \= 50  \# Each sequence is 50 blocks long  
total\_blocks \= num\_training\_sequences \* sequence\_length\_blocks

X\_train\_cnn\_rnn \= np.random.rand(total\_blocks, \*INPUT\_SHAPE).astype(np.float32)  
y\_train\_cnn\_rnn \= np.random.randint(0, 2, size=(total\_blocks, OUTPUT\_DIM)).astype(np.float32)

\# Normalize inputs (example: min-max scaling if values are 0-1, or Z-score if needed)  
\# X\_train\_cnn\_rnn \= (X\_train\_cnn\_rnn \- X\_train\_cnn\_rnn.min()) / (X\_train\_cnn\_rnn.max() \- X\_train\_cnn\_rnn.min())

\# \--- 4\. Training the Model \---  
print("\\n--- Training Hybrid CNN-RNN Model \---")  
\# For stateful training, you'd typically train on sequences and reset states after each sequence.  
\# For simplicity in this example, we'll train stateless, but note the real-time inference implications.  
history\_cnn\_rnn \= cnn\_rnn\_model\_train.fit(X\_train\_cnn\_rnn, y\_train\_cnn\_rnn,  
                                          batch\_size=BATCH\_SIZE, \# Batch size 1 for training if stateful=True  
                                          epochs=EPOCHS,  
                                          validation\_split=0.2,  
                                          verbose=1)

\# \--- 5\. Real-time Inference Example (per block with state management) \---  
print("\\n--- Hybrid CNN-RNN Real-time Inference Example \---")

\# To perform stateful inference, you need to build a stateful model  
\# and manage its states. This is often done by creating a separate inference model  
\# or by using the functional API and explicitly passing states.  
\# For simplicity, we'll demonstrate using a stateful model.  
\# In a real plugin, you'd load the trained weights into this stateful model.

\# Build a stateful model for inference (batch\_size=1 is typical for real-time)  
cnn\_rnn\_model\_inference \= build\_cnn\_rnn\_model(INPUT\_SHAPE, OUTPUT\_DIM, stateful=True)  
\# Copy weights from the trained model  
cnn\_rnn\_model\_inference.set\_weights(cnn\_rnn\_model\_train.get\_weights())

\# Simulate a sequence of blocks (e.g., a short musical phrase)  
num\_inference\_blocks \= 5  
inference\_sequence \= np.random.rand(num\_inference\_blocks, \*INPUT\_SHAPE).astype(np.float32)

print("Processing inference sequence block by block:")  
for i in range(num\_inference\_blocks):  
    current\_block\_input \= inference\_sequence\[i:i+1, :, :, :\] \# Take one block, maintain (1, 256, 288, 1\) shape  
      
    \# Perform inference  
    predictions\_rnn \= cnn\_rnn\_model\_inference.predict(current\_block\_input, verbose=0)  
      
    print(f"Block {i+1}: Predicted probabilities (first 5): {predictions\_rnn\[0, :5\]}")  
    \# Apply a threshold to get binary predictions  
    binary\_predictions\_rnn \= (predictions\_rnn \> 0.5).astype(int)  
    print(f"Block {i+1}: Binary predictions (first 5): {binary\_predictions\_rnn\[0, :5\]}")

\# After a sequence (e.g., a song ends, or a long silence), reset the RNN states  
cnn\_rnn\_model\_inference.reset\_states()  
print("\\nRNN states reset after sequence.")

## **4\. Training Considerations**

The effective training of the proposed neural network architectures for polyphonic pitch detection necessitates careful consideration of the loss function, optimizer, and data augmentation strategies.

### **Loss Function**

Given that polyphonic pitch detection is formulated as a multi-label classification problem, where multiple notes can be active simultaneously, the **Binary Cross-Entropy (BCE) loss function** is the appropriate choice.6 Unlike softmax cross-entropy, which is suitable for single-label classification where classes are mutually exclusive, BCE treats each of the 88 MIDI note predictions as an independent binary classification task. For each output neuron, BCE measures the dissimilarity between the predicted probability (output by the sigmoid activation) and the true binary label (0 or 1, indicating absence or presence of the note). While BCE is well-suited for this decomposition, it can face challenges related to class imbalance, particularly when some notes are significantly more common than others in the training data.7 Advanced variants of BCE, such as weighted BCE or focal loss, can be explored to mitigate these imbalance issues. 17

### **Optimizer**

The **Adam (Adaptive Moment Estimation) optimizer** is highly recommended for training this deep neural network.13 Adam is an adaptive learning rate algorithm that computes individual adaptive learning rates for different parameters, thereby improving training speeds and accelerating convergence.13 It combines the benefits of two other popular optimization algorithms: Momentum (which accelerates convergence in consistent directions) and RMSProp (which controls overshooting by modulating step size based on squared gradients).13 Adam maintains exponentially decaying moving averages of the gradients (first moment) and the squared gradients (second moment) for each parameter, using these to adaptively adjust the learning rate during training.14  
Typical hyperparameters for the Adam optimizer include:

* **α (Learning Rate):** Often initialized at 0.001.14 While Adam adapts learning rates, a reasonable initial value is still essential.  
* **β₁ (Decay rate for momentum):** A typical value is 0.9, giving high weighting to the most recent gradients.13  
* **β₂ (Decay rate for squared gradients):** A typical value is 0.999, capturing long-term memory of gradients for a stable variance estimate.13  
* **ϵ (Epsilon):** A small constant, usually around 1e-8, added for numerical stability to prevent division by zero.13

### **Data Augmentation**

A significant limitation in multi-pitch estimation, particularly for polyphonic music, is the "shortage of large-scale and diverse polyphonic music datasets with multi-pitch annotations".2 To address this data scarcity and enhance the model's robustness and generalization capabilities, **audio data augmentation** is an essential technique.19 Data augmentation involves modifying existing audio samples to create new training data, expanding the coverage of the problem space and making models robust to variations encountered in real-world conditions.19  
It is crucial to apply these augmentation techniques to the **raw audio signal *before*** it is fed into your Butterworth filter bank. This ensures that the filter outputs reflect the augmented audio, allowing the neural network to learn from a wider variety of realistic input conditions.  
Common and effective audio augmentation techniques include:

* **Pitch Shifting:** Altering the pitch of an audio signal without changing its duration. This can simulate different musical keys or variations in instrument tuning.19  
* **Time Stretching:** Adjusting the duration of an audio signal while maintaining its pitch. This mimics variations in tempo or performance speed.19  
* **Speed Perturbation:** Changing the speed of an audio signal by resampling it at a different sample rate, which can simulate variations in playing speed.20  
* **Amplitude Scaling:** Adjusting the overall volume of an audio signal to simulate different recording levels or dynamic variations.20  
* **Noise Injection:** Adding background sounds like street noise, static, or room reverb to simulate real-world acoustic environments and improve robustness to noise.19  
* **SpecAugment:** A method that masks parts of a spectrogram (frequency or time blocks) to force models to focus on broader patterns rather than fixed features, reducing overfitting.19 (While your input isn't a spectrogram, similar masking concepts could potentially be applied to blocks of your 288 filter outputs if carefully designed).

These transformations expand the dataset, making models more robust to variations they might encounter in production. Implementing audio augmentation typically involves libraries like Librosa, TorchAudio, or TensorFlow Signal.19 It is crucial to balance augmentation intensity, as excessive transformation can distort the audio beyond realistic scenarios and reduce credibility.19

## **5\. Latency Considerations for Real-time Inference**

The requirement for **real-time output** is a critical design constraint for your plugin. Latency in audio processing refers to the delay between an audio signal entering a system and its corresponding output. For a musical instrument plugin, low latency is crucial for a natural and responsive playing experience.

### **Inherent Block Latency**

Your system processes audio in **256-sample blocks at a 48kHz sample rate**. This inherently introduces a minimum buffer latency, as the system must collect a full block of samples before processing can begin.

* **Block Duration:** 256 samples / 48,000 samples/second \= 0.00533 seconds, or approximately **5.33 milliseconds (ms)**. 22

  This 5.33ms is the fundamental delay introduced by the block-based processing, even before any neural network computation. The goal for real-time performance is to ensure that the neural network's inference time does not add significantly to this inherent buffer latency.

### **RNN and Neural Network Inference Latency**

The RNN itself, and the preceding CNN layers, introduce computational latency, which is the time it takes for the network to perform its calculations for a given input block.

* **Sequential Processing:** Recurrent Neural Networks (RNNs), including LSTMs and GRUs, are designed to process sequential data by maintaining an internal memory state that is updated with each new input (in your case, each 256-sample block). This sequential nature means that the output for the current block depends on the current input and the state derived from all *previous* blocks.  
* **No *Additional* Buffer Lag from RNN:** The RNN does not introduce an *additional* buffering delay beyond the 256-sample block itself, provided its computation for that block completes within the 5.33ms window. The latency contribution of the RNN is solely its **inference computation time** for that single block. If the network's computation for a block takes longer than 5.33ms, it will cause the audio processing chain to fall behind, leading to audible glitches, dropouts, or increased perceived latency.  
* **Factors Influencing Inference Latency:**  
  * **Model Complexity:** The number of layers (CNN and RNN), the number of filters in CNN layers, and the number of recurrent units (e.g., 256 units) directly impact the number of computations and parameters. More complex models generally lead to higher latency.  
  * **Choice of RNN Cell:** Gated Recurrent Units (GRUs) are generally considered **more computationally efficient and faster to train and infer** than Long Short-Term Memory (LSTM) networks due to their simpler internal structure and fewer parameters (two gates vs. three for LSTMs). For real-time applications with strict latency requirements, GRUs are often preferred if they achieve comparable performance.  
  * **Hardware:** Inference speed is heavily dependent on the processing hardware (CPU vs. GPU). For LV2 plugins, inference typically runs on the CPU. Optimized hardware accelerators exist for RNNs, capable of sub-millisecond latency, but these are specialized solutions not typically found in standard plugin environments. 24  
  * **Inference Engine Optimization:** Deploying the trained neural network using highly optimized inference engines (e.g., ONNX Runtime, TensorFlow Lite) in C++ can significantly reduce the computational overhead compared to running directly within a full deep learning framework.  
  * **Batch Size:** For real-time audio, the batch size is typically 1\. While larger batch sizes can sometimes improve throughput (samples processed per second), a batch size of 1 is necessary for minimal latency per block.

### **Quantifying Latency Contribution**

It is challenging to provide an exact millisecond figure for the RNN's latency contribution without knowing the precise model size, specific hardware, and level of optimization. However, for a responsive musical experience, total latency (including audio interface, buffer, and plugin processing) should ideally be **below 10ms**, with **sub-3ms often considered imperceptible** by human perception. 21  
To achieve real-time performance, the combined inference time of your CNN and RNN for each 256-sample block **must be significantly less than 5.33ms**. This allows the plugin to process the audio block and generate its MIDI output before the next audio block is ready, preventing any additional delay. Choosing GRUs over LSTMs, keeping the network architecture as lean as possible while maintaining accuracy, and employing highly optimized inference code are crucial steps to minimize this computational latency.

## **5\. Conclusion**

The proposed neural network architectures for polyphonic guitar pitch detection integrate either a pure Convolutional Neural Network (CNN) or a hybrid CNN-RNN design, meticulously tailored to leverage your plugin's unique feature extraction and the per-block, real-time inference requirement. The direct input of a **(256, 288\) matrix of Butterworth filter outputs (including fundamental and three overtone filters per fret/string)** for each audio block serves as a powerful, pre-engineered feature set, eliminating the need for the neural network to learn basic frequency decomposition.  
The pure CNN architecture efficiently extracts hierarchical temporal and spectral patterns *within* each 256-sample block using **2D CNN layers**, condensing this information into a single feature vector for immediate prediction. The hybrid CNN-RNN approach extends this by using 2D CNN layers for intra-block feature extraction, followed by a Global Pooling layer, and then feeding into **Bidirectional LSTM or GRU layers**. These recurrent layers are critical for modeling the long-term temporal dependencies inherent in musical sequences by maintaining and updating their internal states across successive audio blocks. This enables the network to understand how pitches evolve and interact over time, even when processing one block at a time. Both architectures explicitly frame polyphonic pitch detection as a multi-label classification problem, employing 88 independent sigmoid output units, each corresponding to a standard MIDI note. This design directly addresses the challenge of simultaneous note occurrences and complex harmonic interactions, enabling the model to predict the presence of multiple pitches concurrently. The use of Binary Cross-Entropy loss and the Adam optimizer further supports this multi-label framework and ensures efficient training.  
Finally, the emphasis on data augmentation, applied to the raw audio *before* filter processing, is paramount, particularly given the scarcity of large-scale annotated polyphonic datasets. Techniques like pitch shifting, time stretching, and noise injection are essential for enhancing the model's robustness and generalization capabilities to real-world guitar performances. This comprehensive architectural design, coupled with appropriate training strategies, provides a robust framework for advancing the state-of-the-art in automatic polyphonic guitar transcription using your specific filter bank outputs and adhering to the per-block, real-time inference constraint.

#### **Referenzen**

1. Toward Fully Self-Supervised Multi-Pitch Estimation \- arXiv, Zugriff am Juni 8, 2025, [https://arxiv.org/html/2402.15569v1](https://arxiv.org/html/2402.15569v1)  
2. Automatic Music Transcription using Convolutional Neural Networks and Constant-Q transform \- arXiv, Zugriff am Juni 8, 2025, [https://arxiv.org/html/2505.04451v1](https://arxiv.org/html/2505.04451v1)  
3. Pitch Contour Exploration Across Audio Domains: A Vision-Based Transfer Learning Approach \- arXiv, Zugriff am Juni 8, 2025, [https://arxiv.org/html/2503.19161](https://arxiv.org/html/2503.19161)  
4. Music Genre Classification using Convolutional Recurrent Neural Networks | Request PDF, Zugriff am Juni 8, 2025, [https://www.researchgate.net/publication/366892015\_Music\_Genre\_Classification\_using\_Convolutional\_Recurrent\_Neural\_Networks](https://www.researchgate.net/publication/366892015_Music_Genre_Classification_using_Convolutional_Recurrent_Neural_Networks)  
5. Multi-label Prediction in Time Series Data using Deep Neural Networks \- Mitsubishi Electric Research Laboratories, Zugriff am Juni 8, 2025, [https://www.merl.com/publications/docs/TR2019-110.pdf](https://www.merl.com/publications/docs/TR2019-110.pdf)  
6. MULTI-LABEL TEMPORAL EVIDENTIAL NEURAL NETWORKS FOR EARLY EVENT DETECTION, Zugriff am Juni 8, 2025, [https://par.nsf.gov/servlets/purl/10443288](https://par.nsf.gov/servlets/purl/10443288)  
7. Two-Way Multi-Label Loss | Papers With Code, Zugriff am Juni 8, 2025, [https://paperswithcode.com/paper/two-way-multi-label-loss](https://paperswithcode.com/paper/two-way-multi-label-loss)  
8. Two-way Multi-Label Loss \- Takumi Kobayashi \- CVF Open Access, Zugriff am Juni 8, 2025, [https://openaccess.thecvf.com/content/CVPR2023/papers/Kobayashi\_Two-Way\_Multi-Label\_Loss\_CVPR\_2023\_paper.pdf](https://openaccess.thecvf.com/content/CVPR2023/papers/Kobayashi_Two-Way_Multi-Label_Loss_CVPR_2023_paper.pdf)  
9. Electric Guitar Playing Style Feature Fusion Using Filter Banks | PDF \- Scribd, Zugriff am Juni 8, 2025, [https://fr.scribd.com/document/719334854/Electric-Guitar-Playing-Style-Feature-fusion-using-Filter-Banks](https://fr.scribd.com/document/719334854/Electric-Guitar-Playing-Style-Feature-fusion-using-Filter-Banks)  
10. Filter Banks and Deep Neural Networks for Portable and Fast Brain-Computer Interfaces \- arXiv, Zugriff am Juni 8, 2025, [https://arxiv.org/pdf/2109.02165](https://arxiv.org/pdf/2109.02165)  
11. Intelligent Guitar Chord Recognition Using Spectrogram-Based Feature Extraction and AlexNet Architecture for Categorization \- The Science and Information (SAI) Organization, Zugriff am Juni 8, 2025, [https://thesai.org/Downloads/Volume16No4/Paper\_75-Intelligent\_Guitar\_Chord\_Recognition.pdf](https://thesai.org/Downloads/Volume16No4/Paper_75-Intelligent_Guitar_Chord_Recognition.pdf)  
12. Masked Conditional Neural Networks for Sound Recognition \- White Rose eTheses Online, Zugriff am Juni 8, 2025, [https://etheses.whiterose.ac.uk/id/eprint/21594/1/Masked%20Conditional%20Neural%20Networks%20for%20Sound%20Recognition.pdf](https://etheses.whiterose.ac.uk/id/eprint/21594/1/Masked%20Conditional%20Neural%20Networks%20for%20Sound%20Recognition.pdf)  
13. Complete Guide to the Adam Optimization Algorithm | Built In, Zugriff am Juni 8, 2025, [https://builtin.com/machine-learning/adam-optimization](https://builtin.com/machine-learning/adam-optimization)  
14. What is Adam Optimizer? \- Analytics Vidhya, Zugriff am Juni 8, 2025, [https://www.analyticsvidhya.com/blog/2023/09/what-is-adam-optimizer/](https://www.analyticsvidhya.com/blog/2023/09/what-is-adam-optimizer/)  
15. When to Use GRUs Over LSTMs? \- Analytics Vidhya, Zugriff am Juni 8, 2025, [https://www.analyticsvidhya.com/blog/2025/03/lstms-and-grus/](https://www.analyticsvidhya.com/blog/2025/03/lstms-and-grus/)  
16. LSTM Vs GRU: Which Is Better For Sequence Processing? \- AI, Zugriff am Juni 8, 2025, [https://aicompetence.org/lstm-vs-gru-sequence-processing/](https://aicompetence.org/lstm-vs-gru-sequence-processing/)  
17. Tutorial on RNN | LSTM: With Implementation \- Analytics Vidhya, Zugriff am Juni 8, 2025, [https://www.analyticsvidhya.com/blog/2022/01/tutorial-on-rnn-lstm-gru-with-implementation/](https://www.analyticsvidhya.com/blog/2022/01/tutorial-on-rnn-lstm-gru-with-implementation/)  
18. Best explanations of RNN LSTM | GRU \- Kaggle, Zugriff am Juni 8, 2025, [https://www.kaggle.com/code/habibmrad1983/best-explanations-of-rnn-lstm-gru](https://www.kaggle.com/code/habibmrad1983/best-explanations-of-rnn-lstm-gru)  
19. How does data augmentation work for audio data? \- Milvus, Zugriff am Juni 8, 2025, [https://milvus.io/ai-quick-reference/how-does-data-augmentation-work-for-audio-data](https://milvus.io/ai-quick-reference/how-does-data-augmentation-work-for-audio-data)  
20. Enhance Your Models with Audio Data Augmentation \- Toolify.ai, Zugriff am Juni 8, 2025, [https://www.toolify.ai/ai-news/enhance-your-models-with-audio-data-augmentation-2309512](https://www.toolify.ai/ai-news/enhance-your-models-with-audio-data-augmentation-2309512)  
21. Audio latency, buffer size and sample rate explained \- Gig Performer®, Zugriff am Juni 8, 2025, [https://gigperformer.com/audio-latency-buffer-size-and-sample-rate-explained](https://gigperformer.com/audio-latency-buffer-size-and-sample-rate-explained)  
22. TorchDrum \- Jordie Shier, Zugriff am Juni 8, 2025, [https://jordieshier.com/adc2024/](https://jordieshier.com/adc2024/)  
23. Neural DSP Latency issues? : r/NeuralDSP \- Reddit, Zugriff am Juni 8, 2025, [https://www.reddit.com/r/NeuralDSP/comments/10qjazp/neural\_dsp\_latency\_issues/](https://www.reddit.com/r/NeuralDSP/comments/10qjazp/neural_dsp_latency_issues/)  
24. EdgeDRNN: Enabling Low-latency Recurrent Neural Network Edge Inference \- CORE, Zugriff am Juni 8, 2025, [https://core.ac.uk/outputs/395077852/?source=2](https://core.ac.uk/outputs/395077852/?source=2)