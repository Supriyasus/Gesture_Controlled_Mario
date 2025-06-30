import cv2
import mediapipe as mp

class PoseControl:
    def __init__(self):
        self.cap = cv2.VideoCapture(0)
        self.hands = mp.solutions.hands.Hands(max_num_hands=1)
        self.prev_action = "idle"
        self.last_frame = None
        self.mode = "menu"  # or "game"

    def get_action(self):
        ret, frame = self.cap.read()
        if not ret:
            return self.prev_action

        frame = cv2.flip(frame, 1)
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        self.last_frame = frame.copy()

        hand_result = self.hands.process(rgb)

        if hand_result.multi_hand_landmarks:
            hand = hand_result.multi_hand_landmarks[0].landmark
            def is_extended(tip, pip):
                return hand[tip].y < hand[pip].y - 0.02

            thumb = hand[mp.solutions.hands.HandLandmark.THUMB_TIP]
            thumb_ip = hand[mp.solutions.hands.HandLandmark.THUMB_IP]
            index = is_extended(mp.solutions.hands.HandLandmark.INDEX_FINGER_TIP, mp.solutions.hands.HandLandmark.INDEX_FINGER_PIP)
            middle = is_extended(mp.solutions.hands.HandLandmark.MIDDLE_FINGER_TIP, mp.solutions.hands.HandLandmark.MIDDLE_FINGER_PIP)
            ring = is_extended(mp.solutions.hands.HandLandmark.RING_FINGER_TIP, mp.solutions.hands.HandLandmark.RING_FINGER_PIP)
            pinky = is_extended(mp.solutions.hands.HandLandmark.PINKY_TIP, mp.solutions.hands.HandLandmark.PINKY_PIP)

            all_fingers = [index, middle, ring, pinky]
            extended_count = sum(all_fingers)

            # === Gesture Logic ===
            if not any(all_fingers) and thumb.x < thumb_ip.x:  # Fist (left hand)
                return "left"
            elif all(all_fingers):  # Open palm
                return "right"
            elif index and middle and not ring and not pinky:  # Peace ✌️
                return "stop"
            elif thumb.y < hand[mp.solutions.hands.HandLandmark.THUMB_CMC].y and not any(all_fingers):  # Thumbs up 👍
                return "jump"
            elif thumb.y > hand[mp.solutions.hands.HandLandmark.THUMB_CMC].y and not any(all_fingers):  # Thumbs down 👎
                return "crouch"

        return "idle"

    def release(self):
        self.cap.release()
        cv2.destroyAllWindows()
