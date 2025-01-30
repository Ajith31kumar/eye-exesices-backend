from flask import Flask, jsonify, request
import cv2
import time
import threading
from cvzone.FaceMeshModule import FaceMeshDetector
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# Initialize variables
cap = cv2.VideoCapture(0)
detector = FaceMeshDetector(maxFaces=1)
blink_counter = 0
counter = 0
ratio_list = []
last_blink_time = None
game_start_time = time.time()
GAME_DURATION = 10  # 10-second game duration
is_game_active = True

def process_camera_frames():
    """ Continuously process camera frames to detect blinks. """
    global blink_counter, counter, ratio_list, last_blink_time, is_game_active

    while is_game_active:
        success, img = cap.read()
        if not success:
            continue

        img, faces = detector.findFaceMesh(img, draw=False)

        if faces:
            face = faces[0]
            left_up = face[159]
            left_down = face[23]
            left_left = face[130]
            left_right = face[243]
            length_ver, _ = detector.findDistance(left_up, left_down)
            length_hor, _ = detector.findDistance(left_left, left_right)

            ratio = int((length_ver / length_hor) * 100)
            ratio_list.append(ratio)
            if len(ratio_list) > 3:
                ratio_list.pop(0)
            ratio_avg = sum(ratio_list) / len(ratio_list)

            # Blink detection logic
            if ratio_avg < 35 and counter == 0:  # Blink detected
                blink_counter += 1
                print(f"Blink Detected! Total Blinks: {blink_counter}")
                last_blink_time = time.time()
                counter = 1  # Start cooldown period for blink detection
            elif ratio_avg >= 35 and counter != 0:  # Cooldown
                counter += 1
                if counter > 10:  # Reset after cooldown
                    counter = 0

        time.sleep(0.03)  # Process frames every 30 ms (approx 33 FPS)

# Start a separate thread to process camera frames
frame_processing_thread = threading.Thread(target=process_camera_frames)
frame_processing_thread.daemon = True
frame_processing_thread.start()

@app.route('/blink-data', methods=['GET'])
def get_blink_data():
    global blink_counter, game_start_time, is_game_active

    elapsed_time = time.time() - game_start_time
    if elapsed_time > GAME_DURATION:
        is_game_active = False  # Stop the game
        print(f"Game Over! Total Blinks: {blink_counter}")  # Debugging
        return jsonify({"blink_count": blink_counter, "game_over": True})

    print(f"Blink Count Sent to Frontend: {blink_counter}")  # Debugging
    return jsonify({"blink_count": blink_counter, "game_over": False})

if __name__ == "__main__":
    try:
        app.run(debug=True)
    finally:
        is_game_active = False
        cap.release()