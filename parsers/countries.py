# Copyright Sean Purdon 2014
# All Rights Reserved

import os

from model.countries import Country


def parse_countries(eu4Dir):
    countries = {}

    commonDir = os.path.join(eu4Dir, 'common')
    tagsDir = os.path.join(commonDir, 'country_tags')

    tagFilenames = os.listdir(tagsDir) 
    tagPaths = map(lambda fn: os.path.join(tagsDir, fn), tagFilenames)
    
    for path in tagPaths:
        with open(path, 'rU') as f:
            for line in f:
                if line.startswith('#') or not line.strip():
                    continue

                tag,_,subPath = map(str.strip, line.partition('='))

                # clean up the path
                subPath,_,_ = subPath.partition('#')
                subPath = subPath.strip().strip('"').strip()

                fn = os.path.join(commonDir, *subPath.split('/'))

                assert tag not in countries
                country = countries[tag] = Country(tag)

                parse_country_file(fn, country)

    return countries


def parse_country_file(fn, country):
    country.name = os.path.basename(fn).rsplit('.', 1)[0]

    with open(fn, 'rU') as f:
        for line in f:
            if line.startswith('color'):
                _,_,end = line.partition('=')

                cols = end.strip().strip('{}')
                cols = filter(None, cols.split())
                
                country.col = tuple(map(int, cols))
