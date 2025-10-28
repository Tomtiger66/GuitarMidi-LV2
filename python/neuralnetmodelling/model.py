import tensorflow as tf
from tensorflow.keras import layers, models
def build_cnn_model(input_shape, output_dim,training=True):
    print("Building CNN model with input shape:", input_shape, "and output dim:", output_dim)
    inputs = layers.Input(shape=input_shape, dtype=tf.float32)
    
    # Conv block 1
    x = layers.Conv1D(32, 3, padding='same', use_bias=False)(inputs)
    x = layers.BatchNormalization()(x)
    x = layers.Activation('relu')(x)
    x = layers.SpatialDropout1D(0.2)(x, training=training)
    x = layers.MaxPooling1D(pool_size=2, strides=2)(x)
    
    # Conv block 2
    x = layers.Conv1D(64, 3, padding='same', use_bias=False)(x)
    x = layers.BatchNormalization()(x)
    x = layers.Activation('relu')(x)
    x = layers.SpatialDropout1D(0.2)(x, training=training)
    x = layers.MaxPooling1D(pool_size=2, strides=2)(x)
    
    # Conv block 3
    x = layers.Conv1D(128, 3, padding='same', use_bias=False)(x)
    x = layers.BatchNormalization()(x)
    x = layers.Activation('relu')(x)
    x = layers.SpatialDropout1D(0.3)(x, training=training)
    x = layers.MaxPooling1D(pool_size=2, strides=2)(x)
    
    # Global average pooling and output
    x = layers.GlobalAveragePooling1D()(x)
    x = layers.Dropout(0.2)(x, training=training)
    outputs = layers.Dense(output_dim, activation='sigmoid', dtype=tf.float32)(x)
    
    model = models.Model(inputs, outputs)
    return model


    # model = models.Sequential()
    # model.add(layers.Input(shape=input_shape, dtype=tf.float32))
    # model.add(layers.Dense(250, activation='relu', dtype=tf.float32))
    # model.add(layers.Dense(150, activation='relu', dtype=tf.float32))
    # model.add(layers.GlobalAveragePooling1D())
    # model.add(layers.Dense(output_dim, activation='sigmoid', dtype=tf.float32))
    return model