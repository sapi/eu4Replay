#!/usr/bin/env python

import unittest

import tests.parsers.saves


def suite():
    return unittest.TestSuite([
        tests.parsers.saves.suite(),
        ])


if __name__ == '__main__':
    tests = suite()

    runner = unittest.TextTestRunner()
    runner.run(tests)
