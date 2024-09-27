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
        elif self.model == 'maximum likelyhood':
            pass
        elif self.model == 'random forest':
            pass
        else:
            pass
        return self.colored_mask

    
    def mahalanobis(self):
        def classify_pixel(pixel, means, cov, thresholds):
            distances = {}
            for i, key in enumerate(means, 1):
                inv_cov = np.linalg.inv(cov[key])
                distance = mahalanobis(pixel, means[key], inv_cov)
                if distance < thresholds[key]:
                    distances[i] = distance
            return min(distances, key=distances.get) if distances else 0
        classified_pixels = np.zeros(self.img_array.shape[:2], dtype=np.int32)
        for i in range(self.img_array.shape[0]):
            for j in range(self.img_array.shape[1]):
                pixel = self.img_array[i, j]
                classified_pixels[i, j] = classify_pixel(pixel, self.mean, self.cov, self.threshold)
        self.colorMask(classified_pixels)


    def maximumLikelyHood(self):
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
        self.classified_pixels = np.array(classified_labels).reshape(self.img_array.shape[0], self.img_array.shape[1])
        self.classified_pixels[self.classified_pixels == None] = 0 

    
    def colorMask(self, classified_pixels):
        for key, value in self.features.items():
            mask = np.zeros((classified_pixels.shape[0], classified_pixels.shape[1], 3), dtype=np.uint8)
            for i in range(classified_pixels.shape[0]):
                for j in range(classified_pixels.shape[1]):
                    mask[i][j] = self.color_map.get(classified_pixels[i][j], self.color_map[None])
            self.colored_mask[key] = mask
