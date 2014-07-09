from io import IOBase
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

    ## Valid objects: tests should pass
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
