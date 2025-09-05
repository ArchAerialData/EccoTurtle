from pathlib import Path

BASE_PATH = Path(__file__).resolve().parent.parent
ASSET_DIR = BASE_PATH / 'assets'
DATA_DIR = BASE_PATH / 'data'

TITLE = "Sea Turtle Echo - Deep Dive"
DEFAULT_W, DEFAULT_H = 1280, 720
SCALE = 4
FPS = 60

# Gameplay pacing
# Each environment lasts this many seconds before switching
ENV_DURATION_SEC = 90.0
# Music fade in/out duration when switching environments (ms)
MUSIC_FADE_MS = 4000
# Constant ocean current that pushes floating objects left (px/sec)
CURRENT_DRIFT_SPEED = 30

# Visual toggles
ENABLE_CRT = False  # Set True for scanline overlay
ENABLE_CAUSTICS = True
CAUSTICS_BRIGHTNESS = 40  # 0-255 alpha for caustics overlay

# Background tracks for each environment
MUSIC_BEACH_FILE = ASSET_DIR / 'music_beach.wav'
MUSIC_CORAL_FILE = ASSET_DIR / 'music_coral.wav'
MUSIC_REEF_FILE = ASSET_DIR / 'music_reef.wav'
MUSIC_OCEAN_FILE = ASSET_DIR / 'music_ocean.wav'
MUSIC_RIG_FILE = ASSET_DIR / 'music_rig.wav'
SFX_EAT_FILE = ASSET_DIR / 'sfx_eat_synth.wav'
SFX_HURT_FILE = ASSET_DIR / 'sfx_hurt_synth.wav'
SFX_DASH_FILE = ASSET_DIR / 'sfx_dash_synth.wav'
SFX_POWERUP_FILE = ASSET_DIR / 'sfx_powerup_synth.wav'

# Ambient loops
AMBIENT_WAVES_FILE = ASSET_DIR / 'ambient_waves.wav'
AMBIENT_GULLS_FILE = ASSET_DIR / 'ambient_gulls.wav'
AMBIENT_HUM_FILE = ASSET_DIR / 'ambient_hum.wav'

SAVE_FILE = DATA_DIR / 'tide_highscore.json'

POWERUP_THRESHOLD = 15
POWERUP_DURATION = 10.0
