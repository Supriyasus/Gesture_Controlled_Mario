import cv2
import mediapipe as mp
import numpy as np

class PoseControl:
    def __init__(self):
        self.cap = cv2.VideoCapture(0)
        if not self.cap.isOpened():
            print("Error: Could not open webcam.")
            exit()

        self.hands = mp.solutions.hands.Hands(
            max_num_hands=1,
            min_detection_confidence=0.7, # Keep these robust
            min_tracking_confidence=0.6
        )
        self.drawing = mp.solutions.drawing_utils
        self.prev_action = "idle"
        self.last_frame = None
        self.mode = "menu" # Initial mode is "menu"

        # TUNE THESE THRESHOLDS CAREFULLY BASED ON YOUR CAMERA AND HANDS
        # Experiment with values like 0.5 to 0.8
        self.extension_threshold_factor = 0.65 # Main threshold for finger extension

    def get_action(self):
        ret, frame = self.cap.read()
        if not ret:
            # print("Warning: Could not read frame from webcam.")
            return self.prev_action # Return previous action if frame not available

        frame = cv2.flip(frame, 1) # Flip for mirror effect
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        self.last_frame = frame.copy() # Store for overlay

        hand_result = self.hands.process(rgb)

        current_action = "idle" # Default to idle for the current frame

        if hand_result.multi_hand_landmarks:
            hand_landmarks = hand_result.multi_hand_landmarks[0]
            # Draw landmarks on the frame for visualization
            self.drawing.draw_landmarks(self.last_frame, hand_landmarks, mp.solutions.hands.HAND_CONNECTIONS)

            landmarks = hand_landmarks.landmark

            def get_distance(a, b):
                ax, ay = landmarks[a].x, landmarks[a].y
                bx, by = landmarks[b].x, landmarks[b].y
                return np.sqrt((ax - bx) ** 2 + (ay - by) ** 2)

            # Use wrist to pinky MCP as a more stable base size for normalization
            base_size = get_distance(mp.solutions.hands.HandLandmark.WRIST,
                                     mp.solutions.hands.HandLandmark.PINKY_MCP)
            if base_size == 0: # Prevent division by zero if landmarks overlap
                base_size = 0.001 # A small epsilon value

            # Function to check if a finger is extended
            def is_extended(tip, mcp):
                return (get_distance(tip, mcp) / base_size) > self.extension_threshold_factor
            
            # Special check for thumb, can have a slightly different threshold or logic
            def is_thumb_extended(thumb_tip, thumb_cmc):
                # Thumb extension distance relative to base_size
                thumb_dist_norm = get_distance(thumb_tip, thumb_cmc) / base_size
                
                # You might need to adjust this factor for the thumb specifically
                # Thumbs often have a slightly different extension profile
                thumb_extension_factor = self.extension_threshold_factor * 0.9 # Slightly lower for thumb
                return thumb_dist_norm > thumb_extension_factor


            index_ext = is_extended(mp.solutions.hands.HandLandmark.INDEX_FINGER_TIP,
                                    mp.solutions.hands.HandLandmark.INDEX_FINGER_MCP)
            middle_ext = is_extended(mp.solutions.hands.HandLandmark.MIDDLE_FINGER_TIP,
                                     mp.solutions.hands.HandLandmark.MIDDLE_FINGER_MCP)
            ring_ext = is_extended(mp.solutions.hands.HandLandmark.RING_FINGER_TIP,
                                   mp.solutions.hands.HandLandmark.RING_FINGER_MCP)
            pinky_ext = is_extended(mp.solutions.hands.HandLandmark.PINKY_TIP,
                                    mp.solutions.hands.HandLandmark.PINKY_MCP)
            
            # Using the specific thumb extension function
            thumb_ext = is_thumb_extended(mp.solutions.hands.HandLandmark.THUMB_TIP,
                                          mp.solutions.hands.HandLandmark.THUMB_CMC)

            # --- DEBUGGING PRINTS (Uncomment to see values in console) ---
            # print(f"Base Size: {base_size:.4f}")
            # print(f"Index Norm Dist: {get_distance(mp.solutions.hands.HandLandmark.INDEX_FINGER_TIP, mp.solutions.hands.HandLandmark.INDEX_FINGER_MCP) / base_size:.4f}")
            # print(f"Middle Norm Dist: {get_distance(mp.solutions.hands.HandLandmark.MIDDLE_FINGER_TIP, mp.solutions.hands.HandLandmark.MIDDLE_FINGER_MCP) / base_size:.4f}")
            # print(f"Ring Norm Dist: {get_distance(mp.solutions.hands.HandLandmark.RING_FINGER_TIP, mp.solutions.hands.HandLandmark.RING_FINGER_MCP) / base_size:.4f}")
            # print(f"Pinky Norm Dist: {get_distance(mp.solutions.hands.HandLandmark.PINKY_TIP, mp.solutions.hands.HandLandmark.PINKY_MCP) / base_size:.4f}")
            # print(f"Thumb Norm Dist: {get_distance(mp.solutions.hands.HandLandmark.THUMB_TIP, mp.solutions.hands.HandLandmark.THUMB_CMC) / base_size:.4f}")
            # print(f"Extended: I:{index_ext} M:{middle_ext} R:{ring_ext} P:{pinky_ext} T:{thumb_ext}")
            # -------------------------------------------------------------

            # === Gesture Detection Logic (Order Matters: Most Specific to Least Specific) ===

            if self.mode == "game":
                # Thumbs up/down (VERY specific: ONLY thumb extended)
                if thumb_ext and not index_ext and not middle_ext and not ring_ext and not pinky_ext:
                    wrist_y = landmarks[mp.solutions.hands.HandLandmark.WRIST].y
                    thumb_y = landmarks[mp.solutions.hands.HandLandmark.THUMB_TIP].y
                    # Adjust sensitivity for thumb up/down by comparing to a point on wrist/palm
                    # A larger difference in Y means more clearly up/down
                    if (thumb_y - wrist_y) < -0.08: # Thumb significantly above wrist
                        current_action = "jump"  # Thumbs up
                    elif (thumb_y - wrist_y) > 0.08: # Thumb significantly below wrist
                        current_action = "crouch"  # Thumbs down
                
                # Peace Sign (specific: Index & Middle extended, others not, NO thumb)
                elif index_ext and middle_ext and not ring_ext and not pinky_ext and not thumb_ext:
                    current_action = "stop"  # Peace ✌️
                
                # Open Palm (general: all fingers extended, check after specific ones)
                elif index_ext and middle_ext and ring_ext and pinky_ext and thumb_ext:
                    current_action = "right"  # Open palm (all extended)
                
                # Fist (general: no fingers extended, check last in game mode)
                elif not index_ext and not middle_ext and not ring_ext and not pinky_ext and not thumb_ext:
                    current_action = "left"  # Fist (all not extended)

            elif self.mode == "menu":
                # Confirmation Gesture (e.g., Index + Thumb extended, others not)
                # This could be an "OK" sign if thumb touches index, or L-shape
                # For simplicity, let's use Index and Thumb extended, others NOT.
                if index_ext and thumb_ext and not middle_ext and not ring_ext and not pinky_ext:
                    current_action = "confirm_select"
                
                # Menu option 2 (3 fingers: Index, Middle, Ring extended, others not)
                elif index_ext and middle_ext and ring_ext and not pinky_ext and not thumb_ext:
                    current_action = "menu_2"
                
                # Menu option 1 (2 fingers: Index, Middle extended, others not)
                elif index_ext and middle_ext and not ring_ext and not pinky_ext and not thumb_ext:
                    current_action = "menu_1"
                
                # Menu option 0 (1 finger: Index extended, OR just thumb extended, others not)
                # Prioritize single index finger for clarity if possible
                elif index_ext and not middle_ext and not ring_ext and not pinky_ext and not thumb_ext:
                    current_action = "menu_0"
                # If index is not extended, but only thumb is, also consider it menu_0
                elif thumb_ext and not index_ext and not middle_ext and not ring_ext and not pinky_ext:
                    current_action = "menu_0"

        # --- DEBUGGING PRINTS ---
        # print(f"Current Mode: {self.mode}, Detected Action: {current_action}")
        # ------------------------

        self.prev_action = current_action # Store for next frame if no hand is detected
        return current_action

    def release(self):
        self.cap.release()
        cv2.destroyAllWindows()