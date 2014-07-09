#!/usr/bin/env python

# Copyright Sean Purdon 2014
# All Rights Reserved


from gui.main import setup


def main():
    app = setup()

    app.MainLoop()


if __name__ == '__main__':
    main()
