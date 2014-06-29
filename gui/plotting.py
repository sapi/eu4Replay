import matplotlib
matplotlib.interactive(False)
matplotlib.use('WXAgg')

from matplotlib.backends.backend_wxagg import FigureCanvasWxAgg
from matplotlib.figure import Figure

from datetime import datetime
import os
import wx


class pnlPlot(wx.Panel):
    def __init__(self, parent, colour=None, dpi=None, **kwargs):
        wx.Panel.__init__(self, parent, **kwargs)
        self.parent = parent

        # Matplotlib setup
        self.figure = Figure(None, dpi)
        self.canvas = FigureCanvasWxAgg(self, -1, self.figure)
        
        self.SetColour(colour)

        self._SetSize()

        self._flResize = False

        # Event bindings
        self.Bind(wx.EVT_IDLE, self._onIdle)
        self.Bind(wx.EVT_SIZE, self._onSize)

        # Plotting data
        self._plotData = []
        self._plotArgs = {}

    def _onSize(self, evt):
        self._flResize = True
        evt.Skip()

    def _onIdle(self, evt):
        if self._flResize:
            self._SetSize()
            self._flResize = False

    def _SetSize(self):
        pixels = tuple(self.GetSize())
        self.SetSize(pixels)
        self.canvas.SetSize(pixels)
        self.figure.set_size_inches(float(pixels[0])/self.figure.get_dpi(),
                                    float(pixels[1])/self.figure.get_dpi())

    def SetColour(self, rgbtuple=None):
        if rgbtuple is None:
            rgbtuple = wx.SystemSettings.GetColour(wx.SYS_COLOUR_BTNFACE).Get()

        clr = [c/255. for c in rgbtuple]
        self.figure.set_facecolor(clr)
        self.figure.set_edgecolor(clr)
        self.canvas.SetBackgroundColour(wx.Colour(*rgbtuple))

    def plot(self, plotForSave=False):
        if not hasattr(self, 'subplot'):
            self.subplot = self.figure.add_subplot(111)

        self.subplot.clear()

        data = self.plotData()
        if not data:
            self.canvas.draw() # show clear()
            return

        if not plotForSave:
            self._SetSize()

        fontsize = self.getPlotArg('fontsize')
        if fontsize is None:
            fontsize = 10

        colours = self.getPlotArg('colours')
        if colours is None or len(colours) == 0:
            colours = ['b', 'g', 'r', 'c', 'm', 'y', 'k']
        
        ## Call down to child
        self._plot(data, colours, fontsize)
        ##

        ylabel = self.getPlotArg('ylabel')
        if ylabel is not None:
            self.subplot.set_ylabel(ylabel, fontsize=fontsize)

        title = self.getPlotArg('title')
        if title is not None:
            self.subplot.set_title(title, fontsize=fontsize)

        self.canvas.draw()
    
    def plotData(self):
        return self._plotData

    def setPlotData(self, data):
        self._plotData = data

    def plotArgs(self):
        return self._plotArgs

    def addPlotArgs(self, **kwargs):
        for k,v in kwargs.iteritems():
            self._plotArgs[k] = v

    def getPlotArg(self, arg):
        return self.plotArgs().get(arg, None)

    def setPlotArgs(self, **kwargs):
        self._plotArgs = kwargs

    def removePlotArg(self, arg):
        if arg in self._plotArgs:
            del self._plotArgs[arg]
    
    def setMotionCallback(self, f):
        self.canvas.mpl_connect('motion_notify_event', f)


class pnlImagePlot(pnlPlot):
    def _plot(self, data, colours, fontsize):
        # we put it in a list to deal with the truth value issue
        # fix this up later
        img = data[0]
        self.subplot.imshow(img)

        hideAxes = self.getPlotArg('hideAxes')
        if hideAxes is not None and hideAxes:
            self.subplot.set_xticks([])
            self.subplot.set_yticks([])

        self.subplot.set_position([0, 0, 1, 1])
