#!/usr/bin/env python

# Copyright Sean Purdon 2014
# All Rights Reserved

# we need to immediately set the matplotlib backend, as this must happen
# before anything from that module is touched
import gui.plotting

from gui.main import setup


def main():
    app = setup()

    app.MainLoop()


if __name__ == '__main__':
    main()
