# Analyzing Deep Learning Models based on Trust Score
# Copyright (C) 2019  Abien Fred Agarap
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
"""Utility functions module"""
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

__version__ = "1.0.1"

import matplotlib.cm as cm
import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns
from sklearn.decomposition import PCA
from sklearn.model_selection import StratifiedShuffleSplit
import tensorflow as tf
from trustscore import TrustScore

np.random.seed(42)


def create_dataset(features, labels, batch_size):
    dataset = tf.data.Dataset.from_tensor_slices((features, labels))
    dataset = dataset.shuffle(features.shape[0])
    dataset = dataset.prefetch(batch_size * 8)
    dataset = dataset.batch(batch_size, True)
    return dataset


def run_model(model, train_features, train_labels, test_features):
    model.fit(train_features, train_labels, batch_size=128, epochs=5, verbose=0)
    predicted_prob_dist = model.predict(test_features)
    predicted_class = tf.argmax(predicted_prob_dist, axis=1)
    likelihood = predicted_prob_dist[range(len(predicted_class)), predicted_class]
    return predicted_class, likelihood


def plot_precision_curve(
    plot_title,
    percentiles,
    labels,
    final_tp,
    final_stderr,
    final_misclassification,
    colors=["blue", "darkorange", "brown", "red", "purple"],
):
    sns.set_style("dark")
    plt.title(plot_title, fontsize=18)
    colors = colors + list(cm.rainbow(np.linspace(0, 1, len(final_tp))))
    plt.xlabel("Percentile", fontsize=14)
    plt.ylabel("Precision", fontsize=14)

    for i, label in enumerate(labels):
        ls = "--" if ("Model" in label) else "-"
        plt.plot(percentiles, final_tp[i], ls, c=colors[i], label=label)
        plt.fill_between(
            percentiles,
            final_tp[i] - final_stderr[i],
            final_tp[i] + final_stderr[i],
            color=colors[i],
            alpha=0.1,
        )

    if 0.0 in percentiles:
        plt.legend(loc="lower right", fontsize=14)
    else:
        plt.legend(loc="upper left", fontsize=14)
    model_acc = 100 * (1 - final_misclassification)
    plt.axvline(x=model_acc, linestyle="dotted", color="black")
    plt.grid()
    plt.show()


def run_precision_plt(
    features,
    labels,
    nfolds,
    percentiles,
    run_model,
    test_size=2e-1,
    plt_title="",
    plt_names=[],
    predict_correct=True,
    classes=10,
    model=None,
):
    def stderr(L):
        return np.std(L) / np.sqrt(len(L))

    all_tp = [[[] for p in percentiles] for _ in plt_names]
    misclassifications = []
    mult = 1 if predict_correct else -1

    folds = StratifiedShuffleSplit(
        n_splits=nfolds, test_size=test_size, random_state=42
    )

    for train_idx, val_idx in folds.split(features, labels):
        train_features, train_labels = features[train_idx, :], labels[train_idx, :]
        val_features, val_labels = features[val_idx, :], labels[val_idx, :]

        predicted_class, likelihood = run_model(
            model, train_features, train_labels, val_features
        )

        val_class = tf.argmax(val_labels, axis=1)
        target_points = (
            np.where(predicted_class.numpy() == val_class.numpy())[0]
            if predict_correct
            else np.where(predicted_class.numpy() != val_class.numpy())[0]
        )
        final_curves = [likelihood]

        pca = PCA(n_components=64)
        if len(train_features.shape) == 2:
            enc_train_features = pca.fit_transform(train_features)
            enc_val_features = pca.transform(val_features)
        else:
            enc_train_features = pca.fit_transform(train_features.reshape(-1, 784))
            enc_val_features = pca.transform(val_features.reshape(-1, 784))

        ts = TrustScore()
        ts.fit(enc_train_features, train_labels, classes=classes)
        scores, _, _, _, _, _ = ts.score(enc_val_features, predicted_class, k=5)
        final_curves.append(scores)

        for p, perc in enumerate(percentiles):
            high_proba = [
                np.where(mult * curve >= np.percentile(mult * curve, perc))[0]
                for curve in final_curves
            ]
            if 0 in map(len, high_proba):
                continue

            tp = [
                len(np.intersect1d(hp, target_points)) / (1.0 * len(hp))
                for hp in high_proba
            ]
            for i in range(len(plt_names)):
                all_tp[i][p].append(tp[i])

        misclassifications.append(len(target_points) / (1.0 * len(val_features)))

    final_tp = [[] for _ in plt_names]
    final_stderr = [[] for _ in plt_names]
    for p, perc in enumerate(percentiles):
        for i in range(len(plt_names)):
            final_tp[i].append(np.mean(all_tp[i][p]))
            final_stderr[i].append(stderr(all_tp[i][p]))

    for i in range(len(all_tp)):
        final_tp[i] = np.array(final_tp[i])
        final_stderr[i] = np.array(final_stderr[i])

    final_misclassification = np.mean(misclassifications)

    plot_precision_curve(
        plt_title,
        percentiles,
        plt_names,
        final_tp,
        final_stderr,
        final_misclassification,
    )
