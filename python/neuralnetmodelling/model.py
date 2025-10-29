import tensorflow as tf
from tensorflow.keras import layers, models

def conv_block(x,numfilters):
    x = layers.Conv1D(numfilters, 3, padding='same', use_bias=False)(x)
    x = layers.BatchNormalization()(x)
    x = layers.Activation('relu')(x)
    return x

def build_cnn_model(input_shape, output_dim,training=True):
    return build_small_cnn_model(input_shape, output_dim,training=True)


def build_small_cnn_model(input_shape, output_dim,training=True):
    print("Building CNN model with input shape:", input_shape, "and output dim:", output_dim)
    inputs = layers.Input(shape=input_shape)
    
    # Conv block 1
    x=conv_block(inputs,32)
    x=conv_block(x,64)

    
    x = layers.MaxPooling1D(pool_size=2, strides=2)(x)
    # x = layers.SpatialDropout1D(0.2)(x, training=training)
    x = layers.Dropout(0.2)(x, training=training)
    x=conv_block(x,128)

    
    
    x = layers.MaxPooling1D(pool_size=2, strides=2)(x)
    # x = layers.SpatialDropout1D(0.3)(x, training=training)
    x = layers.Dropout(0.2)(x, training=training)

    # x = layers.GlobalAveragePooling1D()(x)
    # x=layers.Flatten()(x)
    x = layers.GlobalMaxPooling1D()(x)
    # x=layers.Dense(128,activation='linear')(x)
    x = layers.Dropout(0.2)(x, training=training)
    outputs = layers.Dense(output_dim, activation='sigmoid')(x)
    
    model = models.Model(inputs, outputs)
    return model


    # model = models.Sequential()
    # model.add(layers.Input(shape=input_shape, dtype=tf.float32))
    # model.add(layers.Dense(250, activation='relu', dtype=tf.float32))
    # model.add(layers.Dense(150, activation='relu', dtype=tf.float32))
    # model.add(layers.GlobalAveragePooling1D())
    # model.add(layers.Dense(output_dim, activation='sigmoid', dtype=tf.float32))
    return model

def build_cnn_autoencoder(input_shape, output_dim, training=True):
    inputs = layers.Input(shape=input_shape, dtype=tf.float32)
    
    # Encoder
    x = conv_block(inputs, 32)
    x = conv_block(x, 64)
    x = layers.MaxPooling1D(pool_size=2, strides=2)(x)
    x = layers.SpatialDropout1D(0.2)(x, training=training)
    x = conv_block(x, 128)
    x = layers.MaxPooling1D(pool_size=2, strides=2)(x)
    x = layers.SpatialDropout1D(0.2)(x, training=training)

    # Latent representation with 6 neurons
    x = layers.GlobalMaxPooling1D()(x)
    latent = layers.Dense(6, activation='linear', name='latent_vector')(x)
    
    # Decoder
    # Upsample from latent space
    upsample_length = output_dim  # accounting for 2 pooling layers (each halves length)
    x = layers.Dense(upsample_length * 128, activation='relu')(latent)
    x = layers.Reshape((upsample_length, 128))(x)
    
    x = layers.UpSampling1D(size=2)(x)
    x = conv_block(x, 64)
    x = layers.UpSampling1D(size=2)(x)
    x = conv_block(x, 32)
    x = layers.MaxPooling1D(pool_size=2, strides=2)(x)
    x = layers.SpatialDropout1D(0.3)(x, training=training)
    
    x = layers.GlobalMaxPooling1D()(x)
    x=layers.Dense(128,activation='linear')(x)
    x = layers.Dropout(0.2)(x, training=training)
    outputs = layers.Dense(output_dim, activation='sigmoid', dtype=tf.float32)(x)
    autoencoder = models.Model(inputs, outputs, name="autoencoder")
    return autoencoder