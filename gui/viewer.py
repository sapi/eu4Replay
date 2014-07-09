# Copyright Sean Purdon 2014
# All Rights Reserved

import calendar
from datetime import datetime
import os
from threading import Thread
import wx

from model.display import EU4Map
import model.provinces as provinces
import model.settings as settings
from model.setup import setup_countries, setup_map, setup_provinces
from parsers.provinces import parse_province_original_owners
from parsers.history import build_history
from parsers.saves import parse_save

from helpers import PeriodicThread
from plotting import pnlImagePlot


class frmEU4Viewer(wx.Frame):
    # menu constants
    MENU_FILE_MAP = 110
    MENU_FILE_MAP_LOAD = 111
    MENU_FILE_MAP_BUILD = 112

    MENU_FILE_SAVES = 120
    MENU_FILE_SAVES_LOAD = 121
    MENU_FILE_SAVES_QUICKLOAD = 122

    def __init__(self, parent, **kwargs):
        wx.Frame.__init__(self, None, title='EU4 Replay Viewer', **kwargs)

        #### GUI Elements
        # Base panel
        # (this gives an OS-independent background colour)
        self.pnl = wx.Panel(self)

        self.vbx = wx.BoxSizer(wx.VERTICAL)
        self.pnl.SetSizer(self.vbx)

        # Map panel
        # we haven't yet given this any data to display (this is done when
        # the map is set)
        self.pnlMap = pnlImagePlot(self.pnl)
        self.vbx.Add(self.pnlMap, proportion=1, flag=wx.EXPAND)

        # Bottom stuff
        vbxBottom = wx.BoxSizer(wx.VERTICAL)
        self.vbx.Add(vbxBottom, proportion=0, flag=wx.EXPAND)

        # Sliders
        vbxSliders = wx.BoxSizer(wx.VERTICAL)
        vbxBottom.Add(vbxSliders, proportion=1, flag=wx.EXPAND)

        date = settings.start_date
        d,m,y = date.day, date.month, date.year

        # -- Day
        hbxSliderDay = wx.BoxSizer(wx.HORIZONTAL)
        vbxSliders.Add(hbxSliderDay, proportion=1, flag=wx.EXPAND)

        hbxSliderDay.AddSpacer(5)

        lblDay = wx.StaticText(self.pnl, label='  Day')
        hbxSliderDay.Add(lblDay, proportion=0, flag=wx.CENTER)

        hbxSliderDay.AddSpacer(5)

        self.sliderDay = wx.Slider(self.pnl, value=d, minValue=1, maxValue=31,
                style=wx.SL_HORIZONTAL|wx.SL_AUTOTICKS|wx.SL_LABELS)
        self.sliderDay.SetTickFreq(1)
        hbxSliderDay.Add(self.sliderDay, proportion=1, flag=wx.EXPAND)

        hbxSliderDay.AddSpacer(5)

        # -- Month
        hbxSliderMonth = wx.BoxSizer(wx.HORIZONTAL)
        vbxSliders.Add(hbxSliderMonth, proportion=1, flag=wx.EXPAND)

        hbxSliderMonth.AddSpacer(5)

        lblMonth = wx.StaticText(self.pnl, label='Month')
        hbxSliderMonth.Add(lblMonth, proportion=0, flag=wx.CENTER)

        hbxSliderMonth.AddSpacer(5)

        self.sliderMonth = wx.Slider(self.pnl, value=m, minValue=1, maxValue=12,
                style=wx.SL_HORIZONTAL|wx.SL_AUTOTICKS|wx.SL_LABELS)
        self.sliderMonth.SetTickFreq(1)
        hbxSliderMonth.Add(self.sliderMonth, proportion=1, flag=wx.EXPAND)

        hbxSliderMonth.AddSpacer(5)

        # -- Year
        hbxSliderYear = wx.BoxSizer(wx.HORIZONTAL)
        vbxSliders.Add(hbxSliderYear, proportion=1, flag=wx.EXPAND)

        hbxSliderYear.AddSpacer(5)

        lblYear = wx.StaticText(self.pnl, label=' Year')
        hbxSliderYear.Add(lblYear, proportion=0, flag=wx.CENTER)

        hbxSliderYear.AddSpacer(5)

        self.sliderYear = wx.Slider(self.pnl, value=y, minValue=y,
                maxValue=settings.end_date.year,
                style=wx.SL_HORIZONTAL|wx.SL_AUTOTICKS|wx.SL_LABELS)
        self.sliderYear.SetTickFreq(25)
        hbxSliderYear.Add(self.sliderYear, proportion=1, flag=wx.EXPAND)

        hbxSliderYear.AddSpacer(5)

        # -- (Bindings)
        self.sliderDay.Bind(wx.EVT_SLIDER, self.evt_slider)
        self.sliderMonth.Bind(wx.EVT_SLIDER, self.evt_slider)
        self.sliderYear.Bind(wx.EVT_SLIDER, self.evt_slider)

        # -- (Fonts)
        font = wx.Font(
                lblDay.GetFont().GetPointSize(),
                wx.FONTFAMILY_TELETYPE,
                wx.FONTSTYLE_NORMAL,
                wx.FONTWEIGHT_NORMAL
            )

        lblDay.SetFont(font)
        lblMonth.SetFont(font)
        lblYear.SetFont(font)

        # -- (Disable)
        self.sliderDay.Enable(False)
        self.sliderMonth.Enable(False)
        self.sliderYear.Enable(False)

        # Control panel
        vbxBottom.AddSpacer(5)

        hbxControls = wx.BoxSizer(wx.HORIZONTAL)
        vbxBottom.Add(hbxControls, proportion=0, flag=wx.EXPAND)

        hbxControls.AddSpacer(5)

        self.lblCurrentDate = wx.StaticText(self.pnl, label='Current Date: ')
        hbxControls.Add(self.lblCurrentDate, proportion=0, flag=0)

        hbxControls.AddSpacer(25)

        self.lblStatus = wx.StaticText(self.pnl)
        hbxControls.Add(self.lblStatus, proportion=0, flag=0)

        vbxBottom.AddSpacer(5)

        #### Menus
        ## Menubar object
        menubar = wx.MenuBar()
        self.SetMenuBar(menubar)

        ## File menu
        menuFile = wx.Menu()
        menubar.Append(menuFile, '&File')

        # Map submenu
        menuFileMap = wx.Menu()
        menuFile.AppendMenu(self.MENU_FILE_MAP, '&Map', menuFileMap)

        menuFileMap.Append(self.MENU_FILE_MAP_LOAD, '&Load Provinces File')
        self.Bind(wx.EVT_MENU, self.loadProvincesFile,
                id=self.MENU_FILE_MAP_LOAD)

        menuFileMap.Append(self.MENU_FILE_MAP_BUILD, '&Build Provinces File')
        self.Bind(wx.EVT_MENU, self.buildProvincesFile,
                id=self.MENU_FILE_MAP_BUILD)

        # Saves submenu
        menuFileSaves = wx.Menu()
        menuFile.AppendMenu(self.MENU_FILE_SAVES, '&Saves', menuFileSaves)

        menuFileSaves.Append(self.MENU_FILE_SAVES_LOAD, '&Load Save File')
        self.Bind(wx.EVT_MENU, self.loadSave, id=self.MENU_FILE_SAVES_LOAD)

        #### Instance Variables
        ## Quick-to-load properties
        self.img, self.mapObject = setup_map(settings.eu4_directory)        
        self.countries = setup_countries(settings.eu4_directory)

        ## Properties which require user intervention
        self.provinces = None
        self.save = None
        self._map = None

        #### Further Initialisation
        ## Date label
        self.updateDateLabel(settings.start_date)
        self.updateStatus()

    ## Menu Event Callbacks
    def _promptForPath(self, message, wildcard, style):
        # show the file dialog, and have the user select a path
        dlg = wx.FileDialog(self, message=message, wildcard=wildcard,
                style=style)

        if dlg.ShowModal() != wx.ID_OK:
            dlg.Destroy()
            return

        dlg.Destroy()

        paths = dlg.GetPaths()
        assert len(paths) == 1

        path = paths[0]
        return path

    def loadProvincesFile(self, evt):
        path = self._promptForPath(
                message='Select the provinces file',
                wildcard='Provinces files (*.provinces)|*.provinces',
                style=wx.FD_OPEN
            )

        if path is None:
            return
            
        # prepare the progress dialog
        self.dlgProgress = wx.ProgressDialog(
                title='Loading provinces file',
                message='Parsing provinces data...',
                style=wx.PD_APP_MODAL
            )

        # run asynchronously
        thread = Thread(target=self._loadProvincesFile, args=(path,))
        thread.start()

    def _loadProvincesFile(self, path):
        periodicThread = PeriodicThread(
                target=lambda : wx.CallAfter(self.dlgProgress.Pulse),
                period=0.1,
            )
        periodicThread.start()

        # load the cached data
        self.provinces = provinces.load_from_file(path)

        # load the original owners
        wx.CallAfter(self.dlgProgress.UpdatePulse,
                'Finding original province owners...')

        historyDir = os.path.join(settings.eu4_directory, 'history')
        parse_province_original_owners(historyDir, self.provinces)

        periodicThread.stop()
        wx.CallAfter(self.dlgProgress.Destroy)

        wx.CallAfter(self._createMap)

    def buildProvincesFile(self, evt):
        path = self._promptForPath(
                message='Choose where to save the provinces file',
                wildcard='Provinces files (*.provinces)|*.provinces',
                style=wx.FD_SAVE
            )

        if path is None:
            return

        # prepare the progress dialog
        self.dlgProgress = wx.ProgressDialog(
                title='Building provinces file',
                message='Generating provinces data...',
                style=wx.PD_APP_MODAL
            )

        # run asynchronously
        thread = Thread(target=self._buildProvincesFile, args=(path,))
        thread.start()

    def _buildProvincesFile(self, path):
        periodicThread = PeriodicThread(
                target=lambda : wx.CallAfter(self.dlgProgress.Pulse),
                period=0.1,
            )
        periodicThread.start()

        # generate the provinces data
        # this will take a long time
        self.provinces = setup_provinces(settings.eu4_directory)

        # save the file to disk
        wx.CallAfter(self.dlgProgress.UpdatePulse, 'Writing file...')
        provinces.write_to_file(path, self.provinces)

        # load the original owners
        wx.CallAfter(self.dlgProgress.UpdatePulse,
                'Finding original province owners...')

        historyDir = os.path.join(settings.eu4_directory, 'history')
        parse_province_original_owners(historyDir, self.provinces)

        periodicThread.stop()
        wx.CallAfter(self.dlgProgress.Destroy)

        wx.CallAfter(self._createMap)

    def loadSave(self, evt):
        path = self._promptForPath(
                message='Select the save file',
                wildcard='EU4 Save files (*.eu4)|*.eu4',
                style=wx.FD_OPEN
            )

        if path is None:
            return
            
        # prepare the progress dialog
        self.dlgProgress = wx.ProgressDialog(
                title='Loading save file',
                message='Parsing save data...',
                style=wx.PD_APP_MODAL
            )

        # run asynchronously
        thread = Thread(target=self._loadSaveFile, args=(path,))
        thread.start()

    def _loadSaveFile(self, path):
        periodicThread = PeriodicThread(
                target=lambda : wx.CallAfter(self.dlgProgress.Pulse),
                period=0.1,
            )
        periodicThread.start()

        # load the save
        self.save = parse_save(path)

        # parse the save for province histories
        wx.CallAfter(self.dlgProgress.UpdatePulse,
                'Determining province histories...')

        assert self.provinces is not None # should test for this earlier
        provinceHistories, countryHistories, datesWithEvents \
                = build_history(self.save, self.provinces)

        periodicThread.stop()
        wx.CallAfter(self.dlgProgress.Destroy)

        wx.CallAfter(self._updateMapWithSave, provinceHistories,
                countryHistories, datesWithEvents)

    @property
    def map(self):
        return self._map

    @map.setter
    def map(self, val):
        self._map = val

        self.pnlMap.setPlotData([val.img])
        self.pnlMap.addPlotArgs(hideAxes=True)

        self.pnlMap.plot()

    def _createMap(self):
        if self.provinces is None:
            return

        assert self.countries is not None
        assert self.img is not None
        assert self.mapObject is not None

        self.map = EU4Map(self.img, self.provinces, self.countries,
                self.mapObject)
        self.updateStatus()

    def _updateMapWithSave(self, provinceHistories, countryHistories,
            datesWithEvents):
        assert self.save is not None
        assert self.map is not None

        self.map.loadSave(provinceHistories, countryHistories, datesWithEvents)
        self.pnlMap.plot()

        self.sliderDay.Enable(True)
        self.sliderMonth.Enable(True)
        self.sliderYear.Enable(True)

        self.updateStatus()

    def evt_slider(self, evt):
        day = self.sliderDay.GetValue()
        month = self.sliderMonth.GetValue()
        year = self.sliderYear.GetValue()

        _,numDays = calendar.monthrange(year, month)

        if day > numDays:
            day = numDays

        targetDate = datetime(year, month, day)

        self.updateDateLabel(targetDate)

        # if we have no map, or no save, we can't do anything more
        if self.map is None or self.save is None:
            return

        self.map.renderAtDate(targetDate)
        self.pnlMap.plot()

    def tickDecade(self):
        self.map.tick(EU4Map.DELTA_DECADE)
        self.pnlMap.plot()

        self.updateDateLabel(self.map.date)
        self.updateStatus()

    def updateDateLabel(self, date):
        dateStr = '%02d %s %04d'%(date.day, 
                settings.month_names[date.month - 1], date.year)
        self.lblCurrentDate.SetLabel('Current Date: %s'%dateStr)

    def updateStatus(self):
        status = []

        if self.provinces is None:
            status.append('No province data loaded')

        if self.save is None:
            status.append('No save loaded')

        self.lblStatus.SetLabel(' | '.join(status) if status else '')
