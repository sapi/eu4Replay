# Copyright Sean Purdon 2014
# All Rights Reserved


from datetime import datetime, timedelta

import model.history as history


class EU4Map(object):
    LAKE_COLOUR = (50, 50, 150)
    SEA_COLOUR = (0, 0, 100)
    UNCOLONISED_COLOUR = (200, 200, 200)

    DELTA_DAY = 'DELTA_DAY'
    DELTA_MONTH = 'DELTA_MONTH'
    DELTA_YEAR = 'DELTA_YEAR'
    DELTA_DECADE = 'DELTA_DECADE'

    def __init__(self, img, provinces, countries, mapObject):
        self.img = img
        self.provinces = provinces
        self.countries = countries
        self.mapObject = mapObject

        self.provinceHistories = {}
        self.datesWithEvents = {}

        # build original owners and controllers, so they can be restored
        self.provinceRestoreData = {
                p.id: (p.controller, p.owner) for p in self.provinces.values()
                }

        self.reset()

    def loadSave(self, provinceHistories, datesWithEvents):
        self.provinceHistories = provinceHistories
        self.datesWithEvents = datesWithEvents
        self.reset()

    def reset(self):
        # reset the date
        self.date = history.START_DATE

        # reset province owners
        for pID,(controller,owner) in self.provinceRestoreData.iteritems():
            province = self.provinces[pID]
            province.controller = controller
            province.owner = owner

        # clear the map (everything black)
        self.img[:] = 0

        # do the provinces
        for pID in self.provinces:
            self.drawProvince(pID)

        # fill in all the lakes and seas
        staticElements = [
                (EU4Map.LAKE_COLOUR, 'lakes'),
                (EU4Map.SEA_COLOUR, 'sea_starts'),
                ]

        for col,key in staticElements:
            for pID in self.mapObject[key]:
                assert pID in self.provinces
                province = self.provinces[pID]

                self.img[province.maskIdxs] = col

    def drawProvince(self, pID):
        assert pID in self.provinces
        province = self.provinces[pID]

        # unowned provinces are uncolonised
        if province.owner in self.countries:
            country = self.countries[province.owner]
            assert country.col, '%s has no colour set'%country

            col = country.col
        else:
            col = EU4Map.UNCOLONISED_COLOUR

        assert province.maskIdxs, '%s has no mask'%province
        self.img[province.maskIdxs] = col

    def redraw(self, dirty=None):
        if dirty is None:
            dirty = set(self.provinces)

        for pID in dirty:
            self.drawProvince(pID)

    def tick(self, delta):
        assert delta \
                in [EU4Map.DELTA_DAY, EU4Map.DELTA_MONTH, EU4Map.DELTA_YEAR,
                        EU4Map.DELTA_DECADE]

        y,m,d = self.date.year, self.date.month, self.date.day

        if delta == EU4Map.DELTA_DAY:
            targetDate = self.date + timedelta(days=1)
        elif delta == EU4Map.DELTA_MONTH:
            targetDate = datetime(y + m/12, m%12 + 1, d)
        elif delta == EU4Map.DELTA_YEAR:
            targetDate = datetime(y + 1, m, d)
        elif delta == EU4Map.DELTA_DECADE:
            targetDate = datetime(y + 10, m, d)

        dayDelta = timedelta(days=1)
        dirty = set()

        while self.date < targetDate:
            self.date += dayDelta

            # update our set of dirty provinces
            if self.date not in self.datesWithEvents:
                continue
            
            pIDs = self.datesWithEvents[self.date]
            dirty = dirty.union(pIDs)

            # update the actual province objects
            for pID in pIDs:
                assert pID in self.provinces
                assert pID in self.provinceHistories

                province = self.provinces[pID]
                event = self.provinceHistories[pID][self.date]

                if history.CONTROLLER in event:
                    province.controller = event[history.CONTROLLER]

                if history.OWNER in event:
                    province.owner = event[history.OWNER]
        
        self.redraw(dirty)
