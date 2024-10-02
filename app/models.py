# app/models.py

from app.mask import ImageMask
from scipy.spatial.distance import mahalanobis
from scipy.stats import multivariate_normal
import numpy as np
from collections import defaultdict
from sklearn.ensemble import RandomForestClassifier

class Models(ImageMask):
    def __init__(self) -> None:
        super().__init__()
        self.colored_mask = defaultdict()
        self.binary_masks = defaultdict()

    def getColoredMask(self):
        if self.model == 'Mahalanobis Distance Classifier':
            self.mahalanobis()
        elif self.model == 'Maximum Likelyhood Classifier':
            self.maximumLikelyHood()
        elif self.model == 'Random Forest Classifier':
            self.randomForest()
        else:
            self.parallelepiped()

        return self.colored_mask

    
    def mahalanobis(self): 
        for key, value in self.threshold.items():
            self.threshold[key] = int(value)
        def classify_pixel(pixel, means, thresholds, inv_cov_key):
            distances = {}
            for i, key in enumerate(means, 1):
                distance = mahalanobis(pixel, means[key], inv_cov_key[key])
                if distance < thresholds[key]:
                    distances[i] = distance
            return min(distances, key=distances.get) if distances else 0
        
        inv_cov_key = {}
        for key, value in self.cov.items():
            inv_cov_key[key] = np.linalg.inv(value)

        classified_pixels = np.zeros(self.img_array.shape[:2], dtype=np.int32)
        for i in range(self.img_array.shape[0]):
            for j in range(self.img_array.shape[1]):
                pixel = self.img_array[i, j]
                classified_pixels[i, j] = classify_pixel(pixel, self.mean, self.threshold, inv_cov_key)
        self.colorMask(classified_pixels)


    def maximumLikelyHood(self):
        threshold = 10**(-int(self.threshold))
        height, width, _ = self.img_array.shape
        classified_pixels = np.empty((height, width), dtype=int)
        for i in range(height):
            for j in range(width):
                pixel = self.img_array[i, j]
                max_likelihood = -np.inf
                classified_pixels[i, j] = 0
                for k, key in enumerate(self.mean, 1):
                    likelihood = multivariate_normal(mean=self.mean[key], cov=self.cov[key]).pdf(pixel)
                    if likelihood > max_likelihood and likelihood > threshold:
                        max_likelihood = likelihood
                        classified_pixels[i, j] = k
        self.colorMask(classified_pixels)

    def randomForest(self):
        random_forest =  RandomForestClassifier(n_estimators=100, random_state=25)
        random_forest.fit(self.X_train, self.y_train)
        unclassified_pixel_values = self.img_array.reshape((-1, len(self.bands)))
        classified_labels = random_forest.predict(unclassified_pixel_values)
        classified_pixels = np.array(classified_labels).reshape(self.img_array.shape[0], self.img_array.shape[1])
        self.colorMask(classified_pixels)

    def parallelepiped(self):
        parallelepiped_model = ParallelepipedClassifier()
        parallelepiped_model.fit(self.X_train, self.y_train)
        unclassified_pixel_values = self.img_array.reshape((-1, len(self.bands)))
        labels = parallelepiped_model.classify(unclassified_pixel_values)
        classified_labels = np.array(labels).reshape(self.img_array.shape[0], self.img_array.shape[1])
        classified_pixels = np.array(classified_labels).reshape(self.img_array.shape[0], self.img_array.shape[1])
        classified_pixels[classified_pixels == None] = 0
        self.colorMask(classified_pixels)

    
    def colorMask(self, classified_pixels):
        for key, value in self.features.items():
            mask = np.zeros((classified_pixels.shape[0], classified_pixels.shape[1], 3), dtype=np.uint8)
            for i in range(classified_pixels.shape[0]):
                for j in range(classified_pixels.shape[1]):
                    if classified_pixels[i][j] == value:
                        mask[i][j] = self.color_map.get(value, self.color_map[None])
                    else:
                        mask[i][j] = self.color_map.get(None)
            self.colored_mask[key] = mask



# Parallelepiped Model Class

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

