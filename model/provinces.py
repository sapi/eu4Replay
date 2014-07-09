# Copyright Sean Purdon 2014
# All Rights Reserved

import json
import numpy as np


class Province(object):
    def __init__(self, id, name=u'', rgb=None):
        self.id = id
        self.name = name
        self.rgb = rgb

        self.maskIdxs = None

        self.owner = None
        self.controller = None

    def __unicode__(self):
        return u'Province({s.id}, name={s.name})'.format(s=self)

    def __repr__(self):
        return 'Province(%d)'%self.id

    @classmethod
    def fromDict(cls, d):
        assert 'id' in d
        id = d['id']

        assert 'name' in d
        name = d['name']

        assert 'rgb' in d
        rgb = tuple(d['rgb'])

        instance = cls(id, name=name, rgb=rgb)

        assert 'maskIdxs' in d
        f = lambda arr: np.array(arr, np.integer)
        instance.maskIdxs = tuple(map(f, d['maskIdxs']))

        return instance

    def toDict(self):
        return {
                'id': int(self.id),
                'name': self.name,
                'rgb': map(int, self.rgb),
                'maskIdxs': map(lambda row: map(int, row), self.maskIdxs),
                }


def write_to_file(fn, provinces):
    arr = []

    for province in provinces.values():
        arr.append(province.toDict())

    # ocd :)
    arr.sort(key=lambda d: d['id'])
            
    with open(fn, 'w') as f:
        f.write(json.dumps(arr, encoding='latin-1'))


def load_from_file(fn):
    with open(fn, 'rU') as f:
        arr = json.loads(f.read())

    provinces = {p.id: p for p in map(Province.fromDict, arr)}

    return provinces
