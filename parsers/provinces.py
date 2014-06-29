# Copyright Sean Purdon 2014
# All Rights Reserved

import numpy as np
import os

from model.provinces import Province


def parse_province_definitions(fn):
    provinces = {}

    with open(fn, 'rU') as f:
        for line in f:
            pID,r,g,b,name,_ = line.strip().split(';')

            # skip the header line
            if not pID.isdigit():
                continue 

            # transform arguments
            pID = int(pID)
            rgb = tuple(map(int, (r,g,b)))

            # create the province
            provinces[pID] = Province(pID, name, rgb=rgb)

    return provinces


def parse_province_regions(img, provinces):
    for i,p in enumerate(provinces.values()):
        r,g,b = p.rgb

        p.maskIdxs = np.where(
                (img[:,:,0] == r) & (img[:,:,1] == g) & (img[:,:,2] == b)
            )


def parse_province_original_owners(historyDir, provinces):
    assert os.path.isdir(historyDir)

    subdirs = os.listdir(historyDir)
    assert 'provinces' in subdirs

    provincesDir = os.path.join(historyDir, 'provinces')

    filenames = os.listdir(provincesDir)
    paths = map(lambda fn: os.path.join(provincesDir, fn), filenames)

    for path in paths:
        # work out what province this is for
        pID = lazy_atoi(os.path.basename(path))

        assert pID in provinces
        province = provinces[pID]

        # now grab the data we want from the file
        with open(path, 'rU') as f:
            for line in f:
                if line.startswith('owner'):
                    _,_,owner = line.partition('=')
                    
                    if '#' in owner:
                        owner = owner[:owner.find('#')]

                    province.owner = owner.strip()
                elif line.startswith('controller'):
                    _,_,controller = line.partition('=')

                    if '#' in controller:
                        controller = controller[:controller.find('#')]

                    province.controller = controller.strip()


def lazy_atoi(s):
    out = ''

    for c in s:
        if not c.isdigit():
            break

        out += c

    if not out:
        return 0

    return int(out)
