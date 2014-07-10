# Copyright Sean Purdon 2014
# All Rights Reserved


from datetime import datetime, timedelta
import numpy as np

import model.settings as settings
import parsers.history as history


def get_controller_mask_gen_for_width(width):
    # diagonal stripes based on array indices
    return lambda i,j,k: (i + j)%(2*width) < width


class EU4Map(object):
    LAKE_COLOUR = (50, 50, 150)
    SEA_COLOUR = (0, 0, 100)
    UNCOLONISED_COLOUR = (200, 200, 200)

    DELTA_DAY = 'DELTA_DAY'
    DELTA_MONTH = 'DELTA_MONTH'
    DELTA_YEAR = 'DELTA_YEAR'
    DELTA_DECADE = 'DELTA_DECADE'

    STRIPE_WIDTH = 5

    def __init__(self, img, provinces, countries, mapObject):
        self.img = img
        self.provinces = provinces
        self.countries = countries
        self.mapObject = mapObject

        self.countryHistories = {}
        self.provinceHistories = {}
        self.datesWithEvents = {}

        # controller mask
        fMask = get_controller_mask_gen_for_width(EU4Map.STRIPE_WIDTH)
        self.controllerMask = np.fromfunction(fMask, self.img.shape)

        # build original owners and controllers, so they can be restored
        self.dateCache = {}

        self.dateCache[settings.start_date] = {
                p.id: (p.controller, p.owner) for p in self.provinces.values()
            }

        self.reset()

    def loadSave(self, provinceHistories, countryHistories, datesWithEvents):
        self.countryHistories = countryHistories
        self.provinceHistories = provinceHistories
        self.datesWithEvents = datesWithEvents

        # clear everything in the cache except the start date
        self.dateCache = {
                settings.start_date: self.dateCache[settings.start_date]
            }

        self.reset()

    def updateProvincesForDate(self, date):
        assert date in self.dateCache

        dirty = set()

        for pID,(controller,owner) in self.dateCache[date].iteritems():
            province = self.provinces[pID]

            if province.controller == controller \
                    and province.owner == owner:
                continue

            province.controller = controller
            province.owner = owner

            dirty.add(pID)

        return dirty

    def reset(self):
        # reset the date
        self.date = settings.start_date

        # reset province owners
        self.updateProvincesForDate(settings.start_date)

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
            owner = self.countries[province.owner]
            assert owner.col, '%s has no colour set'%owner

            ownerCol = owner.col
        else:
            ownerCol = EU4Map.UNCOLONISED_COLOUR

        # work out the controller
        if province.controller in (None, '---', province.owner):
            controllerCol = ownerCol
        else:
            controller = self.countries[province.controller]
            assert controller.col, '%s has no colour set'%controller
            
            controllerCol = controller.col

        assert province.maskIdxs is not None, '%s has no mask'%province
        self.img[province.maskIdxs] = np.where(
                self.controllerMask[province.maskIdxs], controllerCol, ownerCol)

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

        self.renderAtDate(targetDate)

    def renderAtDate(self, targetDate):
        # first, find the first date we have cached before the target date
        dayDelta = timedelta(days=1)
        date = targetDate

        # before doing this, check that such a date exists
        earliest = min(self.dateCache)
        
        if date <= earliest:
            date = earliest
        else:
            while date not in self.dateCache:
                date -= dayDelta

        # now, set all provinces back to the target date
        dirty = self.updateProvincesForDate(date)

        # finally, work out what provinces will need to be redrawn in order
        # to reflect the state of the world at the target date
        while date < targetDate:
            date += dayDelta

            # update our set of dirty provinces
            if date not in self.datesWithEvents:
                continue
            
            # either the province has changed hands
            if history.PROVINCES in self.datesWithEvents[date]:
                # grab the dirty pIDs
                pIDs = self.datesWithEvents[date][history.PROVINCES]
                dirty = dirty.union(pIDs)

                # update the actual province objects
                for pID in pIDs:
                    assert pID in self.provinces
                    assert pID in self.provinceHistories
                    assert date in self.provinceHistories[pID]

                    province = self.provinces[pID]
                    event = self.provinceHistories[pID][date]

                    if history.CONTROLLER in event:
                        province.controller = event[history.CONTROLLER]

                    if history.OWNER in event:
                        province.owner = event[history.OWNER]

            # or something has happened to the country
            if history.COUNTRIES in self.datesWithEvents[date]:
                # grab the concerned tags
                tags = self.datesWithEvents[date][history.COUNTRIES]

                # process the events
                for tag in tags:
                    assert tag in self.countries
                    assert tag in self.countryHistories

                    country = self.countries[tag]
                    event = self.countryHistories[tag][date]

                    # if we have a tag change, we must set:
                    #  * the owner of all provinces owned by the old tag; and
                    #  * the controller of all provinces controlled by the
                    #    old tag
                    # to the new tag
                    if event[history.EVENT_TYPE] == history.EVENT_TAG_CHANGE:
                        oldTag = event[history.SOURCE_TAG]

                        ownedPIDs = [pID for pID,p in self.provinces.iteritems()
                                if p.owner == oldTag]

                        for pID in ownedPIDs:
                            province = self.provinces[pID]
                            province.owner = tag

                        controlledPIDs = [pID for pID,p
                                in self.provinces.iteritems()
                                if p.controller == oldTag]

                        for pID in controlledPIDs:
                            province = self.provinces[pID]
                            province.controller = tag

                        # update the dirty provinces
                        pIDs = set(ownedPIDs).union(controlledPIDs)
                        dirty = dirty.union(pIDs)

            # update the date cache so we can quickly get back to this date
            self.dateCache[date] = {
                    p.id: (p.controller, p.owner) 
                        for p in self.provinces.values()
                }
        
        # redraw only changed provinces
        self.redraw(dirty)
        
        # set date
        self.date = date
