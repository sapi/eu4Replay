#!/usr/bin/env python

import unittest

import tests.parsers.files


def suite():
    return unittest.TestSuite([
        tests.parsers.files.suite(),
        ])


if __name__ == '__main__':
    tests = suite()

    runner = unittest.TextTestRunner()
    runner.run(tests)
