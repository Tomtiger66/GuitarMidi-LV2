import tensorflow as tf
from tensorflow.keras import layers, models
from common import OUTPUT_DIM_NOTES, image_height, image_width

IMG_H, IMG_W = 312, 256
NUM_CLASSES = 89
CHANNELS = 1


def bottleneck_residual(x, filters, kernel_size=3, ratio=4):
    inner = max(filters // ratio, 16)
    shortcut = x

    x = layers.Conv1D(inner, 1, padding='same')(x)
    x = layers.BatchNormalization()(x)
    x = layers.LeakyReLU()(x)

    x = layers.Conv1D(inner, kernel_size, padding='same')(x)
    x = layers.BatchNormalization()(x)
    x = layers.LeakyReLU()(x)

    x = layers.Conv1D(filters, 1, padding='same')(x)
    x = layers.BatchNormalization()(x)

    if shortcut.shape[-1] != filters:
        shortcut = layers.Conv1D(filters, 1, padding='same')(shortcut)
        shortcut = layers.BatchNormalization()(shortcut)

    return layers.LeakyReLU()(layers.Add()([x, shortcut]))


def string_layer(x, start, end, max_x, training):
    end = min(int(end), int(max_x))
    start = max(0, int(start))
    print(f"  String slice [{start}:{end}]")

    s = layers.Lambda(lambda y, st=start, en=end: y[:, st:en, :])(x)

    s = layers.Conv1D(64, 1, padding='same', kernel_initializer='he_normal')(s)
    s = layers.BatchNormalization()(s)
    s = layers.LeakyReLU()(s)

    s = bottleneck_residual(s, filters=64, kernel_size=3)
    s = bottleneck_residual(s, filters=64, kernel_size=5)
    s = layers.SpatialDropout1D(0.2)(s, training=training)

    smax = layers.GlobalMaxPooling1D()(s)
    savg = layers.GlobalAveragePooling1D()(s)
    return layers.Concatenate()([smax, savg])  # (B, 128)


def transformer_block(x, num_heads=2, head_size=32, ff_dim=128, dropout=0.1):
    attn = layers.MultiHeadAttention(
        num_heads=num_heads, key_dim=head_size, dropout=dropout
    )(x, x)
    x1 = layers.LayerNormalization(epsilon=1e-6)(layers.Add()([x, attn]))

    ffn = layers.Dense(ff_dim, activation='relu')(x1)
    ffn = layers.Dropout(dropout)(ffn)
    ffn = layers.Dense(x.shape[-1])(ffn)

    return layers.LayerNormalization(epsilon=1e-6)(layers.Add()([x1, ffn]))


def build_1d_cnn_model(batch_sz=64, input_shape=(image_height, image_width),
                       output_dim=OUTPUT_DIM_NOTES, training=True):

    inputs = layers.Input(batch_shape=(batch_sz, *input_shape))

    # --- Stage 1: Frequency compression (B, 312, 256) → (B, 312, 64) ---
    x = layers.Reshape((image_height, 256, 1))(inputs)
    x = layers.Conv2D(8, (1, 16), strides=(1, 4), padding='same',
                      kernel_initializer='he_normal')(x)
    x = layers.BatchNormalization()(x)
    x = layers.LeakyReLU(0.2)(x)
    x = layers.SpatialDropout2D(0.1)(x)
    # (B, 312, 64, 8) → (B, 312, 512)
    x = layers.Reshape((image_height, 512))(x)

    # --- Stage 2: Conv1D backbone FIRST (establishes features) ---
    x = layers.Conv1D(32, 7, padding='same', kernel_initializer='he_normal')(x)
    x = layers.BatchNormalization()(x)
    x = layers.LeakyReLU()(x)
    x = layers.SpatialDropout1D(0.2)(x)

    x = layers.Conv1D(64, 7, padding='same', kernel_initializer='he_normal')(x)
    x = layers.BatchNormalization()(x)
    x = layers.LeakyReLU()(x)
    x = layers.MaxPooling1D(2)(x)
    x = layers.SpatialDropout1D(0.2)(x)
    # x shape: (B, 156, 64)

    # --- Stage 3: Transformer AFTER conv (attends over meaningful features) ---
    x = transformer_block(x, num_heads=2, head_size=32, ff_dim=128, dropout=0.1)

    num_pool_layers = 1
    max_x = image_height / (num_pool_layers + 1)  # 156
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
    # Clamp last string end
    ranges[-1] = (ranges[-1][0], int(max_x) - 1)

    string_features = [
        string_layer(x, s, e, max_x, training)
        for s, e in ranges
    ]
    # Each: (B, 128) → stacked: (B, 6, 128)


    # --- Stage 5: Chord reasoning ---
    stacked = layers.Lambda(lambda t: tf.stack(t, axis=1))(string_features)
    stacked_2d = layers.Reshape((6, 128, 1))(stacked)

    chord = layers.Conv2D(64, kernel_size=(3, 7), padding='same')(stacked_2d)
    chord = layers.BatchNormalization()(chord)
    chord = layers.LeakyReLU()(chord)
    chord = layers.SpatialDropout2D(0.2)(chord)


    # --- FIXED Stage 6: Classification head ---
    chord = layers.Conv2D(32, (3, 3), padding='same')(chord)
    chord = layers.BatchNormalization()(chord)
    chord = layers.LeakyReLU()(chord)

    chord_avg = layers.GlobalAveragePooling2D()(chord)  # (B, 32)
    chord_max = layers.GlobalMaxPooling2D()(chord)      # (B, 32)
    combined = layers.Concatenate()([chord_avg, chord_max])  # (B, 64)

    # Add BN before Dense (you removed it)
    x = layers.Dense(128, kernel_initializer='he_normal')(combined)
    x = layers.BatchNormalization()(x)          # ← important, was missing
    x = layers.LeakyReLU()(x)
    x = layers.Dropout(0.3)(x)

    outputs = layers.Dense(output_dim, activation='sigmoid',
                           dtype='float32')(x)  # ← keep dtype='float32' for mixed precision safety

    return models.Model(inputs, outputs) 