# detector.py
"""
Hand tracking and landmark detection using the modern MediaPipe Tasks API.
Automatically downloads the pre-trained float16 model bundle from Google's CDN if not present,
and implements exponential moving average (EMA) smoothing to filter index fingertip coordinate jitter.
Includes a custom procedural neon skeletal visualization system.
"""
import cv2
import os
import time
import urllib.request
import math
import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision
import config

class HandDetector:
    def __init__(self, max_num_hands=1, min_detection_confidence=0.55, min_tracking_confidence=0.55):
        """
        Initializes the MediaPipe Tasks HandLandmarker in VIDEO mode.
        Sets relaxed confidence thresholds (0.55) to increase tracking persistence
        during complex hand rotations and poor lighting.
        """
        self.model_path = 'hand_landmarker.task'
        
        # Download the model bundle automatically from Google CDN if not present
        if not os.path.exists(self.model_path):
            print("[INFO] 'hand_landmarker.task' not found locally.")
            print("[INFO] Downloading pre-trained MediaPipe model from Google CDN...")
            url = "https://storage.googleapis.com/mediapipe-models/hand_landmarker/hand_landmarker/float16/1/hand_landmarker.task"
            try:
                urllib.request.urlretrieve(url, self.model_path)
                print("[INFO] Model download completed successfully.")
            except Exception as e:
                print(f"[ERROR] Failed to download MediaPipe model: {e}")
                raise FileNotFoundError(f"Could not load or download required hand landmarker model: {e}")
                
        # Configure MediaPipe Tasks BaseOptions
        base_options = python.BaseOptions(model_asset_path=self.model_path)
        
        # Configure HandLandmarkerOptions in VIDEO running mode
        self.options = vision.HandLandmarkerOptions(
            base_options=base_options,
            running_mode=vision.RunningMode.VIDEO,
            num_hands=max_num_hands,
            min_hand_detection_confidence=min_detection_confidence,
            min_hand_presence_confidence=min_tracking_confidence,
            min_tracking_confidence=min_tracking_confidence
        )
        
        # Create Landmarker instance
        self.landmarker = vision.HandLandmarker.create_from_options(self.options)
        
        # History for exponential moving average smoothing
        self.smoothed_x = None
        self.smoothed_y = None
        
        # Keep track of monotonic timestamps for detect_for_video calls
        self.last_timestamp_ms = 0

    def find_hand_position(self, frame, draw_skeleton=False):
        """
        Processes a BGR frame, tracks hand, and returns the smoothed index fingertip coordinates.
        Optionally renders custom high-contrast neon skeleton connections directly on the frame.
        
        Parameters:
            frame: opencv BGR image.
            draw_skeleton (bool): whether to draw joints and bones.
            
        Returns:
            tuple: (x, y) coordinates of smoothed index fingertip, or None if no hand detected.
        """
        h, w, c = frame.shape
        
        # MediaPipe Tasks require RGB images
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb_frame)
        
        # Calculate a monotonically increasing millisecond timestamp
        # In case the system time wraps, is delayed, or moves slightly backwards,
        # we enforce a minimum delta of 16 milliseconds (approx 60 FPS)
        current_time_ms = int(time.time() * 1000)
        if current_time_ms <= self.last_timestamp_ms:
            current_time_ms = self.last_timestamp_ms + 16
            
        self.last_timestamp_ms = current_time_ms
        
        try:
            # Perform detection synchronously in VIDEO mode
            results = self.landmarker.detect_for_video(mp_image, current_time_ms)
        except Exception as e:
            # Safe recovery in case of system capture interruptions
            print(f"[WARNING] MediaPipe inference encountered a frame skipped: {e}")
            return None
            
        fingertip_coords = None
        
        if results.hand_landmarks and len(results.hand_landmarks) > 0:
            # Track the dominant hand (first one returned)
            hand_landmarks = results.hand_landmarks[0]
            
            # Landmark index 8 is INDEX_FINGER_TIP
            tip = hand_landmarks[8]
            
            # Map normalized [0, 1] coordinates into pixel coordinates
            raw_x = int(tip.x * w)
            raw_y = int(tip.y * h)
            
            # Apply a Velocity-Sensitive Adaptive EMA smoothing filter.
            # Large movements (swipes) use large alpha for zero lag and perfect tracking accuracy.
            # Small movements (hovers) use small alpha to completely eliminate joint jitter.
            if self.smoothed_x is None or self.smoothed_y is None:
                self.smoothed_x = float(raw_x)
                self.smoothed_y = float(raw_y)
            else:
                # Calculate movement distance between raw new position and previous smoothed position
                dx = raw_x - self.smoothed_x
                dy = raw_y - self.smoothed_y
                dist = math.sqrt(dx*dx + dy*dy)
                
                # Dynamic alpha interpolation (min_alpha=0.08 for hover, max_alpha=0.96 for fast swipes)
                min_alpha = 0.08
                max_alpha = 0.96
                dist_threshold = 22.0 # pixels
                
                alpha = min_alpha + (max_alpha - min_alpha) * min(1.0, dist / dist_threshold)
                
                self.smoothed_x = alpha * raw_x + (1.0 - alpha) * self.smoothed_x
                self.smoothed_y = alpha * raw_y + (1.0 - alpha) * self.smoothed_y
                
            fingertip_coords = (int(self.smoothed_x), int(self.smoothed_y))
            
            # Draw beautiful skeleton lines and joints if requested
            if draw_skeleton:
                self.draw_custom_skeleton(frame, hand_landmarks)
        else:
            # Reset smoothed history when hand is lost to prevent initial re-entry latency
            self.smoothed_x = None
            self.smoothed_y = None
            
        return fingertip_coords

    def draw_custom_skeleton(self, frame, hand_landmarks):
        """
        Renders a premium neon-styled skeleton overlays on the frame.
        Visualizes the knuckles, bones, and finger extensions.
        """
        h, w, c = frame.shape
        points = []
        for lm in hand_landmarks:
            cx, cy = int(lm.x * w), int(lm.y * h)
            points.append((cx, cy))
            
        # Define joints connections mapping
        connections = [
            [0, 1, 2, 3, 4],       # Thumb
            [0, 5, 6, 7, 8],       # Index Finger
            [9, 10, 11, 12],      # Middle Finger
            [13, 14, 15, 16],     # Ring Finger
            [0, 17, 18, 19, 20],  # Pinky Finger
            [5, 9, 13, 17]        # Palm Knuckles Connection
        ]
        
        glow_color = (255, 255, 0)   # Vibrant neon cyan bones (BGR: Cyan is 255, 255, 0)
        joint_color = (0, 220, 255)  # Glowing gold joints (BGR: Gold/Yellow)
        
        # Draw bones (skeleton connections)
        for segment in connections:
            for i in range(len(segment) - 1):
                pt1_idx = segment[i]
                pt2_idx = segment[i+1]
                if pt1_idx < len(points) and pt2_idx < len(points):
                    cv2.line(frame, points[pt1_idx], points[pt2_idx], glow_color, 2, cv2.LINE_AA)
                    
        # Draw joint nodes
        for pt in points:
            # Inner white core
            cv2.circle(frame, pt, 3, (255, 255, 255), -1, cv2.LINE_AA)
            # Glowing outer circle
            cv2.circle(frame, pt, 5, joint_color, 1, cv2.LINE_AA)

    def close(self):
        """
        Gracefully releases the HandLandmarker resource.
        """
        self.landmarker.close()
