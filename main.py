import pygame
import time
import cv2
from classes.Dashboard import Dashboard
from classes.Level import Level
from classes.Menu import Menu
from classes.Sound import Sound
from entities.Mario import Mario
from pose_control import PoseControl # Ensure this import is correct

windowSize = 640, 480

def main():
    pygame.mixer.pre_init(44100, -16, 2, 4096)
    pygame.init()
    screen = pygame.display.set_mode(windowSize)
    max_frame_rate = 60
    dashboard = Dashboard("./img/font.png", 8, screen)
    sound = Sound()
    level = Level(screen, sound, dashboard)
    menu = Menu(screen, dashboard, level, sound)

    pose = PoseControl()
    pose.mode = "menu" # Crucial: Set initial mode for pose control
    clock = pygame.time.Clock()

    gesture_timer = None
    last_gesture = None
    confirm_delay = 1.2  # seconds to hold a gesture for confirmation

    # === MENU LOOP WITH HAND GESTURE CONTROL ===
    while not menu.start:
        action = pose.get_action()

        # Handle Pygame events (like quitting)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                exit()
            # Optional: Add keyboard events for debugging or alternative control
            # if event.type == pygame.KEYDOWN:
            #     if event.key == pygame.K_1: action = "menu_0"
            #     elif event.key == pygame.K_2: action = "menu_1"
            #     elif event.key == pygame.K_3: action = "menu_2"
            #     elif event.key == pygame.K_RETURN: action = "confirm_select"
            #     elif event.key == pygame.K_ESCAPE: # For manual exit in debug
            #         pygame.quit()
            #         exit()

        # === Level Chooser (called after "Play Game" selected in main menu) ===
        if menu.inChoosingLevel:
            if action.startswith("menu_"):
                # Parse the numerical index from the action string
                index = int(action.split("_")[1])
                # Ensure the index is within valid range of levels
                if 0 <= index < menu.levelCount:
                    # Update selected level only if it's different to avoid redundant updates
                    if menu.currSelectedLevel != index + 1:
                        menu.currSelectedLevel = index + 1
                        menu.drawLevelChooser()
                        pygame.display.update()
                        # Reset timer if selection changes during holding
                        gesture_timer = time.time()
                        last_gesture = action

            # Confirm selection in level chooser
            if action == "confirm_select":
                if gesture_timer is None or last_gesture != action: # Start/reset timer if new gesture
                    gesture_timer = time.time()
                    last_gesture = action
                elif (time.time() - gesture_timer) >= confirm_delay: # If held long enough
                    print("[INFO] Level selection confirmed!")
                    menu.inChoosingLevel = False
                    menu.dashboard.state = "start"
                    menu.dashboard.time = 0 # Reset game time for new level
                    menu.level.loadLevel(menu.levelNames[menu.currSelectedLevel - 1])
                    menu.dashboard.levelName = menu.levelNames[menu.currSelectedLevel - 1].split("Level")[1]
                    menu.start = True # Exit menu loop, start game
                    pose.mode = "game" # Crucial: Switch pose control to game mode
                    time.sleep(1) # Small delay for transition
                    gesture_timer = None # Reset for next use
                    last_gesture = None
            else: # If confirm_select gesture is released or not held
                if last_gesture == "confirm_select": # Only reset if we were holding confirm
                    gesture_timer = None
                    last_gesture = None
        
        # === Main Menu Selection (Play Game, Settings, Exit) ===
        # This block processes menu_X gestures for the main menu options
        elif action.startswith("menu_"):
            index = int(action.split("_")[1]) # This index is 0, 1, or 2 for menu options

            if index != last_gesture: # If a new menu option gesture is made
                last_gesture = index
                gesture_timer = time.time() # Start timer for this new gesture
            else: # Same gesture is being held
                if time.time() - gesture_timer >= confirm_delay: # Check if held long enough
                    menu.state = index # Update menu's internal state
                    menu.update() # Redraw menu to show selection
                    pygame.display.update()
                    print(f"[INFO] Main Menu Gesture Confirmed: Option {index + 1}")

                    if menu.state == 0: # Play Game
                        menu.chooseLevel() # This sets menu.inChoosingLevel = True
                    elif menu.state == 1: # Settings
                        menu.inSettings = True
                        menu.state = 0 # Reset menu state for potential sub-options in settings
                        # You might need to add a separate menu.drawSettings() here
                    elif menu.state == 2: # Exit Game
                        pygame.quit()
                        exit()

                    time.sleep(1) # Visual feedback delay
                    gesture_timer = None # Reset for next menu interaction
                    last_gesture = None
        else: # If no menu_X or confirm_select gesture is currently held
            # Reset timer if the gesture is no longer active
            if last_gesture is not None and not (isinstance(last_gesture, int) and action.startswith("menu_")) and action != "confirm_select":
                gesture_timer = None
                last_gesture = None

        menu.update() # Update menu graphics (e.g., highlighting selection)

        # === Webcam Overlay ===
        if pose.last_frame is not None:
            # Resize webcam feed to fit a smaller area on the screen
            frame = cv2.resize(pose.last_frame, (160, 120))
            # Convert OpenCV's BGR to RGB for Pygame
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            # Create a Pygame surface from the numpy array (swapaxes for correct orientation)
            frame_surface = pygame.surfarray.make_surface(frame.swapaxes(0, 1))
            screen.blit(frame_surface, (10, 10)) # Position the webcam feed

        pygame.display.update() # Update the entire display
        clock.tick(max_frame_rate) # Cap frame rate

    # === Countdown before game starts ===
    print("Starting game in...")
    for i in range(3, 0, -1):
        print(i)
        time.sleep(1)
    print("Let's-a go!")

    # === GAME LOOP ===
    mario = Mario(0, 0, level, screen, dashboard, sound)

    while not mario.restart:
        pygame.display.set_caption("Super Mario running with {:d} FPS".format(int(clock.get_fps())))
        action = pose.get_action() # Get action based on hand pose (pose.mode is "game")

        # === Pose-Controlled Actions for Mario ===
        if action == "left":
            mario.traits["goTrait"].direction = -1
            mario.traits["goTrait"].brake = False
        elif action == "right":
            mario.traits["goTrait"].direction = 1
            mario.traits["goTrait"].brake = False
        elif action == "stop": # Peace sign
            mario.traits["goTrait"].direction = 0 # Stop horizontal movement
            mario.traits["goTrait"].brake = True # Apply brake
        elif action == "jump": # Thumbs up
            mario.traits["jumpTrait"].jump = True
        elif action == "crouch": # Thumbs down
            mario.traits["goTrait"].direction = 0 # Stop horizontal movement
            mario.traits["goTrait"].brake = True # Apply brake (or could implement actual crouch if Mario has it)

        # === Game Update Logic ===
        if mario.pause:
            mario.pauseObj.update() # Handle pause menu
        else:
            level.drawLevel(mario.camera) # Draw game world
            dashboard.update() # Update score, time, etc.
            mario.update() # Update Mario's state and position

        # === Webcam Preview Overlay (during game) ===
        if pose.last_frame is not None:
            frame = cv2.resize(pose.last_frame, (160, 120))
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            frame_surface = pygame.surfarray.make_surface(frame.swapaxes(0, 1))
            screen.blit(frame_surface, (10, 10))

        pygame.display.update()
        clock.tick(max_frame_rate)

    pose.release() # Release webcam resources
    return 'restart' # Signal to restart the game loop

if __name__ == "__main__":
    exitmessage = 'restart'
    while exitmessage == 'restart':
        exitmessage = main()