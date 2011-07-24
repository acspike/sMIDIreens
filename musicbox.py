#!/usr/bin/env python
import sys
import os.path
import math

from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch

from smidireens import *


def repetitions(notes_on):
    '''find smallest number of ticks between two notes of the same pitch'''
    reps = {}
    for e in notes_on:
        note = ord(e[1][1])
        time = e[0]
        if not reps.has_key(note):
            reps[note] = [time, float("inf")]
        else:
            last, smallest = reps[note]
            reps[note] = [time, min(smallest, time - last)]
    smallest = float("inf")
    for x in reps.values():
        smallest = min(smallest, x[1])
    return smallest
    
def successions(notes_on):
    '''find smallest number of ticks between two successive notes of any pitch'''
    notes = list(set([x[0] for x in notes_on]))
    notes.sort()
    durations = [y - x for x,y in zip(notes, notes[1:])]
    return min(*durations)

if __name__ == '__main__':
    filename = sys.argv[-1]
    f = open(filename, 'r')
    m = f.read()
    f.close()
    
    notes = []
    for chunk in split_chunks(m):
        chunktype = chunk[:4]
        if chunktype == 'MThd':
            mtype,tracks,ticks = struct.unpack('>HHH',chunk[8:14])
            print chunktype, tracks, ticks
        elif chunktype == 'MTrk':
            events = split_events(chunk)
            notes += absolute_notes(events)
    notes.sort(key=lambda x: x[0])
    
    #keep NoteOn events 
    notes = [e for e in notes if (ord(e[1][0]) & 0xF0) == 0x90 and ord(e[1][2]) > 0]
    
    #find inches per tick
    #repetitions shouldn't be closer than 5/16in        
    min_rep = repetitions(notes)
    rep_tickinch = (5.0/16.0) / min_rep
    min_suc = successions(notes)
    suc_tickinch = (5.0/16.0) / (2 * min_suc)
    tickinch = max(rep_tickinch, suc_tickinch)
    time_division = (5.0/32.0) / tickinch
    division_height = (time_division * tickinch)
    divisions = int(math.floor(10.5/division_height))
    pitches = 20
    line_height = divisions * division_height
    line_width = 2.25
    pitch_width = 2.25 / (pitches - 1)
    print min_rep, rep_tickinch, min_suc, suc_tickinch, divisions
    
    
    #divide events into a list[page][column]
    column_ticks = time_division * divisions
    
    max_tick = notes[-1][0]
    total_columns = math.ceil((1.0 * max_tick) / column_ticks)
    total_pages = math.ceil(total_columns / 3.0)
    
    pages = []
    for i in range(int(total_pages)):
        pages.append([[],[],[]])
    
    for e in notes:
        ticks = e[0]
        column = math.floor(ticks/(1.0*column_ticks))
        page = int(math.floor(column/3))
        column = int(column % 3)
        pages[page][column].append(e)    
    
    #calculate a look up from midi note to line number
    # 0 makes the 0th note/line exist in the lookup
    midi_base_note = 48    
    intervals = [0,2,2,1,2,2,2,1,2,2,1,2,2,2,1,2,2,1,2,2]
    def running_sum(a):
        tot = 0
        for item in a:
            tot += item
            yield tot
    steps = list(running_sum(intervals))
    midi_notes = {}
    for i,x in enumerate(steps):
        midi_notes[x + midi_base_note] = i
    
    
    WIDTH, HEIGHT = letter
    c = canvas.Canvas(os.path.basename(filename) + '.pdf',pagesize=letter)
    for page in pages:
        for column in range(3):
            column_edge = (0.25 + (column * 2.75))
            #column edges
            c.line(column_edge * inch, 0 * inch, column_edge * inch, 11 * inch)
            #pitch lines
            for i in range(pitches):
                x = column_edge + 0.25 + (pitch_width * i)
                y1 = 0.25
                y2 = y1 + line_height
                c.line(x * inch, y1 * inch, x * inch, y2 * inch)
            #time lines
            for i in range(divisions + 1):
                y = 0.25 + (i * division_height)
                x1 = column_edge + 0.25
                x2 = column_edge + 2.5
                c.line(x1 * inch, y * inch, x2 * inch, y * inch)
                
            dots = page[column]
            for e in dots:
                y = 0.25 + ((e[0] % column_ticks) * tickinch)
                note = ord(e[1][1])
                if not midi_notes.has_key(note):
                    print "Unplayable note:", e
                else:
                    x = column_edge + 2.75 - (0.25 + (midi_notes[note] * pitch_width))
                    c.circle(x * inch, y * inch, (1.0/16) * inch, 0, 1)
                     
        
        c.showPage()
    c.save()
