# Copyright Sean Purdon 2014
# All Rights Reserved

import wx

from model.display import EU4Map
from model.setup import setup_data
from parsers.history import build_history
from parsers.saves import parse_save

from viewer import frmEU4Viewer

# explicit imports to keep py2exe happy
from scipy.special import _ufuncs_cxx
from scipy import linalg


class App(wx.App):
    def OnInit(self):
        self.frmMain = frmEU4Viewer(self, size=(800,600))
        self.frmMain.Show()

        return True


def setup():
    app = App()

    return app
