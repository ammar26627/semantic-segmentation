# app/parallelepiped.py

import numpy as np

class ParallelepipedClassifier:
    def __init__(self):
        self.thresholds = {}

    def fit(self, X, y):
        classes = np.unique(y)
        for cls in classes:
            class_data = X[y == cls]
            min_values = np.min(class_data, axis=0)
            max_values = np.max(class_data, axis=0)
            self.thresholds[cls] = (min_values, max_values)

    def classify(self, X):
        labels = []
        for point in X:
            label = self._classify_point(point)
            labels.append(label)
        return labels

    def _classify_point(self, point):
        for label, (min_values, max_values) in self.thresholds.items():
            if np.all(point >= min_values) and np.all(point <= max_values):
                return label
        return None
