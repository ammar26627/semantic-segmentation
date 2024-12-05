# app/route.py

# from app import socketio
from flask import jsonify, send_file, request, Blueprint, session, Response
from app.process_image import preprocess, get_area, preprocess_multiband
from app.extras import log_resource_usage, intro
from app.models import Models
from app.mask import ImageMask
from app.gee_image import GeeImage
import base64, json, threading
from queue import Queue
from collections import defaultdict
from googleapiclient.errors import HttpError
from app.image_thread import ImageThread
from flask_socketio import SocketIO, emit
from app.combine_image import merge_images_with_geojson
from PIL import Image


ip_set = set()

# Create a Blueprint for routes
api_bp = Blueprint('api', __name__)




@api_bp.route('/get_gee_image', methods=['POST'])
def gee_image():
    """
    Endpoint to get a Google Earth Engine image based on the region of interest (ROI).
    """
    roi_data = request.json
    roi_data = {
    "geojson": [
        {
            "type": "Feature",
            "properties": {
                "roi": "Aligarh",
                "fill": "#800080"
            },
            "geometry": {
                "type": "Polygon",
                "coordinates": [
                    [
                        [
                            76.59221687258076,
                            28.979550388465597
                        ],
                        [
                            76.59221687258076,
                            28.148311356185218
                        ],
                        [
                            77.86516932883694,
                            28.148311356185218
                        ],
                        [
                            77.86516932883694,
                            28.979550388465597
                        ],
                        [
                            76.59221687258076,
                            28.979550388465597
                        ]
                    ]
                ]
            }
        }
    ],
    "bands": {
        "band1": "B4",
        "band2": "B3",
        "band3": "B2"
    },
    "height": 30
}
    # Initialize GeeImage and set ROI
    image = GeeImage()
    # with open('app/Andaman_and_Nicobar.json') as f:
    #     roi_data = json.load(f)
    image.setRoiData(roi_data)  # Set the ROI in the image

    session['image'] = image



    return jsonify({'status': "Stream Started"}), 200
    # def generate():
    #     while True:
    #         message = sse_queue.get()  # Blocks until a message is available
    #         if message == "Done":
    #             break
    #         yield f"data: {json.dumps(message)}\n\n"

    # image_thread = ImageThread(function=image.getImage, sse_queue=sse_queue)
    # # image_thread.image_with_thread_pool(num_threads=4, items=image.roi_array)
    # threading.Thread(target=image_thread.image_with_thread_pool, args=(4, image.roi_array)).start()

    # # Signal the end of the stream
    # # sse_queue.put("DONE")

    # # Return an SSE response
    # return Response(generate(), mimetype='text/event-stream')

@api_bp.route('/stream_images', methods=['GET'])
def stream_images():
    """
    SSE endpoint to stream processed images.
"""
    # Retrieve ROI array from session
    image = session.get('image')
    try:
        if not image.roi_array:
            return jsonify({'error': 'No ROI data found'}), 400
    except Exception as e:
        print(e)


    sse_queue = Queue()

    def generate():
        while True:
            message = sse_queue.get()
            if message['status'] == "Completed":
                # yield message
                # print("Completed straming now saving image")
                # merger = merge_images_with_geojson(image.img_array, 30)
                # print(merger)
                
                # preprocessed_image = preprocess(merger, False)
                
                # with open("combine.png", "wb") as f:
                #     f.write(preprocessed_image.getvalue())
                # print("sent")
                yield f"data: {json.dumps({'status': 'done'})}\n\n"
                break
            yield f"data: {json.dumps(message)}\n\n"

    image_thread = ImageThread(image.getImage, sse_queue)
    threading.Thread(target=image_thread.image_with_thread_pool, args=(50, image.roi_array)).start()
    return Response(generate(), mimetype='text/event-stream')
    # return "200", 200

# @api_bp.route('/get_big_images', methods=['GET'])
# def large_image():
#     img_array = session.get('array')
#     print(img_array)
#     combined_image = merge_images(img_array, 30)
#     preprocessed_image = preprocess(combined_image, False)
#     return send_file(
#             preprocessed_image, 
#             mimetype="image/png", 
#         )


@api_bp.route('/get_mask', methods=['POST'])
def get_mask():
    """
    Endpoint to get a Google Earth Engine image based on the region of interest (ROI).
    """
    class_data = request.json
    image_mask = ImageMask()
    image_mask.setClassData(class_data)

    session['image_mask'] = image_mask


    return jsonify({'status': "Stream Started"}), 200

@api_bp.route('/get_mask_stream', methods=['GET'])
def generate_mask():
    """
    Endpoint to generate a colored mask based on class data.
    """
    class_data = request.json
    if 'image' in session:
        image = session['image']
        image_mask = session['image_mask']
    else:
        return 'Please select an ROI first. If the problem persist, enable cookies in the browser.', 400
    
    mask_queue = Queue()
    def generate():
        while True:
            message = mask_queue.get()
            if message['status'] == "Completed":
                yield f"data: {json.dumps(message)}\n\n"
                break
            yield f"data: {json.dumps(message)}\n\n"
    image_thread = ImageThread(helper=image_mask, sse_queue=mask_queue)
    threading.Thread(target=image_thread.image_with_thread_pool, args=(4, image.roi_array, True)).start()
    return Response(generate(), mimetype='text/event-stream')

    mask = Models(image.bands, image.scale, image.img_array, image.start_date, image.end_date)
    
    try:
        mask.setClassData(class_data)  # Set the class data in the image
        colored_mask_pngs = mask.getColoredMask()  # Get the colored mask images
    except Exception as e:
        return 'Error while generating mask. Please refresh and retry.', 400

    response = defaultdict()
    for key, value in colored_mask_pngs.items():
        area = get_area(value, mask.scale)  # Calculate area
        png_mask = preprocess(value, True)  # Preprocess the mask (Remove black background)
        base_64 = base64.b64encode(png_mask.getvalue()).decode('utf-8')  # Convert to base64
        response[key] = [base_64, 1, area]  # Build the response dictionary

    # Empty the session variable
    session.pop('image', None)
    session.pop('band', None)
    session.pop('scale', None)
    session.pop('start_date', None)
    session.pop('end_date', None)

    return jsonify(response)

@api_bp.route("/image-url")
def image_url():
    image = GeeImage()
    roi_data = request.json
    try:
        image.setRoiData(roi_data)  # Set the ROI in the image
        image_url = image.getImageUrl()  # Fetch the image based on ROI
        session["band"] = image.bands
        session["scale"] = image.scale
        session["start_date"] = image.start_date
        session["end_date"] = image.end_date
        session["image_url"] = image_url
        response = {"image_url": image_url}
        return jsonify(response), 200
    except Exception as e:
        return (
            "Selected ROI too large. Please select an area less scale of 5 KM. Please refresh and retry",
            400,
        )

@api_bp.route("/resource_usage")
def checkResource():
    return log_resource_usage(), 200

@api_bp.route('/')
def default():
    return intro(), 200

@api_bp.route('/get_ip')
def ip():
    ip_address = list(ip_set)
    return jsonify(ip_address), 200

@api_bp.route('/set_ip')
def set_ip():
    ip_address = request.headers.get('X-Forwarded-For', request.remote_addr)
    ip_set.add(ip_address)
    return "Ip Recieved", 200

