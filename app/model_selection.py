import numpy as np
import cv2
from shapely.geometry import Polygon

def process_roi_selection(roi_arrays, selected_array):
    """
    Process the selected area and check if it's within any of the multiple ROIs.
    If the selected area overlaps multiple ROIs, assign it to the ROI with the most overlap.
    
    Parameters:
    - roi_arrays: List of arrays containing coordinates of multiple ROIs.
    - selected_array: Array containing coordinates of the selected region.
    """
    def get_overlap_area(selected_region, roi_region):
        """
        Calculate the overlap area between the selected region and a given ROI.

        Parameters:
        - selected_region: List of tuples [(x1, y1), (x2, y2), (x3, y3), (x4, y4)] representing the coordinates of the selected region.
        - roi_region: List of tuples [(x1, y1), (x2, y2), (x3, y3), (x4, y4)] representing the coordinates of the ROI.

        Returns:
        - The area of overlap between the selected region and the ROI.
        """
        # Create Polygon objects using Shapely
        selected_polygon = Polygon(selected_region)
        roi_polygon = Polygon(roi_region)

        # Calculate the intersection area between the selected region and the ROI
        intersection = selected_polygon.intersection(roi_polygon)
        
        # Return the area of the intersection (or 0 if no intersection)
        return intersection.area

    # def visualize_results(roi_region, selected_region, result, roi_name):
    #     """
    #     Visualize the ROI and selected region on a canvas.

    #     Parameters:
    #     - roi_region: List of tuples [(x1, y1), (x2, y2), (x3, y3), (x4, y4)] representing the coordinates of the larger ROI.
    #     - selected_region: List of tuples [(x1, y1), (x2, y2), (x3, y3), (x4, y4)] representing the selected area.
    #     - result: The result of containment check (True or False).
    #     - roi_name: Name or identifier of the current ROI being checked.
    #     """
    #     # Create a white canvas for visualization
    #     canvas = np.ones((500, 500, 3), dtype=np.uint8) * 255

    #     # Convert coordinates to integer arrays for drawing
    #     roi_polygon = np.array(roi_region, dtype=np.int32)
    #     selected_polygon = np.array(selected_region, dtype=np.int32)

    #     # Draw the ROI and selected region
    #     cv2.polylines(canvas, [roi_polygon], isClosed=True, color=(0, 255, 0), thickness=2)  # Green ROI
    #     cv2.polylines(canvas, [selected_polygon], isClosed=True, color=(255, 0, 0), thickness=2)  # Red selected region

    #     # Display result text on the canvas
    #     result_text = f"Selected Area is inside {roi_name}" if result else "Selected Area is outside ROI"
    #     cv2.putText(canvas, result_text, (50, 450), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)

    #     # Show the canvas
    #     cv2.imshow(f"ROI and Selected Region - {roi_name}", canvas)
    #     cv2.waitKey(0)
    #     cv2.destroyAllWindows()


    # List to hold the ROIs that the selected area belongs to
    matching_rois = []

    # Variable to track the ROI with the most overlap
    max_overlap = 0
    best_roi_index = -1

    # Check each ROI and calculate the overlap area
    for idx, roi_region in enumerate(roi_arrays):
        overlap_area = get_overlap_area(selected_array, roi_region)
        print(f"ROI {idx + 1} overlap area: {overlap_area}")

        # If the overlap area is greater than the current max overlap, update the best ROI
        if overlap_area > max_overlap:
            max_overlap = overlap_area
            best_roi_index = idx

    # Visualize the best ROI and selected area
    if best_roi_index != -1:
        best_roi_region = roi_arrays[best_roi_index]
        # visualize_results(best_roi_region, selected_array, True, f"ROI {best_roi_index + 1}")
        print(f"Selected area is inside ROI {best_roi_index + 1} with the most overlap.")
    else:
        print("Selected area is outside all ROIs.")


# Main Execution
if __name__ == "_main_":
    # List of arrays representing multiple ROIs (replace these with actual data)
    roi_arrays = [
        [(50, 50), (150, 50), (150, 150), (50, 150)],  # Example ROI 1
        [(200, 200), (300, 200), (300, 300), (200, 300)],  # Example ROI 2
        [(100, 100), (200, 100), (200, 200), (100, 200)],  # Example ROI 3
    ]

    # Array representing the selected region (replace this with actual data)
    selected_array = [(120, 120), (180, 120), (180, 180), (120, 180)]  # Example selected region

    # Process the ROI selection
    process_roi_selection(roi_arrays, selected_array)