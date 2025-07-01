import pygame
import time
import cv2
from classes.Dashboard import Dashboard
from classes.Level import Level
from classes.Menu import Menu
from classes.Sound import Sound
from entities.Mario import Mario
from pose_control import PoseControl

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
    pose.mode = "menu" # Set initial mode for pose control
    clock = pygame.time.Clock()

    gesture_timer = None
    last_gesture = None
    confirm_delay = 1.2  # seconds to hold a gesture for confirmation

    # === MENU LOOP WITH HAND GESTURE CONTROL ===
    while not menu.start:
        action = pose.get_action()

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
                index = int(action.split("_")[1])
                if 0 <= index < menu.levelCount:
                    if menu.currSelectedLevel != index + 1:
                        menu.currSelectedLevel = index + 1
                        menu.drawLevelChooser()
                        pygame.display.update()
                        gesture_timer = time.time() # Reset timer if selection changes
                        last_gesture = action

            if action == "confirm_select":
                if gesture_timer is None or last_gesture != action:
                    gesture_timer = time.time()
                    last_gesture = action
                elif (time.time() - gesture_timer) >= confirm_delay:
                    print("[INFO] Level selection confirmed!")
                    menu.inChoosingLevel = False
                    menu.dashboard.state = "start"
                    menu.dashboard.time = 0
                    menu.level.loadLevel(menu.levelNames[menu.currSelectedLevel - 1])
                    menu.dashboard.levelName = menu.levelNames[menu.currSelectedLevel - 1].split("Level")[1]
                    menu.start = True
                    pose.mode = "game" # Switch pose control to game mode
                    time.sleep(1)
                    gesture_timer = None
                    last_gesture = None
            else:
                if last_gesture == "confirm_select":
                    gesture_timer = None
                    last_gesture = None
        
        # === Main Menu Selection (Play Game, Settings, Exit) ===
        elif action.startswith("menu_"):
            index = int(action.split("_")[1])

            if index != last_gesture:
                last_gesture = index
                gesture_timer = time.time()
            else:
                if time.time() - gesture_timer >= confirm_delay:
                    menu.state = index
                    menu.update()
                    pygame.display.update()
                    print(f"[INFO] Main Menu Gesture Confirmed: Option {index + 1}")

                    if menu.state == 0: # Play Game
                        menu.chooseLevel()
                    elif menu.state == 1: # Settings
                        menu.inSettings = True
                        menu.state = 0
                    elif menu.state == 2: # Exit Game
                        pygame.quit()
                        exit()

                    time.sleep(1)
                    gesture_timer = None
                    last_gesture = None
        else: # If no menu_X or confirm_select gesture is currently held
            if last_gesture is not None and not (isinstance(last_gesture, int) and action.startswith("menu_")) and action != "confirm_select":
                gesture_timer = None
                last_gesture = None

        menu.update()

        # === Webcam Overlay ===
        if pose.last_frame is not None:
            frame = cv2.resize(pose.last_frame, (160, 120))
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            frame_surface = pygame.surfarray.make_surface(frame.swapaxes(0, 1))
            screen.blit(frame_surface, (10, 10))

        pygame.display.update()
        clock.tick(max_frame_rate)

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

        # Reset control states every frame
        mario.traits["goTrait"].direction = 0
        mario.traits["goTrait"].brake = True
        mario.traits["goTrait"].boost = False
        mario.traits["jumpTrait"].jump = False  # <== THIS IS CRUCIAL

        # Apply pose-based actions
        if action == "left":
            mario.traits["goTrait"].direction = -1
            mario.traits["goTrait"].brake = False
        elif action == "right":
            mario.traits["goTrait"].direction = 1
            mario.traits["goTrait"].brake = False
        elif action == "jump":
            mario.traits["jumpTrait"].jump = True  # Will now persist if gesture is held
        elif action == "boost":
            mario.traits["goTrait"].boost = True
            print("Mario Boost Activated!")


        # === Game Update Logic ===
        if mario.pause:
            mario.pauseObj.update()
        else:
            level.drawLevel(mario.camera)
            dashboard.update()
            mario.update()

        # === Webcam Preview Overlay (during game) ===
        if pose.last_frame is not None:
            frame = cv2.resize(pose.last_frame, (160, 120))
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            frame_surface = pygame.surfarray.make_surface(frame.swapaxes(0, 1))
            screen.blit(frame_surface, (10, 10))

        pygame.display.update()
        clock.tick(max_frame_rate)

    pose.release()
    return 'restart'

if __name__ == "__main__":
    exitmessage = 'restart'
    while exitmessage == 'restart':
        exitmessage = main()