# GuitarMidi-LV2 Library
 # Copyright (C) 2026 Gerald Mwangi
 #
 # This program is free software; you can redistribute it and/or
 # modify it under the terms of the GNU Lesser General Public
 # License as published by the Free Software Foundation; either
 # version 2 of the License, or (at your option) any later version.
 #
 # This program is distributed in the hope that it will be useful,
 # but WITHOUT ANY WARRANTY; without even the implied warranty of
 # MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
 # Lesser General Public License for more details.
 #
 # You should have received a copy of the GNU Lesser General
 # Public License along with this program; if not, write to the
 # Free Software Foundation, Inc., 51 Franklin Street, Fifth Floor,
 # Boston, MA  02110-1301  USA
import tensorflow as tf
from tensorflow import keras
import numpy as np
import datetime
from model import build_cnn_model
from common import INPUT_SHAPE, OUTPUT_DIM_NOTES
import os
# ============================================================================
# PART 1: VISUALIZE MODEL ARCHITECTURE
# ============================================================================

def visualize_model_architecture():
    """
    Creates model graph and architecture visualization in TensorBoard
    """
    # Build the model
    model = build_cnn_model(INPUT_SHAPE, OUTPUT_DIM_NOTES, training=True)
    
    # Create a log directory with timestamp
    log_dir = "logs/model_architecture/" + datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    os.makedirs(log_dir, exist_ok=True)
    
    # Create TensorBoard callback for graph visualization
    tensorboard_callback = keras.callbacks.TensorBoard(
        log_dir=log_dir,
        histogram_freq=0,
        write_graph=True,
        write_images=False,
        update_freq='epoch',
        profile_batch=0
    )
    
    # Create dummy data to build the graph
    dummy_input = np.random.random((1,) + INPUT_SHAPE).astype(np.float32)
    
    # Build the model with the input shape
    model(dummy_input)
    
    # Save model summary to text file
    with open(f'{log_dir}/model_summary.txt', 'w') as f:
        model.summary(print_fn=lambda x: f.write(x + '\n'))
    
    # Write the graph
    writer = tf.summary.create_file_writer(log_dir)
    with writer.as_default():
        tf.summary.graph(tf.function(lambda x: model(x)).get_concrete_function(
            tf.TensorSpec(shape=(None,) + INPUT_SHAPE, dtype=tf.float32)
        ).graph)
    writer.close()
    
    print(f"Model architecture saved to: {log_dir}")
    print(f"Run: tensorboard --logdir={log_dir}")
    
    return model, log_dir


# ============================================================================
# PART 2: VISUALIZE LAYER ACTIVATIONS
# ============================================================================

def visualize_layer_activations(model, input_sample, log_dir=None):
    """
    Visualizes activations of each layer for a specific input
    
    Args:
        model: Trained Keras model
        input_sample: Input data (should be shape (1, time_steps, num_filters, 1))
        log_dir: Directory to save logs (creates new one if None)
    """
    if log_dir is None:
        log_dir = "logs/activations/" + datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    
    # Create activation model
    layer_outputs = [layer.output for layer in model.layers if len(layer.output.shape) > 1]
    layer_names = [layer.name for layer in model.layers if len(layer.output.shape) > 1]
    
    activation_model = keras.Model(inputs=model.input, outputs=layer_outputs)
    
    # Get activations
    activations = activation_model.predict(input_sample, verbose=0)
    
    # Write activations to TensorBoard
    writer = tf.summary.create_file_writer(log_dir + "/activations")
    
    with writer.as_default():
        for i, (activation, name) in enumerate(zip(activations, layer_names)):
            # For Conv2D layers, visualize filters
            if len(activation.shape) == 4:  # (batch, height, width, channels)
                # Take first sample from batch
                act = activation[0]
                
                # Visualize first 32 filters (or all if less than 32)
                num_filters = min(32, act.shape[-1])
                
                # Create a grid of activations
                for filter_idx in range(num_filters):
                    filter_activation = act[:, :, filter_idx]
                    # Normalize to [0, 1]
                    filter_activation = (filter_activation - filter_activation.min()) / (
                        filter_activation.max() - filter_activation.min() + 1e-8
                    )
                    # Add batch and channel dimensions for TensorBoard
                    filter_activation = filter_activation[np.newaxis, :, :, np.newaxis]
                    
                    tf.summary.image(
                        f"{name}/filter_{filter_idx}",
                        filter_activation,
                        step=0,
                        max_outputs=1
                    )
                
                # Also create a histogram of activation values
                tf.summary.histogram(f"{name}/activation_distribution", activation, step=0)
            
            elif len(activation.shape) == 2:  # Dense layer (batch, units)
                # Histogram for dense layers
                tf.summary.histogram(f"{name}/activation_distribution", activation, step=0)
    
    writer.close()
    print(f"Layer activations saved to: {log_dir}")
    print(f"Run: tensorboard --logdir={log_dir}")
    
    return activations


# ============================================================================
# PART 3: VISUALIZE TRAINING METRICS (if you have training history)
# ============================================================================

def setup_training_visualization(log_dir=None):
    """
    Returns TensorBoard callback for training visualization
    Use this during model.fit()
    """
    if log_dir is None:
        log_dir = "logs/training/" + datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    
    tensorboard_callback = keras.callbacks.TensorBoard(
        log_dir=log_dir,
        histogram_freq=1,  # Log weight histograms every epoch
        write_graph=True,
        write_images=True,
        update_freq='epoch',
        profile_batch='10,20',  # Profile batches 10-20 for performance analysis
        embeddings_freq=1
    )
    
    print(f"Training logs will be saved to: {log_dir}")
    print(f"Run: tensorboard --logdir={log_dir}")
    
    return tensorboard_callback


# ============================================================================
# PART 4: VISUALIZE PREDICTIONS
# ============================================================================

def visualize_predictions(predictions, ground_truth=None, log_dir=None):
    """
    Visualize model predictions in TensorBoard
    
    Args:
        predictions: Model output (OUTPUT_DIM_NOTES,)
        ground_truth: Ground truth labels if available
        log_dir: Directory to save logs
    """
    if log_dir is None:
        log_dir = "logs/predictions/" + datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    
    writer = tf.summary.create_file_writer(log_dir)
    
    with writer.as_default():
        # Create a bar chart of predictions
        for note_idx, prob in enumerate(predictions):
            tf.summary.scalar(f"note_{note_idx}_probability", prob, step=0)
        
        # If ground truth is available, log the comparison
        if ground_truth is not None:
            # Calculate metrics
            threshold = 0.5
            pred_binary = (predictions > threshold).astype(int)
            
            # Log confusion metrics
            true_positives = np.sum((pred_binary == 1) & (ground_truth == 1))
            false_positives = np.sum((pred_binary == 1) & (ground_truth == 0))
            false_negatives = np.sum((pred_binary == 0) & (ground_truth == 1))
            
            tf.summary.scalar("metrics/true_positives", true_positives, step=0)
            tf.summary.scalar("metrics/false_positives", false_positives, step=0)
            tf.summary.scalar("metrics/false_negatives", false_negatives, step=0)
    
    writer.close()
    print(f"Predictions saved to: {log_dir}")
    print(f"Run: tensorboard --logdir={log_dir}")


# ============================================================================
# MAIN EXECUTION
# ============================================================================

if __name__ == "__main__":
    print("=" * 80)
    print("TensorBoard Visualization for CNN Model")
    print("=" * 80)
    
    # Step 1: Visualize model architecture
    print("\n[1/4] Creating model architecture visualization...")
    model, arch_log_dir = visualize_model_architecture()
    
    # Step 2: Load your trained weights
    print("\n[2/4] Loading trained weights...")
    model.load_weights('checkpoints/guitarmidi_epoch13_valAcc0.5885.weights.h5')
    
    # Step 3: Prepare your input sample
    print("\n[3/4] Preparing input sample...")
    # Replace with your actual input preparation code
    # Example:
    # outsample = 2035
    # input_for_model = np.expand_dims(nn_input_test[int(outsample)], axis=0)
    # input_for_model = np.expand_dims(input_for_model, axis=-1)
    
    # For demonstration, create dummy input
    input_for_model = np.random.random((1,) + INPUT_SHAPE).astype(np.float32)
    
    # Step 4: Visualize layer activations
    print("\n[4/4] Visualizing layer activations...")
    activations = visualize_layer_activations(model, input_for_model)
    
    # Step 5: Get predictions and visualize
    print("\n[5/5] Visualizing predictions...")
    predictions = model.predict(input_for_model, verbose=0)
    visualize_predictions(predictions[0])
    
    print("\n" + "=" * 80)
    print("VISUALIZATION COMPLETE!")
    print("=" * 80)
    print("\nTo view all visualizations, run:")
    print("  tensorboard --logdir=logs")
    print("\nThen open your browser to: http://localhost:6006")
    print("\nIn TensorBoard, you can explore:")
    print("  - GRAPHS tab: Model architecture and computational graph")
    print("  - IMAGES tab: Layer activation visualizations")
    print("  - DISTRIBUTIONS/HISTOGRAMS tabs: Activation distributions")
    print("  - SCALARS tab: Prediction probabilities and metrics")
    print("=" * 80)


# ============================================================================
# INTEGRATION WITH YOUR EXISTING CODE
# ============================================================================

"""
To integrate with your existing code, add this after loading your model:

from model import build_cnn_model
from common import INPUT_SHAPE, OUTPUT_DIM_NOTES
import numpy as np

# Your existing code...
cnn_model = build_cnn_model(INPUT_SHAPE, OUTPUT_DIM_NOTES)
cnn_model.load_weights('checkpoints/guitarmidi_epoch13_valAcc0.5885.weights.h5')

# Prepare your input
input_for_model = np.expand_dims(nn_input_test[int(outsample)], axis=0)
input_for_model = np.expand_dims(input_for_model, axis=-1)

# Add TensorBoard visualization
import datetime
log_dir = "logs/" + datetime.datetime.now().strftime("%Y%m%d-%H%M%S")

# Visualize architecture
visualize_model_architecture()

# Visualize activations
visualize_layer_activations(cnn_model, input_for_model, log_dir)

# Get predictions
predictions_cnn = cnn_model.predict(input_for_model, verbose=0)

# Visualize predictions
visualize_predictions(predictions_cnn[0], log_dir=log_dir)

# Launch TensorBoard
print("Run: tensorboard --logdir=logs")
"""