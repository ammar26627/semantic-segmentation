import numpy as np, io
from PIL import Image

def get_area(image, scale):
    count = np.count_nonzero(image)
    return (count*scale)/10**6

def preprocess(image_array, is255):
    if image_array.ndim != 3 or image_array.shape[2] != 3:
        raise ValueError("Input image_array must be an RGB image array with shape (height, width, 3).")
    
    if not is255:
        image_array_255 = (image_array * 255).astype(np.uint8)
    else:
        image_array_255 = image_array
    black_pixel_mask = np.all(image_array_255 == [0, 0, 0], axis=-1)

    rgba_image = np.zeros((image_array_255.shape[0], image_array_255.shape[1], 4), dtype=np.uint8)
    rgba_image[:, :, :3] = image_array_255
    rgba_image[:, :, 3] = 255
    rgba_image[black_pixel_mask, 3] = 0
    img = Image.fromarray(rgba_image, 'RGBA')
    image_png_io = io.BytesIO()
    img.save(image_png_io, format="PNG")
    image_png_io.seek(0)
    
    return image_png_io