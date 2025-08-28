import os
import math
import random
import struct
import wave

import pygame

from .config import (MUSIC_FILE, SFX_DASH_FILE, SFX_EAT_FILE,
                     SFX_HURT_FILE, SFX_POWERUP_FILE)


def write_wav_deep_synth_melody(path, tempo_bpm=100, bars=16, sample_rate=44100):
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

        data += struct.pack('<h', int(sample*32767))

    with wave.open(path, 'wb') as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        wf.writeframes(data)


def write_wav_synth_beep(path, freq=880, ms=150, sample_rate=44100, shape="saw"):
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

        s = max(-1.0, min(1.0, val * 0.3 * fade))
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
    music = str(MUSIC_FILE)
    eat = str(SFX_EAT_FILE)
    hurt = str(SFX_HURT_FILE)
    dash = str(SFX_DASH_FILE)
    powerup = str(SFX_POWERUP_FILE)

    if not os.path.exists(music):
        write_wav_deep_synth_melody(music, tempo_bpm=100, bars=16)
    if not os.path.exists(eat):
        write_wav_synth_beep(eat, freq=523, ms=100, shape="sine")
    if not os.path.exists(hurt):
        write_wav_synth_beep(hurt, freq=110, ms=300, shape="saw")
    if not os.path.exists(dash):
        write_wav_synth_beep(dash, freq=293, ms=150, shape="saw")
    if not os.path.exists(powerup):
        write_wav_synth_beep(powerup, freq=440, ms=500, shape="powerup")

    return music, eat, hurt, dash, powerup
