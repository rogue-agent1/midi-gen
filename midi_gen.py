#!/usr/bin/env python3
"""midi_gen - MIDI file generation (notes, chords, sequences)."""
import sys, struct

NOTE_NAMES = {"C":0,"C#":1,"Db":1,"D":2,"D#":3,"Eb":3,"E":4,"F":5,"F#":6,"Gb":6,"G":7,"G#":8,"Ab":8,"A":9,"A#":10,"Bb":10,"B":11}

def note_to_midi(note, octave=4):
    return NOTE_NAMES[note] + (octave + 1) * 12

def var_length(value):
    result = []
    result.append(value & 0x7F)
    value >>= 7
    while value:
        result.append((value & 0x7F) | 0x80)
        value >>= 7
    return bytes(reversed(result))

def create_midi(events, tempo=120):
    # header
    header = b"MThd" + struct.pack(">IHHh", 6, 0, 1, 480)
    # track
    track_data = bytearray()
    # tempo meta event
    us_per_beat = int(60_000_000 / tempo)
    track_data += b"\x00\xff\x51\x03" + struct.pack(">I", us_per_beat)[1:]
    for delta, event_type, *params in events:
        track_data += var_length(delta)
        if event_type == "note_on":
            channel, note, velocity = params
            track_data += bytes([0x90 | channel, note, velocity])
        elif event_type == "note_off":
            channel, note = params
            track_data += bytes([0x80 | channel, note, 0])
    # end of track
    track_data += b"\x00\xff\x2f\x00"
    track = b"MTrk" + struct.pack(">I", len(track_data)) + bytes(track_data)
    return header + track

def melody_events(notes, duration=480, velocity=100, channel=0):
    events = []
    for note_name, octave in notes:
        midi_note = note_to_midi(note_name, octave)
        events.append((0, "note_on", channel, midi_note, velocity))
        events.append((duration, "note_off", channel, midi_note))
    return events

def test():
    assert note_to_midi("C", 4) == 60
    assert note_to_midi("A", 4) == 69
    assert note_to_midi("C", 5) == 72
    vl = var_length(0)
    assert vl == b"\x00"
    vl2 = var_length(127)
    assert vl2 == b"\x7f"
    vl3 = var_length(128)
    assert vl3 == b"\x81\x00"
    # generate MIDI
    notes = [("C",4),("E",4),("G",4),("C",5)]
    events = melody_events(notes)
    midi_data = create_midi(events)
    assert midi_data[:4] == b"MThd"
    assert b"MTrk" in midi_data
    assert len(midi_data) > 20
    print("OK: midi_gen")

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "test":
        test()
    else:
        print("Usage: midi_gen.py test")
