# Copyright Sean Purdon 2014
# All Rights Reserved

class Country(object):
    def __init__(self, tag):
        self.tag = tag

        self.name = None
        self.col = None

    def __repr__(self):
        return 'Country(%s)'%self.tag
