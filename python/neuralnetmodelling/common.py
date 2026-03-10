import  os
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import tensorflow as tf
from fretboard import FretBoard,num_frets,num_strings,num_harmonics
from fretboardnonredundant import FretBoard
# Common parameters
frame_size=256
image_width = 256

SAMPLERATE=48000
fretboard=FretBoard(2,SAMPLERATE)
image_height = fretboard.get_num_filters() 
num_channels = 1
num_classes = 129 # For MIDI notes+silence class
INPUT_SHAPE = (image_height,image_width, num_channels)
INPUT_SHAPE_AUDIO = (1,image_width, num_channels)
OUTPUT_DIM_NOTES = num_classes # For notes output
OUTPUT_DIM_ONSETS = 1 # For onsets output

def fast_gpu_map(parsed,training=True):
# 1. Decoding and Basic Setup
    input_raw = tf.io.decode_raw(parsed["input"], tf.float32)
    label_raw = tf.io.decode_raw(parsed["output"], tf.int8)
    
    input_tensor = tf.reshape(input_raw, INPUT_SHAPE)
    input_tensor = tf.cast(input_tensor, tf.float32)
    
    output_tensor = tf.cast(tf.reshape(label_raw, [OUTPUT_DIM_NOTES]), tf.float32)
    
    # Constants for clarity
    SILENCE_IDX = OUTPUT_DIM_NOTES - 1
    silence_vector = tf.zeros_like(output_tensor)# tf.one_hot(SILENCE_IDX, depth=OUTPUT_DIM_NOTES, dtype=tf.float32)
    zero_input = tf.zeros_like(input_tensor)

    # 2. Extract Logic Components
    # Identify if any actual notes are active (indices 0 to 87)
    note_labels = output_tensor[:SILENCE_IDX]
    any_notes_active = tf.reduce_any(tf.greater(note_labels, 0.5))
    
    # Check current states
    silence_label_is_up = tf.greater(output_tensor[SILENCE_IDX], 0.5)
    max_en=tf.reduce_max(tf.abs(input_tensor)) 
    energy_is_low = max_en< 0.01
    # if ~energy_is_low:
    #     input_tensor/=max_en
    # 3. The "Vice Versa" Logic
    # We "Force Silence" if: 
    # - Energy is low OR 
    # - The silence label was already up OR 
    # - No notes are active
    should_force_silence = energy_is_low | silence_label_is_up | (~any_notes_active)

    # Apply transformations
    output_tensor = tf.where(should_force_silence, silence_vector, output_tensor)
    input_tensor = tf.where(should_force_silence, zero_input, input_tensor)



    return input_tensor, output_tensor

def parse_example(example_proto):
    return tf.io.parse_single_example(example_proto, feature_description)

def save_data_slices(output_dir,nn_slices,batch_size,filenum_offset=0):
    totalsamples=nn_slices.shape[0]
    filenum_offset=filenum_offset//frame_size
    # Create directories if they don't exist
    os.makedirs(output_dir, exist_ok=True)
    print(f'Saving {totalsamples} samples to disk with filenamuber offset {filenum_offset}...')
    for i in range(0,totalsamples,batch_size):
        current_in=None
        
        if (totalsamples-i)<batch_size:
            current_in=nn_slices[i:]
        else:
            current_in=nn_slices[i:(i+batch_size)]
            
        # Define file paths for the current slice
        input_filepath = os.path.join(output_dir, f'slice_{i+filenum_offset:05d}.npy') # 05d for zero-padding up to 99999

        # Save the slices
        np.save(input_filepath, current_in)
        # if i % 1000 == 0:
        #     print(f"Saved slice {i}/{totalsamples}")

    print(f"Serialization complete. {totalsamples} Files saved in '{output_dir}'.")

# Load a single sample from files    
def load_sample_from_files(input_path_tensor):
    input_path = input_path_tensor.numpy().decode('utf-8')
    inputname=os.path.basename(input_path)
    
    parentdir=os.path.dirname(os.path.dirname(input_path))
    # print("current dir: "+parentdir)
    output_path=os.path.join(parentdir,'output',inputname)

    # print("input: "+input_path)
    # print("output: "+output_path)
    # Load data
    image = (np.load(input_path).astype(np.float32)/127.0).reshape(INPUT_SHAPE)
    label = (np.load(output_path).astype(np.float32)/127.0).reshape(OUTPUT_DIM_NOTES)

    # Ensure shape
    image = tf.ensure_shape(image, INPUT_SHAPE)
    label = tf.ensure_shape(label, (OUTPUT_DIM_NOTES,)) 
    
    # Return features and label
    return image, label
feature_description = {
    "input":  tf.io.FixedLenFeature([], tf.string),
    "output": tf.io.FixedLenFeature([], tf.string),
}


# TensorFlow wrapper for loading sample from files
def tf_load_sample_from_files(ipath):
    parsed = tf.io.parse_single_example(ipath, feature_description)
 
    # Decode as int8 as planned
    input_raw = tf.io.decode_raw(parsed["input"], tf.int8)
    output_raw = tf.io.decode_raw(parsed["output"], tf.int8)

    # Explicitly cast to float16 to match your 5080's Mixed Precision policy
    # This is faster than implicit casting during division
    input_tensor = tf.cast(tf.reshape(input_raw, INPUT_SHAPE), tf.float32)
    output_tensor = tf.cast(tf.reshape(output_raw, [OUTPUT_DIM_NOTES]), tf.float32)

    # Use multiplication by the reciprocal (1/127 ≈ 0.007874016) 
    # Multiplications are generally faster for CPUs than divisions
    return input_tensor * 0.007874016, output_tensor


    
def plot_heatmap(plotdata,downsample_factor=1000):
    num_cols=plotdata.shape[1]
    num_rows=plotdata.shape[0]

    # --- Downsampling the data ---
    print(f"Downsampling data by a factor of {downsample_factor}...")
    # Calculate the new number of columns after downsampling
    new_num_cols = num_cols // downsample_factor

    # Ensure the original number of columns is a multiple of the downsample_factor
    # If not, you might lose some data at the end or need a more complex aggregation.
    # For simplicity, we'll slice to a multiple of downsample_factor
    effective_cols = new_num_cols * downsample_factor
    data_sliced = plotdata[:, :effective_cols]
    print(data_sliced.shape)
    # Reshape the data for averaging:
    # -1: infer dimension
    # downsample_factor: group columns into blocks
    # num_rows: keep rows as isp
    # This reshapes (19, M*N) to (19, M, N)
    reshaped_data = data_sliced.reshape(num_rows, new_num_cols, downsample_factor)

    # Average along the last axis (the downsample_factor axis)
    downsampled_data = np.max(reshaped_data, axis=2)

    print(f"Downsampled array shape: {downsampled_data.shape}")

    # --- Plotting the Heatmap ---
    print("Creating heatmap...")
    plt.figure(figsize=(20, 8)) # Adjust figure size as needed, especially width for more columns
    sns.heatmap(downsampled_data, cmap='viridis', cbar_kws={'label': 'Value'})
    plt.title(f'Heatmap of ({num_rows}, {num_cols}) Array (Downsampled by {downsample_factor})')
    plt.xlabel(f'Column Bins (Each bin represents {downsample_factor} original columns)')
    plt.ylabel('Row Index')
    plt.show()
    print("Heatmap displayed.")
    
    
def reshape_to_nn_input(indata):
    return reshape_to_nn_output(indata,collapse_time=False)
    # num_cols=indata.shape[1]
    # num_rows=indata.shape[0]
    # downsample_factor = frame_size
    # # --- Downsampling the data ---
    # print(f"reshape data by a factor of {downsample_factor}...")
    # # Calculate the new number of columns after downsampling
    # new_num_cols = num_cols // downsample_factor

    # # Ensure the original number of columns is a multiple of the downsample_factor
    # # If not, you might lose some data at the end or need a more complex aggregation.
    # # For simplicity, we'll slice to a multiple of downsample_factor
    # effective_cols = new_num_cols * downsample_factor
    # data_sliced = indata[:, :effective_cols]
    # print(data_sliced.shape)
    # # Reshape the data for averaging:
    # # -1: infer dimension
    # # downsample_factor: group columns into blocks
    # # num_rows: keep rows as isp
    # # This reshapes (19, M*N) to (19, M, N)
    # reshaped_data = np.max(data_sliced.reshape(num_rows, new_num_cols, downsample_factor),axis=2)
    # reshaped_data=np.swapaxes(reshaped_data,0,1)
    # # reshaped_data=np.swapaxes(reshaped_data,1,2)
    
    # print('Reshaped the input data to  ')
    # print(reshaped_data.shape)
    # return reshaped_data

def reshape_to_nn_output(outdata,collapse_time=True):
    num_samples=outdata.shape[1]
    num_midi_classes=outdata.shape[0]
    downsample_factor = frame_size
    # --- Downsampling the data ---
    print("Reshape to nn output. Collapse time: ",collapse_time)
    print("data shape",outdata.shape)
    print(f"reshape data by a factor of {downsample_factor}...")
    # Calculate the new number of columns after downsampling
    num_frames = num_samples // downsample_factor

    # Ensure the original number of columns is a multiple of the downsample_factor
    # If not, you might lose some data at the end or need a more complex aggregation.
    # For simplicity, we'll slice to a multiple of downsample_factor
    effective_cols = num_frames * downsample_factor
    data_sliced = outdata[:, :effective_cols]
    print("effective data shape",data_sliced.shape)
    # Reshape the data for averaging:
    # -1: infer dimension
    # downsample_factor: group columns into blocks
    # num_rows: keep rows as isp
    # This reshapes (19, M*N) to (19, M, N)
    reshaped_data = data_sliced.reshape(num_midi_classes, num_frames, downsample_factor)
    
    #Take only one sample per frame
    if collapse_time:
        reshaped_data=np.max(reshaped_data,axis=2)
    reshaped_data=np.swapaxes(reshaped_data,0,1)
    
    print('Reshaped the output data to  ')
    print(reshaped_data.shape)
    return reshaped_data