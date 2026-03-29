#!/usr/bin/env python3
"""MIDI file generator — create simple melodies programmatically."""
import sys, struct

def var_length(value):
    result = [value & 0x7F]
    value >>= 7
    while value:
        result.append((value & 0x7F) | 0x80); value >>= 7
    return bytes(reversed(result))

def note_to_midi(note_str):
    notes = {"C":0,"D":2,"E":4,"F":5,"G":7,"A":9,"B":11}
    name = note_str[0].upper(); octave = int(note_str[-1])
    sharp = 1 if "#" in note_str else (-1 if "b" in note_str else 0)
    return notes[name] + sharp + (octave + 1) * 12

class MIDITrack:
    def __init__(self): self.events = []
    def note(self, pitch, duration=480, velocity=100, channel=0):
        if isinstance(pitch, str): pitch = note_to_midi(pitch)
        self.events.append((0, bytes([0x90|channel, pitch, velocity])))
        self.events.append((duration, bytes([0x80|channel, pitch, 0])))
    def rest(self, duration=480):
        if self.events: self.events[-1] = (self.events[-1][0] + duration, self.events[-1][1])
    def encode(self):
        data = bytearray()
        for delta, evt in self.events:
            data.extend(var_length(delta)); data.extend(evt)
        data.extend(var_length(0)); data.extend(b"\xff\x2f\x00")
        return b"MTrk" + struct.pack(">I", len(data)) + bytes(data)

def encode_midi(tracks, ticks_per_beat=480):
    header = b"MThd" + struct.pack(">IHhH", 6, 1 if len(tracks) > 1 else 0, len(tracks), ticks_per_beat)
    return header + b"".join(t.encode() for t in tracks)

def main():
    if len(sys.argv) < 2: print("Usage: midi_gen.py <demo|test>"); return
    if sys.argv[1] == "test":
        assert var_length(0) == b"\x00"
        assert var_length(127) == b"\x7f"
        assert var_length(128) == b"\x81\x00"
        assert note_to_midi("C4") == 60; assert note_to_midi("A4") == 69
        assert note_to_midi("C#4") == 61
        t = MIDITrack()
        t.note("C4", 480); t.note("E4", 480); t.note("G4", 480)
        data = t.encode()
        assert data[:4] == b"MTrk"
        midi = encode_midi([t])
        assert midi[:4] == b"MThd"
        size = struct.unpack(">I", midi[4:8])[0]; assert size == 6
        t2 = MIDITrack(); t2.note(60); t2.rest(240); t2.note(64)
        assert len(t2.events) == 4
        print("All tests passed!")
    else:
        t = MIDITrack()
        for note in ["C4","D4","E4","F4","G4","A4","B4","C5"]:
            t.note(note, 480)
        midi = encode_midi([t])
        print(f"MIDI: {len(midi)} bytes, {len(t.events)} events")

if __name__ == "__main__": main()
