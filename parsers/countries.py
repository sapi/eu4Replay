# Copyright Sean Purdon 2014
# All Rights Reserved

import os

from model.countries import Country
import model.settings as settings
from tools.paths import get_path_components


def parse_countries():
    countries = {}

    for f in settings.mods.mod.iterdir('common', 'country_tags'):
        for line in f:
            if line.startswith('#') or not line.strip():
                continue

            tag,_,subPath = map(str.strip, line.partition('='))

            # clean up the path
            subPath,_,_ = subPath.partition('#')
            subPath = subPath.strip().strip('"').strip()

            components = ['common'] + get_path_components(subPath)

            assert tag not in countries
            country = countries[tag] = Country(tag)

            parse_country_file(components, country)

    return countries


def parse_country_file(pathComponents, country):
    basename = os.path.basename(os.path.join(*pathComponents))
    country.name = basename.rsplit('.', 1)[0]

    with settings.mods.mod.open(*pathComponents) as f:
        for line in f:
            if line.startswith('color'):
                _,_,end = line.partition('=')

                cols = end.strip().strip('{}')
                cols = filter(None, cols.split())
                
                country.col = tuple(map(int, cols))


def create_dynamic_countries(save, countries):
    # build lists of masters
    assert 'countries' in save
    subjects = { 
            tag : data['subjects'] if 'subjects' in data else []
                for tag,data in save['countries'].iteritems()
                if isinstance(data, dict)
            }

    masters = {}

    for master,subjs in subjects.iteritems():
        for subject in subjs:
            masters[subject] = master

    # now actually create the country objects
    assert 'dynamic_countries' in save

    for tag in save['dynamic_countries']:
        if tag not in countries:
            countries[tag] = Country(tag)

        country = countries[tag]

        if tag in masters:
            master = countries[masters[tag]]
            country.col = master.col
        else:
            country.col = [0, 0, 0]
