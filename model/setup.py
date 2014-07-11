# Copyright Sean Purdon 2014
# All Rights Reserved

import os
from matplotlib.pyplot import imread
from StringIO import StringIO
import sys

import model.settings as settings
from parsers.countries import parse_countries
from parsers.provinces \
        import parse_province_definitions, parse_province_regions, \
               parse_province_original_owners
from parsers.files import parse_file


def flushed_write(s):
    sys.stdout.write(s)
    sys.stdout.flush()


def setup_data():
    # load country data
    flushed_write('Loading country data...')
    countries = parse_countries()
    flushed_write('done!\n')

    # load province data
    flushed_write('Loading province definitions...')
    provinces = parse_province_definitions()
    flushed_write('done!\n')

    flushed_write('Loading province owners...')
    parse_province_original_owners(provinces)
    flushed_write('done!\n')

    # load map
    flushed_write('Loading map file...')
    img = imread(settings.mods.mod.mapImageFile)
    flushed_write('done!\n')

    # load map metadata
    flushed_write('Loading map metadata...')

    with settings.mods.mod.mapSettingsFile as f:
        mapObject = parse_file(f)

    flushed_write('done!\n')

    # locate provinces (need coffee for this one...)
    flushed_write('Locating provinces on map...')
    parse_province_regions(img, provinces)
    flushed_write('done!\n')

    return countries, provinces, img, mapObject


def setup_map():
    img = imread(settings.mods.mod.mapImageFile)

    with settings.mods.mod.mapSettingsFile as f:
        mapObject = parse_file(f)

    return img, mapObject


def setup_countries():
    countries = parse_countries()
    return countries


def setup_provinces():
    provinces = parse_province_definitions()
    img = imread(settings.mods.mod.mapImageFile)
    parse_province_regions(img, provinces)

    return provinces
