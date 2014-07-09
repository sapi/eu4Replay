# Copyright Sean Purdon 2014
# All Rights Reserved

from datetime import datetime
from StringIO import StringIO

## Save Format
# 
# < crap on first line >
# key=value
# value -{ "string", number, yes|no, array or dict

def read_object(stream):
    output = StringIO()

    # read to the start of the object
    _, tpe = read_token(stream, {'{': False, '': False})

    # empty tpe is EOF
    # EOF indicates a failure to read an object, so we should return None
    if not tpe:
        return None

    # we don't want any leading spaces
    c = stream.read(1)

    while c.isspace():
        c = stream.read(1)

    stream.seek(-1, 1)

    # now read until we get back to 0
    indent = 1

    while indent:
        token, tpe = read_token(stream, {'{': False, '}': False, '': False},
                readSize=64)

        output.write(token)

        # if we hit EOF, we failed to read the object, and should return None
        if not tpe:
            return None

        indent += 1 if tpe == '{' else -1

        if indent:
            output.write(tpe)

    # seek to start of stream
    output.seek(0)

    return output


def parse_object(stream):
    pos = stream.tell()
    obj = parse_object_dict(stream)

    if obj is not None:
        return obj

    # we failed to parse a dict, but maybe it's an array
    stream.seek(pos)
    obj = parse_object_array(stream)

    return obj # will be None if the parse failed


def parse_object_array(stream):
    # grab all the data at once
    data = stream.read()

    # if we have anything but whitespace, then maybe we have an array
    if not data.strip():
        return None

    # we seem to have two types of arrays:
    #  (1) newline-delimited arrays of strings
    #  (2) whitespace-delimited arrays of tokens

    # first, check if this is an array of strings
    strings = map(str.strip, data.splitlines())

    if all(s.startswith('"') and s.endswith('"') for s in strings):
        return map(parse_token, strings)

    return map(parse_token, filter(None, data.split()))


def parse_object_dict(stream):
    d = {}

    while 1:
        token, tpe = read_key(stream)

        # an empty type here means EOF before key
        # this is ok; it's what we would expect
        # however, this could mean that it's an array instead
        # (come on Paradox, would it have hurt to use []? ><)
        # in any case, return, and handle that problem elsewhere
        if not tpe:
            break

        # there are sometimes empty objects chilling here
        if tpe == '{':
            substream = read_object(stream)
            obj = parse_object(substream) if substream is not None else None
            # ignore this object
            # warning: here be dragons
            continue

        assert tpe == '='

        key = parse_token(token)
        token, tpe = read_value(stream)

        # an empty type here always indicates EOF
        # however, it's an EOF where we really weren't expecting one
        # that suggests that the object is invalid
        if not tpe:
            return None

        if tpe == '{':
            substream = read_object(stream)
            obj = parse_object(substream) if substream is not None else None

            # if we already have a key for this value, then we have a number
            # of options:
            #
            #  (1) if possible, merge dictionaries
            #  (2) if possible, extend lists
            #  (3) otherwise, if we have an existing list, add to it
            #  (4) failing that, make a new list
            #
            # note that there are some problematic corner cases:
            #  * merging dictionaries could replace keys
            #  * adding to an existing list doesn't make sense if the existing
            #    list didn't come from this method (but from the file instead)
            if key in d:
                existing = d[key]

                if isinstance(obj, dict) and isinstance(existing, dict):
                    existing.update(obj)
                elif isinstance(obj, list) and isinstance(existing, list):
                    existing.extend(obj)
                elif isinstance(existing, list):
                    existing.append(obj)
                else:
                    d[key] = [existing, obj]
            else:
                d[key] = obj
        else:
            if key in d:
                existing = d[key]

                if isinstance(existing, list):
                    existing.append(token)
                else:
                    d[key] = [existing, token]
            else:
                d[key] = parse_token(token)

    # if we got to this point, and we don't have any keys, then clearly we
    # failed to build a valid object
    # we should therefore return none
    return d if d else None


def read_key(stream):
    endTokenMarkers = {
            '=': False,
            '{': True,
            '': False,
            }

    return read_token(stream, endTokenMarkers)


def read_value(stream):
    endTokenMarkers = {
            '{': True,
            '\n': False,
            '': False,
            }

    # repeat till we have a value
    token, tpe = read_token(stream, endTokenMarkers)

    while not token and tpe == '\n':
        token, tpe = read_token(stream, endTokenMarkers)

    return token, tpe


def read_token(stream, endTokenMarkers, readSize=8):
    output = ''

    # read in chunks of readSize
    # we keep track of how many bytes we will have to rewind once a valid
    # end token marker is found
    s = stream.read(readSize)
    n = len(s)

    while 1:
        if not s:
            c = s
            break

        for c in s:
            n -= 1

            if c in endTokenMarkers:
                break

            output += c

        if c in endTokenMarkers:
            break

        s = stream.read(readSize)
        n = len(s)

    # rewind every remaining byte in our read, plus the token if necessary
    stream.seek(-(n + endTokenMarkers[c]), 1)

    return output, c


def parse_token(token):
    # remove newlines, tabs etc
    token = token.strip()

    # Dates: 1444.1.28 || "1444.1.28"
    if token.count('.') == 2:
        token = token.strip('"')
        return datetime(*map(int, token.split('.')))

    # String: "<string>"
    if token.startswith('"') and token.endswith('"'):
        return token.strip('"')

    # Boolean: yes|no
    if token in ('yes', 'no'):
        return token == 'yes'

    # Numbers
    if '.' in token:
        try:
            return float(token)
        except ValueError:
            pass
    else:
        try:
            return int(token)
        except ValueError:
            pass

    # Default: just give it back as a string
    return token


def wrap_stream(f):
    # If we are on a system which uses carriage returns for newlines (ie, \r\n),
    # then a call to f.read, say f.read(8), may actually consume more than 8
    # bytes of data if a newline is encountered.
    # This makes rewinding of the stream impractical.
    #
    # To get around this, we can wrap f in a StringIO instance.
    # Each \n char in the new stream will be exactly one byte when read.
    #
    # If performance is necessary, this method could instead return a proxy
    # object which reads lines from f and interposes newlines on demand (eg,
    # using a generator).
    return StringIO(f.read())
    

def parse_save(fn, topLevelKeys=None):
    with open(fn, 'rU') as f:
        if topLevelKeys is None:
            f.readline() # consume header
            stream = wrap_stream(f)
            return parse_object(stream)

        d = {}

        while 1:
            line = f.readline()

            for k in topLevelKeys:
                if line.startswith(k):
                    stream = read_object(f)
                    assert stream is not None

                    d[k] = parse_object(stream)

                    if len(d) == len(topLevelKeys):
                        break

        return d
