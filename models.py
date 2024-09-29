from mask import ImageMask
from scipy.spatial.distance import mahalanobis
from scipy.stats import multivariate_normal
import numpy as np
from collections import defaultdict
from parallelepiped import ParallelepipedClassifier
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
        elif self.model == 'random forest':
            pass
        else:
            self.parallelepiped()
        return self.colored_mask

    
    def mahalanobis(self):
        def classify_pixel(pixel, means, cov, thresholds, inv_cov_key):
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
                classified_pixels[i, j] = classify_pixel(pixel, self.mean, self.cov, self.threshold, inv_cov_key)
        self.colorMask(classified_pixels)


    def maximumLikelyHood(self):
        self.threshold = 1e-10 #hard code
        height, width, _ = self.img_array.shape
        classified_pixels = np.empty((height, width), dtype=int)
        for i in range(height):
            for j in range(width):
                pixel = self.img_array[i, j]
                max_likelihood = -np.inf
                classified_pixels[i, j] = 0
                for k, key in enumerate(self.mean, 1):
                    likelihood = multivariate_normal(mean=self.mean[key], cov=self.cov[key]).pdf(pixel)
                    if likelihood > max_likelihood and likelihood > self.threshold:
                        max_likelihood = likelihood
                        classified_pixels[i, j] = k
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
