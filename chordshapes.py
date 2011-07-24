#!/usr/bin/env python
import sys

from smidireens import *

def chords(ab_notes):
    on = {}
    chords = []
    last_time = ''
    for x in ab_notes:
        status = ord(x[1][0]) & 0xF0
        note = ord(x[1][1])
        vel = ord(x[1][2])

        if status == 0x80 or (status == 0x90 and vel == 0):
            if x[0] != last_time:
                chord = list(sorted(on.keys()))
                if chord:
                    chords.append(chord)

            if not note in on:
                print '0x80', note, on
                raise NoteRunningError
            else:
                on[note] -= 1
            if on[note] == 0:
                del on[note]
        elif status == 0x90:
            if note in on:
                #print '0x90', note, on, len(chords)
                #raise NoteRunningError
                on[note] += 1
                print 'doubled', note, on, x[0], len(chords)
            else:
                on[note] = 1
        else:
            print status, note, on, len(chords)
            raise TrackParseError
        last_time = x[0]
        
    return chords
   
def standard_guitar(trans=0):
    tuning = [x+trans for x in [40,45,50,55,59,64]]
    guitar = [[x+y for y in range(16)] for x in tuning]
    return guitar

def suitable_chord(chord):
    items = [x for x in chord if x not in ['X',0]]
    if not items:
        return True
    else:
        return max(items) - min(items) <= 4

def find_chord(guitar, chord):
    fingerings = []
    def recurse(string, tones, fingering):
        if not tones:
            fingerings.append(fingering)
            return
        if string >= len(guitar):
            return
        if fingering[string] == 'X':
            tone = tones[0]
            tones_left = tones[1:]
            try:
                fret = guitar[string].index(tone)
                fingering_clone = fingering[:]
                fingering_clone[string] = fret
                recurse(0, tones_left, fingering_clone)
            except ValueError:
                pass
        recurse(string+1, tones, fingering[:])

    empty_fingering = ['X' for x in range(len(guitar))]
    recurse(0,chord,empty_fingering)

    good_fingerings = [f for f in fingerings if suitable_chord(f)]
    if not good_fingerings:
        good_fingerings = fingerings

    return good_fingerings



if __name__ == '__main__':
    f = open(sys.argv[-1], 'r')
    m = f.read()
    f.close()
    
    notes = []
    for chunk in split_chunks(m):
        chunktype = chunk[:4]
        if chunktype == 'MThd':
            mtype,tracks,ticks = struct.unpack('>HHH',chunk[8:14])
            print chunktype, ticks
        elif chunktype == 'MTrk':
            notes += absolute_notes(split_events(chunk))
    notes.sort(key=lambda x: x[0])

    #print notes

    guitar = standard_guitar(0)
    for chord in chords(notes):
        print '-' * 20
        for c in find_chord(guitar, chord):
            print '-'.join([str(x) for x in c])

    

