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
    pose.mode = "menu"
    clock = pygame.time.Clock()

    gesture_timer = None
    last_gesture = None
    confirm_delay = 1.2  # seconds to hold a gesture

    # === MENU LOOP WITH HAND GESTURE CONTROL ===
    while not menu.start:
        action = pose.get_action()

        # === Level Chooser (finger selection + confirm) ===
        if menu.inChoosingLevel:
            if action.startswith("menu_"):
                index = int(action.split("_")[1])
                if 0 <= index < menu.levelCount:
                    menu.currSelectedLevel = index + 1
                    menu.drawLevelChooser()
                    pygame.display.update()

            if action == "confirm_select":
                menu.inChoosingLevel = False
                menu.dashboard.state = "start"
                menu.dashboard.time = 0
                menu.level.loadLevel(menu.levelNames[menu.currSelectedLevel - 1])
                menu.dashboard.levelName = menu.levelNames[menu.currSelectedLevel - 1].split("Level")[1]
                menu.start = True
                pose.mode = "game"
                time.sleep(1)

        # === Main Menu Selection Confirm ===
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
                    print(f"[INFO] Gesture Confirmed: Option {index + 1}")

                    if menu.state == 0:
                        menu.chooseLevel()
                    elif menu.state == 1:
                        menu.inSettings = True
                        menu.state = 0
                    elif menu.state == 2:
                        pygame.quit()
                        exit()

                    time.sleep(1)
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

    # === Countdown ===
    for i in range(3, 0, -1):
        print(i)
        time.sleep(1)
    print("Let's-a go!")

    # === GAME LOOP ===
    mario = Mario(0, 0, level, screen, dashboard, sound)

    while not mario.restart:
        pygame.display.set_caption("Super Mario running with {:d} FPS".format(int(clock.get_fps())))
        action = pose.get_action()

        # === Pose-Controlled Actions ===
        if action == "left":
            mario.traits["goTrait"].direction = -1
            mario.traits["goTrait"].brake = False
        elif action == "right":
            mario.traits["goTrait"].direction = 1
            mario.traits["goTrait"].brake = False
        elif action == "stop":
            mario.traits["goTrait"].direction = 0
            mario.traits["goTrait"].brake = True
        elif action == "jump":
            mario.traits["jumpTrait"].jump = True
        elif action == "crouch":
            mario.traits["goTrait"].direction = 0
            mario.traits["goTrait"].brake = True

        # === Game Update Logic ===
        if mario.pause:
            mario.pauseObj.update()
        else:
            level.drawLevel(mario.camera)
            dashboard.update()
            mario.update()

        # === Webcam Preview Overlay ===
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
