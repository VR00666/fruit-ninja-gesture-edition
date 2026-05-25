# renderer.py
"""
Game rendering module for Fruit Ninja.
Draws procedural vector fruit graphics (with stems, rinds, seeds, and slices), 
glowing neon blade trails, fluid juice splash particles, heart icons for lives,
and custom gesture-driven interactive UI overlays on the OpenCV webcam feed.
"""
import cv2
import numpy as np
import math
import time
import config

class GameRenderer:
    def __init__(self):
        """
        Initializes the GameRenderer.
        Uses OpenCV's Hershey fonts for clean, high-performance UI rendering.
        """
        self.font = cv2.FONT_HERSHEY_DUPLEX
        self.font_bold = cv2.FONT_HERSHEY_TRIPLEX

    def apply_dark_overlay(self, frame, alpha=0.45):
        """
        Applies a semi-transparent dark tint to the camera feed to make game objects
        and glowing neon effects pop visually.
        """
        overlay = np.zeros_like(frame)
        # Blend the frame with a black canvas
        cv2.addWeighted(overlay, alpha, frame, 1.0 - alpha, 0, frame)

    def draw_heart(self, frame, center, size, color, filled=True):
        """
        Draws a beautiful heart shape programmatically in OpenCV.
        Constructed from two top circles and a bottom triangle.
        """
        x, y = center
        r = size // 4
        
        # Two top circles
        c1 = (x - r, y - r // 2)
        c2 = (x + r, y - r // 2)
        
        if filled:
            cv2.circle(frame, c1, r, color, -1, cv2.LINE_AA)
            cv2.circle(frame, c2, r, color, -1, cv2.LINE_AA)
            # Bottom triangle points
            pts = np.array([
                [x - 2 * r, y - r // 2],
                [x + 2 * r, y - r // 2],
                [x, y + size // 2]
            ], np.int32)
            cv2.fillPoly(frame, [pts], color, cv2.LINE_AA)
        else:
            # Draw outline
            thickness = 2
            cv2.circle(frame, c1, r, color, thickness, cv2.LINE_AA)
            cv2.circle(frame, c2, r, color, thickness, cv2.LINE_AA)
            cv2.line(frame, (x - 2 * r, y - r // 2), (x, y + size // 2), color, thickness, cv2.LINE_AA)
            cv2.line(frame, (x + 2 * r, y - r // 2), (x, y + size // 2), color, thickness, cv2.LINE_AA)

    def draw_ui(self, frame, score, lives, high_score):
        """
        Draws the score, lives (hearts), and high score on the screen with modern drop-shadows.
        """
        # Score Shadow & Text (Top Left)
        cv2.putText(frame, f"SCORE: {score}", (22, 42), self.font, 1.0, (0, 0, 0), 3, cv2.LINE_AA)
        cv2.putText(frame, f"SCORE: {score}", (20, 40), self.font, 1.0, config.COLOR_WHITE, 1, cv2.LINE_AA)
        
        # High Score (Top Middle)
        hs_text = f"BEST: {high_score}"
        text_size = cv2.getTextSize(hs_text, self.font, 0.7, 2)[0]
        hs_x = (config.WIDTH - text_size[0]) // 2
        cv2.putText(frame, hs_text, (hs_x + 2, 37), self.font, 0.7, (0, 0, 0), 3, cv2.LINE_AA)
        cv2.putText(frame, hs_text, (hs_x, 35), self.font, 0.7, (180, 255, 180), 1, cv2.LINE_AA)

        # Lives Icons (Top Right - Red hearts)
        start_x = config.WIDTH - 40
        spacing = 35
        for i in range(config.MAX_LIVES):
            center = (start_x - i * spacing, 30)
            if i < lives:
                self.draw_heart(frame, center, 24, config.COLOR_UI_HEART_ACTIVE, filled=True)
            else:
                self.draw_heart(frame, center, 24, config.COLOR_UI_HEART_LOST, filled=False)

    def draw_combo(self, frame, combo_count, combo_timer):
        """
        Draws an animated floating combo alert when a multi-slice is made.
        Fades out and rises over time.
        """
        now = time.time()
        elapsed = now - combo_timer
        if elapsed > 1.0:
            return
            
        # Animate vertical rising and scale fading
        offset_y = int(elapsed * 45)
        opacity = max(0, 1.0 - elapsed)
        
        text = f"{combo_count}x COMBO!"
        
        # Calculate size to center it
        size = cv2.getTextSize(text, self.font_bold, 1.2, 3)[0]
        x = (config.WIDTH - size[0]) // 2
        y = (config.HEIGHT // 2) - 80 - offset_y
        
        # Draw floating combo banner with drop shadow
        cv2.putText(frame, text, (x + 3, y + 3), self.font_bold, 1.2, (0, 0, 0), 4, cv2.LINE_AA)
        # BGR: flashing yellow/mango combo text
        cv2.putText(frame, text, (x, y), self.font_bold, 1.2, (50, 220, 255), 2, cv2.LINE_AA)

    def draw_blade_trail(self, frame, slice_obj):
        """
        Renders a stunning dual-stage glowing neon sword trail.
        - Stage 1: Thick alpha-blended outer cyan glow.
        - Stage 2: Thin, razor-sharp pure white core.
        """
        points = slice_obj.get_recent_points()
        if len(points) < 2:
            return
            
        # Draw outer glow on a separate layer for translucent blending
        overlay = frame.copy()
        num_pts = len(points)
        
        for i in range(num_pts - 1):
            p1 = points[i]
            p2 = points[i+1]
            
            # Progress factor (0.0 at tail, 1.0 at fingertip)
            factor = i / (num_pts - 1)
            
            # Neon color fade: darker cyan to bright cyan
            color = (
                int(255 * factor), 
                int(255 * factor), 
                int(120 * factor + 50)
            )
            
            # Thickness scales up towards the tip
            thickness = int(14 * factor) + 1
            cv2.line(overlay, p1, p2, color, thickness, cv2.LINE_AA)
            
        # Blend the outer glow onto main frame
        cv2.addWeighted(overlay, 0.45, frame, 0.55, 0, frame)
        
        # Draw the razor-sharp white core directly on the frame
        for i in range(num_pts - 1):
            p1 = points[i]
            p2 = points[i+1]
            factor = i / (num_pts - 1)
            thickness = int(3 * factor) + 1
            cv2.line(frame, p1, p2, config.COLOR_WHITE, thickness, cv2.LINE_AA)
            
        # Draw a beautiful glowing slicing tip point (cursor) at the fingertip
        tip = points[-1]
        cv2.circle(frame, tip, 8, (255, 255, 0), 2, cv2.LINE_AA) # outer cyan glow ring
        cv2.circle(frame, tip, 4, config.COLOR_WHITE, -1, cv2.LINE_AA) # inner solid white core

    def draw_particle(self, frame, p):
        """
        Draws an individual juice particle with its color faded by its remaining life.
        """
        # Linear decay BGR color to fade out juice drops
        color = (
            int(p.color[0] * p.life),
            int(p.color[1] * p.life),
            int(p.color[2] * p.life)
        )
        cv2.circle(frame, (int(p.x), int(p.y)), int(p.radius), color, -1, cv2.LINE_AA)

    def draw_fruit(self, frame, fruit):
        """
        Draws procedural vector graphics for fruits, including stems, leaves,
        rinds, interior seeds, and rotating sliced halves.
        """
        if not fruit.is_sliced:
            # Whole fruit
            center = (int(fruit.x), int(fruit.y))
            r = int(fruit.radius)
            angle_deg = fruit.angle
            
            # Setup rotation transform matrix for drawing internal details
            rot_matrix = cv2.getRotationMatrix2D(center, angle_deg, 1.0)
            
            if fruit.type == 'watermelon':
                # Green outer rind
                cv2.circle(frame, center, r, config.COLOR_WATERMELON_OUTER, -1, cv2.LINE_AA)
                # Pink inner flesh
                cv2.circle(frame, center, int(r * 0.85), config.COLOR_WATERMELON_INNER, -1, cv2.LINE_AA)
                
                # Small seeds inside (rotated)
                seed_color = config.COLOR_BLACK
                seed_offsets = [(-r//3, -r//3), (r//3, -r//3), (-r//4, r//4), (r//4, r//4), (0, 0)]
                for dx, dy in seed_offsets:
                    # Apply rotation
                    rx = int(center[0] + dx * math.cos(math.radians(angle_deg)) - dy * math.sin(math.radians(angle_deg)))
                    ry = int(center[1] + dx * math.sin(math.radians(angle_deg)) + dy * math.cos(math.radians(angle_deg)))
                    cv2.circle(frame, (rx, ry), 2, seed_color, -1, cv2.LINE_AA)
                    
            elif fruit.type == 'apple':
                # Apple Red body
                cv2.circle(frame, center, r, config.COLOR_APPLE, -1, cv2.LINE_AA)
                # Cute stem (drawn at top, rotated)
                stem_angle = math.radians(angle_deg - 90) # Upwards relative to apple rotation
                stem_end_x = int(center[0] + (r + 8) * math.cos(stem_angle))
                stem_end_y = int(center[1] + (r + 8) * math.sin(stem_angle))
                cv2.line(frame, center, (stem_end_x, stem_end_y), (42, 42, 120), 3, cv2.LINE_AA) # brown stem
                
                # Highlight shine
                shine_angle = math.radians(angle_deg - 135)
                sx = int(center[0] + (r * 0.5) * math.cos(shine_angle))
                sy = int(center[1] + (r * 0.5) * math.sin(shine_angle))
                cv2.circle(frame, (sx, sy), r // 5, (255, 200, 200), -1, cv2.LINE_AA)

            elif fruit.type == 'orange':
                # Orange outer body
                cv2.circle(frame, center, r, config.COLOR_ORANGE, -1, cv2.LINE_AA)
                # Inner white ring
                cv2.circle(frame, center, int(r * 0.90), config.COLOR_WHITE, 1, cv2.LINE_AA)
                # Citrus segment wedges
                for i in range(8):
                    wedge_angle = angle_deg + i * 45
                    rad = math.radians(wedge_angle)
                    line_end_x = int(center[0] + r * 0.85 * math.cos(rad))
                    line_end_y = int(center[1] + r * 0.85 * math.sin(rad))
                    cv2.line(frame, center, (line_end_x, line_end_y), config.COLOR_WHITE, 1, cv2.LINE_AA)
                cv2.circle(frame, center, int(r * 0.15), config.COLOR_WHITE, -1, cv2.LINE_AA)

            elif fruit.type == 'pineapple':
                # Pineapple oval body
                axes = (r, int(r * 1.35))
                # Fill drawing matrix
                cv2.ellipse(frame, center, axes, angle_deg, 0, 360, config.COLOR_PINEAPPLE, -1, cv2.LINE_AA)
                # Draw cross-hatch segment lines
                for dx in range(-r, r, 12):
                    # Simple procedural lines
                    pass
                # Spiky green leaves (drawn at top, rotated)
                leaf_angle = math.radians(angle_deg - 90)
                lx = int(center[0] + (axes[1] + 12) * math.cos(leaf_angle))
                ly = int(center[1] + (axes[1] + 12) * math.sin(leaf_angle))
                cv2.line(frame, center, (lx, ly), (34, 139, 34), 6, cv2.LINE_AA)

            elif fruit.type == 'mango':
                # Kidmey-shaped mango
                # We can draw it as an offset double circle or slightly elongated ellipse
                axes = (int(r * 1.2), r)
                cv2.ellipse(frame, center, axes, angle_deg, 0, 360, config.COLOR_MANGO, -1, cv2.LINE_AA)
                # Stylized blush highlight
                blush_angle = math.radians(angle_deg - 45)
                bx = int(center[0] + (r * 0.3) * math.cos(blush_angle))
                by = int(center[1] + (r * 0.3) * math.sin(blush_angle))
                cv2.circle(frame, (bx, by), r // 3, (80, 100, 255), -1, cv2.LINE_AA) # soft red-gold blush
                
        else:
            # Sliced halves (falling independently)
            # We use cv2.ellipse with 0-180 and 180-360 start/end angles to draw clean semi-circles
            h1_c = (int(fruit.h1_x), int(fruit.h1_y))
            h2_c = (int(fruit.h2_x), int(fruit.h2_y))
            r = int(fruit.radius)
            
            # Half 1 (0 to 180 degrees)
            cv2.ellipse(frame, h1_c, (r, r), fruit.h1_angle, 0, 180, fruit.color, -1, cv2.LINE_AA)
            # Sliced face highlight (white line along cut edge)
            cut_rad1 = math.radians(fruit.h1_angle)
            cut_x1 = int(h1_c[0] + r * math.cos(cut_rad1))
            cut_y1 = int(h1_c[1] + r * math.sin(cut_rad1))
            cut_x2 = int(h1_c[0] - r * math.cos(cut_rad1))
            cut_y2 = int(h1_c[1] - r * math.sin(cut_rad1))
            cv2.line(frame, (cut_x1, cut_y1), (cut_x2, cut_y2), config.COLOR_WHITE, 2, cv2.LINE_AA)
            
            # Half 2 (180 to 360 degrees)
            cv2.ellipse(frame, h2_c, (r, r), fruit.h2_angle, 180, 360, fruit.color, -1, cv2.LINE_AA)
            # Sliced face highlight for second half
            cut_rad2 = math.radians(fruit.h2_angle)
            cut_x3 = int(h2_c[0] + r * math.cos(cut_rad2))
            cut_y3 = int(h2_c[1] + r * math.sin(cut_rad2))
            cut_x4 = int(h2_c[0] - r * math.cos(cut_rad2))
            cut_y4 = int(h2_c[1] - r * math.sin(cut_rad2))
            cv2.line(frame, (cut_x3, cut_y3), (cut_x4, cut_y4), config.COLOR_WHITE, 2, cv2.LINE_AA)

    def draw_bomb(self, frame, bomb):
        """
        Draws a detailed bomb with a dark spherical body, glowing red fuse collar,
        glowing hazard line, and an active animated yellow fuse spark.
        """
        center = (int(bomb.x), int(bomb.y))
        r = int(bomb.radius)
        angle_deg = bomb.angle
        
        # Draw dark bomb body
        cv2.circle(frame, center, r, config.COLOR_BOMB, -1, cv2.LINE_AA)
        
        # Red pulsing danger outline
        glow_pulse = int(abs(math.sin(time.time() * 8)) * 3) + 1
        cv2.circle(frame, center, r + glow_pulse, config.COLOR_BOMB_GLOW, 2, cv2.LINE_AA)
        
        # Draw red hazard stripe/X (rotated)
        x_len = int(r * 0.4)
        rad = math.radians(angle_deg)
        x1 = int(center[0] - x_len * math.cos(rad))
        y1 = int(center[1] - x_len * math.sin(rad))
        x2 = int(center[0] + x_len * math.cos(rad))
        y2 = int(center[1] + x_len * math.sin(rad))
        cv2.line(frame, (x1, y1), (x2, y2), config.COLOR_BOMB_GLOW, 3, cv2.LINE_AA)
        
        # Fuse collar (little neck at top)
        neck_angle = math.radians(angle_deg - 90)
        nx = int(center[0] + r * math.cos(neck_angle))
        ny = int(center[1] + r * math.sin(neck_angle))
        cv2.circle(frame, (nx, ny), 5, (100, 100, 100), -1, cv2.LINE_AA)
        
        # Fuse wire (curved line)
        fx1 = nx
        fy1 = ny
        fx2 = int(nx + 12 * math.cos(math.radians(angle_deg - 75)))
        fy2 = int(ny + 12 * math.sin(math.radians(angle_deg - 75)))
        cv2.line(frame, (fx1, fy1), (fx2, fy2), (120, 150, 180), 2, cv2.LINE_AA)
        
        # Active spark (flashing gold circle)
        if bomb.fuse_spark_timer % 2 == 0:
            cv2.circle(frame, (fx2, fy2), 5, config.COLOR_FUSE, -1, cv2.LINE_AA)
            cv2.circle(frame, (fx2, fy2), 8, config.COLOR_FUSE, 1, cv2.LINE_AA)

    def draw_menu(self, frame, slice_obj):
        """
        Renders the highly stylized interactive gesture-driven start menu overlay.
        Includes title text and a glowing "SLICE TO PLAY" swipe bar.
        """
        self.apply_dark_overlay(frame, 0.6)
        
        # Title Shadow & Text
        title_text = "FRUIT NINJA"
        t_size = cv2.getTextSize(title_text, self.font_bold, 1.8, 4)[0]
        tx = (config.WIDTH - t_size[0]) // 2
        ty = 160
        cv2.putText(frame, title_text, (tx + 3, ty + 3), self.font_bold, 1.8, (0, 0, 0), 5, cv2.LINE_AA)
        cv2.putText(frame, title_text, (tx, ty), self.font_bold, 1.8, (0, 220, 255), 2, cv2.LINE_AA)
        
        subtitle_text = "GESTURE EDITION"
        s_size = cv2.getTextSize(subtitle_text, self.font, 0.9, 2)[0]
        sx = (config.WIDTH - s_size[0]) // 2
        sy = 205
        cv2.putText(frame, subtitle_text, (sx + 2, sy + 2), self.font, 0.9, (0, 0, 0), 3, cv2.LINE_AA)
        cv2.putText(frame, subtitle_text, (sx, sy), self.font, 0.9, config.COLOR_WHITE, 1, cv2.LINE_AA)

        # Drawing the interactive Slice Button
        btn_y = 310
        btn_w, btn_h = 320, 50
        btn_x = (config.WIDTH - btn_w) // 2
        
        # Pulsing outline for the gesture bar
        pulse = int(abs(math.sin(time.time() * 5)) * 4) + 1
        cv2.rectangle(frame, (btn_x - pulse, btn_y - pulse), (btn_x + btn_w + pulse, btn_y + btn_h + pulse), (0, 255, 0), 2, cv2.LINE_AA)
        # Background bar
        overlay = frame.copy()
        cv2.rectangle(overlay, (btn_x, btn_y), (btn_x + btn_w, btn_y + btn_h), (0, 100, 0), -1, cv2.LINE_AA)
        cv2.addWeighted(overlay, 0.4, frame, 0.6, 0, frame)
        
        # Interactive Text
        btn_text = "SWIPE HERE TO START"
        b_size = cv2.getTextSize(btn_text, self.font, 0.7, 2)[0]
        bx = btn_x + (btn_w - b_size[0]) // 2
        by = btn_y + (btn_h + b_size[1]) // 2
        cv2.putText(frame, btn_text, (bx, by), self.font, 0.7, config.COLOR_WHITE, 1, cv2.LINE_AA)
        
        # Instruction text below
        inst_text = "Keep hand in camera view & wave index finger"
        i_size = cv2.getTextSize(inst_text, self.font, 0.5, 1)[0]
        ix = (config.WIDTH - i_size[0]) // 2
        cv2.putText(frame, inst_text, (ix, 410), self.font, 0.5, config.COLOR_GRAY, 1, cv2.LINE_AA)
        
        # Returns the rectangle boundary for collision check
        return (btn_x, btn_y, btn_w, btn_h)

    def draw_game_over(self, frame, score, high_score):
        """
        Renders the custom game-over screen featuring high score announcements
        and a "SWIPE TO RESTART" gesture interface.
        """
        self.apply_dark_overlay(frame, 0.7)
        
        # GAME OVER banner
        go_text = "GAME OVER"
        go_size = cv2.getTextSize(go_text, self.font_bold, 1.8, 4)[0]
        gox = (config.WIDTH - go_size[0]) // 2
        goy = 150
        cv2.putText(frame, go_text, (gox + 3, goy + 3), self.font_bold, 1.8, (0, 0, 0), 5, cv2.LINE_AA)
        cv2.putText(frame, go_text, (gox, goy), self.font_bold, 1.8, (0, 0, 255), 2, cv2.LINE_AA)
        
        # Score announcements
        sc_text = f"FINAL SCORE: {score}"
        sc_size = cv2.getTextSize(sc_text, self.font, 0.9, 2)[0]
        scx = (config.WIDTH - sc_size[0]) // 2
        scy = 210
        cv2.putText(frame, sc_text, (scx, scy), self.font, 0.9, config.COLOR_WHITE, 1, cv2.LINE_AA)
        
        hs_text = f"BEST SCORE: {high_score}"
        hs_size = cv2.getTextSize(hs_text, self.font, 0.7, 1)[0]
        hsx = (config.WIDTH - hs_size[0]) // 2
        hsy = 245
        cv2.putText(frame, hs_text, (hsx, hsy), self.font, 0.7, (180, 255, 180), 1, cv2.LINE_AA)
        
        # Restart Button Bar
        btn_y = 310
        btn_w, btn_h = 320, 50
        btn_x = (config.WIDTH - btn_w) // 2
        
        pulse = int(abs(math.sin(time.time() * 5)) * 4) + 1
        cv2.rectangle(frame, (btn_x - pulse, btn_y - pulse), (btn_x + btn_w + pulse, btn_y + btn_h + pulse), (0, 0, 255), 2, cv2.LINE_AA)
        
        overlay = frame.copy()
        cv2.rectangle(overlay, (btn_x, btn_y), (btn_x + btn_w, btn_y + btn_h), (0, 0, 100), -1, cv2.LINE_AA)
        cv2.addWeighted(overlay, 0.4, frame, 0.6, 0, frame)
        
        btn_text = "SWIPE HERE TO RESTART"
        b_size = cv2.getTextSize(btn_text, self.font, 0.7, 2)[0]
        bx = btn_x + (btn_w - b_size[0]) // 2
        by = btn_y + (btn_h + b_size[1]) // 2
        cv2.putText(frame, btn_text, (bx, by), self.font, 0.7, config.COLOR_WHITE, 1, cv2.LINE_AA)
        
        return (btn_x, btn_y, btn_w, btn_h)
