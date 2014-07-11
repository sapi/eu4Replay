from datetime import datetime
from StringIO import StringIO
import unittest

from parsers.saves import parse_object
from parsers.saves import read_token


def suite():
    loader = unittest.TestLoader()

    return unittest.TestSuite([
        loader.loadTestsFromTestCase(ParseObjectReadingTests),
        loader.loadTestsFromTestCase(ParseObjectParsingTests),
        loader.loadTestsFromTestCase(ReadTokenTests),
        ])


class ParseObjectReadingTests(unittest.TestCase):
    def _buildStream(self, s):
        # parse_object requires there to be no starting brace
        # this is because the top level of the save file has no braces, and
        # the starting brace is removed before a recursive call
        if s.strip().startswith('{'):
            _,_,s = s.partition('{')

        return StringIO(s)

    def checkIsValid(self, s, expectedRemainder, **kwargs):
        stream = self._buildStream(s)
        obj = parse_object(stream, **kwargs)

        self.assertIsNotNone(obj)

        remaining = stream.read().strip()
        expectedRemainder = expectedRemainder.strip()

        self.assertEqual(remaining, expectedRemainder)

    def checkIsInvalid(self, s, **kwargs):
        stream = self._buildStream(s)
        obj = parse_object(stream, **kwargs)

        self.assertIsNone(obj)

    ## Valid objects: tests should pass
    def testSingleKeyValuePairIsValid(self):
        s = '''{
                key=value
               }'''
        expectedRemainder = ''

        self.checkIsValid(s, expectedRemainder)

    def testSingleElementArrayIsValid(self):
        s = '''{
                element
               }'''
        expectedRemainder = ''

        self.checkIsValid(s, expectedRemainder)

    def testNestedDictIsValid(self):
        s = '''{
                key={
                    key=value
                    }
                }'''
        expectedRemainder = ''

        self.checkIsValid(s, expectedRemainder)

    def testOnlyFirstObjectIsParsedWhenIdentical(self):
        s = '''{
                key=value
                }'''
        expectedRemainder = s

        self.checkIsValid(s*2, expectedRemainder)

    def testOnlyFirstObjectIsParsedWhenDifferent(self):
        s = '''{
                key=value
                }'''
        other = '''{
                    element
                    }'''
        expectedRemainder = other

        self.checkIsValid(s + other, expectedRemainder)

    def testObjectParsedWhenNextObjectIsInvalid(self):
        s = '''{
                key=value
                }'''
        other = '''{
                    element'''
        expectedRemainder = other

        self.checkIsValid(s + other, expectedRemainder)

    def testNoBracesIsValid(self):
        s = 'key=value'
        expectedRemainder = ''

        self.checkIsValid(s, expectedRemainder)

    ## Invalid objects: tests should fail
    def testEmptyObjectIsInvalid(self):
        s = ''

        self.checkIsInvalid(s)

    def testMissingEndBraceIsInvalid(self):
        s = '''{
                key=value'''

        self.checkIsInvalid(s, allowEOF=False)


class ParseObjectParsingTests(unittest.TestCase):
    def _buildStream(self, s):
        # parse_object requires there to be no starting brace
        # this is because the top level of the save file has no braces, and
        # the starting brace is removed before a recursive call
        if s.strip().startswith('{'):
            _,_,s = s.partition('{')

        return StringIO(s)

    def checkIsValid(self, s, expected):
        stream = self._buildStream(s)
        result = parse_object(stream)
        
        if isinstance(expected, dict):
            self.assertIsInstance(result, dict)
            self.assertDictEqual(result, expected)
        else:
            self.assertIsInstance(result, list)
            self.assertListEqual(result, expected)

    def checkIsInvalid(self, s):
        stream = self._buildStream(s)
        result = parse_object(stream)

        self.assertIsNone(result)

    ## Valid objects: tests should pass
    # Simple dicts
    def testSingleKeyValuePairIsValid(self):
        s = '''
                key=value
            '''
        expected = {
                'key': 'value',
                }

        self.checkIsValid(s, expected)

    def testTwoKeyValuePairsAreValid(self):
        s = '''
                key=value
                key2=value2
            '''
        expected = {
                'key': 'value',
                'key2': 'value2',
                }

        self.checkIsValid(s, expected)

    def testTwoKeyValuePairsWithBlankLineAreValid(self):
        s = '''
                key=value
                
                key2=value2
            '''

        expected = {
                'key': 'value',
                'key2': 'value2',
                }

        self.checkIsValid(s, expected)

    # Simple arrays
    def testSingleElementArrayIsValid(self):
        s = '''
                { item }
            '''
        expected = [
                'item',
                ]

        self.checkIsValid(s, expected)

    def testSingleElementStringArrayIsValid(self):
        s = '''{
                "Multiple Word String"
            }'''
        expected = [
                'Multiple Word String',
                ]

        self.checkIsValid(s, expected)

    def testMultipleElementArrayIsValid(self):
        s = '''
                { multiple words are different }
            '''
        expected = [
                'multiple',
                'words',
                'are',
                'different',
                ]

        self.checkIsValid(s, expected)

    def testMultipleElementStringArrayIsValid(self):
        s = '''{
                "Multiple Word String"
                "Another String"
            }'''
        expected = [
                'Multiple Word String',
                'Another String',
                ]

        self.checkIsValid(s, expected)

    # Stupid formats
    def testDictWithSpacesAroundEqualsIsValid(self):
        s = '''
                key = value
            '''
        expected = {
                'key': 'value',
                }

        self.checkIsValid(s, expected)

    def testDictWithSpacesAfterValueBeforeNewlineIsValid(self):
        s = '''
                key=value     
                key2=value2
            '''
        expected = {
                'key': 'value',
                'key2': 'value2',
                }

        self.checkIsValid(s, expected)

    def testDictWithIntValueIsValid(self):
        s = '''
                key=0
            '''
        expected = {
                'key': 0,
                }

        self.checkIsValid(s, expected)

    def testDictWithFloatValueIsValid(self):
        s = '''
                key=0.1
            '''
        expected = {
                'key': 0.1,
                }

        self.checkIsValid(s, expected)

    def testDictWithStringValueIsValid(self):
        s = '''
                key="value"
            '''
        expected = {
                'key': 'value',
                }

        self.checkIsValid(s, expected)

    def testDictWithDateValueIsValid(self):
        s = '''
                key="1444.1.1"
            '''
        expected = {
                'key': datetime(1444, 1, 1),
                }

        self.checkIsValid(s, expected)

    def testDictWithBooleanTrueIsValid(self):
        s = '''
                key=yes
            '''
        expected = {
                'key': True,
                }

        self.checkIsValid(s, expected)

    def testDictWithBooleanFalseIsValid(self):
        s = '''
                key=no
            '''
        expected = {
                'key': False,
                }

        self.checkIsValid(s, expected)

    # Nested objects
    def testDictInsideDictIsValid(self):
        s = '''
                key={
                    key=value
                }
            '''
        expected = {
                'key': {
                    'key': 'value',
                    },
                }

        self.checkIsValid(s, expected)

    def testDictInsideDictInsideDictIsValid(self):
        s = '''
                key={
                    key={
                        key=value
                    }
                }
            '''
        expected = {
                'key': {
                    'key': {
                        'key': 'value',
                        },
                    },
                }

        self.checkIsValid(s, expected)

    def testArrayInsideDictIsValid(self):
        s = '''
                key={ one two three four }
            '''
        expected = {
                'key': ['one', 'two', 'three', 'four']
                }

        self.checkIsValid(s, expected)

    def testDictInsideDictWithBraceOnNewLineIsValid(self):
        s = '''
                key=
                {
                    key=value
                }
            '''
        expected = {
                'key': {
                    'key': 'value',
                    },
                }

        self.checkIsValid(s, expected)

    def testDictInsideDictWithSpacesBeforeBraceIsValid(self):
        s = '''
                key=      {
                    key=value
                }
            '''
        expected = {
                'key': {
                    'key': 'value',
                    },
                }

        self.checkIsValid(s, expected)

    def testDictInsideDictWithSpacesAfterBraceIsValid(self):
        s = '''
                key={     
                    key=value
                }
            '''
        expected = {
                'key': {
                    'key': 'value',
                    },
                }

        self.checkIsValid(s, expected)

    # Repeated keys (oh, god, why is this possible Paradox?!)
    def testRepeatedKeyValuePairsMergeAndAreValid(self):
        s = '''
                key=one
                key=two
            '''
        expected = {
                'key': ['one', 'two'],
            }

        self.checkIsValid(s, expected)

    def testRepeatedKeysWithDictValuesMergeAndAreValid(self):
        s = '''
                key={
                    one=1
                }
                key={
                    two=2
                }
            '''
        expected = {
                'key': {
                    'one': 1,
                    'two': 2,
                    }
                }

        self.checkIsValid(s, expected)

    def testRepeatedKeysWithDictValuesWithRepeatedKeysTakeFirst(self):
        s = '''
                key={
                    one=1
                }
                key={
                    one=2
                }
            '''
        expected = {
                'key': {
                    'one': 1,
                    },
                }

        self.checkIsValid(s, expected)

    # Key at EOF
    def testKeyAtEOFIsValid(self):
        s = 'key=value'
        expected = {
                'key': 'value',
                }

        self.checkIsValid(s, expected)

    # Invalid child objects
    def testObjectWithInvalidChildObjectIsValid(self):
        s = '''
                key={
                    key=
                }
            '''
        expected = {
                'key': None,
                }

        self.checkIsValid(s, expected)

    def testObjectWithEmptyChildObjectIsValid(self):
        s = '''
                key = { }
            '''
        expected = {
                'key': None,
                }

        self.checkIsValid(s, expected)

    def testObjectWithExtraneousChildObjectIsValid(self):
        # this comes up quite often, but god knows why...
        s = '''
                key=value
                {
                }
                key2 = {
                    key=value
                }
                {
                }
            '''
        expected = {
                'key': 'value',
                'key2': {
                    'key': 'value',
                    }
                }

        self.checkIsValid(s, expected)

    ## Invalid objects: tests should fail
    def testEmptyObjectIsInvalid(self):
        s = ''

        self.checkIsInvalid(s)

    def testObjectWithKeyButNoValueIsInvalid(self):
        s = 'key='

        self.checkIsInvalid(s)

    def testObjectWithKeyValuePairThenHangingStringIsInvalid(self):
        s = '''
                key=value
                key2
            '''

        self.checkIsInvalid(s)

    def testObjectWithKeyValuePairThenKeyButNoValueIsInvalid(self):
        s = '''
                key=value
                key2=
            '''

        self.checkIsInvalid(s)


class ReadTokenTests(unittest.TestCase):
    def setUp(self):
        self.EOFMarkers = {
                '': False,
                }

        self.equalsAndEOFMarkersWithNoRewind = {
                '': False,
                '=': False,
                }

        self.equalsAndEOFMarkersWithRewind = {
                '': False,
                '=': True,
                }

    def check(self, s, endTokenMarkers, expected):
        stream = StringIO(s)

        result = read_token(stream, endTokenMarkers)
        self.assertEqual(result, expected)

    def checkMultiple(self, s, endTokenMarkers, expected):
        stream = StringIO(s)

        for etm,exp in zip(endTokenMarkers, expected):
            result = read_token(stream, etm)
            self.assertEqual(result, exp)

    def testEOFAtStartOfStream(self):
        s = ''
        endTokenMarkers = self.EOFMarkers
        expected = ('', '')

        self.check(s, endTokenMarkers, expected)

    def testReadToEOF(self):
        s = 'test'
        endTokenMarkers = self.EOFMarkers
        expected = ('test', '')

        self.check(s, endTokenMarkers, expected)

    def testReadToMarker(self):
        s = 'test=val'
        endTokenMarkers = self.equalsAndEOFMarkersWithNoRewind
        expected = ('test', '=')

        self.check(s, endTokenMarkers, expected)

    def testReadToMarkerThenToEOF(self):
        s = 'test=val'
        endTokenMarkers = [self.equalsAndEOFMarkersWithNoRewind]*2
        expected = [
                ('test', '='),
                ('val', ''),
                ]

        stream = self.checkMultiple(s, endTokenMarkers, expected)

    def testRewindAfterReadingMarker(self):
        s = 'test=val'
        endTokenMarkers = [
                self.equalsAndEOFMarkersWithRewind,
                self.EOFMarkers,
                ]
        expected = [
                ('test', '='),
                ('=val', ''),
                ]

        stream = self.checkMultiple(s, endTokenMarkers, expected)
