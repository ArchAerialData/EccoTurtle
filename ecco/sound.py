import os
import math
import random
import struct
import wave

import pygame

from .environment import Environment
from .config import (MUSIC_BEACH_FILE, MUSIC_CORAL_FILE, MUSIC_REEF_FILE,
                     MUSIC_OCEAN_FILE, MUSIC_RIG_FILE,
                     SFX_DASH_FILE, SFX_EAT_FILE,
                     SFX_HURT_FILE, SFX_POWERUP_FILE,
                     ENV_DURATION_SEC)


def write_wav_deep_synth_melody(path, tempo_bpm=100, duration_sec=90.0, sample_rate=44100):
    melody = [
        ("A3",2),("C4",2),("E4",2),("D4",2),
        ("F3",2),("A3",2),("C4",2),("E4",2),
        ("G3",2),("B3",2),("D4",2),("C4",2),
        ("F3",2),("A3",2),("G3",2),("E3",2),
        ("A4",1),("G4",1),("F4",2),("E4",2),("D4",2),
        ("C4",2),("E4",2),("A3",2),("C4",2),
        ("D4",1),("E4",1),("F4",2),("G4",2),("A4",2),
        ("E4",4),("A3",4),
    ]
    bass_prog = ["A1","F1","G1","A1","F1","C1","D1","E1"]
    bass_notes = []
    for i in range(bars):
        bass_notes += [(bass_prog[i % 8], 8)]

    A4 = 440.0
    NOTES = {'C':-9, 'C#':-8, 'Db':-8, 'D':-7, 'D#':-6, 'Eb':-6, 'E':-5, 'F':-4, 'F#':-3,
             'Gb':-3, 'G':-2, 'G#':-1, 'Ab':-1, 'A':0, 'A#':1, 'Bb':1, 'B':2}

    def note_to_freq(name):
        if name is None:
            return None
        pitch = ''.join([c for c in name if c.isalpha() or c == '#'])
        octave = int(''.join([c for c in name if c.isdigit()]))
        semis = NOTES[pitch] + (octave-4)*12
        return A4 * (2 ** (semis/12))

    spb = 60.0/tempo_bpm
    # We generate enough bars to cover the requested duration
    bars = max(1, int(math.ceil((duration_sec) / (8*spb))))
    total_beats = bars*8
    total_seconds = total_beats*spb
    num_samples = int(total_seconds*sample_rate)

    mel_timeline = [None]*num_samples
    bass_timeline = [None]*num_samples

    def place_line(line, start_beat, timeline):
        t = start_beat
        for n, d in line:
            start_s = int(t*spb*sample_rate)
            end_s = int((t+d)*spb*sample_rate)
            f = note_to_freq(n)
            for i in range(start_s, min(end_s, num_samples)):
                timeline[i] = f
            t += d

    beats_total = sum(d for _, d in melody)
    bars_len_beats = bars * 8
    while beats_total < bars_len_beats:
        melody += melody
        beats_total = sum(d for _, d in melody)

    place_line(melody[:bars_len_beats], 0, mel_timeline)
    place_line(bass_notes, 0, bass_timeline)

    # Stereo mix buffers (L/R)
    data = bytearray()
    reverb_buffer = [0.0] * 8000
    reverb_idx = 0

    for i in range(num_samples):
        m = mel_timeline[i]
        b = bass_timeline[i]
        sample = 0.0

        if b is not None:
            t = (i/sample_rate)*b
            saw = 2.0 * ((t % 1.0) - 0.5)
            sub = math.sin(2*math.pi*b*0.5*t/sample_rate)
            env = min(1.0, (i % int(8*spb*sample_rate)) / (sample_rate*0.1))
            env *= max(0.3, 1.0 - ((i % int(8*spb*sample_rate)) / (8*spb*sample_rate)))
            sample += 0.25 * (saw * 0.7 + sub * 0.3) * env

        if m is not None:
            lead = 0.0
            detune_cents = [-7, -3, 0, 3, 7]
            for cents in detune_cents:
                freq = m * (2 ** (cents/1200))
                t = (i/sample_rate)*freq
                saw = 2.0 * ((t % 1.0) - 0.5)
                lead += saw * 0.15

            note_pos = i % int(2*spb*sample_rate)
            attack = min(1.0, note_pos/(sample_rate*0.05))
            decay = max(0.7, 1.0 - (note_pos-sample_rate*0.05)/(sample_rate*0.1)) if note_pos > sample_rate*0.05 else 1.0
            sustain = 0.7
            release = max(0.0, 1.0 - (note_pos-sample_rate*1.5)/(sample_rate*0.5)) if note_pos > sample_rate*1.5 else 1.0
            env = attack * decay * sustain * release

            lead = lead * 0.6 + random.random()*0.002
            sample += lead * env * 0.3

        reverb_buffer[reverb_idx] = sample * 0.3
        reverb_idx = (reverb_idx + 1) % len(reverb_buffer)
        reverb = reverb_buffer[(reverb_idx - 3500) % len(reverb_buffer)] * 0.4
        reverb += reverb_buffer[(reverb_idx - 7000) % len(reverb_buffer)] * 0.2
        sample += reverb

        if abs(sample) > 0.7:
            sample = math.tanh(sample)
        else:
            sample = max(-1.0, min(1.0, sample))

        # Subtle chorus + stereo spread: 6 ms delay to right, 3 ms to left
        delay_l = int(0.003 * sample_rate)
        delay_r = int(0.006 * sample_rate)
        idx_l = max(0, i - delay_l)
        idx_r = max(0, i - delay_r)

        # Simple echoes using reverb buffer content
        echo_l = reverb_buffer[(reverb_idx - 2500) % len(reverb_buffer)] * 0.15
        echo_r = reverb_buffer[(reverb_idx - 4500) % len(reverb_buffer)] * 0.15

        # The dry signal
        s = sample
        # L/R mix with tiny detune to emulate 90s console width
        left = s * 0.85 + echo_l
        right = s * 0.85 + echo_r

        left = max(-1.0, min(1.0, left))
        right = max(-1.0, min(1.0, right))

        data += struct.pack('<hh', int(left*32767), int(right*32767))

    with wave.open(path, 'wb') as wf:
        wf.setnchannels(2)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        wf.writeframes(data)


def write_wav_synth_beep(path, freq=880, ms=150, sample_rate=44100,
                         shape="saw", volume=0.3):
    samples = int(sample_rate * ms/1000.0)
    data = bytearray()
    for i in range(samples):
        t = i/sample_rate
        if shape == "saw":
            val = 2.0 * ((freq*t % 1.0) - 0.5)
        elif shape == "sine":
            val = math.sin(2*math.pi*freq*t)
        elif shape == "powerup":
            val = math.sin(2*math.pi*freq*t) * 0.5
            val += math.sin(2*math.pi*freq*1.5*t) * 0.3
            val += math.sin(2*math.pi*freq*2*t) * 0.2
        else:
            val = 1.0 if math.sin(2*math.pi*freq*t) >= 0 else -1.0

        attack = min(1.0, i/(samples*0.1))
        release = max(0.0, 1.0 - (i-samples*0.7)/(samples*0.3)) if i > samples*0.7 else 1.0
        fade = attack * release

        s = max(-1.0, min(1.0, val * volume * fade))
        data += struct.pack('<h', int(s*32767))

    with wave.open(path, 'wb') as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        wf.writeframes(data)


_sfx = {}

def play_sfx(name):
    ch = pygame.mixer.find_channel()
    if ch and name in _sfx:
        ch.play(_sfx[name])


def load_or_generate_audio():
    music_map = {
        Environment.BEACH: str(MUSIC_BEACH_FILE),
        Environment.CORAL_COVE: str(MUSIC_CORAL_FILE),
        Environment.ROCKY_REEF: str(MUSIC_REEF_FILE),
        Environment.OCEAN_FLOOR: str(MUSIC_OCEAN_FILE),
        Environment.OIL_RIG: str(MUSIC_RIG_FILE),
    }

    eat = str(SFX_EAT_FILE)
    hurt = str(SFX_HURT_FILE)
    dash = str(SFX_DASH_FILE)
    powerup = str(SFX_POWERUP_FILE)

    # Generate music for each environment if missing with varied moods
    if not os.path.exists(music_map[Environment.BEACH]):
        write_wav_deep_synth_melody(music_map[Environment.BEACH], tempo_bpm=120, duration_sec=ENV_DURATION_SEC)
    if not os.path.exists(music_map[Environment.CORAL_COVE]):
        write_wav_deep_synth_melody(music_map[Environment.CORAL_COVE], tempo_bpm=100, duration_sec=ENV_DURATION_SEC)
    if not os.path.exists(music_map[Environment.ROCKY_REEF]):
        write_wav_deep_synth_melody(music_map[Environment.ROCKY_REEF], tempo_bpm=90, duration_sec=ENV_DURATION_SEC)
    if not os.path.exists(music_map[Environment.OCEAN_FLOOR]):
        write_wav_deep_synth_melody(music_map[Environment.OCEAN_FLOOR], tempo_bpm=70, duration_sec=ENV_DURATION_SEC)
    if not os.path.exists(music_map[Environment.OIL_RIG]):
        write_wav_deep_synth_melody(music_map[Environment.OIL_RIG], tempo_bpm=60, duration_sec=ENV_DURATION_SEC)

    # Softer chomp sound
    if not os.path.exists(eat):
        write_wav_synth_beep(eat, freq=330, ms=180, shape="sine", volume=0.2)
    if not os.path.exists(hurt):
        write_wav_synth_beep(hurt, freq=110, ms=300, shape="saw")
    if not os.path.exists(dash):
        write_wav_synth_beep(dash, freq=293, ms=150, shape="saw")
    if not os.path.exists(powerup):
        write_wav_synth_beep(powerup, freq=440, ms=500, shape="powerup")

    return music_map, eat, hurt, dash, powerup
