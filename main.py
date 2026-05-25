# main.py
"""
Fruit Ninja Gesture Edition - Main Game Loop and State Machine.
Supports hand tracking via MediaPipe as primary controller, with mouse swipe backup.
Plays asynchronous Windows-native procedural beep sounds for responsive audio feedback.
"""
import cv2
import numpy as np
import time
import random
import os
import threading
import winsound
import config
from detector import HandDetector
from game_objects import Fruit, Bomb, Particle, Slice
from renderer import GameRenderer

# Global variables for mouse-tracking backup
mouse_x = 0
mouse_y = 0
is_mouse_active = False

def mouse_callback(event, x, y, flags, param):
    """
    OpenCV mouse movement callback. Acts as a backup input method.
    """
    global mouse_x, mouse_y, is_mouse_active
    if event == cv2.EVENT_MOUSEMOVE:
        mouse_x = x
        mouse_y = y
        is_mouse_active = True


class SoundManager:
    def __init__(self):
        """
        Manages procedural sound feedback using Windows Winsound system.
        Runs sound generation in daemon threads to prevent stuttering in the game loop.
        """
        self.enabled = True

    def _play_slice_thread(self):
        try:
            # High frequency sweep (800Hz to 1600Hz) in 40ms to simulate a sword slash
            for freq in range(900, 1500, 150):
                winsound.Beep(freq, 10)
        except Exception:
            pass

    def _play_bomb_thread(self):
        try:
            # Low, rumbling, exploding tone sweep
            winsound.Beep(180, 180)
            winsound.Beep(100, 300)
        except Exception:
            pass

    def _play_game_over_thread(self):
        try:
            # Melancholic descending tone sweep
            winsound.Beep(400, 150)
            winsound.Beep(300, 150)
            winsound.Beep(200, 400)
        except Exception:
            pass

    def play_slice(self):
        if self.enabled:
            threading.Thread(target=self._play_slice_thread, daemon=True).start()

    def play_bomb(self):
        if self.enabled:
            threading.Thread(target=self._play_bomb_thread, daemon=True).start()

    def play_game_over(self):
        if self.enabled:
            threading.Thread(target=self._play_game_over_thread, daemon=True).start()


class FruitNinjaGame:
    def __init__(self):
        """
        Initializes game systems, state machine, and window.
        """
        self.detector = HandDetector()
        self.renderer = GameRenderer()
        self.sounds = SoundManager()
        
        # Game State Machine
        self.STATE_MENU = 0
        self.STATE_PLAYING = 1
        self.STATE_GAME_OVER = 2
        self.state = self.STATE_MENU
        
        # High Score file
        self.highscore_file = "highscore.txt"
        self.high_score = self.load_high_score()
        
        # Setup camera
        self.cap = cv2.VideoCapture(0)
        if not self.cap.isOpened():
            print("[WARNING] Webcam not detected. Falling back to mouse controls!")
            
        # Lock OpenCV capture size
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, config.WIDTH)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, config.HEIGHT)
        
        # Slicing trail
        self.slice_trail = Slice()
        
        # Game entities lists
        self.fruits = []
        self.bombs = []
        self.particles = []
        
        # Gameplay variables
        self.score = 0
        self.lives = config.MAX_LIVES
        self.spawn_cooldown = config.INITIAL_SPAWN_COOLDOWN
        self.difficulty = 0.0
        
        # Combo tracker
        self.combo_count = 0
        self.combo_timer = 0.0
        
        # Window setup
        self.window_name = "Fruit Ninja: Gesture Edition"
        cv2.namedWindow(self.window_name)
        cv2.setMouseCallback(self.window_name, mouse_callback)

    def load_high_score(self):
        """
        Loads the high score from highscore.txt. Returns 0 if file does not exist.
        """
        if os.path.exists(self.highscore_file):
            try:
                with open(self.highscore_file, 'r') as f:
                    return int(f.read().strip())
            except Exception:
                return 0
        return 0

    def save_high_score(self):
        """
        Saves the current high score to highscore.txt.
        """
        try:
            with open(self.highscore_file, 'w') as f:
                f.write(str(self.high_score))
        except Exception:
            pass

    def reset_game(self):
        """
        Resets score, lives, and objects for a new game session.
        """
        self.score = 0
        self.lives = config.MAX_LIVES
        self.difficulty = 0.0
        self.spawn_cooldown = config.INITIAL_SPAWN_COOLDOWN
        self.fruits.clear()
        self.bombs.clear()
        self.particles.clear()
        self.slice_trail.clear()
        self.combo_count = 0
        self.combo_timer = 0.0

    def check_interaction_box(self, box):
        """
        Checks if the slicing trail cuts through a UI button box (x, y, w, h).
        Used for completely hand-driven interactive UI interfaces.
        """
        bx, by, bw, bh = box
        points = self.slice_trail.get_recent_points()
        if len(points) < 2:
            return False
            
        # Check if any point in the trail intersects the button bounding box
        for px, py in points:
            if bx <= px <= bx + bw and by <= py <= by + bh:
                return True
        return False

    def spawn_wave(self):
        """
        Spawns a wave of fruits and bombs based on progressive difficulty.
        """
        # Determine wave size (increases slowly with difficulty)
        max_fruits = 1
        if self.difficulty > 2.0:
            max_fruits = 2
        if self.difficulty > 6.0:
            max_fruits = 3
            
        num_fruits = random.randint(1, max_fruits)
        
        # Spawn fruits
        for _ in range(num_fruits):
            fruit_type = random.choice(list(config.FRUIT_TYPES.keys()))
            x = random.randint(100, config.WIDTH - 100)
            y = config.HEIGHT + 50
            
            # Initial velocities
            vy = random.uniform(config.LAUNCH_VY_MIN, config.LAUNCH_VY_MAX)
            vx = random.uniform(config.LAUNCH_VX_MIN, config.LAUNCH_VX_MAX)
            
            # Push horizontal direction inward toward center arc
            if x < config.WIDTH // 2:
                vx = abs(vx)
            else:
                vx = -abs(vx)
                
            self.fruits.append(Fruit(fruit_type, x, y, vx, vy))
            
        # Spawning bomb with scaling difficulty probability
        bomb_prob = min(config.BOMB_PROBABILITY_MAX, config.BOMB_PROBABILITY_INITIAL + self.difficulty * config.DIFFICULTY_SCALING_RATE)
        if random.random() < bomb_prob:
            bx = random.randint(120, config.WIDTH - 120)
            by = config.HEIGHT + 50
            
            bvy = random.uniform(config.LAUNCH_VY_MIN - 1.0, config.LAUNCH_VY_MAX)
            bvx = random.uniform(config.LAUNCH_VX_MIN, config.LAUNCH_VX_MAX)
            if bx < config.WIDTH // 2:
                bvx = abs(bvx)
            else:
                bvx = -abs(bvx)
                
            self.bombs.append(Bomb(bx, by, bvx, bvy))

    def update_physics(self):
        """
        Updates physics calculations for active fruits, bombs, and particles.
        """
        # Update particles (remove dead particles)
        self.particles = [p for p in self.particles if p.update()]
        
        # Update bombs
        active_bombs = []
        for bomb in self.bombs:
            if bomb.update():
                active_bombs.append(bomb)
        self.bombs = active_bombs
        
        # Update fruits
        active_fruits = []
        for fruit in self.fruits:
            if fruit.update():
                active_fruits.append(fruit)
            else:
                # If fruit fell below screen without being sliced, lose a life!
                if not fruit.is_sliced:
                    self.lives -= 1
                    # Play a quick low pitch error beep for miss feedback
                    threading.Thread(target=lambda: winsound.Beep(240, 100), daemon=True).start()
                    
                    if self.lives <= 0:
                        self.sounds.play_game_over()
                        if self.score > self.high_score:
                            self.high_score = self.score
                            self.save_high_score()
                        self.state = self.STATE_GAME_OVER
                        
        self.fruits = active_fruits

    def check_collisions(self):
        """
        Checks collisions between the active slicing trail and in-game targets.
        """
        velocity = self.slice_trail.get_last_velocity()
        
        # Only check collisions if the player is actively swiping fast enough
        if velocity < config.MIN_SLICE_VELOCITY:
            return
            
        slice_angle = self.slice_trail.get_last_angle()
        sliced_this_frame = []
        
        # Check fruit slicing
        for fruit in self.fruits:
            if not fruit.is_sliced and self.slice_trail.check_collision(fruit):
                # Slice!
                fruit.slice(slice_angle)
                sliced_this_frame.append(fruit)
                
                # Add score
                self.score += fruit.points
                self.difficulty += config.DIFFICULTY_SCALING_RATE
                
                # Spawn juice splatters
                num_drops = random.randint(12, 20)
                for _ in range(num_drops):
                    self.particles.append(Particle(fruit.x, fruit.y, fruit.color))
                    
        # Check bomb collisions
        for bomb in self.bombs:
            if self.slice_trail.check_collision(bomb):
                # EXPLOSION!
                self.sounds.play_bomb()
                
                # Spawn tons of explosion sparks
                for _ in range(40):
                    # Red, orange, and golden spark particles
                    spark_color = random.choice([(0, 0, 255), (0, 150, 255), (0, 255, 255)])
                    self.particles.append(Particle(bomb.x, bomb.y, spark_color))
                    
                if self.score > self.high_score:
                    self.high_score = self.score
                    self.save_high_score()
                    
                self.state = self.STATE_GAME_OVER
                return
                
        # Handle Combo announcements
        if len(sliced_this_frame) > 0:
            self.sounds.play_slice()
            
            if len(sliced_this_frame) >= 2:
                # Combo!
                self.combo_count = len(sliced_this_frame)
                self.combo_timer = time.time()
                # Award bonus combo points
                self.score += self.combo_count

    def run(self):
        """
        Main execution loop.
        """
        global is_mouse_active
        
        frame_time = 1.0 / config.FPS
        
        while True:
            start_tick = time.time()
            
            # Read camera frame
            ret, frame = self.cap.read()
            if not ret or frame is None:
                # Mock a beautiful solid dark background frame if camera is unavailable
                frame = np.zeros((config.HEIGHT, config.WIDTH, 3), dtype=np.uint8)
                cv2.putText(frame, "Webcam Offline - Using Mouse", (20, config.HEIGHT - 20), 
                            self.renderer.font, 0.5, (100, 100, 100), 1, cv2.LINE_AA)
            else:
                # Resize capture to match config settings
                frame = cv2.resize(frame, (config.WIDTH, config.HEIGHT))
                # Flip horizontally for mirrored view
                frame = cv2.flip(frame, 1)
                
            # Hand tracking position (skeleton disabled)
            hand_pos = self.detector.find_hand_position(frame, draw_skeleton=False)
            
            # Select tracked input source (override mouse with hand coordinates)
            input_pos = None
            if hand_pos is not None:
                input_pos = hand_pos
                is_mouse_active = False # Hand is active, disable mouse tracking
            elif is_mouse_active:
                input_pos = (mouse_x, mouse_y)
                
            # Update slicing trail
            if input_pos is not None:
                self.slice_trail.add_point(input_pos)
            else:
                # decay trail points if nothing was tracked
                if len(self.slice_trail.points) > 0:
                    self.slice_trail.points.pop(0)
                    self.slice_trail.timestamps.pop(0)

            # State Machine Loop
            if self.state == self.STATE_MENU:
                # Render MENU
                btn_box = self.renderer.draw_menu(frame, self.slice_trail)
                # Check for "SWIPE TO START" collision
                if self.check_interaction_box(btn_box):
                    self.sounds.play_slice()
                    self.reset_game()
                    self.state = self.STATE_PLAYING
                    
            elif self.state == self.STATE_PLAYING:
                # Darken background slightly to increase BGR contrast
                self.renderer.apply_dark_overlay(frame, 0.40)
                
                # Wave spawning logic
                self.spawn_cooldown -= 1
                if self.spawn_cooldown <= 0:
                    self.spawn_wave()
                    # Calculate spawn intervals based on scaling difficulty
                    cooldown_val = max(config.MIN_SPAWN_COOLDOWN, config.INITIAL_SPAWN_COOLDOWN - int(self.difficulty * 2))
                    self.spawn_cooldown = random.randint(int(cooldown_val * 0.8), int(cooldown_val * 1.2))
                    
                # Update physics
                self.update_physics()
                
                # Check slice collisions
                self.check_collisions()
                
                # Draw particles
                for p in self.particles:
                    self.renderer.draw_particle(frame, p)
                    
                # Draw bombs
                for bomb in self.bombs:
                    self.renderer.draw_bomb(frame, bomb)
                    
                # Draw fruits
                for fruit in self.fruits:
                    self.renderer.draw_fruit(frame, fruit)
                    
                # Draw glowing blade trail
                self.renderer.draw_blade_trail(frame, self.slice_trail)
                
                # Draw Score and Hearts
                self.renderer.draw_ui(frame, self.score, self.lives, self.high_score)
                
                # Draw combo overlays
                self.renderer.draw_combo(frame, self.combo_count, self.combo_timer)
                
            elif self.state == self.STATE_GAME_OVER:
                # Render GAME OVER
                btn_box = self.renderer.draw_game_over(frame, self.score, self.high_score)
                # Check for "SWIPE TO RESTART" collision
                if self.check_interaction_box(btn_box):
                    self.sounds.play_slice()
                    self.reset_game()
                    self.state = self.STATE_PLAYING

            # Display frame
            cv2.imshow(self.window_name, frame)
            
            # Sleep to match frame cap
            elapsed = time.time() - start_tick
            sleep_time = max(0.001, frame_time - elapsed)
            time.sleep(sleep_time)
            
            # Press 'q' or 'ESC' or check if window close button clicked
            key = cv2.waitKey(1) & 0xFF
            if key == ord('q') or key == 27:
                break
                
            # Graceful exit if OpenCV window is closed manually by user
            if cv2.getWindowProperty(self.window_name, cv2.WND_PROP_VISIBLE) < 1:
                break
                
        # Clean up
        self.cap.release()
        self.detector.close()
        cv2.destroyAllWindows()


if __name__ == "__main__":
    game = FruitNinjaGame()
    game.run()
