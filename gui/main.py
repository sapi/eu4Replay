# Copyright Sean Purdon 2014
# All Rights Reserved

import wx

from viewer import frmEU4Viewer

# explicit imports to keep py2exe happy seem to be required on Windows
try:
    from scipy.special import _ufuncs_cxx
except ImportError:
    pass
from scipy import linalg


class App(wx.App):
    def OnInit(self):
        self.frmMain = frmEU4Viewer(self, size=(800,600))
        self.frmMain.Show()

        return True


def setup():
    app = App()

    return app
