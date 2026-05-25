# ⚔️ Fruit Ninja: Gesture Edition

A high-performance, visually stunning, **gesture-controlled Fruit Ninja clone** built entirely in Python using **OpenCV** and the modern **MediaPipe Tasks API**.

Wave your index finger in front of your webcam to slice through apples, watermelons, oranges, pineapples, and mangos while dodging dangerous bombs! No mouse, keyboard, or physical controllers are required.

---

## ✨ Key Features

*   **RAZOR-SHARP GESTURE CONTROL**: Uses a modern computer vision pipeline to map your index fingertip in real-time. Full hand joint rendering is disabled for a clean, minimalist HUD.
*   **VELOCITY-SENSITIVE ADAPTIVE EMA FILTER**:
    *   *Hovering/Slow Movements*: Drop to $\alpha = 0.08$ to completely freeze skeletal hand jitter.
    *   *Explosive Swipes*: Scale up to $\alpha = 0.96$ to provide **zero tracking latency** during fast slices.
*   **ANTI-TUNNELING COLLISION PHYSICS**: Solves the classic game development "tunneling" bug. Your swipes are treated as continuous line segments rather than single coordinates, running precise **line-to-circle closest point checks** so rapid cuts never skip a fruit.
*   **REAL-TIME SPLIT KINEMATICS**: Sliced fruits split into procedural left/right halves that fly outward, spin, and fall under gravity perpendicular to your exact swiping angle.
*   **PREMIUM VECTOR GRAPHICS**: Features custom vector rendering for all objects (detailed orange citrus wedges, striped watermelon rinds, flashing bomb sparks, and translucent juice splatters) alongside a multi-layered neon blade trail.
{{ ... }}
*   `.gitignore`: Properly configured to ignore python byte-caches, local high scores, and heavy ML models.

---

## 📜 License

Distributed under the MIT License. See `LICENSE` for more information.
