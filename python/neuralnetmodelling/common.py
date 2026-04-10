import csv
import  os
import pathlib
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import tensorflow as tf
from fretboard import FretBoard,num_frets,num_strings,num_harmonics
from fretboardnonredundant import FretBoard
# Common parameters
frame_size=256
image_width = 256
Q_FACTOR=6
FRAME_LAG=3
SAMPLERATE=48000
fretboard=FretBoard(2,SAMPLERATE)
image_height = fretboard.get_num_filters() 
num_channels = 1
num_classes = 129 # For MIDI notes+silence class
INPUT_SHAPE = (image_height,image_width, num_channels)
INPUT_SHAPE_AUDIO = (1,image_width, num_channels)
OUTPUT_DIM_NOTES = num_classes # For notes output
OUTPUT_DIM_ONSETS = 1 # For onsets output


def parse_filtered_audio_record(example_proto):
    parsed=tf.io.parse_single_example(example_proto, feature_description)
    input_raw = tf.io.decode_raw(parsed["input"], tf.int8)
    label_raw = tf.io.decode_raw(parsed["output"], tf.int8)
    # print tf.print shape of input_raw and label_raw
    # tf.print("input_raw shape:", tf.shape(input_raw))
    # tf.print("label_raw shape:", tf.shape(label_raw))
    input_tensor = tf.reshape(input_raw, INPUT_SHAPE)
    input_tensor = tf.cast(input_tensor, tf.float32)
    input_tensor=input_tensor/127
    output_tensor = tf.cast(tf.reshape(label_raw, [OUTPUT_DIM_NOTES]), tf.float32)
    return input_tensor,output_tensor
def fast_gpu_map(input_tensor,output_tensor,training=True):


    
    # Constants for clarity
    SILENCE_IDX = OUTPUT_DIM_NOTES - 1
    silence_vector = tf.one_hot(SILENCE_IDX, depth=OUTPUT_DIM_NOTES, dtype=tf.float32)
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
    output_tensor=output_tensor[40:77] # Only keep the 37 note labels we care about
    input_tensor = tf.where(should_force_silence, zero_input, input_tensor)

    # 4. Augmentation (Only if we aren't in a forced silence state)
    if training:
        noise = tf.random.normal(shape=tf.shape(input_tensor), mean=0.0, stddev=0.01)
        # We only add noise to frames that actually have content to avoid 
        # teaching the model that "noise = note"
        input_tensor = tf.where(should_force_silence, zero_input, input_tensor + noise)
        input_tensor = tf.clip_by_value(input_tensor, -1.0, 1.0)
        num_masks = 2
        mask_width = 5 # How many filter bins to hide
        for _ in range(num_masks):
            start = tf.random.uniform([], 0, INPUT_SHAPE[0] - mask_width, dtype=tf.int32)
            indices = tf.range(start, start + mask_width)
            # Create a mask of 1s, then set the specific indices to 0
            mask = tf.one_hot(indices, depth=INPUT_SHAPE[0])
            mask = 1.0 - tf.reduce_sum(mask, axis=0)
            mask = tf.reshape(mask, (INPUT_SHAPE[0],1, 1))
            input_tensor = input_tensor * mask

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


def count_concurrent_notes_distribution(dataset, max_polyphony=129, has_filtered_audio=True): # has_filtered_audio True means dataset only has tuples (input,output). false means it has (audio_path,startframe,output)
    # 1. Ensure the dataset is batched for vectorized math
    # If the input dataset is already batched, this line won't hurt.
    batched_ds = dataset#.batch(batch_size,drop_remainder=True) if not hasattr(dataset, '_batch_size') else dataset

    # State: Histogram of size max_polyphony
    initial_state = tf.zeros((max_polyphony,), dtype=tf.int64)
    
    def reduce_fn(old_state, next_element):
        if has_filtered_audio:
            _, labels_batch = next_element # Shape: (batch, OUTPUT_DIM_NOTES)
        else:
            _,_, labels_batch = next_element 
        active_notes_only = labels_batch[..., :-1]
        # 1. Count active notes for every sample in the batch at once
        # Resulting shape: (batch_size,)
        num_active_batch = tf.reduce_sum(tf.cast(active_notes_only, tf.int32), axis=-1)
        before=num_active_batch
        #print labels_batch and num_active_batch for debugging
        # print("Labels batch (first 5 samples):", labels_batch[:5])
        # print("Num active batch (first 5 samples):", num_active_batch[:5])

        # # print shapes
        # print("Labels batch shape:", labels_batch.shape)
        # print("Num active batch shape:", num_active_batch.shape)
        
        # 2. Clip values to stay within histogram bounds
        num_active_batch = tf.clip_by_value(num_active_batch, 0, max_polyphony - 1)

        # tf.cond(
        #     tf.reduce_any(
        #         tf.equal(num_active_batch,1)
        #     ),
        #     lambda: tf.print("Before clipping", before," after: ", num_active_batch),
        #     lambda: tf.print('')
        # )

        # 3. Use bincount to create a mini-histogram for the entire batch
        # This is the secret to speed—no loops, no individual one-hots.
        batch_hist = tf.math.bincount(
            num_active_batch, 
            minlength=max_polyphony, 
            maxlength=max_polyphony, 
            dtype=tf.int64
        )
        
        return old_state + batch_hist

    # Perform the reduction on the graph
    hist = batched_ds.reduce(initial_state, reduce_fn)
    return hist.numpy()

def plot_histogram(hist,size=OUTPUT_DIM_NOTES):
    plt.bar(range(size), hist)
    plt.xlabel('MIDI Note Number')
    plt.ylabel('Count')
    plt.title('Histogram of MIDI Note Occurrences')
    plt.xlim(0, size)  # Limit x-axis to the range of interest
    plt.show()

def filter_polyphony(dataset: tf.data.Dataset, num_notes: int, exact: bool,start_note=0,end_note=OUTPUT_DIM_NOTES, has_filtered_audio=False) -> tf.data.Dataset:
    def filter_func(label):
        labels = tf.cast(label > 0.5, tf.int32)
        numactive = tf.reduce_sum(labels[start_note:end_note])
        if exact:
            return numactive == num_notes
        else:
            return numactive <= num_notes

    if has_filtered_audio:
        return dataset.filter(lambda a, l: filter_func(l))
    else:
        return dataset.filter(lambda a, fnr, l: filter_func(l))
    
def make_proto(feature_map: np.ndarray, label_bytes: bytes)->bytes:
    feature={
        "input": tf.train.Feature(
            bytes_list=tf.train.BytesList(value=[feature_map.tobytes()])
        ),
        "output": tf.train.Feature(
            bytes_list=tf.train.BytesList(value=[label_bytes])
        )
    }
    return tf.train.Example(
        features=tf.train.Features(feature=feature)
    ).SerializeToString()

def write_prefiltered_tfrecord(
    dataset: tf.data.Dataset,
    output_prefix: str,
    records_per_file: int = 1000,
) -> None:

    pathlib.Path(output_prefix).parent.mkdir(parents=True, exist_ok=True)

    writer = None
    file_index = 0
    record_count = 0

    try:
        for input_tensor, output_tensor in dataset:
            input_np = tf.reshape(input_tensor, [INPUT_SHAPE[0], INPUT_SHAPE[1]]).numpy()
            input_np = np.clip(input_np * 127, -128, 127).astype(np.int8)
            label_np = output_tensor.numpy().astype(np.int8)

            proto = make_proto(input_np, label_np.tobytes())

            if writer is None or record_count >= records_per_file:
                if writer is not None:
                    writer.close()
                shard_path = f"{output_prefix}_{file_index:07d}.tfrecord"
                writer = tf.io.TFRecordWriter(shard_path)
                file_index += 1
                record_count = 0

            writer.write(proto)
            record_count += 1
    finally:
        if writer is not None:
            writer.close()

    print(f"Wrote {file_index} shard(s) to {output_prefix}_*.tfrecord")

# This function counts the occurrences of each MIDI note in the dataset, assuming the dataset is batched and has a specific structure. It uses tf.data.Dataset.reduce to efficiently aggregate counts across the entire dataset without explicit Python loops, which is crucial for performance on large datasets.
def count_midi_notes(dataset,outputsize=OUTPUT_DIM_NOTES,has_filtered_audio=False):
    # Since we are now batched, we sum across the batch dimension first
    initial_state = tf.zeros((outputsize,), dtype=tf.int32)
    if has_filtered_audio:
        def reduce_fn(old_state, next_element):
            
            _, labels_batch = next_element # Shape: (batch, OUTPUT_DIM_NOTES)
            # # print the shape of labels_batch for debugging with tf.print
            # tf.print("Labels batch shape in reduce_fn:", tf.shape(labels_batch))
            # # Sum the batch of labels first, then add to the global state
            batch_sum = tf.reduce_sum(tf.cast(labels_batch, tf.int32), axis=0)
            # tf.print("Batch sum in reduce_fn:", batch_sum)
            return old_state + batch_sum
    else:
        def reduce_fn(old_state, next_element):
            _,_, labels_batch = next_element
            # # Sum the batch of labels first, then add to the global state
            # tf.print("Labels batch shape in reduce_fn:", tf.shape(labels_batch))
            batch_sum = tf.reduce_sum(tf.cast(labels_batch, tf.int32), axis=0)
            return old_state +  batch_sum

    return dataset.reduce(initial_state, reduce_fn).numpy()

# This function writes the MIDI note histogram to a CSV file. It calls count_midi_notes to get the histogram data, then uses Python's built-in csv module to write the note numbers and their corresponding counts to a CSV file. It also prints the histogram to the console for verification.
def write_note_histogram(dataset,output_path,outputsize=OUTPUT_DIM_NOTES,has_filtered_audio=False):
    notes_histo = count_midi_notes(dataset, outputsize, has_filtered_audio)
    with open(output_path, mode='w', newline='') as csv_file:
        writer = csv.writer(csv_file)
        writer.writerow(['MIDI Note', 'Count'])
        print("Writing note histogram to CSV:")
        for note, count in enumerate(notes_histo):
            print(f"Note {note}: {count}")
            writer.writerow([note, count])
    print(f"Note histogram written to {output_path}")