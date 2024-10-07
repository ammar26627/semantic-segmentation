# app/models.py

from app.mask import ImageMask
from scipy.spatial.distance import mahalanobis
from scipy.stats import multivariate_normal
import numpy as np
from collections import defaultdict
from sklearn.ensemble import RandomForestClassifier

class Models(ImageMask):
    def __init__(self, bands, scale, img_array, start_date, end_date) -> None:
        super().__init__(bands, scale, img_array, start_date, end_date)
        reshaped_array = self.img_array.reshape((-1, len(self.bands)))
        self.non_zero_mask = (reshaped_array != 0).any(axis=1)
        self.non_zero_img_array = reshaped_array[self.non_zero_mask]
        self.output_pixels = np.zeros(self.non_zero_img_array.shape[0], dtype=np.int32)
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
            for key, i in self.features.items():
                distance = mahalanobis(pixel, means[key], inv_cov_key[key])
                if distance < thresholds[key]:
                    distances[i] = distance
            return min(distances, key=distances.get) if distances else 0
        
        inv_cov_key = {}
        for key, value in self.cov.items():
            inv_cov_key[key] = np.linalg.inv(value)

        for i, pixel in enumerate(self.non_zero_img_array):
            self.output_pixels[i] = classify_pixel(pixel, self.mean, self.threshold, inv_cov_key)
        self.colorMask()


    def maximumLikelyHood(self):
        threshold = 10**(-int(self.threshold))
        for i, pixel in enumerate(self.non_zero_img_array):
            max_likelihood = -np.inf
            for key, k in self.features.items():
                likelihood = multivariate_normal(mean=self.mean[key], cov=self.cov[key]).pdf(pixel)
                if likelihood > max_likelihood and likelihood > threshold:
                    max_likelihood = likelihood
                    self.output_pixels[i] = k
        self.colorMask()

    def randomForest(self):
        random_forest =  RandomForestClassifier(n_estimators=100, random_state=25)
        random_forest.fit(self.X_train, self.y_train)
        self.output_pixels = random_forest.predict(self.non_zero_img_array)
        self.colorMask()

    def parallelepiped(self):
        parallelepiped_model = ParallelepipedClassifier()
        parallelepiped_model.fit(self.X_train, self.y_train)
        self.output_pixels = parallelepiped_model.classify(self.non_zero_img_array)
        self.colorMask()

    
    def colorMask(self):
        non_zero_mask = np.any(self.img_array != 0, axis=-1)
        for key, value in self.features.items():
            mask = np.zeros((self.img_array.shape[0], self.img_array.shape[1], 3), dtype=np.uint8)
            k = 0
            for i in range(self.img_array.shape[0]):
                for j in range(self.img_array.shape[1]):
                    if non_zero_mask[i, j]:
                        if self.output_pixels[k] == value:
                            mask[i][j] = self.color_map.get(value, self.color_map[None])
                        else:
                            mask[i][j] = self.color_map.get(None)
                        k += 1
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

