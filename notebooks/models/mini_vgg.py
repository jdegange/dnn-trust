from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

__version__ = '1.0.0'

import tensorflow as tf


class MiniVGG(tf.keras.Model):
    def __init__(self, **kwargs):
        super(MiniVGG, self).__init__()
        self.conv1_layer_1 = tf.keras.layers.Conv2D(
                32,
                (3, 3),
                activation=tf.nn.relu,
                input_shape=kwargs['input_shape']
                )
        self.conv1_layer_2 = tf.keras.layers.Conv2D(
                32,
                (3, 3),
                activation=tf.nn.relu
                )
        self.pool_layer_1 = tf.keras.layers.MaxPooling2D(
                pool_size=(2, 2)
                )
        self.conv2_layer_1 = tf.keras.layers.Conv2D(
                64,
                (3, 3),
                activation=tf.nn.relu
                )
        self.conv2_layer_2 = tf.keras.layers.Conv2D(
                64,
                (3, 3),
                activation=tf.nn.relu
                )
        self.pool_layer_2 = tf.keras.layers.MaxPooling2D(
                pool_size=(2, 2)
                )
        self.dropout_layer_1 = tf.keras.layers.Dropout(rate=0.25)
        self.flatten = tf.keras.layers.Flatten()
        self.fc_layer = tf.keras.layers.Dense(
                units=256,
                activation=tf.nn.relu
                )
        self.dropout_layer_2 = tf.keras.layers.Dropout(rate=0.50)
        self.output_layer = tf.keras.layers.Dense(
                units=kwargs['num_classes'],
                activation=tf.nn.softmax
                )

    @tf.function
    def call(self, features):
        activation = self.conv1_layer_1(features)
        activation = self.conv1_layer_2(activation)
        activation = self.pool_layer_1(activation)
        activation = self.conv2_layer_1(activation)
        activation = self.conv2_layer_2(activation)
        activation = self.pool_layer_2(activation)
        activation = self.dropout_layer_1(activation)
        activation = self.flatten(activation)
        activation = self.fc_layer(activation)
        activation = self.dropout_layer_2(activation)
        output = self.output_layer(activation)
        return output