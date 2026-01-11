import  os
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import tensorflow as tf
# Common parameters
frame_size=256
image_width = 256
image_height = 312 # Assuming this is your updated 288+some context/padding, or just 288 filter outputs
num_channels = 1
num_classes = 129 # For MIDI notes+silence class
INPUT_SHAPE = (image_height,image_width, num_channels)
OUTPUT_DIM_NOTES = num_classes # For notes output
OUTPUT_DIM_ONSETS = 1 # For onsets output
SAMPLES_PER_CHUNK = 316
# Common functions
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
    print("Loaded sample from ",input_path)
    inputname=os.path.basename(input_path)
    
    parentdir=os.path.dirname(os.path.dirname(input_path))
    # print("current dir: "+parentdir)
    output_path=os.path.join(parentdir,'output',inputname)

    # print("input: "+input_path)
    # print("output: "+output_path)
    # Load data

    images = np.load(input_path).astype(np.float32)#.reshape(INPUT_SHAPE)
    
    print("Image shape: ",images.shape)
    labels = np.load(output_path).astype(np.float32)#.reshape(OUTPUT_DIM_NOTES)
    
    print("Label shape: ",labels.shape)

    image=[]
    label=[]
    # Reshape data
    for i in range(10):#images.shape[0]):
        img=images[i].reshape(INPUT_SHAPE)
        lbl=labels[i].reshape((OUTPUT_DIM_NOTES,))
        #Ensure shape
        img=tf.ensure_shape(img, INPUT_SHAPE)
        lbl=tf.ensure_shape(lbl, (OUTPUT_DIM_NOTES,)) 
        # Append to list
        image.append(img)
        label.append(lbl)
    # Ensure shape
    # image = tf.ensure_shape(image, INPUT_SHAPE)
    # label = tf.ensure_shape(label, (OUTPUT_DIM_NOTES,)) 
    
    # Return features and label
    #print sizes of image and label
    print("Loaded sample from ",input_path)
    print("Image shape: ",len(image),image[0].shape)
    print("Label shape: ",len(label),label[0].shape)
    return image,label  # Return (features, labels)



def load_chunk_from_file(input_path_tensor):
    input_path = input_path_tensor.numpy().decode('utf-8')
    #print("Loaded sample from ",input_path)
    inputname=os.path.basename(input_path)
    
    parentdir=os.path.dirname(os.path.dirname(input_path))
    # print("current dir: "+parentdir)
    output_path=os.path.join(parentdir,'output',inputname)

    # print("input: "+input_path)
    # print("output: "+output_path)
    # Load data

    images = np.load(input_path, mmap_mode='r').astype(np.float32)#.reshape(INPUT_SHAPE)
    
    #print("Image shape: ",images.shape)
    labels = np.load(output_path, mmap_mode='r').astype(np.float32)#.reshape(OUTPUT_DIM_NOTES)
    
    #print("Label shape: ",labels.shape)
    
    image_chunk=images.reshape((SAMPLES_PER_CHUNK,image_height,image_width,num_channels))
    label_chunk=labels.reshape((SAMPLES_PER_CHUNK,OUTPUT_DIM_NOTES))
    
    return image_chunk, label_chunk

def tf_load_chunk(ipath):
    # This returns the full 316-sample blocks
    return tf.py_function(load_chunk_from_file, [ipath], [tf.float32, tf.float32])

def unchunk_mapper(ipath):
    # img_chunk shape: (316, 312, 256, 1)
    # lbl_chunk shape: (316, OUTPUT_DIM_NOTES)
    img_chunk, lbl_chunk = tf_load_chunk(ipath)
    
# Explicitly set the shapes of the chunks before slicing
    img_chunk.set_shape([None, 312, 256, 1])
    lbl_chunk.set_shape([None, OUTPUT_DIM_NOTES])
    # from_tensor_slices slices along the FIRST dimension (the 316)
    return tf.data.Dataset.from_tensor_slices((img_chunk, lbl_chunk))

# TensorFlow wrapper for loading sample from files
def tf_load_sample_from_files(ipath):
    image, label = tf.py_function(
        load_sample_from_files, [ipath], [tf.float32, tf.float32]
    )

    image.set_shape(INPUT_SHAPE)
    label.set_shape((OUTPUT_DIM_NOTES,))

    return image,label,#tf.data.Dataset.from_tensor_slices((image, label)) # Return (features, labels, sample_weights)   
    
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
    print(f"reshape data by a factor of {downsample_factor}...")
    # Calculate the new number of columns after downsampling
    num_frames = num_samples // downsample_factor

    # Ensure the original number of columns is a multiple of the downsample_factor
    # If not, you might lose some data at the end or need a more complex aggregation.
    # For simplicity, we'll slice to a multiple of downsample_factor
    effective_cols = num_frames * downsample_factor
    data_sliced = outdata[:, :effective_cols]
    print(data_sliced.shape)
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