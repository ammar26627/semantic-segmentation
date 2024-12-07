import numpy as np
from collections import defaultdict

class DeepLearning:
    def __init__(self, model):
        self.model = model
        self.features = {'Shrubs_and_Scrubs': 1,
                         'Grass': 2, 
                         'Agriculture': 3, 
                         'Built': 4, 
                         'Barren': 5, 
                         'Snow': 6, 
                         'Water': 7, 
                         'Flooded_Vegetation': 8, 
                         'Trees': 9}
        self.color_map = {
                0: [0, 0, 0],        # Unlabeled (Black)
                1: [90, 195, 223],   # Shrub_And_Scrub (BGR)
                2: [83, 176, 136],   # Grass
                3: [53, 150, 228],   # Crops
                4: [27, 40, 196],    # Built
                5: [143, 155, 165],  # Bare
                6: [225, 159, 179],  # Snow_And_Ice
                7: [223, 155, 65],   # Water
                8: [198, 135, 122],  # Flooded_Vegetation
                9: [73, 125, 57],    # Trees
                None: [0, 0, 0]      # Unlabeled (Black)
            }
        self.output_pixels = []
        self.colored_mask = defaultdict()
        self.binary_masks = defaultdict()

    def unet(self, img_array):
        padded_arrays = self.split_and_pad_array(img_array, 256)
        predictions_padded_arrays = []
        for padded_array in padded_arrays:
            prediction = self.predict(padded_array)
            predicted_labels = np.squeeze(prediction)
            predictions_padded_arrays.append(np.argmax(predicted_labels, axis=-1))
        self.output_pixels = self.merge_arrays(predictions_padded_arrays)
        self.colorMask(img_array)

    def colorMask(self, img_array):
        non_zero_mask = np.any(img_array != 0, axis=-1)
        for key, value in self.features.items():
            mask = np.zeros((img_array.shape[0], img_array.shape[1], 3), dtype=np.uint8)
            for i in range(img_array.shape[0]):
                for j in range(img_array.shape[1]):
                    if non_zero_mask[i, j]:
                        if self.output_pixels[i][j] == value:
                            mask[i][j] = self.color_map.get(value, self.color_map[None])
                        else:
                            mask[i][j] = self.color_map.get(None)
                    else:
                        mask[i][j] = self.color_map.get(None)
            self.colored_mask[key] = mask


    def getColoredMask(self):
        return self.colored_mask


    @staticmethod
    def predict(self, img_array):
        input_image = np.expand_dims(img_array, axis=0)
        predicted_mask = self.model.predict(input_image)
        predicted_mask = np.squeeze(predicted_mask)
        predicted_mask = np.argmax(predicted_mask, axis=-1)
        return predicted_mask

    @staticmethod
    def split_and_pad_array(array, target_size):
        padded_arrays = []

        for i in range(0, array.shape[0], target_size):
            for j in range(0, array.shape[1], target_size):
                # Extract the subarray
                sub_array = array[i : i + target_size, j : j + target_size]

                # Calculate the padding sizes
                pad_height = target_size - sub_array.shape[0]
                pad_width = target_size - sub_array.shape[1]

                # Pad the subarray with [0, 0, 0]
                padded_sub_array = np.pad(
                    sub_array,
                    ((0, pad_height), (0, pad_width), (0, 0)),
                    mode="constant",
                    constant_values=0,
                )
                padded_arrays.append(padded_sub_array)

        return padded_arrays


    @staticmethod
    def merge_arrays(padded_arrays, original_shape, target_size):
        reconstructed_array = np.zeros(original_shape, dtype=padded_arrays[0].dtype)
        index = 0
        for i in range(0, original_shape[0], target_size):
            for j in range(0, original_shape[1], target_size):
                end_i = min(i + target_size, original_shape[0])
                end_j = min(j + target_size, original_shape[1])
                sub_array = padded_arrays[index][: end_i - i, : end_j - j]
                reconstructed_array[i:end_i, j:end_j] = sub_array
                index += 1
        return reconstructed_array
