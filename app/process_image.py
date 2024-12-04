# app/process_image.py

import numpy as np, io
from PIL import Image

def get_area(image, scale):
    non_black_pixels = np.count_nonzero(np.any(image != [0, 0, 0], axis=-1))
    area_km2 = (non_black_pixels * scale**2) / 10**6
    return area_km2

def preprocess(image_array, is255):
    print('In preprocess')
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
    # print("processing image", i)
    # img.save(f"./images/{i}.png")
    image_png_io = io.BytesIO()
    img.save(image_png_io, format="PNG")
    image_png_io.seek(0)
    
    return image_png_io

def preprocess_multiband(image_array, is255, i):
    """
    Preprocess a multi-band image array and save it as a PNG with transparency for zero-valued pixels.
    
    Parameters:
        image_array (np.ndarray): Input image array with shape (height, width, num_bands).
        is255 (bool): Indicates whether the image_array is already scaled to 0-255.
        output_file (str): File path to save the processed PNG image.

    Returns:
        io.BytesIO: In-memory PNG image.
    """
    if image_array.ndim != 3:
        raise ValueError("Input image_array must be a 3D array with shape (height, width, num_bands).")
    
    # Check if the number of bands is supported for saving as RGB(A)
    num_bands = image_array.shape[2]
    if num_bands < 3:
        raise ValueError("Input image_array must have at least 3 bands for RGB visualization.")
    
    # Normalize to 0-255 if needed
    if not is255:
        image_array_255 = (image_array * 255).astype(np.uint8)
    else:
        image_array_255 = image_array.astype(np.uint8)
    
    # Create an RGBA image from the first three bands
    rgba_image = np.zeros((image_array_255.shape[0], image_array_255.shape[1], 4), dtype=np.uint8)
    rgba_image[:, :, :3] = image_array_255[:, :, :3]  # Use the first 3 bands as RGB
    
    # Mask for transparency where all band values are 0
    black_pixel_mask = np.all(image_array_255 == 0, axis=-1)
    rgba_image[:, :, 3] = 255  # Set full opacity
    rgba_image[black_pixel_mask, 3] = 0  # Set transparency for black pixels
    
    # Save the image
    img = Image.fromarray(rgba_image, 'RGBA')
    # img.save(f'./images/{i}')
    
    # Save to in-memory BytesIO
    image_png_io = io.BytesIO()
    img.save(image_png_io, format="PNG")
    image_png_io.seek(0)
    
    return image_png_io