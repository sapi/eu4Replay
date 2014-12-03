# Copyright Sean Purdon 2014
# All Rights Reserved

from datetime import datetime

import model.settings as settings


PROVINCES = 'PROVINCES'
COUNTRIES = 'COUNTRIES'

CONTROLLER = 'controller'
OWNER = 'owner'

EVENT_TYPE = 'EVENT_TYPE'
EVENT_TAG_CHANGE = 'EVENT_TAG_CHANGE'
SOURCE_TAG = 'SOURCE_TAG'


def build_history(save, provinces):
    # first, build up histories for all of the provinces
    provinceHistories = {}

    # the most important part of the histories is the changes recorded in the
    # province histories section of the save file
    assert 'provinces' in save

    for nID,d in save['provinces'].iteritems():
        pID = -nID

        events = provinceHistories[pID] = {}

        assert pID in provinces
        p = provinces[pID]

        # add owner as of start date
        events[settings.start_date] = {CONTROLLER: p.controller, OWNER: p.owner}

        if 'history' not in d:
            continue

        for date,evt in d['history'].iteritems():
            if not isinstance(date, datetime):
                continue

            out = {}

            if 'controller' in evt:
                out[CONTROLLER] = evt['controller']['controller']

            if 'owner' in evt:
                out[OWNER] = evt['owner']

            if out:
                events[date] = out

    # we also need to check for tag change events, as these aren't necessarily
    # reflected in the province histories
    countryHistories = {}

    assert 'countries' in save
    
    for tag,d in save['countries'].iteritems():
        # some mods put extra data in the 'countries' dict
        if not isinstance(d, dict) or 'history' not in d:
            continue

        if tag not in countryHistories:
            events = countryHistories[tag] = {}

        # NB: currently assume there is only one event per day
        for date,evt in d['history'].iteritems():
            if not isinstance(date, datetime):
                continue

            if 'changed_tag_from' in evt:
                events[date] = {
                        EVENT_TYPE: EVENT_TAG_CHANGE,
                        SOURCE_TAG: evt['changed_tag_from']
                    }

    # now, build up a dict of all the provinces which had events on a given
    # day, to save searching later
    provinceDates = {
            pID: set(evts) for pID,evts in provinceHistories.iteritems()
                if evts
        }

    datesWithProvinceEvents = reduce(set.union, provinceDates.values(), set())

    countryDates = {
            tag: set(evts) for tag,evts in countryHistories.iteritems()
                if evts
        }

    datesWithCountryEvents = reduce(set.union, countryDates.values(), set())

    dates = datesWithProvinceEvents.union(datesWithCountryEvents)

    datesWithEvents = {
            date: {
                    PROVINCES: [pID for pID,eventDates 
                                in provinceDates.iteritems()
                                if date in eventDates],
                    COUNTRIES: [tag for tag,eventDates
                                in countryDates.iteritems()
                                if date in eventDates],
                } for date in dates
            }

    return provinceHistories, countryHistories, datesWithEvents
