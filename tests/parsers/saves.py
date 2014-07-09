from datetime import datetime
from StringIO import StringIO
import unittest

from parsers.saves import read_object, parse_object


def suite():
    loader = unittest.TestLoader()

    return unittest.TestSuite([
        loader.loadTestsFromTestCase(ReadObjectTests),
        loader.loadTestsFromTestCase(ParseObjectTests),
        ])


class ReadObjectTests(unittest.TestCase):
    def _stripObjectString(self, s):
        return s.strip().strip('{}').strip()

    def assertObjectValid(self, obj, expected):
        objString = self._stripObjectString(obj.read())
        expectedString = self._stripObjectString(expected)

        self.assertTrue(objString, expectedString)

    def assertObjectInvalid(self, obj):
        self.assertIsNone(obj)

    def check(self, s, shouldBeValid, expected=None):
        if expected is None:
            expected = s

        stream = StringIO(s)
        obj = read_object(stream)
        
        if shouldBeValid:
            self.assertObjectValid(obj, expected)
        else:
            self.assertObjectInvalid(obj)

    ## Valid objects: tests should pass
    def testSingleKeyValuePairIsValid(self):
        s = '''{
                key=value
               }'''

        self.check(s, True)

    def testSingleElementArrayIsValid(self):
        s = '''{
                element
               }'''

        self.check(s, True)

    def testNestedDictIsValid(self):
        s = '''{
                key={
                    key=value
                    }
                }'''

        self.check(s, True)

    def testOnlyFirstObjectIsParsedWhenIdentical(self):
        s = '''{
                key=value
                }'''

        self.check(s*2, True, expected=s)

    def testOnlyFirstObjectIsParsedWhenDifferent(self):
        s = '''{
                key=value
                }'''
        other = '''{
                    element
                    }'''

        self.check(s + other, True, expected=s)

    def testObjectParsedWhenNextObjectIsInvalid(self):
        s = '''{
                key=value
                }'''
        other = '''{
                    element'''

        self.check(s + other, True, expected=s)


    ## Invalid objects: tests should fail
    def testEmptyObjectIsInvalid(self):
        s = ''

        self.check(s, False)

    def testMissingEndBraceIsInvalid(self):
        s = '''{
                key=value'''

        self.check(s, False)

    def testNoBracesIsInvalid(self):
        s = 'key=value'

        self.check(s, False)


class ParseObjectTests(unittest.TestCase):
    def checkIsValid(self, s, expected):
        stream = StringIO(s)
        result = parse_object(stream)
        
        if isinstance(expected, dict):
            self.assertIsInstance(result, dict)
            self.assertDictEqual(result, expected)
        else:
            self.assertIsInstance(result, list)
            self.assertListEqual(result, expected)

    def checkIsInvalid(self, s):
        stream = StringIO(s)
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
                item
            '''
        expected = [
                'item',
                ]

        self.checkIsValid(s, expected)

    def testSingleElementStringArrayIsValid(self):
        s = '''
                "Multiple Word String"
            '''
        expected = [
                'Multiple Word String',
                ]

        self.checkIsValid(s, expected)

    def testMultipleElementArrayIsValid(self):
        s = '''
                multiple words are different
            '''
        expected = [
                'multiple',
                'words',
                'are',
                'different',
                ]

        self.checkIsValid(s, expected)

    def testMultipleElementStringArrayIsValid(self):
        s = '''
                "Multiple Word String"
                "Another String"
            '''
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
