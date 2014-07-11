# Copyright Sean Purdon 2014
# All Rights Reserved

from datetime import datetime
from StringIO import StringIO

## Save Format
# 
# < crap on first line >
# key=value
# value -{ "string", number, yes|no, array or dict
#
# dict: as above (top level of save file is dict)
# array: either space-delimited non-strings, or newline delimited "strings"


def parse_object(stream, allowEOF=True):
    pos = stream.tell()
    obj = parse_object_dict(stream, allowEOF=allowEOF)

    if obj is not None:
        return obj

    # we failed to parse a dict, but maybe it's an array
    stream.seek(pos)
    obj = parse_object_array(stream)

    return obj # will be None if the parse failed


def parse_object_array(stream):
    # read to the end of the array
    data, tpe = read_array(stream)

    # if we terminated on anything *except* an end of object char, we cannot
    # parse an array (this includes EOF)
    # this is because an array cannot be at file scope
    if tpe != '}':
        return None

    # if we have anything but whitespace, then maybe we have an array
    if not data.strip():
        return None

    # we seem to have two types of arrays:
    #  (1) newline-delimited arrays of strings
    #  (2) whitespace-delimited arrays of tokens

    # first, check if this is an array of strings
    # make sure to remove any empty lines so that the all() isn't confused
    strings = map(str.strip, data.splitlines())
    strings = filter(None, strings)

    if all(s.startswith('"') and s.endswith('"') for s in strings):
        return map(parse_token, strings)

    # build an array from all tokens, separated by whitespace, which are not
    # themselves only whitespace
    tokens = map(str.strip, data.split())
    tokens = filter(None, tokens)
    arr = map(parse_token, tokens)

    return arr

def parse_object_dict(stream, allowEOF):
    d = {}

    endOfObjectMarks = ('', '}') if allowEOF else ('}',)

    while 1:
        token, tpe = read_key(stream)
        key = parse_token(token)

        # in a well-formed object, we expect to terminate here
        # we should also exit with failure if we get an unexpected EOF
        # it is always an error to have a non-null key upon termination
        if tpe in endOfObjectMarks:
            if not key:
                break
            return None
        elif not tpe:
            return None

        # there are sometimes empty objects chilling here
        # we consume them to move the stream forward, then ignore them
        # warning: here be dragons
        if tpe == '{':
            obj = parse_object(stream)
            continue

        assert tpe == '='

        token, tpe = read_value(stream)

        # if we're at the start of an object, recursively parse it
        # as this is a nested object, finding an EOF while parsing it will
        # necessarily mean that we can't finish parsing *this* object
        # as such, EOFs cannot be permitted
        if tpe == '{':
            obj = parse_object(stream, allowEOF=False)

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
                    # EARLIER keys take precedence
                    obj.update(existing)
                    d[key] = obj
                elif isinstance(obj, list) and isinstance(existing, list):
                    existing.extend(obj)
                elif isinstance(existing, list):
                    existing.append(obj)
                else:
                    d[key] = [existing, obj]
            else:
                d[key] = obj
        else:
            # if we see the end of object marks here, then:
            #  - if we read a token, we should parse that before breaking
            #  - if we did not, this was an unexpected EOF, which is an error
            token = parse_token(token)

            if not token and tpe in endOfObjectMarks:
                return None

            if key in d:
                existing = d[key]

                if isinstance(existing, list):
                    existing.append(token)
                else:
                    d[key] = [existing, token]
            else:
                d[key] = token

            # break on end of object after parsing
            # as before, exit with failure on unexpected EOF
            if tpe in endOfObjectMarks:
                break
            elif not tpe:
                return None

    # if we got to this point, and we don't have any keys, then clearly we
    # failed to build a valid object
    # we should therefore return None
    return d if d else None


def read_array(stream):
    endTokenMarkers = {
            '}': False, # valid
            '=': False, # invalid
            '': False, # invalid
            }

    return read_token(stream, endTokenMarkers)


def read_key(stream):
    endTokenMarkers = {
            '=': False,
            '{': False,
            '}': False,
            '': False,
            }

    return read_token(stream, endTokenMarkers)


def read_value(stream):
    endTokenMarkers = {
            '{': False,
            '}': False,
            '\n': False,
            '': False,
            }

    # repeat till we have a value
    token, tpe = read_token(stream, endTokenMarkers)

    while not token and tpe == '\n':
        token, tpe = read_token(stream, endTokenMarkers)

    return token, tpe


def read_token(stream, endTokenMarkers, readSize=8):
    output = []
    lengths = []

    # read in chunks of readSize
    # we keep track of how many bytes we will have to rewind once a valid
    # end token marker is found
    s = stream.read(readSize)
    lengths.append(len(s))

    while 1:
        if not s:
            c = s
            break

        for c in s:
            if c in endTokenMarkers:
                break

            output.append(c)

        if c in endTokenMarkers:
            break

        s = stream.read(readSize)
        lengths.append(len(s))

    # rewind every remaining byte in our read, plus the token if necessary
    n = sum(lengths) - len(output) - 1
    stream.seek(-(n + endTokenMarkers[c]), 1)

    output = ''.join(output)

    return output, c


def parse_token(token):
    # remove newlines, tabs etc
    token = token.strip()

    # Dates: 1444.1.28 || "1444.1.28"
    if token.count('.') == 2:
        token = token.strip('"')
        try:
            return datetime(*map(int, token.split('.')))
        except ValueError:
            pass

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
    

def parse_file(f, topLevelKeys=None, header=False):
    if topLevelKeys is None:
        if header:
            f.readline() # consume header

        stream = wrap_stream(f)
        return parse_object(stream)

    d = {}

    while 1:
        line = f.readline()

        for k in topLevelKeys:
            if line.startswith(k):
                stream = wrap_stream(f)
                d[k] = parse_object(stream)

                if len(d) == len(topLevelKeys):
                    break

    return d
