# Copyright Sean Purdon 2014
# All Rights Reserved

import wx

from model.display import EU4Map
from model.setup import setup_data
from parsers.history import build_history
from parsers.saves import parse_provinces_data

from plotting import pnlImagePlot


class App(wx.App):
    def OnInit(self):
        self.frmMain = frmEU4Viewer(self)
        self.frmMain.Show()

        return True


class frmEU4Viewer(wx.Frame):
    def __init__(self, parent):
        wx.Frame.__init__(self, None)

        self.pnl = wx.Panel(self)

        self.vbx = wx.BoxSizer(wx.VERTICAL)
        self.pnl.SetSizer(self.vbx)

        self.pnlMap = pnlImagePlot(self.pnl)
        self.vbx.Add(self.pnlMap, proportion=1, flag=wx.EXPAND)

        hbxControls = wx.BoxSizer(wx.HORIZONTAL)
        self.vbx.Add(hbxControls, proportion=0, flag=0)

        btnTick = wx.Button(self.pnl, label='Tick')
        hbxControls.Add(btnTick, proportion=0, flag=0)

        btnTick.Bind(wx.EVT_BUTTON, self.evt_btnTick)

    def setMap(self, eu4Map):
        self.map = eu4Map

        self.pnlMap.setPlotData([eu4Map.img])
        self.pnlMap.addPlotArgs(hideAxes=True)

        self.pnlMap.plot()

    def evt_btnTick(self, evt):
        self.tickDecade()

    def tickDecade(self):
        self.map.tick(EU4Map.DELTA_DECADE)
        self.pnlMap.plot()


def setup():
    app = App()

    return app, app.frmMain


if __name__ == '__main__':
    app, viewer = setup()

    countries, provinces, img, mapObject = setup_data('/mnt/hgfs/eu4')
    save = parse_provinces_data('data/autosave.eu4')
    provinceHistories, datesWithEvents = build_history(save, provinces)

    eu4Map = EU4Map(img, provinces, countries, mapObject)
    eu4Map.loadSave(provinceHistories, datesWithEvents)

    viewer.setMap(eu4Map)

    app.MainLoop()
