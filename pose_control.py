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
            min_detection_confidence=0.7,
            min_tracking_confidence=0.6
        )
        self.drawing = mp.solutions.drawing_utils
        self.prev_action = "idle"
        self.last_frame = None
        self.mode = "menu"

        self.extension_threshold_factor = 0.75
        self.thumb_extension_factor_multiplier = 0.9

    def get_distance(self, p1, p2):
        return np.sqrt((p1.x - p2.x)**2 + (p1.y - p2.y)**2)

    def get_action(self):
        ret, frame = self.cap.read()
        if not ret:
            return self.prev_action

        frame = cv2.flip(frame, 1)
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        self.last_frame = frame.copy()

        hand_result = self.hands.process(rgb)
        current_action = "idle"

        index_ext = middle_ext = ring_ext = pinky_ext = thumb_ext = False

        if hand_result.multi_hand_landmarks:
            hand_landmarks = hand_result.multi_hand_landmarks[0]
            self.drawing.draw_landmarks(self.last_frame, hand_landmarks, mp.solutions.hands.HAND_CONNECTIONS)
            landmarks = hand_landmarks.landmark

            base_size = self.get_distance(
                landmarks[mp.solutions.hands.HandLandmark.WRIST],
                landmarks[mp.solutions.hands.HandLandmark.PINKY_MCP]
            )
            base_size = base_size if base_size != 0 else 0.001

            def is_finger_extended(tip, mcp):
                return (self.get_distance(landmarks[tip], landmarks[mcp]) / base_size) > self.extension_threshold_factor

            def is_thumb_extended():
                tip = landmarks[mp.solutions.hands.HandLandmark.THUMB_TIP]
                ip = landmarks[mp.solutions.hands.HandLandmark.THUMB_IP]
                mcp = landmarks[mp.solutions.hands.HandLandmark.THUMB_MCP]
                wrist_x = landmarks[mp.solutions.hands.HandLandmark.WRIST].x
                return (tip.x > ip.x > mcp.x) if wrist_x < tip.x else (tip.x < ip.x < mcp.x)

            index_ext = is_finger_extended(mp.solutions.hands.HandLandmark.INDEX_FINGER_TIP, mp.solutions.hands.HandLandmark.INDEX_FINGER_MCP)
            middle_ext = is_finger_extended(mp.solutions.hands.HandLandmark.MIDDLE_FINGER_TIP, mp.solutions.hands.HandLandmark.MIDDLE_FINGER_MCP)
            ring_ext = is_finger_extended(mp.solutions.hands.HandLandmark.RING_FINGER_TIP, mp.solutions.hands.HandLandmark.RING_FINGER_MCP)
            pinky_ext = is_finger_extended(mp.solutions.hands.HandLandmark.PINKY_TIP, mp.solutions.hands.HandLandmark.PINKY_MCP)
            thumb_ext = is_thumb_extended()

            # 🎮 Game mode gestures (relaxed)
            if self.mode == "game":
                if index_ext and middle_ext and not ring_ext:
                    current_action = "boost"
                elif index_ext and not middle_ext:
                    current_action = "jump"
                elif not index_ext and not middle_ext and not ring_ext and not pinky_ext and not thumb_ext:
                    current_action = "left"
                elif index_ext and middle_ext and ring_ext and pinky_ext and thumb_ext:
                    current_action = "right"

            # Menu mode gestures
            elif self.mode == "menu":
                if index_ext and thumb_ext and not middle_ext and not ring_ext and not pinky_ext:
                    current_action = "confirm_select"
                elif index_ext and middle_ext and ring_ext and not pinky_ext and not thumb_ext:
                    current_action = "menu_2"
                elif index_ext and middle_ext and not ring_ext and not pinky_ext and not thumb_ext:
                    current_action = "menu_1"
                elif index_ext and not middle_ext and not ring_ext and not pinky_ext and not thumb_ext:
                    current_action = "menu_0"
                elif thumb_ext and not index_ext and not middle_ext and not ring_ext and not pinky_ext:
                    current_action = "menu_0"

            # Visual feedback on fingertips
            fingertip_status = [thumb_ext, index_ext, middle_ext, ring_ext, pinky_ext]
            fingertip_indices = [4, 8, 12, 16, 20]
            for i, idx in enumerate(fingertip_indices):
                cx = int(landmarks[idx].x * self.last_frame.shape[1])
                cy = int(landmarks[idx].y * self.last_frame.shape[0])
                color = (0, 255, 0) if fingertip_status[i] else (0, 0, 255)
                cv2.circle(self.last_frame, (cx, cy), 6, color, -1)

        # On-screen debug
        if self.last_frame is not None:
            cv2.putText(self.last_frame, f"Mode: {self.mode}", (20, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
            cv2.putText(self.last_frame, f"Action: {current_action}", (20, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
            cv2.putText(self.last_frame,
                        f"I:{int(index_ext)} M:{int(middle_ext)} R:{int(ring_ext)} P:{int(pinky_ext)} T:{int(thumb_ext)}",
                        (20, 90), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 0), 1)

        # Console debug
        print(f"[Gesture Debug] Mode: {self.mode} | I:{index_ext} M:{middle_ext} R:{ring_ext} P:{pinky_ext} T:{thumb_ext} => Action: {current_action}")

        self.prev_action = current_action
        return current_action

    def release(self):
        self.cap.release()
        cv2.destroyAllWindows()
