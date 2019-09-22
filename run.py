"Visualization tool for understanding trust score"
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

__author__ = 'Abien Fred Agarap'
__version__ = '1.0.0'

import sys

import matplotlib.pyplot as plt
import numpy as np
from sklearn.decomposition import PCA
import tensorflow as tf

from notebooks.models.dnn import NeuralNet
from notebooks.models.lenet import LeNet
from notebooks.models.mini_vgg import MiniVGG
from notebooks.trustscore import TrustScore

index = int(sys.argv[1])


def load_model(model_name, model_path, num_classes=10, **kwargs):
    if (model_name == 'LeNet') or (model_name == 'lenet'):
        model = LeNet(num_classes=num_classes)
    elif (model_name == 'MiniVGG') or (model_name == 'mini_vgg'):
        assert 'input_shape' in kwargs,\
                'Expected argument : [input_shape]'
        input_shape = kwargs['input_shape']
        model = MiniVGG(input_shape=input_shape, num_classes=num_classes)
    elif (model_name == 'NeuralNet') or (model_name == 'dnn'):
        assert 'input_shape' in kwargs,\
                'Expected argument : [input_shape]'
        assert 'units' in kwargs,\
            'Expected argument : [units]'
        assert 'dropout_rate' in kwargs,\
            'Expected argument : [dropout_rate]'
        input_shape = kwargs['input_shape']
        units = kwargs['units']
        dropout_rate = kwargs['dropout_rate']
        model = NeuralNet(
                input_shape=input_shape,
                units=units,
                dropout_rate=dropout_rate,
                num_classes=num_classes
                )
    model.load_weights(model_path)
    model.trainable = False
    return model


def load_data():
    (train_features, train_labels),\
            (test_features, test_labels) =\
            tf.keras.datasets.mnist.load_dta()
    train_features = train_features.astype('float32') / 255.
    train_labels = tf.keras.utils.to_categorical(train_labels)
    test_features = test_features.astype('float32') / 255.
    test_labels = tf.keras.utils.to_categorical(test_labels)

    pca = PCA(n_components=64)
    enc_train_features = pca.fit_transform(
            train_features.reshape(
                -1, train_features.shape[1] * train_features.shape[2]
                )
            )
    enc_test_features = pca.transform(
            test_features.reshape(
                -1, test_features.shape[1] * test_features.shape[2]
                )
            )
    return (train_features, train_labels),\
           (test_features, test_labels),\
           (enc_train_features, enc_test_features)


(train_features, train_labels), (test_features, test_labels) = tf.keras.datasets.mnist.load_data()
train_features = train_features.astype('float32') / 255.
train_labels = tf.keras.utils.to_categorical(train_labels)
test_features = test_features.astype('float32') / 255.
test_labels = tf.keras.utils.to_categorical(test_labels)

pca = PCA(n_components=64)
enc_train_features = pca.fit_transform(train_features.reshape(-1, 784))
enc_test_features = pca.transform(test_features.reshape(-1, 784))

ts = TrustScore(alpha=5e-2)
ts.fit(enc_train_features, train_labels)

predictions = model(test_features[index].reshape(-1, 28, 28, 1))

trust_score, closest_not_pred,\
        pred_idx, closest_not_pred_idx = ts.score(
                enc_test_features[index].reshape(-1, 64),
                predictions.numpy().reshape(1, -1)
                )

predictions = predictions.numpy().reshape(-1)
pred_idx = pred_idx[0]
closest_not_pred_idx = closest_not_pred_idx[0]

plt.figure(figsize=(15, 5))
plt.subplot(131)
plt.imshow(test_features[index].reshape(28, 28), cmap='gray')
plt.title('label : {}'.format(tf.argmax(test_labels[index])))
plt.subplot(132)
plt.imshow(test_features[pred_idx].reshape(28, 28), cmap='gray')
plt.title('predicted : {} ({:.6f})\ntrust score : {:.6f}'.format(
    tf.argmax(predictions).numpy(),
    tf.math.reduce_max(predictions),
    trust_score[0]
    ))
plt.subplot(133)
plt.imshow(test_features[closest_not_pred_idx].reshape(28, 28), cmap='gray')
plt.title('closest not predicted : {} ({:.6f})'.format(
    tf.argmax(test_labels[closest_not_pred_idx]),
    tf.math.reduce_max(test_labels[closest_not_pred_idx])
    ))
plt.show()

scatter = np.array([
    [enc_test_features[index][0], enc_test_features[index][1]],
    [enc_test_features[pred_idx][0], enc_test_features[pred_idx][1]],
    [enc_test_features[closest_not_pred_idx][0], enc_test_features[closest_not_pred_idx][1]]
            ])
print(scatter)
plt.scatter(scatter[:, 0], scatter[:, 1], alpha=0.5, c=np.arange(3))
plt.show()
