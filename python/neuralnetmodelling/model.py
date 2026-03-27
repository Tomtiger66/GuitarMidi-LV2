import tensorflow as tf
from tensorflow.keras import layers, models, regularizers


from common import OUTPUT_DIM_NOTES, image_height, image_width

IMG_H, IMG_W = image_height, image_width
NUM_CLASSES = 89
CHANNELS = 1
reg = regularizers.l2(1e-4)
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
    reg = regularizers.l2(1e-3)

    s = layers.Lambda(lambda y, st=start, en=end: y[:, st:en, :], name=f"{prefix}_slice")(x)

    s = layers.Conv1D(64, 1, padding='same', kernel_regularizer=reg, name=f"{prefix}_proj")(s)
    s = layers.BatchNormalization(name=f"{prefix}_proj_bn")(s)
    s = layers.LeakyReLU(name=f"{prefix}_proj_act")(s)

    # Single residual block
    shortcut = s
    s = layers.Conv1D(64, 3, padding='same', kernel_regularizer=reg, name=f"{prefix}_res1_conv1")(s)
    s = layers.BatchNormalization(name=f"{prefix}_res1_bn1")(s)
    s = layers.LeakyReLU(name=f"{prefix}_res1_act1")(s)
    s = layers.Conv1D(64, 3, padding='same', kernel_regularizer=reg, name=f"{prefix}_res1_conv2")(s)
    s = layers.BatchNormalization(name=f"{prefix}_res1_bn2")(s)
    s = layers.Add(name=f"{prefix}_res1_add")([s, shortcut])
    s = layers.LeakyReLU(name=f"{prefix}_res1_out")(s)

    s = layers.GlobalMaxPooling1D(name=f"{prefix}_gmax")(s)
    return s

def transformer_block(x, num_heads=2, head_size=32, ff_dim=128, dropout=0.1, name_prefix="tfm"):
    attn = layers.MultiHeadAttention(
        num_heads=num_heads, key_dim=head_size, dropout=dropout, name=f"{name_prefix}_mha", kernel_regularizer=reg
    )(x, x)
    x1 = layers.LayerNormalization(epsilon=1e-6, name=f"{name_prefix}_ln1")(
        layers.Add(name=f"{name_prefix}_attn_add")([x, attn]))

    ffn = layers.Dense(ff_dim, activation='relu', name=f"{name_prefix}_ffn1")(x1)
    ffn = layers.Dropout(dropout, name=f"{name_prefix}_ffn_drop")(ffn)
    ffn = layers.Dense(x.shape[-1], name=f"{name_prefix}_ffn2")(ffn)

    return layers.LayerNormalization(epsilon=1e-6, name=f"{name_prefix}_ln2")(
        layers.Add(name=f"{name_prefix}_ffn_add")([x1, ffn]))

def build_1d_cnn_model(batch_sz=64, input_shape=(image_height, image_width),
                       output_dim=OUTPUT_DIM_NOTES, training=True):
    print("Image height: ", image_height)
    inputs = layers.Input(batch_shape=(batch_sz, *input_shape), name="input_spectrogram")
    # local_mean = layers.AveragePooling2D(pool_size=(5, 1), strides=(1, 1), padding='same', name="local_mean")(inputs)
    # x = layers.Subtract(name="local_contrast")([inputs, local_mean])
    x=inputs
    # --- Stage 1: Frequency compression (B, 312, 256) → (B, 312, 512) ---
    x = layers.Reshape((image_height, 256, 1), name="reshape_to_2d")(x)
    x = layers.Conv2D(8, (1, 16), strides=(1, 4), padding='same',
                      kernel_initializer='he_normal', name="freq_compress_conv2d")(x)
    x = layers.BatchNormalization(name="freq_compress_bn")(x)
    x = layers.LeakyReLU(0.2, name="freq_compress_act")(x)
    x = layers.SpatialDropout2D(0.1, name="freq_compress_drop")(x)
    x = layers.Reshape((image_height, 512), name="reshape_to_1d")(x)

    # # --- Stage 2: Conv1D backbone ---
    # x = layers.Conv1D(128, 1, padding='same', kernel_initializer='he_normal', name="backbone_squeeze")(x)
    # x = layers.BatchNormalization(name="backbone_squeeze_bn")(x)
    # x = layers.LeakyReLU(name="backbone_squeeze_act")(x)

    # x = layers.Conv1D(32, 7, padding='same', kernel_initializer='he_normal', name="backbone_conv1")(x)
    # x = layers.BatchNormalization(name="backbone_bn1")(x)
    # x = layers.LeakyReLU(name="backbone_act1")(x)
    # x = layers.SpatialDropout1D(0.2, name="backbone_drop1")(x)

    # x = layers.Conv1D(64, 7, padding='same', kernel_initializer='he_normal', name="backbone_conv2")(x)
    # x = layers.BatchNormalization(name="backbone_bn2")(x)
    # x = layers.LeakyReLU(name="backbone_act2")(x)
    # x = layers.MaxPooling1D(2, name="backbone_pool")(x)
    # x = layers.SpatialDropout1D(0.2, name="backbone_drop2")(x)
    x = layers.Conv1D(64, 1, padding='same', kernel_initializer='he_normal', kernel_regularizer=reg, name="backbone_squeeze")(x)
    x = layers.BatchNormalization(name="backbone_squeeze_bn")(x)
    x = layers.LeakyReLU(name="backbone_squeeze_act")(x)

    #x = layers.MaxPooling1D(2, name="backbone_pool")(x)
    x = layers.SpatialDropout1D(0.2, name="backbone_drop")(x)
    # --- Stage 3: Transformer ---
    x = transformer_block(x, num_heads=6, head_size=64, ff_dim=256, dropout=0.1, name_prefix="tfm_block1")

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

    # --- Stage 5: Chord reasoning ---
    stacked = layers.Lambda(lambda t: tf.stack(t, axis=1), name="stack_strings")(string_features)
    stacked_2d = layers.Reshape((6, 64, 1), name="strings_to_2d")(stacked)

    chord = layers.Conv2D(64, kernel_size=(3, 7), padding='same', name="chord_conv1")(stacked_2d)
    chord = layers.BatchNormalization(name="chord_bn1")(chord)
    chord = layers.LeakyReLU(name="chord_act1")(chord)
    chord = layers.SpatialDropout2D(0.2, name="chord_drop1")(chord)

    # --- Stage 6: Classification head ---
    chord = layers.Conv2D(64, (3, 3), padding='same', name="chord_conv2", kernel_regularizer=reg)(chord)
    chord = layers.BatchNormalization(name="chord_bn2")(chord)
    chord = layers.LeakyReLU(name="chord_act2")(chord)

    # --- Stage 6: Reduce channels per string, keep 6 strings ---
    # Pool over the frequency/feature axis (axis=2), keep strings (axis=1)
    chord_max = layers.Lambda(lambda t: tf.reduce_max(t, axis=2), name="reduce_freq_max")(chord)
    chord_avg = layers.Lambda(lambda t: tf.reduce_mean(t, axis=2), name="reduce_freq_avg")(chord)
    # Each: (B, 6, 64)

    per_string = layers.Concatenate(axis=-1, name="per_string_cat")([chord_max, chord_avg])
    
    combined = layers.Flatten(name="string_combined")(per_string)
    outputs = layers.Dense(output_dim, activation='sigmoid',
                           bias_initializer=tf.initializers.Constant(-1.0),
                           dtype='float32', name="output_notes")(combined)
    return models.Model(inputs, outputs, name="guitar_note_detector")
