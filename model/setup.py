# Copyright Sean Purdon 2014
# All Rights Reserved

import os
from scipy.ndimage import imread
from StringIO import StringIO
import sys

from parsers.countries import parse_countries
from parsers.provinces \
        import parse_province_definitions, parse_province_regions, \
               parse_province_original_owners
from parsers.files import parse_object


def flushed_write(s):
    sys.stdout.write(s)
    sys.stdout.flush()


def setup_data(eu4Dir):
    # required directories / files
    mapDir = os.path.join(eu4Dir, 'map')
    provinceDefintionsFilename = os.path.join(mapDir, 'definition.csv')
    mapFile = os.path.join(mapDir, 'provinces.bmp')
    mapMetadataFilename = os.path.join(mapDir, 'default.map')

    historyDir = os.path.join(eu4Dir, 'history')

    # load country data
    flushed_write('Loading country data...')
    countries = parse_countries(eu4Dir)
    flushed_write('done!\n')

    # load province data
    flushed_write('Loading province definitions...')
    provinces = parse_province_definitions(provinceDefintionsFilename)
    flushed_write('done!\n')

    flushed_write('Loading province owners...')
    parse_province_original_owners(historyDir, provinces)
    flushed_write('done!\n')

    # load map
    flushed_write('Loading map file...')
    img = imread(mapFile)
    flushed_write('done!\n')

    # load map metadata
    flushed_write('Loading map metadata...')

    with open(mapMetadataFilename, 'rU') as f:
        mapObject = parse_object(StringIO(f.read()))

    flushed_write('done!\n')

    # locate provinces (need coffee for this one...)
    flushed_write('Locating provinces on map...')
    parse_province_regions(img, provinces)
    flushed_write('done!\n')

    return countries, provinces, img, mapObject


def setup_map(eu4Dir):
    mapDir = os.path.join(eu4Dir, 'map')
    mapFilename = os.path.join(mapDir, 'provinces.bmp')
    mapMetadataFilename = os.path.join(mapDir, 'default.map')

    img = imread(mapFilename)

    with open(mapMetadataFilename, 'rU') as f:
        mapObject = parse_object(StringIO(f.read()))

    return img, mapObject


def setup_countries(eu4Dir):
    countries = parse_countries(eu4Dir)
    return countries


def setup_provinces(eu4Dir):
    mapDir = os.path.join(eu4Dir, 'map')
    provinceDefintionsFilename = os.path.join(mapDir, 'definition.csv')
    mapFilename = os.path.join(mapDir, 'provinces.bmp')

    provinces = parse_province_definitions(provinceDefintionsFilename)
    img = imread(mapFilename)
    parse_province_regions(img, provinces)

    return provinces
