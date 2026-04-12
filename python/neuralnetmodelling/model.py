import tensorflow as tf
from tensorflow.keras import layers, models, regularizers


from common import OUTPUT_DIM_NOTES, image_height, image_width

IMG_H, IMG_W = image_height, image_width
NUM_CLASSES = 89
CHANNELS = 1
reg = None#regularizers.l2(1e-6)


# Diagram of the model in ASCII art. Each block should be drawn as a box. The six string layers should be drawn as parallel boxes after the transformer, and then combined into a single box for the chord reasoning, followed by the output layer.:
# Input Spectrogram (148 butterworth filter outputs (37  notes, 4 harmonics per note) x 256 samples)
#     |
# Local Contrast Normalization
#     |
# Time Compression (1D Conv along time axis)
#     |
# Transformer Block acting over the frequency features (Multi-Head Self-attention + FFN)
#     |
# String-aware Slicing into 6 parallel paths
#     |         |         |         |         |         |
# String 1    String 2    String 3    String 4    String 5    String 6
#     |         |         |         |         |         |
# Chord Reasoning (Conv across strings) followed by hollow neighborhood suppression and Global Max Pooling per string
#     |
# Output Notes (Dense Layer)


def bottleneck_residual(x, filters, kernel_size=3, ratio=4, name_prefix="res"):
    inner = max(filters // ratio, 16)
    shortcut = x

    x = layers.Conv1D(inner, 1, padding='same', name=f"{name_prefix}_squeeze")(x)
    x = layers.BatchNormalization(name=f"{name_prefix}_bn1")(x)
    x = layers.LeakyReLU(name=f"{name_prefix}_act1")(x)

    x = layers.Conv1D(inner, kernel_size, padding='same', name=f"{name_prefix}_conv_k{kernel_size}")(x)
    x = layers.BatchNormalization(name=f"{name_prefix}_bn2")(x)
    x = layers.LeakyReLU(name=f"{name_prefix}_act2")(x)

    x = layers.Conv1D(filters, 1, padding='same', name=f"{name_prefix}_expand")(x)
    x = layers.BatchNormalization(name=f"{name_prefix}_bn3")(x)

    if shortcut.shape[-1] != filters:
        shortcut = layers.Conv1D(filters, 1, padding='same', name=f"{name_prefix}_shortcut_proj")(shortcut)
        shortcut = layers.BatchNormalization(name=f"{name_prefix}_shortcut_bn")(shortcut)

    return layers.LeakyReLU(name=f"{name_prefix}_out")(layers.Add(name=f"{name_prefix}_add")([x, shortcut]))

def string_layer(x, start, end, max_x, training, string_idx=0):
    end = min(int(end), int(max_x))
    start = max(0, int(start))
    prefix = f"str{string_idx}"
    
    s = layers.Lambda(lambda y, st=start, en=end: y[:, st:en, :], name=f"{prefix}_slice")(x)
    # res = layers.Conv1D(64, 4, strides=4, padding='valid',
    #                     kernel_regularizer=reg, name=f"{prefix}_res_proj")(s)
    x = layers.Conv1D(32, 1, padding='same', kernel_initializer='he_normal', name=f"{prefix}_backbone_squeeze", kernel_regularizer=reg)(s)
    x = layers.BatchNormalization(name=f"{prefix}_backbone_squeeze_bn")(x)
    x = layers.LeakyReLU(name=f"{prefix}_backbone_squeeze_act")(x)

    x = layers.Conv1D(32, 8, padding='same', kernel_initializer='he_normal', name=f"{prefix}_backbone_conv1", kernel_regularizer=reg)(x)
    x = layers.BatchNormalization(name=f"{prefix}_backbone_bn1")(x)
    x = layers.LeakyReLU(name=f"{prefix}_backbone_act1")(x)
    x = layers.SpatialDropout1D(0.2, name=f"{prefix}_backbone_drop1")(x)

    x = layers.Conv1D(64, 8, padding='same', kernel_initializer='he_normal', name=f"{prefix}_backbone_conv2", kernel_regularizer=reg)(x)
    x = layers.BatchNormalization(name=f"{prefix}_backbone_bn2")(x)
    s = layers.LeakyReLU(name=f"{prefix}_backbone_act2")(x)

    

    # Collapse 4 harmonic bins → 1 vector per note
    s = layers.Conv1D(64, 4, strides=4, padding='valid', 
                      kernel_regularizer=reg, name=f"{prefix}_harmonic_collapse")(s)
    s = layers.BatchNormalization(name=f"{prefix}_harmonic_bn")(s)
    s = layers.LeakyReLU(name=f"{prefix}_harmonic_act")(s)
    #s=layers.Add(name=f"{prefix}_res1_conv1")([s, res])
    # Now shape is (batch, 13, 64) — one vector per note

    # --- Strict "Hollow" Neighborhood Suppression ---
    def hollow_suppression(y):
        # Pad by 1 on the spatial dimension (frets) to handle the 0th and 12th frets safely
        y_padded = tf.pad(y, [[0, 0], [1, 1], [0, 0]])
        
        # Shifted views to get strictly the neighbors
        left_neighbors = y_padded[:, :-2, :]   # Fret - 1
        right_neighbors = y_padded[:, 2:, :]   # Fret + 1
        
        # Average strictly the surrounding frets (leaving the center out entirely)
        surround_avg = (left_neighbors + right_neighbors) / 2.0
        
        # Subtract the bleeding energy from the center note
        return y - surround_avg

    s = layers.Lambda(hollow_suppression, name=f"{prefix}_hollow_suppress")(s)
    s = layers.LeakyReLU(name=f"{prefix}_hollow_act")(s)

    # Optional: A 1x1 conv to mix the newly sharpened features
    s = layers.Conv1D(64, 1, padding='same', kernel_regularizer=reg, name=f"{prefix}_post_suppress_conv")(s)
    s = layers.BatchNormalization(name=f"{prefix}_post_suppress_bn")(s)
    s = layers.LeakyReLU(name=f"{prefix}_post_suppress_act")(s)

    return s



def transformer_block(x, num_heads=2, head_size=32, ff_dim=128, dropout=0.1, name_prefix="tfm"):
    # --- Attention Block ---
    # 1. Apply LayerNorm BEFORE attention (Off-ramp)
    x_norm1 = layers.LayerNormalization(epsilon=1e-6, name=f"{name_prefix}_ln1")(x)
    
    # 2. Compute Attention
    attn = layers.MultiHeadAttention(
        num_heads=num_heads, key_dim=head_size, dropout=dropout, name=f"{name_prefix}_mha", kernel_regularizer=reg
    )(x_norm1, x_norm1)
    
    # 3. Add to original input WITHOUT normalizing the result (Clear highway!)
    x1 = layers.Add(name=f"{name_prefix}_attn_add")([x, attn])

    # --- Feed Forward Block ---
    # 1. Apply LayerNorm BEFORE FFN (Off-ramp)
    x_norm2 = layers.LayerNormalization(epsilon=1e-6, name=f"{name_prefix}_ln2")(x1)
    
    # 2. Compute FFN
    ffn = layers.Dense(ff_dim, activation='relu', name=f"{name_prefix}_ffn1")(x_norm2)
    ffn = layers.Dropout(dropout, name=f"{name_prefix}_ffn_drop")(ffn)
    ffn = layers.Dense(x.shape[-1], name=f"{name_prefix}_ffn2")(ffn)

    # 3. Add to x1 WITHOUT normalizing the result (Clear highway!)
    return layers.Add(name=f"{name_prefix}_ffn_add")([x1, ffn])

def chord_conv_block(string_features, filters, kernel_size=(3,4), name_prefix="chord"):
    # store the original string features for later as residuals
    

    max_len = max(s.shape[1] for s in string_features)
    padded = []
    for i, s in enumerate(string_features):
        diff = max_len - s.shape[1]
        if diff > 0:
            s = layers.ZeroPadding1D((0, diff), name=f"{name_prefix}_pad_str{i}")(s)
        padded.append(s)
    string_residuals = padded.copy()
    expanded = [layers.Reshape((1, max_len, 64), name=f"{name_prefix}_expand_str{i}")(s) for i, s in enumerate(padded)]
    stacked = layers.Concatenate(axis=1, name=f"{name_prefix}_stack_strings")(expanded)  # (B, 6, max_len, 64)


    chord=layers.Conv2D(filters, kernel_size, padding='same', name=f"{name_prefix}_conv1",kernel_regularizer=reg)(stacked)
    chord=layers.BatchNormalization(name=f"{name_prefix}_bn1")(chord)
    chord=layers.LeakyReLU(name=f"{name_prefix}_act1")(chord)
    chord=layers.Conv2D(filters, kernel_size, padding='same', name=f"{name_prefix}_conv2",kernel_regularizer=reg)(chord)
    chord=layers.BatchNormalization(name=f"{name_prefix}_bn2")(chord)
    chord=layers.LeakyReLU(name=f"{name_prefix}_act2")(chord)
    chord=layers.SpatialDropout2D(0.2, name=f"{name_prefix}_drop1")(chord)
    # Split the chord features back into per-string tensors
    split_chords = [layers.Lambda(lambda t, i=i: t[:, i, :, :], name=f"{name_prefix}_slice_str{i}")(chord) for i in range(len(string_features))]
    

    # Per string global max pooling and dense layers
    processed_strings = []
    for i, s in enumerate(split_chords):
        # Add residual connection from original string features
        s = layers.Add(name=f"{name_prefix}_res_str{i}")([s, string_residuals[i]])

        s = layers.GlobalMaxPooling1D(name=f"{name_prefix}_gmax_str{i}")(s)
        # s = layers.Dense(64, name=f"{name_prefix}_dense_str{i}", kernel_regularizer=reg)(s)
        s = layers.BatchNormalization(name=f"{name_prefix}_bn_str{i}")(s)
        s = layers.LeakyReLU(name=f"{name_prefix}_act_str{i}")(s)
        processed_strings.append(s)
    return processed_strings


def build_1d_cnn_model(batch_sz=64, input_shape=(image_height, image_width),
                       output_dim=OUTPUT_DIM_NOTES, training=True):
    print("Image height: ", image_height)
    inputs = layers.Input(batch_shape=(batch_sz, *input_shape), name="input_spectrogram")
    local_mean = layers.AveragePooling2D(pool_size=(5, 1), strides=(1, 1), padding='same', name="local_mean")(inputs)
    x = layers.Subtract(name="local_contrast")([inputs, local_mean])
    # x=inputs
    # --- Stage 1: Frequency compression (B, 312, 256) → (B, 312, 512) ---
    x = layers.Reshape((image_height, 256, 1), name="reshape_to_2d")(x)
    x = layers.Conv2D(8, (1, 16), strides=(1, 4), padding='same',
                      kernel_initializer='he_normal', name="freq_compress_conv2d")(x)
    x = layers.BatchNormalization(name="freq_compress_bn")(x)
    x = layers.LeakyReLU(0.2, name="freq_compress_act")(x)
    x = layers.SpatialDropout2D(0.1, name="freq_compress_drop")(x)
    x = layers.Reshape((image_height, 512), name="reshape_to_1d")(x)

    # --- Stage 2: Conv1D backbone ---
    # x = layers.Conv1D(32, 1, padding='same', kernel_initializer='he_normal', name="backbone_squeeze", kernel_regularizer=reg)(x)
    # x = layers.BatchNormalization(name="backbone_squeeze_bn")(x)
    # x = layers.LeakyReLU(name="backbone_squeeze_act")(x)

    # x = layers.Conv1D(32, 8, padding='same', kernel_initializer='he_normal', name="backbone_conv1", kernel_regularizer=reg)(x)
    # x = layers.BatchNormalization(name="backbone_bn1")(x)
    # x = layers.LeakyReLU(name="backbone_act1")(x)
    # x = layers.SpatialDropout1D(0.2, name="backbone_drop1")(x)

    # x = layers.Conv1D(64, 8, padding='same', kernel_initializer='he_normal', name="backbone_conv2", kernel_regularizer=reg)(x)
    # x = layers.BatchNormalization(name="backbone_bn2")(x)
    # x = layers.LeakyReLU(name="backbone_act2")(x)
    # x = layers.MaxPooling1D(2, name="backbone_pool")(x)
    # x = layers.SpatialDropout1D(0.2, name="backbone_drop2")(x)
    # x = layers.Conv1D(64, 1, padding='same', kernel_initializer='he_normal', kernel_regularizer=reg, name="backbone_squeeze")(x)
    # x = layers.BatchNormalization(name="backbone_squeeze_bn")(x)
    # x = layers.LeakyReLU(name="backbone_squeeze_act")(x)

    #x = layers.MaxPooling1D(2, name="backbone_pool")(x)
    # x = layers.SpatialDropout1D(0.2, name="backbone_drop")(x)
    # --- Stage 3: Transformer ---
    x = transformer_block(x, num_heads=2, head_size=32, ff_dim=128, dropout=0.1, name_prefix="tfm_block1")

    num_pool_layers = 0
    max_x = image_height / (num_pool_layers + 1)
    print(f"Before string split: {x.shape}, max_x={max_x}")

    # --- Stage 4: String-aware slicing ---
    totalnotes = 37
    window_size = 13
    offsets = [0, 5, 10, 15, 19, 24]

    def slice_range(offset):
        s = int(offset / totalnotes * max_x)
        e = int((offset + window_size) / totalnotes * max_x)
        return s, e

    ranges = [slice_range(o) for o in offsets]
    ranges[-1] = (ranges[-1][0], int(max_x) - 1)

    string_features = [
        string_layer(x, s, e, max_x, training, string_idx=i)
        for i, (s, e) in enumerate(ranges)
    ]



    # --- Stage 5: Chord reasoning (Conv1D across strings) ---
    processed_strings = chord_conv_block(string_features, filters=64, kernel_size=(3,4), name_prefix="chord_block")

    combined = layers.Concatenate(name="string_combined")(processed_strings)



    outputs = layers.Dense(output_dim, activation= None if training else 'sigmoid',
                        bias_initializer=tf.initializers.Constant(-2),
                        dtype='float32', name="output_notes")(combined)
    return models.Model(inputs, outputs, name="guitar_note_detector")


