# Copyright Sean Purdon 2014
# All Rights Reserved

from datetime import datetime


CONTROLLER = 'controller'
OWNER = 'owner'
START_DATE = datetime(1444, 11, 11)


def build_history(save, provinces):
    # first, build up histories for all of the provinces
    provinceHistories = {}

    for nID,d in save.iteritems():
        pID = -nID

        events = provinceHistories[pID] = {}

        assert pID in provinces
        p = provinces[pID]

        # add owner as of start date
        events[START_DATE] = {CONTROLLER: p.controller, OWNER: p.owner}

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

    # now, build up a dict of all the provinces which had events on a given
    # day, to save searching later
    provinceDates = {
            pID: set(evts) for pID,evts in provinceHistories.iteritems()
            }

    dates = reduce(set.union, provinceDates.values())

    datesWithEvents = {
            date: [pID for pID,eventDates in provinceDates.iteritems()
                    if date in eventDates] for date in dates
            }

    return provinceHistories, datesWithEvents
