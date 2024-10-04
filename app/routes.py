# app/route.py

from flask import jsonify, send_file, request, Blueprint, session
from app.process_image import preprocess, get_area
from app.extras import log_resource_usage, intro
from app.models import Models
from app.mask import ImageMask
from app.gee_image import GeeImage
import base64
from collections import defaultdict
from googleapiclient.errors import HttpError
# from test import test


# Create a Blueprint for routes
api_bp = Blueprint('api', __name__)


@api_bp.route('/get_gee_image', methods=['POST'])
def gee_image():
    """
    Endpoint to get a Google Earth Engine image based on the region of interest (ROI).
    """
    image = GeeImage()
    roi_data = request.json
    try:
        image.setRoiData(roi_data)  # Set the ROI in the image
        image.getImage()  # Fetch the image based on ROI
    except HttpError as e:
        return 'Selected ROI is too large. Select between between scale of 2 and 3.', 400
    except Exception as e:
        return 'An error has occured while fetching satellite imagery. Please refresh and retry', 400

    norm_image = image.getNormalizedImage()  # Normalize the image for processing

    if 'image' not in session:
        session['image'] = image
    image_png = preprocess(norm_image, False)  # Preprocess the image (Remove black background)
    
    # Send the image as a response
    return send_file(image_png, mimetype='image/png'), 200

@api_bp.route('/get_mask', methods=['POST'])
def generate_mask():
    """
    Endpoint to generate a colored mask based on class data.
    """
    class_data = request.json
    print(class_data)
    if 'image' in session:
        image = session['image']
        mask = Models(image.bands, image.scale, image.img_array, image.sentinal_image, image.start_date, image.end_date)
    else:
        return 'Please select an ROI first. If the problem persist, enable cookies in the browser.', 400
    
    # try:
    #     print(image.roi)
    #     image.setClassData(class_data)  # Set the class data in the image
    #     colored_mask_pngs = image.getColoredMask()  # Get the colored mask images
    # except Exception as e:
    #     print(e)
    #     return 'Error while generating mask. Please refresh and retry.', 400
    mask.setClassData(class_data)  # Set the class data in the image
    colored_mask_pngs = mask.getColoredMask()  # Get the colored mask images
    response = defaultdict()

    for key, value in colored_mask_pngs.items():
        area = get_area(value, mask.scale)  # Calculate area
        png_mask = preprocess(value, True)  # Preprocess the mask (Remove black background)
        base_64 = base64.b64encode(png_mask.getvalue()).decode('utf-8')  # Convert to base64
        response[key] = [base_64, 1, area]  # Build the response dictionary

    # Empty the session variable
    # session.pop('image', None)

    return jsonify(response)

@api_bp.route("/resource_usage")
def checkResource():

    return log_resource_usage(), 200

@api_bp.route('/')
def default():
    # test()
    return intro(), 200
