from pathlib import Path

BASE_PATH = Path(__file__).resolve().parent.parent
ASSET_DIR = BASE_PATH / 'assets'
DATA_DIR = BASE_PATH / 'data'

TITLE = "Sea Turtle Echo - Deep Dive"
DEFAULT_W, DEFAULT_H = 1280, 720
SCALE = 4
FPS = 60

MUSIC_FILE = ASSET_DIR / 'turtle_deep_synth.wav'
SFX_EAT_FILE = ASSET_DIR / 'sfx_eat_synth.wav'
SFX_HURT_FILE = ASSET_DIR / 'sfx_hurt_synth.wav'
SFX_DASH_FILE = ASSET_DIR / 'sfx_dash_synth.wav'
SFX_POWERUP_FILE = ASSET_DIR / 'sfx_powerup_synth.wav'

SAVE_FILE = DATA_DIR / 'tide_highscore.json'

POWERUP_THRESHOLD = 15
POWERUP_DURATION = 10.0
