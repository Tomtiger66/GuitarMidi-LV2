import tensorflow as tf
from tensorflow.keras import layers, models
def build_cnn_model(input_shape, output_dim,training=True):
    print("Building CNN model with input shape:", input_shape, "and output dim:", output_dim)
    model = models.Sequential()
    model.add(layers.Input(shape=input_shape, dtype=tf.float32))

    # Conv block 1
    model.add(layers.Conv1D(filters=32, kernel_size=3, padding='same', use_bias=False))
    model.add(layers.BatchNormalization())
    model.add(layers.Activation('relu'))
    if training:
        model.add(layers.SpatialDropout1D(0.2))
    model.add(layers.MaxPooling1D(pool_size=2, strides=2))

    # Conv block 2
    model.add(layers.Conv1D(filters=64, kernel_size=3, padding='same', use_bias=False))
    model.add(layers.BatchNormalization())
    model.add(layers.Activation('relu'))
    if training:
        model.add(layers.SpatialDropout1D(0.2))
    model.add(layers.MaxPooling1D(pool_size=2, strides=2))

    # Conv block 3
    model.add(layers.Conv1D(filters=128, kernel_size=3, padding='same', use_bias=False))
    model.add(layers.BatchNormalization())
    model.add(layers.Activation('relu'))
    if training:
        model.add(layers.SpatialDropout1D(0.3))
    model.add(layers.MaxPooling1D(pool_size=2, strides=2))

    model.add(layers.GlobalAveragePooling1D())
    if training:
        model.add(layers.Dropout(0.2))
    model.add(layers.Dense(output_dim, activation='sigmoid', dtype=tf.float32))

    return model