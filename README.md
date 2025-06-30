# Super Mario Implementation in Python with Hand Gesture Control

This is inspired by Meth-Meth-Method's [super mario game](https://github.com/meth-meth-method/super-mario/) but enhanced with **computer vision-based hand gesture controls** using MediaPipe and OpenCV.

## Features

- **Hand Gesture Control**: Control Mario using hand gestures captured by your webcam
- **Classic Keyboard Controls**: Traditional keyboard input still supported
- **Real-time Webcam Preview**: See your hand gestures in the corner of the game screen
- **Multiple Levels**: Level 1-1 and Level 1-2 available
- **Menu Navigation**: Navigate menus using hand gestures
- **Classic Mario Gameplay**: Enemies (Goombas, Koopas), power-ups, coins, and more

## Installation & Running

### Prerequisites
Make sure you have a webcam connected to your computer for hand gesture control.

### Installation
```bash
pip install -r requirements.txt
```

### Running the Game
```bash
python main.py
```

## Hand Gesture Controls

### Menu Navigation
- **1-5 Fingers**: Select menu options (hold gesture for 1.2 seconds to confirm)
- **Confirm Selection**: Hold the gesture to confirm your choice

### In-Game Controls
- **👊 Fist (Left Hand)**: Move Mario left
- **🖐️ Open Palm**: Move Mario right  
- **✌️ Peace Sign (2 Fingers)**: Stop Mario
- **👍 Thumbs Up**: Jump
- **👎 Thumbs Down**: Crouch/Duck

### Traditional Keyboard Controls (Alternative)
- **Arrow Keys / H,L**: Move left/right
- **Space / Up Arrow / K**: Jump
- **Left Shift**: Boost/Run faster
- **Escape / F5**: Pause game
- **Left Mouse Click**: Add coin at cursor position
- **Right Mouse Click**: Add enemies (Goomba, Koopa, Red Mushroom) at cursor

## Standalone Windows Build

```bash
pip install py2exe
python compile.py py2exe
```

## Game Features

### Entities
- **Mario**: The main player character with small and big forms
- **Goombas**: Walking enemies that can be stomped
- **Koopas**: Shell enemies that can be kicked after stomping
- **Coins**: Collectible items for points
- **Power-ups**: Red Mushrooms to make Mario bigger
- **Blocks**: Coin blocks and random item boxes

### Levels
- **Level 1-1**: Classic first level layout
- **Level 1-2**: Additional level content

### Audio
- Background music and sound effects for jumps, coins, power-ups, and enemy interactions

## Technical Details

- **Computer Vision**: Uses MediaPipe for hand landmark detection
- **Game Engine**: Built with Pygame
- **Image Processing**: OpenCV for webcam capture and processing
- **Architecture**: Object-oriented design with traits system for character behaviors

## Current State
![Alt text](img/pics.png "current state")

## Dependencies
- **pygame** (≥2.1.0): Game development framework
- **opencv-python** (≥4.11.0): Computer vision and webcam capture
- **mediapipe** (≥0.10.21): Hand landmark detection and gesture recognition
- **scipy** (≥1.10.0): Scientific computing utilities	
