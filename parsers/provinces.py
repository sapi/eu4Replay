# Copyright Sean Purdon 2014
# All Rights Reserved

import numpy as np
import os

from model.provinces import Province
import model.settings as settings


def parse_province_definitions():
    provinces = {}

    with settings.mods.mod.provinceDefinitionFile as f:
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


def parse_province_original_owners(provinces):
    for f in settings.mods.mod.iterdir('history', 'provinces'):
        # work out what province this is for
        pID = lazy_atoi(os.path.basename(f.name))

        assert pID in provinces
        province = provinces[pID]

        # now grab the data we want from the file
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
