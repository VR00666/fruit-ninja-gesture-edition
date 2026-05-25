# ⚔️ Fruit Ninja: Gesture Edition

A high-performance, visually stunning, **gesture-controlled Fruit Ninja clone** built entirely in Python using **OpenCV** and the modern **MediaPipe Tasks API**.

Wave your index finger in front of your webcam to slice through apples, watermelons, oranges, pineapples, and mangos while dodging dangerous bombs! No mouse, keyboard, or physical controllers are required.

---

## ✨ Key Features

*   **RAZOR-SHARP GESTURE CONTROL**: Uses a modern computer vision pipeline to map your index fingertip in real-time. Full hand joint rendering is disabled for a clean, minimalist HUD.
*   **VELOCITY-SENSITIVE ADAPTIVE EMA FILTER**: Integrates an advanced movement-sensitive filter:
    *   *Hovering/Slow Movements*: Drop to $\alpha = 0.08$ to completely freeze skeletal hand jitter.
    *   *Explosive Swipes*: Scale up to $\alpha = 0.96$ to provide **zero tracking latency** during fast slices.
*   **ANTI-TUNNELING COLLISION PHYSICS**: Solves the classic game development "tunneling" bug. Your swipes are treated as continuous line segments rather than single coordinates, running precise **line-to-circle closest point checks** so rapid cuts never skip a fruit.
*   **REAL-TIME SPLIT KINEMATICS**: Sliced fruits split into procedural left/right halves that fly outward, spin, and fall under gravity perpendicular to your exact swiping angle.
*   **PREMIUM VECTOR GRAPHICS**: Features custom vector rendering for all objects (detailed orange citrus wedges, striped watermelon rinds, flashing bomb sparks, and translucent juice splatters) alongside a multi-layered neon blade trail.
*   **ASYNCHRONOUS WINDOWS-NATIVE AUDIO**: Plays background sound effects sweeps using Windows winsound system, keeping the game at a locked **60 FPS** without audio latency.
*   **INTERACTIVE GESTURE UI & FALLBACKS**: Swipe your fingertip directly across on-screen UI buttons to start/restart. Includes automatic mouse tracking fallback if your webcam is offline.

---

## 🛠️ Installation & Setup

### 1. Prerequisites
- **Python 3.10+** (Fully tested and verified on Python 3.14!)
- A working webcam connected to your system.

### 2. Install Dependencies
Clone the repository and install the required modules:
```bash
pip install opencv-python mediapipe numpy
```

### 3. Run the Game
```bash
python main.py
```
*Note: The script will automatically download the official pre-trained `hand_landmarker.task` model (approx. 5.6 MB) from Google's CDN on the first run.*

---

## 🎮 How to Play

1.  Stand back and make sure your hand is visible to the webcam.
2.  Hover your **white and cyan glowing cursor** over the green **"SWIPE HERE TO START"** bar and slice across it to begin.
3.  **Slice Fruits**: Slice incoming fruits to score points. Slicing multiple fruits in a single swipe yields a **Combo** with major score bonuses!
4.  **Dodge Bombs**: Slicing dark grey bombs with glowing red hazard marks will trigger an instant Game Over.
5.  **Watch your Lives**: Letting a fruit fall below the screen untouched costs you 1 of your 3 lives.

---

## 📂 Code Structure

*   `main.py`: Entry point controlling the global game loop, state machine (`MENU`, `PLAYING`, `GAME_OVER`), wave spawning, and winsound audio threads.
*   `detector.py`: Wraps MediaPipe Tasks `HandLandmarker` in video mode with adaptive EMA filtering and monotonic timestamp checks.
*   `game_objects.py`: Object physics definitions for `Fruit` halves, `Bomb` sweeps, juice `Particle` flows, and anti-tunneling `Slice` segments.
*   `renderer.py`: Handles OpenCV canvas overlay rendering, glowing blade trails, and custom procedurally drawn fruit meshes/wedges/hearts.
*   `config.py`: Centralized configuration variables for screens, color palettes, difficulty scaling coefficients, and physics ranges.
*   `.gitignore`: Properly configured to ignore python byte-caches, local high scores, and heavy ML models.

---

## 📜 License
Distributed under the MIT License. See `LICENSE` for more information.
