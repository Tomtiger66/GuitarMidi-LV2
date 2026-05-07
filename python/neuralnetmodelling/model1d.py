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
from tensorflow.keras import layers, models
from tensorflow.keras.models import Model
from common import OUTPUT_DIM_NOTES,image_height,image_width

    # --- Configuration for your specific input ---
IMG_H, IMG_W = 312, 256  
NUM_CLASSES = 89        
PATCH_H, PATCH_W = 24, 16 # Chosen patch size
CHANNELS = 1            
HIDDEN_D = 384           # Chosen hidden dimension
TRANSFORMER_LAYERS = 4   # Chosen layer count
NUM_HEADS = 6            # Chosen number of heads (divisor of 384)
DROPOUT_RATE = 0.1
def conv_block(x,numfilters):
    x = layers.Conv1D(numfilters, 3, padding='same', activation=None)(x)
    x = layers.BatchNormalization()(x)
    x = layers.Activation('relu')(x)
    return x
def partitioned_average_pooling(x):
    splits = tf.split(x, [7,7,7,6,6,6], axis=1)   # sum=39 height slices
    pooled = [tf.reduce_mean(part, axis=[1,2]) for part in splits]
    return tf.concat(pooled, axis=1)

def partitioned_average_pooling_1d(x):
    splits = tf.split(x, [7,7,7,6,6,6], axis=1)   # sum=39 height slices
    pooled = [tf.reduce_mean(part, axis=[1]) for part in splits]
    return tf.concat(pooled, axis=1)

def build_1d_cnn_model(batch_sz=64, input_shape=(image_height, image_width), output_dim=OUTPUT_DIM_NOTES, training=True,
                       gru_units=128, gru_layers=1, bidirectional=True, stateful=False):  # Added GRU params
    print("Building CNN model with input shape:", input_shape, "and output dim:", output_dim)
    inputs = layers.Input(shape=input_shape)
    x=layers.Lambda(lambda x: tf.reduce_max(x, axis=2))(inputs)
    # Conv block 1
    x=conv_block(x,32)
    x = layers.MaxPooling1D(4)(x)
    x = layers.SpatialDropout1D(0.2)(x, training=training)
    x=conv_block(x,64)

    
    x = layers.MaxPooling1D(2)(x)
    x = layers.SpatialDropout1D(0.2)(x, training=training)
    # x = layers.Dropout(0.2)(x, training=training)
    x=conv_block(x,64)

    
    
    x = layers.MaxPooling1D(2)(x)
    x = layers.SpatialDropout1D(0.3)(x, training=training)
    # x = layers.Dropout(0.2)(x, training=training)

    x = layers.GlobalAveragePooling1D()(x)
    # x=layers.Flatten()(x)
    # x = layers.GlobalMaxPooling1D()(x)
    # x=layers.Dense(128,activation='linear')(x)
    x = layers.Dropout(0.4)(x, training=training)
    outputs = layers.Dense(output_dim, activation='sigmoid')(x)
    
    model = models.Model(inputs, outputs)
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