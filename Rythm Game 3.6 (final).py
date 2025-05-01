import sys
import pygame
import random
import librosa
import time
import warnings
import numpy as np
import os
import math
from pygame import gfxdraw

# Suppress librosa warnings
warnings.filterwarnings("ignore", category=UserWarning)

# Constants
SCREEN_WIDTH = 1280
SCREEN_HEIGHT = 720
ARROW_SIZE = 80 
ARROW_SPEED = 850
HIT_ZONE_Y = SCREEN_HEIGHT - 100
HIT_MARGIN = 15
FPS = 60
CORNER_RADIUS = 13
GLOW_ALPHA = 150  
FAST_MODE_MULTIPLIER = 2 
MARGIN_SIZE = 10
BOUNCE_DURATION = 0.2
PARTICLE_COUNT = 100
PROGRESS_BAR_WIDTH = 200
PROGRESS_BAR_HEIGHT = 10
PROGRESS_BAR_Y = 50

# Character Display Constants
IMAGE_X = SCREEN_WIDTH // 2 - 300      # X position (center of screen)
IMAGE_Y = SCREEN_HEIGHT // 2 + 150     # Y position (center of screen)
IMAGE_SCALE = 0.5                      # Miku size scaling factor
TETO_SCALE = 0.5                       # Teto size scaling factor
TETO_OFFSET_X = -100                   # Teto's horizontal offset from Miku
TETO_OFFSET_Y = -30                      # Teto's vertical offset from Miku
TETO_SWITCH_INTERVAL = 1000            # 2 seconds between switches
MAX_BOUNCE = 0                         # Max bounce height in pixels
BOUNCE_SPEED = 0.002                   # Bounce animation speed

# Colors
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
NEON_GREEN = (57, 255, 20)
NEON_RED = (255, 20, 57)
NEON_BLUE = (20, 57, 255)
NEON_YELLOW = (255, 234, 44)
NEON_PURPLE = (180, 20, 255)
NEON_PINK = (255, 20, 180)
GRAY = (50, 50, 50)
DARK_GRAY = (20, 20, 20)
HIT_ZONE_BG = (100, 100, 100, 100)

COLORS = {
    "left": NEON_YELLOW,
    "down": NEON_BLUE,
    "up": NEON_RED,
    "right": NEON_GREEN
}

GLOW_COLORS = {
    "left": (*NEON_YELLOW, GLOW_ALPHA),
    "down": (*NEON_BLUE, GLOW_ALPHA),
    "up": (*NEON_RED, GLOW_ALPHA),
    "right": (*NEON_GREEN, GLOW_ALPHA)
}

def get_beat_times(filename):
    try:
        y, sr = librosa.load(filename, sr=None)
        tempo, beat_frames = librosa.beat.beat_track(y=y, sr=sr)
        return librosa.frames_to_time(beat_frames, sr=sr).tolist()
    except Exception as e:
        print(f"Error processing audio file: {e}")
        return [i * 0.5 for i in range(30)]

def draw_hit_zone(screen):
    hit_zone_bg = pygame.Surface((SCREEN_WIDTH - 850, HIT_MARGIN * 2 + 20), pygame.SRCALPHA)
    pygame.draw.rect(hit_zone_bg, HIT_ZONE_BG, (0, 0, hit_zone_bg.get_width(), hit_zone_bg.get_height()), 
                    border_radius=10)
    screen.blit(hit_zone_bg, (SCREEN_WIDTH - (SCREEN_WIDTH - 850) - 50, HIT_ZONE_Y - HIT_MARGIN - 10))
    pygame.draw.rect(screen, WHITE, (SCREEN_WIDTH - (SCREEN_WIDTH - 850) - 50, int(HIT_ZONE_Y - HIT_MARGIN - 25),
                        SCREEN_WIDTH - 850, 3), border_radius=1)

def draw_frame(screen):
    frame_color = (40, 40, 40, 200)
    frame_surface = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
    pygame.draw.rect(frame_surface, frame_color, (0, 0, SCREEN_WIDTH, MARGIN_SIZE))
    bottom_frame_y = HIT_ZONE_Y + HIT_MARGIN + 75
    pygame.draw.rect(frame_surface, frame_color, (0, bottom_frame_y, SCREEN_WIDTH, SCREEN_HEIGHT - bottom_frame_y))
    pygame.draw.rect(frame_surface, frame_color, (0, 0, MARGIN_SIZE, SCREEN_HEIGHT))
    pygame.draw.rect(frame_surface, frame_color, (SCREEN_WIDTH - MARGIN_SIZE, 0, MARGIN_SIZE, SCREEN_HEIGHT))
    screen.blit(frame_surface, (0, 0))

def load_arrow_image(direction):
    try:
        img = pygame.image.load(f"{direction}.png").convert_alpha()
        return pygame.transform.scale(img, (ARROW_SIZE, ARROW_SIZE))
    except:
        surf = pygame.Surface((ARROW_SIZE, ARROW_SIZE), pygame.SRCALPHA)
        color = COLORS[direction]
        if direction == "left":
            points = [(ARROW_SIZE, 0), (0, ARROW_SIZE//2), (ARROW_SIZE, ARROW_SIZE)]
        elif direction == "right":
            points = [(0, 0), (ARROW_SIZE, ARROW_SIZE//2), (0, ARROW_SIZE)]
        elif direction == "up":
            points = [(0, ARROW_SIZE), (ARROW_SIZE//2, 0), (ARROW_SIZE, ARROW_SIZE)]
        elif direction == "down":
            points = [(0, 0), (ARROW_SIZE//2, ARROW_SIZE), (ARROW_SIZE, 0)]
        pygame.draw.polygon(surf, color, points)
        return surf

def load_miku_images():
    """Load and scale Miku images for direction display"""
    try:
        miku_up = pygame.image.load("miku_up.png")
        miku_left = pygame.image.load("miku_left.png")
        miku_right = pygame.image.load("miku_right.png")
        miku_down = pygame.image.load("miku_down.png")
        
        # Scale images according to the constant
        miku_up = pygame.transform.scale(miku_up, 
            (int(miku_up.get_width() * IMAGE_SCALE), 
             int(miku_up.get_height() * IMAGE_SCALE)))
        miku_left = pygame.transform.scale(miku_left, 
            (int(miku_left.get_width() * IMAGE_SCALE), 
             int(miku_left.get_height() * IMAGE_SCALE)))
        miku_right = pygame.transform.scale(miku_right, 
            (int(miku_right.get_width() * IMAGE_SCALE), 
             int(miku_right.get_height() * IMAGE_SCALE)))
        miku_down = pygame.transform.scale(miku_down, 
            (int(miku_down.get_width() * IMAGE_SCALE), 
             int(miku_down.get_height() * IMAGE_SCALE)))
        
        return {
            "up": miku_up,
            "left": miku_left,
            "right": miku_right,
            "down": miku_down
        }
    except FileNotFoundError as e:
        print(f"Error loading Miku image files: {e}")
        return None

def load_teto_images():
    """Load and scale Teto images"""
    try:
        teto1 = pygame.image.load("teto1.png").convert_alpha()
        teto2 = pygame.image.load("teto2.png").convert_alpha()
        
        # Scale images
        teto1 = pygame.transform.scale(teto1, 
            (int(teto1.get_width() * TETO_SCALE), 
             int(teto1.get_height() * TETO_SCALE)))
        teto2 = pygame.transform.scale(teto2, 
            (int(teto2.get_width() * TETO_SCALE), 
             int(teto2.get_height() * TETO_SCALE)))
        
        return teto1, teto2
    except FileNotFoundError as e:
        print(f"Error loading Teto image files: {e}")
        # Create placeholder images
        teto1 = pygame.Surface((100, 100), pygame.SRCALPHA)
        pygame.draw.circle(teto1, (255, 100, 100), (50, 50), 50)
        teto2 = pygame.Surface((100, 100), pygame.SRCALPHA)
        pygame.draw.rect(teto2, (100, 100, 255), (25, 25, 50, 50))
        return teto1, teto2

class Arrow:
    def __init__(self, direction, spawn_time):
        self.direction = direction
        self.spawn_time = float(spawn_time)
        self.x = {"left": SCREEN_WIDTH - 450, "down": SCREEN_WIDTH - 350, "up": SCREEN_WIDTH - 250, "right": SCREEN_WIDTH - 150}[direction]
        self.y = -ARROW_SIZE
        self.hit = False
        self.glow = True
        self.bounce_time = 0
        self.original_y = HIT_ZONE_Y
        self.shake_offset = [0, 0]
        self.arrow_images = {
            "left": load_arrow_image("left"),
            "down": load_arrow_image("down"),
            "up": load_arrow_image("up"),
            "right": load_arrow_image("right")
        }

    def update(self, elapsed_time, combo):
        if not self.hit:
            self.y = -ARROW_SIZE + ARROW_SPEED * (elapsed_time - self.spawn_time)
        
        if self.bounce_time > 0:
            self.bounce_time -= 1
            bounce_progress = 1 - (self.bounce_time / (BOUNCE_DURATION * FPS))
            bounce_height = 30 * (1 - (bounce_progress - 1)**2)
            self.y = self.original_y - bounce_height
        
        if combo > 50 and not self.hit:
            self.shake_offset = [random.randint(-5, 5), random.randint(-5, 5)]
        else:
            self.shake_offset = [0, 0]

    def draw(self, screen):
        if self.hit and self.bounce_time <= 0:
            return
            
        draw_x = self.x + self.shake_offset[0]
        draw_y = self.y + self.shake_offset[1]
        arrow_img = self.arrow_images[self.direction]
        
        outline_surface = pygame.Surface((ARROW_SIZE + 6, ARROW_SIZE + 6), pygame.SRCALPHA)
        mask = pygame.mask.from_surface(arrow_img)
        outline = mask.outline()
        for point in outline:
            for dx, dy in [(-1,-1), (-1,0), (-1,1), (0,-1), (0,1), (1,-1), (1,0), (1,1)]:
                x, y = point[0] + 3 + dx, point[1] + 3 + dy
                if 0 <= x < ARROW_SIZE + 6 and 0 <= y < ARROW_SIZE + 6:
                    outline_surface.set_at((x, y), WHITE)
        
        screen.blit(outline_surface, (draw_x - 3, draw_y - 3))
        screen.blit(arrow_img, (draw_x, draw_y))

class Particle:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.color = random.choice([NEON_GREEN, NEON_RED, NEON_BLUE, NEON_YELLOW, NEON_PURPLE, NEON_PINK])
        self.size = random.randint(3, 8)
        self.speed = random.uniform(2, 6)
        self.angle = random.uniform(0, 2 * math.pi)
        self.lifetime = random.randint(30, 90)
    
    def update(self):
        self.x += math.cos(self.angle) * self.speed
        self.y += math.sin(self.angle) * self.speed
        self.lifetime -= 1
        self.size = max(0, self.size - 0.1)
    
    def draw(self, screen):
        pygame.draw.circle(screen, self.color, (int(self.x), int(self.y)), int(self.size))

class TetoAnimation:
    def __init__(self):
        self.teto1, self.teto2 = load_teto_images()
        self.current_teto = self.teto1
        self.switch_timer = 0
        self.bounce_height = 0
        self.pos = [IMAGE_X + TETO_OFFSET_X, IMAGE_Y + TETO_OFFSET_Y]
    
    def update(self, dt, miku_pos):
        """Update the Teto animation"""
        self.switch_timer += dt
        if self.switch_timer >= TETO_SWITCH_INTERVAL:
            self.current_teto = self.teto2 if self.current_teto == self.teto1 else self.teto1
            self.switch_timer = 0
        
        # Calculate bounce using sine wave
        self.bounce_height = math.sin(pygame.time.get_ticks() * BOUNCE_SPEED) * MAX_BOUNCE
        
        # Calculate position relative to Miku
        self.pos = [
            miku_pos[0] + TETO_OFFSET_X,
            miku_pos[1] + TETO_OFFSET_Y + self.bounce_height
        ]
    
    def draw(self, screen):
        """Draw the current Teto image"""
        teto_rect = self.current_teto.get_rect()
        screen.blit(self.current_teto, 
                   (self.pos[0] - teto_rect.width // 2, 
                    self.pos[1] - teto_rect.height // 2))

class SongSelector:
    def __init__(self):
        downloads_path = os.path.expanduser("~/Downloads")
        self.soundtrack_folder = os.path.join(downloads_path, "Rhythm Game soundtrack")
        if not os.path.exists(self.soundtrack_folder):
            os.makedirs(self.soundtrack_folder)
        
        self.songs = [f for f in os.listdir(self.soundtrack_folder) if f.lower().endswith('.wav')]
        if not self.songs:
            self.songs = ["No songs found - add WAV files to the folder"]
            self.empty_folder = True
        else:
            self.empty_folder = False
            
        self.selected_song = None
        self.hovered_song = None
        self.font = pygame.font.SysFont('Arial', 32)
        self.title_font = pygame.font.SysFont('Arial', 48)
        self.song_rects = []
        self.scroll_offset = 0
        self.scroll_bar_height = 0
        self.scroll_bar_pos = 0
        self.scroll_bar_dragging = False
        self.scroll_area_height = SCREEN_HEIGHT - 250  # Height available for songs display
        
    def draw(self, screen):
        screen.fill(DARK_GRAY)
        title = self.title_font.render("Select a Song", True, WHITE)
        screen.blit(title, (SCREEN_WIDTH//2 - title.get_width()//2, 50))
        instr = self.font.render("Click a song to select it", True, WHITE)
        screen.blit(instr, (SCREEN_WIDTH//2 - instr.get_width()//2, 120))
        
        # Calculate scroll bar parameters
        total_songs_height = len(self.songs) * 60
        if total_songs_height > self.scroll_area_height:
            self.scroll_bar_height = max(30, int((self.scroll_area_height / total_songs_height) * self.scroll_area_height))
            scrollable_height = total_songs_height - self.scroll_area_height
            self.scroll_bar_pos = int((-self.scroll_offset / scrollable_height) * (self.scroll_area_height - self.scroll_bar_height))
        else:
            self.scroll_bar_height = 0
        
        # Draw songs list with clipping
        clip_rect = pygame.Rect(200, 200, 600, self.scroll_area_height)
        old_clip = screen.get_clip()
        screen.set_clip(clip_rect)
        
        self.song_rects = []
        y_pos = 200 + self.scroll_offset
        for i, song in enumerate(self.songs):
            rect = pygame.Rect(200, y_pos, 600, 50)
            self.song_rects.append(rect)
            
            if song == self.selected_song:
                pygame.draw.rect(screen, NEON_RED, rect, 2)
                pygame.draw.rect(screen, (*NEON_RED, 50), rect)
            elif song == self.hovered_song and not self.empty_folder:
                pygame.draw.rect(screen, WHITE, rect, 1)
            
            text_color = WHITE if not self.empty_folder else NEON_RED
            text = self.font.render(os.path.splitext(song)[0], True, text_color)
            screen.blit(text, (210, y_pos + 10))
            y_pos += 60
        
        screen.set_clip(old_clip)
        
        # Draw scroll bar if needed
        if self.scroll_bar_height > 0:
            scroll_bar_rect = pygame.Rect(810, 200 + self.scroll_bar_pos, 20, self.scroll_bar_height)
            pygame.draw.rect(screen, GRAY, scroll_bar_rect)
            pygame.draw.rect(screen, WHITE, scroll_bar_rect, 1)
        
        back_rect = pygame.Rect(50, SCREEN_HEIGHT - 100, 200, 50)
        pygame.draw.rect(screen, NEON_BLUE, back_rect, 2)
        back_text = self.font.render("Back", True, NEON_BLUE)
        screen.blit(back_text, (back_rect.centerx - back_text.get_width()//2, 
                               back_rect.centery - back_text.get_height()//2))
        return back_rect
    
    def handle_event(self, event):
        if self.empty_folder:
            return None
            
        if event.type == pygame.MOUSEMOTION:
            mouse_pos = pygame.mouse.get_pos()
            
            # Check if we're dragging the scroll bar
            if self.scroll_bar_height > 0 and self.scroll_bar_dragging:
                scroll_bar_y = mouse_pos[1] - 200  # Relative to scroll area
                scroll_bar_y = max(0, min(scroll_bar_y, self.scroll_area_height - self.scroll_bar_height))
                total_songs_height = len(self.songs) * 60
                scrollable_height = total_songs_height - self.scroll_area_height
                self.scroll_offset = -int((scroll_bar_y / (self.scroll_area_height - self.scroll_bar_height)) * scrollable_height)
                self.scroll_bar_pos = scroll_bar_y
            
            # Check for hovered song
            self.hovered_song = None
            for i, rect in enumerate(self.song_rects):
                if rect.collidepoint(mouse_pos):
                    self.hovered_song = self.songs[i]
                    break
        
        elif event.type == pygame.MOUSEBUTTONDOWN:
            mouse_pos = pygame.mouse.get_pos()
            
            # Check if clicking on scroll bar
            if self.scroll_bar_height > 0 and 810 <= mouse_pos[0] <= 830 and 200 <= mouse_pos[1] <= 200 + self.scroll_area_height:
                if 200 + self.scroll_bar_pos <= mouse_pos[1] <= 200 + self.scroll_bar_pos + self.scroll_bar_height:
                    self.scroll_bar_dragging = True
                else:
                    # Jump to clicked position
                    scroll_bar_y = mouse_pos[1] - 200
                    total_songs_height = len(self.songs) * 60
                    scrollable_height = total_songs_height - self.scroll_area_height
                    self.scroll_offset = -int((scroll_bar_y / self.scroll_area_height) * scrollable_height)
                    self.scroll_bar_pos = int((-self.scroll_offset / scrollable_height) * (self.scroll_area_height - self.scroll_bar_height))
                return None
            
            for i, rect in enumerate(self.song_rects):
                if rect.collidepoint(mouse_pos):
                    self.selected_song = self.songs[i]
                    return "song_selected"
            
            back_rect = pygame.Rect(50, SCREEN_HEIGHT - 100, 200, 50)
            if back_rect.collidepoint(mouse_pos):
                return "back"
        
        elif event.type == pygame.MOUSEBUTTONUP:
            self.scroll_bar_dragging = False
        
        elif event.type == pygame.MOUSEWHEEL:
            self.scroll_offset += event.y * 30
            total_songs_height = len(self.songs) * 60
            max_offset = max(0, total_songs_height - self.scroll_area_height)
            self.scroll_offset = min(0, max(self.scroll_offset, -max_offset))
        
        return None

# Initialize pygame
pygame.init()
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Anime Rhythm")
clock = pygame.time.Clock()

# Load Miku images
miku_images = load_miku_images()
current_miku_image = miku_images["up"] if miku_images else None

# Initialize Teto animation
teto_animation = TetoAnimation()

try:
    background = pygame.image.load("background.png").convert()
    background = pygame.transform.scale(background, (SCREEN_WIDTH - 2*MARGIN_SIZE, SCREEN_HEIGHT - 2*MARGIN_SIZE))
except:
    try:
        background = pygame.image.load("background.jpg").convert()
        background = pygame.transform.scale(background, (SCREEN_WIDTH - 2*MARGIN_SIZE, SCREEN_HEIGHT - 2*MARGIN_SIZE))
    except:
        background = pygame.Surface((SCREEN_WIDTH - 2*MARGIN_SIZE, SCREEN_HEIGHT - 2*MARGIN_SIZE))
        for y in range(background.get_height()):
            darkness = int(10 + (y / background.get_height()) * 20)
            pygame.draw.line(background, (darkness, darkness, darkness), (0, y), (background.get_width(), y))

# Game variables
score = 0
combo = 0
hit_effects = []
fast_mode = False
fullscreen = False
current_song = None
particles = []
accuracy = 0
total_arrows = 0
hit_arrows = 0
waiting_for_end_screen = False
game_paused = False
pause_time = 0
pause_offset = 0

# Initialize song selector
song_selector = SongSelector()

try:
    title_font = pygame.font.Font("arcade.ttf", 72)
    subtitle_font = pygame.font.Font("arcade.ttf", 36)
    score_font = pygame.font.Font("arcade.ttf", 32)
    combo_font = pygame.font.Font("arcade.ttf", 48)
    effect_font = pygame.font.Font("arcade.ttf", 24)
except:
    title_font = pygame.font.SysFont('Arial', 72)
    subtitle_font = pygame.font.SysFont('Arial', 36)
    score_font = pygame.font.SysFont('Arial', 32)
    combo_font = pygame.font.SysFont('Arial', 48)
    effect_font = pygame.font.SysFont('Arial', 24)

STATE_OPENING = 0
STATE_MENU = 1
STATE_SONG_SELECT = 2
STATE_PLAYING = 3
STATE_GAME_OVER = 4

current_state = STATE_OPENING
opening_start = time.time()
game_over_time = 0

running = True
while running:
    dt = clock.tick(FPS) / 1000.0
    
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        
        if current_state == STATE_OPENING and event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
            current_state = STATE_MENU
        
        elif current_state == STATE_MENU:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    current_state = STATE_SONG_SELECT
                elif event.key == pygame.K_f:
                    fast_mode = not fast_mode
                elif event.key == pygame.K_1:
                    fullscreen = not fullscreen
                    if fullscreen:
                        screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
                    else:
                        screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        
        elif current_state == STATE_SONG_SELECT:
            result = song_selector.handle_event(event)
            if result == "song_selected" and not song_selector.empty_folder:
                current_song = os.path.join(song_selector.soundtrack_folder, song_selector.selected_song)
                current_state = STATE_PLAYING
                beat_times = get_beat_times(current_song)
                arrows = [Arrow(random.choice(list(COLORS.keys())), float(t)) for t in beat_times]
                try:
                    pygame.mixer.music.load(current_song)
                    start_time = time.time()
                    if fast_mode:
                        pygame.mixer.music.play(0, 0.0, fast_mode=True)
                        pygame.mixer.music.set_volume(0.7)
                    else:
                        pygame.mixer.music.play()
                except Exception as e:
                    print(f"Error loading music: {e}")
                    current_state = STATE_SONG_SELECT
                    hit_effects.append({
                        'text': "ERROR LOADING SONG!",
                        'color': NEON_RED,
                        'x': SCREEN_WIDTH//2 - 100,
                        'y': SCREEN_HEIGHT//2,
                        'timer': 60,
                        'size': 1.0
                    })
            elif result == "back":
                current_state = STATE_MENU
        
        elif current_state == STATE_PLAYING:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_f:
                    fast_mode = not fast_mode
                    if pygame.mixer.music.get_busy() and not game_paused:
                        current_pos = pygame.mixer.music.get_pos() / 1000.0
                        pygame.mixer.music.stop()
                        try:
                            pygame.mixer.music.load(current_song)
                            if fast_mode:
                                pygame.mixer.music.play(0, current_pos, fast_mode=True)
                                pygame.mixer.music.set_volume(0.7)
                            else:
                                pygame.mixer.music.play(0, current_pos)
                        except:
                            pass
                elif event.key == pygame.K_ESCAPE:
                    pygame.mixer.music.stop()
                    current_state = STATE_MENU
                    score = 0
                    combo = 0
                    hit_effects = []
                    total_arrows = 0
                    hit_arrows = 0
                    waiting_for_end_screen = False
                    game_paused = False
                elif event.key == pygame.K_BACKSPACE and waiting_for_end_screen:
                    if total_arrows > 0:
                        accuracy = (hit_arrows / total_arrows) * 100
                    else:
                        accuracy = 0
                    
                    pygame.mixer.music.stop()
                    game_over_time = time.time()
                    particles = [Particle(random.randint(0, SCREEN_WIDTH), 
                                        random.randint(0, SCREEN_HEIGHT)) 
                               for _ in range(PARTICLE_COUNT)]
                    current_state = STATE_GAME_OVER
                elif event.key == pygame.K_p:
                    if game_paused:
                        game_paused = False
                        pygame.mixer.music.unpause()
                        pause_offset += time.time() - pause_time
                    else:
                        game_paused = True
                        pygame.mixer.music.pause()
                        pause_time = time.time()
                
                # Update Miku image based on key press
                if miku_images:
                    if event.key == pygame.K_LEFT:
                        current_miku_image = miku_images["left"]
                    elif event.key == pygame.K_RIGHT:
                        current_miku_image = miku_images["right"]
                    elif event.key == pygame.K_UP:
                        current_miku_image = miku_images["up"]
                    elif event.key == pygame.K_DOWN:
                        current_miku_image = miku_images["down"]
        
        elif current_state == STATE_GAME_OVER:
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                current_state = STATE_MENU
                score = 0
                combo = 0
                hit_effects = []
                total_arrows = 0
                hit_arrows = 0
                particles = []
                waiting_for_end_screen = False
    
    if current_state == STATE_OPENING:
        screen.fill(DARK_GRAY)
        draw_frame(screen)
        title = title_font.render("Anime Rhythm", True, NEON_GREEN)
        subtitle = subtitle_font.render("PRESS SPACE TO CONTINUE", True, WHITE)
        
        pulse = 1 + 0.1 * np.sin(time.time() * 3)
        title = pygame.transform.scale(title, (int(title.get_width() * pulse), int(title.get_height() * pulse)))
        
        shadow = title_font.render("Anime Rhythm", True, (0, 0, 0))
        screen.blit(shadow, (SCREEN_WIDTH//2 - shadow.get_width()//2 + 3, SCREEN_HEIGHT//3 + 3))
        screen.blit(title, (SCREEN_WIDTH//2 - title.get_width()//2, SCREEN_HEIGHT//3))
        screen.blit(subtitle, (SCREEN_WIDTH//2 - subtitle.get_width()//2, SCREEN_HEIGHT//2))
    
    elif current_state == STATE_MENU:
        screen.fill(DARK_GRAY)
        draw_frame(screen)
        title = title_font.render("Anime Rhythm", True, NEON_GREEN)
        subtitle = subtitle_font.render("PRESS SPACE TO SELECT SONG", True, WHITE)
        controls = subtitle_font.render("F: TOGGLE FAST MODE  |  1: FULLSCREEN", True, WHITE)
        
        keys_img = pygame.Surface((400, 150), pygame.SRCALPHA)
        key_colors = [NEON_YELLOW, NEON_BLUE, NEON_RED, NEON_GREEN]
        for i, (key, color) in enumerate(zip(["←", "↓", "↑", "→"], key_colors)):
            key_text = subtitle_font.render(key, True, color)
            keys_img.blit(key_text, (50 + i * 100, 50))
        
        screen.blit(title, (SCREEN_WIDTH//2 - title.get_width()//2, SCREEN_HEIGHT//3))
        screen.blit(keys_img, (SCREEN_WIDTH//2 - keys_img.get_width()//2, SCREEN_HEIGHT//2 - 50))
        screen.blit(subtitle, (SCREEN_WIDTH//2 - subtitle.get_width()//2, SCREEN_HEIGHT//2 + 100))
        screen.blit(controls, (SCREEN_WIDTH//2 - controls.get_width()//2, SCREEN_HEIGHT//2 + 150))
    
    elif current_state == STATE_SONG_SELECT:
        back_rect = song_selector.draw(screen)
    
    elif current_state == STATE_PLAYING:
        if not game_paused:
            elapsed_time = time.time() - start_time - pause_offset
        else:
            elapsed_time = pause_time - start_time - pause_offset
        
        screen.fill(DARK_GRAY)
        screen.blit(background, (MARGIN_SIZE, MARGIN_SIZE))
        draw_frame(screen)
        
        # Update Teto animation based on Miku's position
        teto_animation.update(dt * 1000, [IMAGE_X, IMAGE_Y])  # dt in milliseconds
        
        # Draw Teto images (behind Miku)
        teto_animation.draw(screen)
        
        # Draw Miku character in the center if images are loaded
        if current_miku_image:
            image_rect = current_miku_image.get_rect()
            screen.blit(current_miku_image, (IMAGE_X - image_rect.width // 2, 
                                           IMAGE_Y - image_rect.height // 2))
        
        # Draw song progress bar and name at top
        try:
            song_length = pygame.mixer.Sound(current_song).get_length()
            progress = min(elapsed_time / song_length, 1.0)
            
            # Draw song name above progress bar
            if current_song:
                song_name = os.path.splitext(os.path.basename(current_song))[0]
                name_text = effect_font.render(song_name, True, WHITE)
                screen.blit(name_text, (SCREEN_WIDTH//2 - name_text.get_width()//2, PROGRESS_BAR_Y - 25))
            
            # Draw progress bar
            pygame.draw.rect(screen, GRAY, (SCREEN_WIDTH//2 - PROGRESS_BAR_WIDTH//2, PROGRESS_BAR_Y, 
                                          PROGRESS_BAR_WIDTH, PROGRESS_BAR_HEIGHT))
            pygame.draw.rect(screen, NEON_GREEN, (SCREEN_WIDTH//2 - PROGRESS_BAR_WIDTH//2, PROGRESS_BAR_Y, 
                                                int(PROGRESS_BAR_WIDTH * progress), PROGRESS_BAR_HEIGHT))
            # Draw progress percentage
            percent_text = effect_font.render(f"{int(progress * 100)}%", True, WHITE)
            screen.blit(percent_text, (SCREEN_WIDTH//2 - percent_text.get_width()//2, PROGRESS_BAR_Y + PROGRESS_BAR_HEIGHT + 5))
        except:
            pass
        
        # Update and draw arrows
        for arrow in arrows[:]:
            if not game_paused and elapsed_time >= arrow.spawn_time:
                arrow.update(elapsed_time, combo)
                if arrow.y < SCREEN_HEIGHT:
                    arrow.draw(screen)
                elif not arrow.hit:
                    arrows.remove(arrow)
                    combo = 0
                    hit_effects.append({
                        'text': "MISS!",
                        'color': NEON_RED,
                        'x': arrow.x,
                        'y': HIT_ZONE_Y - 50,
                        'timer': 30,
                        'size': 1.0
                    })
                    total_arrows += 1
                elif arrow.hit:
                    arrows.remove(arrow)
                    total_arrows += 1
                    hit_arrows += 1
            elif game_paused and elapsed_time >= arrow.spawn_time and arrow.y < SCREEN_HEIGHT:
                arrow.draw(screen)
        
        draw_hit_zone(screen)
        
        if not game_paused:
            keys = pygame.key.get_pressed()
            for key, direction in zip([pygame.K_LEFT, pygame.K_DOWN, pygame.K_UP, pygame.K_RIGHT],
                                    ["left", "down", "up", "right"]):
                if keys[key]:
                    for arrow in arrows:
                        if (arrow.direction == direction and 
                            not arrow.hit and 
                            abs(arrow.y + ARROW_SIZE - HIT_ZONE_Y) <= HIT_MARGIN):
                            arrow.hit = True
                            arrow.glow = False
                            arrow.original_y = arrow.y
                            arrow.bounce_time = BOUNCE_DURATION * FPS
                            
                            points = 100 + (combo // 5) * 10
                            score += points
                            combo += 1
                            hit_arrows += 1
                            
                            hit_effects.append({
                                'text': f"PERFECT! +{points}",
                                'color': NEON_GREEN,
                                'x': arrow.x - 50,
                                'y': HIT_ZONE_Y - 80,
                                'timer': 45,
                                'size': 0.5
                            })
                            break
        
        for effect in hit_effects[:]:
            effect['size'] = min(effect['size'] + 0.05, 1.2)
            size = int(24 * effect['size'])
            
            text_surface = pygame.Surface((200, 50), pygame.SRCALPHA)
            font = pygame.font.SysFont('Arial', size)
            
            for dx, dy in [(-1,-1), (-1,1), (1,-1), (1,1)]:
                outline = font.render(effect["text"], True, BLACK)
                text_surface.blit(outline, (25 + dx, 10 + dy))
            
            main_text = font.render(effect["text"], True, effect["color"])
            text_surface.blit(main_text, (25, 10))
            
            screen.blit(text_surface, (effect["x"], effect["y"]))
            effect["timer"] -= 1
            effect["y"] -= 1
            if effect["timer"] <= 0:
                hit_effects.remove(effect)
        
        score_text = score_font.render(f"SCORE: {score}", True, WHITE)
        pygame.draw.rect(screen, (0, 0, 0, 150), (15, 15, score_text.get_width() + 20, score_text.get_height() + 10))
        screen.blit(score_text, (25, 20))
        
        if combo > 0:
            combo_size = min(32 + combo // 2, 72)
            current_combo_font = pygame.font.SysFont('Arial', combo_size)
            combo_text = current_combo_font.render(f"{combo}x", True, NEON_PINK)
            screen.blit(combo_text, (SCREEN_WIDTH - 150 - combo_size//2, 20))
        
        if fast_mode:
            fast_text = score_font.render("FAST MODE", True, NEON_RED)
            pygame.draw.rect(screen, (0, 0, 0, 150), 
                           (SCREEN_WIDTH - fast_text.get_width() - 30, SCREEN_HEIGHT - 45, 
                            fast_text.get_width() + 20, fast_text.get_height() + 10))
            screen.blit(fast_text, (SCREEN_WIDTH - fast_text.get_width() - 20, SCREEN_HEIGHT - 40))
        
        if game_paused:
            pause_text = title_font.render("PAUSED", True, NEON_RED)
            screen.blit(pause_text, (SCREEN_WIDTH//2 - pause_text.get_width()//2, SCREEN_HEIGHT//2 - 100))
        
        if len(arrows) == 0 and not pygame.mixer.music.get_busy() and not game_paused:
            waiting_for_end_screen = True
            # Calculate accuracy here before showing results
            if total_arrows > 0:
                accuracy = (hit_arrows / total_arrows) * 100
            else:
                accuracy = 0
        else:
            waiting_for_end_screen = False

        if waiting_for_end_screen:
            prompt_text = subtitle_font.render("Press BACKSPACE to view results", True, NEON_GREEN)
            screen.blit(prompt_text, (SCREEN_WIDTH//2 - prompt_text.get_width()//2, SCREEN_HEIGHT//2 + 50))
    
    elif current_state == STATE_GAME_OVER:
        screen.fill(DARK_GRAY)
        
        for particle in particles[:]:
            particle.update()
            particle.draw(screen)
            if particle.lifetime <= 0:
                particles.remove(particle)
        
        if random.random() < 0.3 and len(particles) < PARTICLE_COUNT * 1.5:
            particles.append(Particle(random.randint(0, SCREEN_WIDTH), 
                                    random.randint(0, SCREEN_HEIGHT)))
        
        game_over_text = title_font.render("GAME OVER", True, NEON_RED)
        screen.blit(game_over_text, (SCREEN_WIDTH//2 - game_over_text.get_width()//2, 150))
        
        score_text = title_font.render(f"FINAL SCORE: {score}", True, WHITE)
        screen.blit(score_text, (SCREEN_WIDTH//2 - score_text.get_width()//2, 250))
        
        accuracy_text = title_font.render(f"ACCURACY: {accuracy:.1f}%", True, NEON_GREEN)
        screen.blit(accuracy_text, (SCREEN_WIDTH//2 - accuracy_text.get_width()//2, 350))
        
        restart_text = subtitle_font.render("Press ESC to return to menu", True, WHITE)
        screen.blit(restart_text, (SCREEN_WIDTH//2 - restart_text.get_width()//2, 500))
    
    pygame.display.flip()

pygame.quit()
sys.exit()