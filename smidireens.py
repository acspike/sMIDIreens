#!/usr/bin/env python
import struct

class TrackParseError(BaseException):
    pass
class NoteRunningError(BaseException):
    pass

def readVarLen(m, cursor):
    value = 0
    while (ord(m[cursor]) & 0x80):
        value = (value << 7) + (ord(m[cursor]) & 0x7F)
        cursor += 1
    value = (value << 7) + (ord(m[cursor]) & 0x7F)
    cursor += 1
    return value, cursor

def split_chunks(s):
    '''Breaks a midi file (string) into chunks'''
    chunks = []
    cursor = 0
    while cursor < len(s):
        start = cursor
        cursor += 4
        chunklen = struct.unpack('>I',s[cursor:cursor+4])[0]
        end = cursor + 4 + chunklen
        chunks.append(s[start:end])
        cursor = end
    return chunks

def split_events(c):
    '''Breaks a midi track chunk into events'''
    events = []
    cursor = 8
    time = 0
    last = 0
    while cursor < len(c):
        timedelta, cursor = readVarLen(c, cursor)
        start = cursor
        raw_byte = c[cursor]
        byte = ord(raw_byte)
        running_status = False
        high = byte & 0xF0
        if (high in [0xC0,0xD0]):
            end = cursor + 2
            last = raw_byte
        elif (high in [0x80,0x90,0xA0,0xB0,0xE0]):
            end = cursor + 3
            last = raw_byte
        else:
            if (byte == 0xFF):
                fflen,cursor = readVarLen(c,cursor+2)
                end = cursor + fflen
            elif (byte in [0xF0,0xF7]):
                flen,cursor = readVarLen(c,cursor+1)
                end = cursor + flen
            elif (high == 0xF0):
                print repr(c[:start]),repr(c[start:])
                raise TrackParseError
            else:
                running_status = True
                last_high = ord(last) & 0xF0
                if (last_high in [0xC0,0xD0]):
                    end = cursor + 1
                elif (last_high in [0x80,0x90,0xA0,0xB0,0xE0]):
                    end = cursor + 2
                else:
                    print repr(last)
                    print repr(c[:start]),repr(c[start:])
                    raise TrackParseError
        if running_status:
            events.append((timedelta,last + c[start:end]))
            running_status = False
        else:
            events.append((timedelta,c[start:end]))
        cursor = end
    return events

def absolute_notes(events):
    time = 0
    out_events = []
    for e in events:
        timedelta = e[0]
        status = ord(e[1][0]) & 0xF0

        time += timedelta
        if status in [0x80,0x90]:
            out_events.append((time, e[1]))
    return out_events

def durations(ab_notes):
    on = {}
    durations = []
    for e in ab_notes:
        status = ord(e[1][0]) & 0xF0
        note = e[1][1]
        if status == 0x90:
            if note in on:
                print '0x90', note, on
                raise NoteRunningError
            on[note] = e[0]
        else:
            if not note in on:
                print '0x80', note, on
                raise NoteRunningError
            time = e[0] - on[note]
            del on[note]
            durations.append(time)
    return durations

