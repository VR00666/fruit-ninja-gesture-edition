# game_objects.py
"""
Definitions for Fruit, Bomb, Particle, and Slice objects in the game.
Includes physics simulation, rotation, and continuous line-segment collision detection.
"""
import math
import time
import random
import config

class Particle:
    def __init__(self, x, y, color):
        """
        A particle representing juice splashes or bomb sparks.
        """
        self.x = float(x)
        self.y = float(y)
        self.color = color
        
        # Random burst velocities
        angle = random.uniform(0, 2 * math.pi)
        speed = random.uniform(2.0, 8.0)
        self.vx = math.cos(angle) * speed
        self.vy = math.sin(angle) * speed - random.uniform(1.0, 4.0) # Upward bias
        
        self.radius = random.randint(3, 7)
        self.life = 1.0  # Decays from 1.0 to 0.0
        self.decay_rate = random.uniform(0.03, 0.06)

    def update(self):
        """
        Updates particle position and lifetime.
        Returns False if the particle has died and should be removed.
        """
        self.x += self.vx
        self.y += self.vy
        
        # Apply slight gravity
        self.vy += 0.2
        
        # Decay life
        self.life -= self.decay_rate
        if self.radius > 1:
            self.radius -= 0.1
            
        return self.life > 0.0 and self.radius > 0.5


class Fruit:
    def __init__(self, fruit_type, x, y, vx, vy):
        """
        A fruit with parabolic physics and rotation. Can be sliced into halves.
        """
        self.type = fruit_type
        cfg = config.FRUIT_TYPES[fruit_type]
        self.radius = cfg['radius']
        self.color = cfg['color']
        self.points = cfg['points']
        self.display_name = cfg['display_name']
        
        # Physics
        self.x = float(x)
        self.y = float(y)
        self.vx = float(vx)
        self.vy = float(vy)
        
        self.angle = random.uniform(0, 360)
        self.spin = random.uniform(config.SPIN_MIN, config.SPIN_MAX)
        
        # Sliced state
        self.is_sliced = False
        self.slice_time = 0.0
        
        # Left and Right half properties (active after slice)
        self.h1_x = 0.0
        self.h1_y = 0.0
        self.h1_vx = 0.0
        self.h1_vy = 0.0
        self.h1_angle = 0.0
        self.h1_spin = 0.0
        
        self.h2_x = 0.0
        self.h2_y = 0.0
        self.h2_vx = 0.0
        self.h2_vy = 0.0
        self.h2_angle = 0.0
        self.h2_spin = 0.0

    def update(self):
        """
        Updates fruit physics.
        If sliced, updates its two falling halves.
        Returns False if the object falls off the bottom of the screen.
        """
        if not self.is_sliced:
            # Standard single fruit physics
            self.x += self.vx
            self.y += self.vy
            self.vy += config.GRAVITY
            self.angle += self.spin
            
            # Active fruits are off-screen when they fall past the bottom
            # (allowing a buffer for radius)
            if self.y > config.HEIGHT + 100:
                return False
        else:
            # Sliced halves physics
            self.h1_x += self.h1_vx
            self.h1_y += self.h1_vy
            self.h1_vy += config.GRAVITY
            self.h1_angle += self.h1_spin
            
            self.h2_x += self.h2_vx
            self.h2_y += self.h2_vy
            self.h2_vy += config.GRAVITY
            self.h2_angle += self.h2_spin
            
            # Sliced halves are done when both fall off-screen
            if self.h1_y > config.HEIGHT + 100 and self.h2_y > config.HEIGHT + 100:
                return False
                
        return True

    def slice(self, slice_angle_rad):
        """
        Triggers the slicing event, splitting the fruit into two physical halves
        that fly apart perpendicular to the slice angle.
        """
        if self.is_sliced:
            return
            
        self.is_sliced = True
        self.slice_time = time.time()
        
        # Calculate split directions perpendicular to the slice angle
        # This gives a highly realistic cutting-apart feel!
        split_angle1 = slice_angle_rad + math.pi/2
        split_angle2 = slice_angle_rad - math.pi/2
        
        # Halves fly outward from the split point
        split_speed = random.uniform(3.0, 6.0)
        
        self.h1_x = self.x
        self.h1_y = self.y
        self.h1_vx = self.vx + math.cos(split_angle1) * split_speed
        self.h1_vy = self.vy + math.sin(split_angle1) * split_speed - 1.5 # slight upward bounce
        self.h1_angle = self.angle
        self.h1_spin = self.spin - random.uniform(2.0, 6.0)
        
        self.h2_x = self.x
        self.h2_y = self.y
        self.h2_vx = self.vx + math.cos(split_angle2) * split_speed
        self.h2_vy = self.vy + math.sin(split_angle2) * split_speed - 1.5
        self.h2_angle = self.angle
        self.h2_spin = self.spin + random.uniform(2.0, 6.0)


class Bomb:
    def __init__(self, x, y, vx, vy):
        """
        A dangerous bomb that causes game over if sliced.
        """
        self.x = float(x)
        self.y = float(y)
        self.vx = float(vx)
        self.vy = float(vy)
        
        self.radius = 32
        self.angle = random.uniform(0, 360)
        self.spin = random.uniform(-4, 4)
        
        self.fuse_spark_timer = 0

    def update(self):
        """
        Updates bomb position.
        Returns False if it falls off-screen.
        """
        self.x += self.vx
        self.y += self.vy
        self.vy += config.GRAVITY
        self.angle += self.spin
        
        self.fuse_spark_timer += 1
        
        if self.y > config.HEIGHT + 100:
            return False
            
        return True


class Slice:
    def __init__(self):
        """
        Manages the player's swipe trail and handles collision checks.
        """
        self.points = []       # List of (x, y) coordinates
        self.timestamps = []   # List of float epoch times

    def add_point(self, pt):
        """
        Adds a tracked fingertip point to the slice trail.
        """
        self.points.append(pt)
        self.timestamps.append(time.time())
        
        # Restrict trail size
        if len(self.points) > config.MAX_TRAIL_POINTS:
            self.points.pop(0)
            self.timestamps.pop(0)

    def clear(self):
        """
        Clears the slice trail completely.
        """
        self.points.clear()
        self.timestamps.clear()

    def get_recent_points(self):
        """
        Filters out points that are too old to keep the trail tight.
        """
        now = time.time()
        valid_points = []
        
        for pt, ts in zip(self.points, self.timestamps):
            # Keep points that are less than 0.25 seconds old
            if now - ts < 0.25:
                valid_points.append(pt)
                
        return valid_points

    def get_last_velocity(self):
        """
        Calculates the instantaneous pixel speed between the last two frames.
        """
        points = self.get_recent_points()
        if len(points) < 2:
            return 0.0
            
        p1 = points[-2]
        p2 = points[-1]
        return math.sqrt((p2[0] - p1[0])**2 + (p2[1] - p1[1])**2)

    def get_last_angle(self):
        """
        Calculates the angle of the last swipe segment in radians.
        """
        points = self.get_recent_points()
        if len(points) < 2:
            return 0.0
            
        p1 = points[-2]
        p2 = points[-1]
        return math.atan2(p2[1] - p1[1], p2[0] - p1[0])

    def check_collision(self, obj):
        """
        Performs continuous line-segment vs circle collision checks across the trail.
        This prevents fast swings from passing through fruit colliders (tunneling).
        
        Returns:
            bool: True if collision occurred, False otherwise.
        """
        points = self.get_recent_points()
        if len(points) < 2:
            return False
            
        cx, cy = obj.x, obj.y
        r = obj.radius
        
        # Check collision with each segment of the trail
        for i in range(len(points) - 1):
            p1 = points[i]
            p2 = points[i+1]
            
            # Segment vector AB
            ab_x = p2[0] - p1[0]
            ab_y = p2[1] - p1[1]
            
            # Vector AC from segment start to circle center
            ac_x = cx - p1[0]
            ac_y = cy - p1[1]
            
            ab_len_sq = ab_x*ab_x + ab_y*ab_y
            
            if ab_len_sq == 0:
                # Segment is a single point, check simple distance
                dist = math.sqrt(ac_x*ac_x + ac_y*ac_y)
                if dist <= r:
                    return True
                continue
                
            # Projection factor t (normalized position of projection along segment)
            t = (ac_x * ab_x + ac_y * ab_y) / ab_len_sq
            
            # Clamp t to range [0, 1] to stay on the line segment
            t = max(0.0, min(1.0, t))
            
            # Find the closest point on the segment
            closest_x = p1[0] + t * ab_x
            closest_y = p1[1] + t * ab_y
            
            # Calculate distance from circle center to closest point
            dist = math.sqrt((cx - closest_x)**2 + (cy - closest_y)**2)
            
            if dist <= r:
                return True
                
        return False
