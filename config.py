# config.py
"""
Configuration settings and constants for the Fruit Ninja game.
"""

# Screen & Camera Dimensions
WIDTH = 640
HEIGHT = 480
FPS = 60

# Colors (OpenCV uses BGR format)
COLOR_WHITE = (255, 255, 255)
COLOR_BLACK = (0, 0, 0)
COLOR_GRAY = (128, 128, 128)

# Beautiful HSL/custom palettes mapped to BGR for game elements
COLOR_APPLE = (34, 34, 220)       # Deep Apple Red
COLOR_WATERMELON_OUTER = (34, 139, 34) # Forest Green
COLOR_WATERMELON_INNER = (80, 80, 240)  # Juicy Pink/Red
COLOR_ORANGE = (0, 140, 255)      # Rich Orange
COLOR_PINEAPPLE = (0, 200, 230)   # Golden Pineapple Yellow
COLOR_MANGO = (0, 180, 255)       # Sunny Mango Yellow
COLOR_BOMB = (40, 40, 40)         # Sleek dark gray
COLOR_BOMB_GLOW = (0, 0, 255)     # Pulsing red danger glow
COLOR_FUSE = (0, 215, 255)        # Spark yellow

# Slicing Blade Trail Color
COLOR_BLADE = (255, 240, 120)     # Neon light cyan/blue
COLOR_BLADE_GLOW = (255, 255, 255) # Pure white core

# UI Colors
COLOR_UI_TEXT = (255, 255, 255)
COLOR_UI_HEART_ACTIVE = (50, 50, 255) # Bright BGR Red
COLOR_UI_HEART_LOST = (60, 60, 60)    # Grayed out heart

# Physics Settings
GRAVITY = 0.45                    # Gravity force pulling objects down (pixels/frame^2)

# Initial Launch Velocities
LAUNCH_VX_MIN = -4.0
LAUNCH_VX_MAX = 4.0
LAUNCH_VY_MIN = -16.0
LAUNCH_VY_MAX = -12.0

# Rotation speed in degrees per frame
SPIN_MIN = -6
SPIN_MAX = 6

# Spawning Rates (in frames, at 60 FPS)
INITIAL_SPAWN_COOLDOWN = 90       # 1.5 seconds between launches initially
MIN_SPAWN_COOLDOWN = 40           # Hardest difficulty spawn rate (0.66 seconds)
DIFFICULTY_SCALING_RATE = 0.05    # How quickly difficulty increases per sliced fruit

# Bomb Spawning Probability
BOMB_PROBABILITY_INITIAL = 0.15   # 15% chance initially
BOMB_PROBABILITY_MAX = 0.40       # Max 40% chance

# Slicing Parameters
MAX_TRAIL_POINTS = 12             # Number of historic points retained for the blade trail
MIN_SLICE_VELOCITY = 15.0         # Minimum pixels traveled between frames to count as active slice
SMOOTHING_ALPHA = 0.30            # Exponential Moving Average smoothing factor for hand tracking (smaller = smoother, larger = faster response)

# Game Rules
MAX_LIVES = 3
COMBO_WINDOW_MS = 400             # Timeframe to group slices into a single combo

# Fruit Types Definitions
FRUIT_TYPES = {
    'apple': {
        'radius': 30,
        'color': COLOR_APPLE,
        'points': 1,
        'display_name': 'Apple'
    },
    'watermelon': {
        'radius': 45,
        'color': COLOR_WATERMELON_INNER,
        'points': 2,
        'display_name': 'Watermelon'
    },
    'orange': {
        'radius': 28,
        'color': COLOR_ORANGE,
        'points': 1,
        'display_name': 'Orange'
    },
    'pineapple': {
        'radius': 38,
        'color': COLOR_PINEAPPLE,
        'points': 2,
        'display_name': 'Pineapple'
    },
    'mango': {
        'radius': 32,
        'color': COLOR_MANGO,
        'points': 1,
        'display_name': 'Mango'
    }
}
