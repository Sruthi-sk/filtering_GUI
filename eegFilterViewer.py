# -*- coding: utf-8 -*-
"""
Created on Tue Oct 18 12:59:18 2022

_______________________________________________________________________________

EEG waveform viewer like EDF browser
Widgets: Bandpass filter - low and high freq, Order of filter, Window Size
Data: Sine wave (theta, alpha), recorded data
EDF browser - min filter order is 2

To Do:
(Features left to add)
- 2 arrows like mne - move eeg left and right
- Sine wave alternate to recorded data - button to generate synthetic data? 
    (The plot fn can check flag to see if user wants synthetic data)
- Add more filters
- Add zooming in capability
_______________________________________________________________________________

"""

import time
import wx

import os
import pyedflib
import numpy as np
# import matplotlib.pyplot as plt
from matplotlib.figure import Figure
from matplotlib.backends.backend_wxagg import FigureCanvasWxAgg as FigureCanvas
# from matplotlib.backends.backend_wx import NavigationToolbar2Wx

# from brainflow.board_shim import BoardShim, BrainFlowInputParams, LogLevels, BoardIds
from brainflow.data_filter import DataFilter, FilterTypes, DetrendOperations 
import mne

mainfolder = './eeg_test/'
defaultfile = "./eeg_synthetic_data.edf"
os.chdir(mainfolder)

class guiLog:
    
    def WriteText(string):
        print(string)
    
    def write(string):
        print(string)

app = wx.App(False)
#%%  file dialog  -----------------------------------------------------------------------

# to pre-establish a file filter 
wildcard = "EDF file (*.edf)|*.edf|"     \
           "All files (*.*)|*.*"
           
DEBUG = 1

class CanvasPanel(wx.Panel):
    def __init__(self, parent):
        if DEBUG:
            print("In Canvas init")
        wx.Panel.__init__(self, parent)
        self.panel_manager = parent
        self.figure = Figure() #figsize=(5,3)
        self.axes = self.figure.add_subplot(111)
        self.canvas = FigureCanvas(self, -1, self.figure)
        
        drawBtn = wx.Button(self, label='Plot raw data ')
        self.Bind(wx.EVT_BUTTON, self.draw, drawBtn)
        # self.draw()
        drawFilteredBtn = wx.Button(self, label='Plot with Brainflow filter ')
        self.Bind(wx.EVT_BUTTON, self.drawFiltered, drawFilteredBtn)
        
        drawFilteredFIRBtn = wx.Button(self, label='Plot with mne FIR filter ')
        self.Bind(wx.EVT_BUTTON, self.drawFilteredmneFIR, drawFilteredFIRBtn )
        drawFilteredIIRBtn = wx.Button(self, label='Plot with mne IIR filter ')
        self.Bind(wx.EVT_BUTTON, self.drawFilteredmneIIR, drawFilteredIIRBtn)
        
        claBtn = wx.Button(self, label='Clear plot ')
        self.Bind(wx.EVT_BUTTON, self.drawclear, claBtn)
        
        # sizer = wx.BoxSizer(wx.VERTICAL)
        # sizer.Add(drawBtn, 0, wx.ALL | wx.CENTER, 5) 
        # sizer.Add(drawFilteredBtn, 0, wx.ALL | wx.CENTER, 5)
        # sizer.Add(claBtn, 0, wx.ALL | wx.CENTER, 5) 
        # sizer.Add(self.canvas, 1, wx.LEFT | wx.TOP | wx.GROW)
        
        flexsizer = wx.FlexGridSizer(cols = 1, hgap = 3, vgap = 1)
        flexsizer.AddMany([ (drawBtn, 1, wx.EXPAND), (drawFilteredBtn, 1, wx.EXPAND), 
                           (drawFilteredFIRBtn, 1, wx.EXPAND),
                           (drawFilteredIIRBtn, 1, wx.EXPAND), (claBtn, 1, wx.EXPAND)
                           ])
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(flexsizer, flag=wx.ALL | wx.CENTER , border=1)
        sizer.Add(self.canvas, 1, wx.LEFT | wx.TOP | wx.GROW) 
        self.SetSizer(sizer)
        self.Fit()
        
        self.SetSizer(sizer)
        self.Fit()

    def getparams(self):
        path = self.panel_manager.upP.filepath
        print(path)
        try:
            f = pyedflib.EdfReader(path)
            print(f.getHeader())
            sf=f.getSampleFrequency(chn=4)
            n_signals = f.signals_in_file
            # signal_labels = f.getSignalLabels()
            sigbufs = np.zeros((n_signals, f.getNSamples()[0]))
            for i in np.arange(n_signals):
                sigbufs[i, :] = f.readSignal(i)
            f._close()
            
            channel = self.panel_manager.upP.chan_selected.GetValue()
            win_sec = self.panel_manager.upP.window_size.GetValue()
            if DEBUG:
                print("Channel: ",channel," , Window size: ",win_sec)
            if not channel.isnumeric() or int(channel) not in np.arange(0,16) \
                or not win_sec.isnumeric() or int(win_sec) not in np.arange(1,f.file_duration):
                wx.MessageBox("Check if channel number is correct( Synthetic data channels: 0-16) \
                              or if you have entered window size > {} (file duration):/"
                              .format(f.file_duration),"Error",
                              wx.OK|wx.ICON_INFORMATION)
                rawdata = None
                print("error")
            else:
                win_sec = int(win_sec)
                raw_data = sigbufs[int(channel),: int(win_sec*sf)]
                return raw_data,int(sf)
            return None,None
        except:
            wx.MessageBox("Select a file!","Error",
                          wx.OK|wx.ICON_INFORMATION)
            
    def draw(self,evt):
        if DEBUG:
            print("Drawing canvas")
        raw_data,sf = self.getparams()
        self.axes.plot(raw_data)
        self.canvas.draw()
        
    def drawclear(self,evt):
        if DEBUG:
            print("Drawing canvas")
        self.axes.clear()
        self.canvas.draw()

    def drawFiltered(self,evt):
        if DEBUG:
            print("Drawing canvas filtered")
        raw_data,sf = self.getparams()
        filterOrder = int(self.panel_manager.upP.bandorder.GetValue())
        filterLow = int(self.panel_manager.upP.bandlow.GetValue())
        filterHigh = int(self.panel_manager.upP.bandhigh.GetValue())
        print(sf,filterOrder,filterLow,filterHigh,type(filterOrder))
        filter_data = raw_data.copy()
        
        #Brainflow filters - buttreworth, chebyshev - IIR filters
        DataFilter.detrend(filter_data, DetrendOperations.CONSTANT.value)
        # DataFilter.perform_bandstop(filter_data, sf, 48, 50, 2,FilterTypes.BUTTERWORTH.value, 0)
        DataFilter.perform_bandpass(filter_data, sf, filterLow, filterHigh, filterOrder,
                                    FilterTypes.BUTTERWORTH.value, 0)
        
        self.axes.plot(filter_data)
        self.canvas.draw()

    def drawFilteredmneFIR(self,evt):
        if DEBUG:
            print("Drawing canvas filtered")
        raw_data,sf = self.getparams()
        filterOrder = int(self.panel_manager.upP.bandorder.GetValue())
        filterLow = int(self.panel_manager.upP.bandlow.GetValue())
        filterHigh = int(self.panel_manager.upP.bandhigh.GetValue())
        print(sf,filterOrder,filterLow,filterHigh,type(filterOrder))
        filter_data = raw_data.copy()
        
        # iir_params = dict(order=filterOrder, ftype='butter', output='sos')
        filter_data = mne.filter.filter_data(filter_data,  sfreq= sf, l_freq = filterLow, h_freq = filterHigh, 
                               filter_length='auto', method='fir', iir_params=None, copy=True, 
                               phase='zero', fir_window='hamming', fir_design='firwin', pad='reflect_limited', 
                               verbose=None)
        
        self.axes.plot(filter_data)
        self.canvas.draw()
        
    def drawFilteredmneIIR(self,evt):
        if DEBUG:
            print("Drawing canvas filtered")
        raw_data,sf = self.getparams()
        filterOrder = int(self.panel_manager.upP.bandorder.GetValue())
        filterLow = int(self.panel_manager.upP.bandlow.GetValue())
        filterHigh = int(self.panel_manager.upP.bandhigh.GetValue())
        print(sf,filterOrder,filterLow,filterHigh,type(filterOrder))
        filter_data = raw_data.copy()
        
        iir_params = dict(order=filterOrder, ftype='butter', output='sos')
        filter_data = mne.filter.filter_data(filter_data,  sfreq= sf, l_freq = filterLow, h_freq = filterHigh, 
                               filter_length='auto', method='iir', iir_params=iir_params, copy=True, 
                               phase='zero', fir_window='hamming', fir_design='firwin', pad='reflect_limited', 
                               verbose=None)
        
        self.axes.plot(filter_data)
        self.canvas.draw()
            
class FileOpenPanel(wx.Panel):
    def __init__(self, parent, log):
        self.log = log
        self.panel_manager = parent
        wx.Panel.__init__(self, parent, -1)

        bOpen = wx.Button(self, -1, "Open File", (50,50))
        self.Bind(wx.EVT_BUTTON, self.OnOpenFile, bOpen)
        
        self.filechosen = wx.StaticText(self, label="Undefined", style = wx.ALIGN_CENTER)
        self.filepath = ""
        
        chan_selected_label = wx.StaticText(self, label="Channel :")
        self.chan_selected =  wx.TextCtrl(self,value='5')
        window_size_label = wx.StaticText(self, label="Window size :")
        self.window_size =  wx.TextCtrl(self,value='2')        
        # hbox1 = wx.BoxSizer(wx.HORIZONTAL)
        # hbox1.Add(channelstatic, flag=wx.RIGHT, border=8)  
        # hbox1.Add(self.chan_selected, proportion=1)          
        
        bandlow_label = wx.StaticText(self, label="Bandpass Freq Low :")
        self.bandlow =  wx.TextCtrl(self,value='4')
        bandhigh_label = wx.StaticText(self, label="Bandpass Freq High :")
        self.bandhigh =  wx.TextCtrl(self,value='8')
        bandorder_label = wx.StaticText(self, label="Bandpass Filter order :")
        self.bandorder =  wx.TextCtrl(self,value='2')
        
        flexsizer = wx.FlexGridSizer(cols = 2)
        flexsizer.AddMany([ chan_selected_label, self.chan_selected , 
                           window_size_label, self.window_size,
                            bandlow_label, self.bandlow, bandhigh_label, self.bandhigh, 
                           bandorder_label, self.bandorder 
                           ])
        
        self.bPlot = wx.Button(self, -1, "Enable plotting panel", (50,50))
        self.Bind(wx.EVT_BUTTON, self.OnEnablePlot, self.bPlot)
        
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(bOpen, 0, wx.ALL | wx.CENTER, 5)  
        sizer.Add(self.filechosen, 0, wx.ALL | wx.CENTER , 5)  
        # sizer.Add(hbox1, flag=wx.ALL | wx.CENTER, border=10) #wx.EXPAND|wx.LEFT|wx.RIGHT|wx.TOP
        sizer.Add(flexsizer, flag=wx.ALL | wx.CENTER, border=10)
        sizer.Add((-1, 10))
        sizer.Add(self.bPlot, 0, wx.ALL | wx.CENTER, 5) 
        self.SetSizer(sizer)
        self.Fit()

    def OnOpenFile(self, evt):
        self.log.WriteText("CWD: %s\n" % os.getcwd())

        dlg = wx.FileDialog(
            self, message="Choose a file",
            defaultDir=os.getcwd(),
            defaultFile=defaultfile,
            wildcard=wildcard,
            style=wx.FD_OPEN | #wx.FD_MULTIPLE |
                  wx.FD_CHANGE_DIR | wx.FD_FILE_MUST_EXIST |
                  wx.FD_PREVIEW
            )

        # Show the dialog and retrieve the user response. If it is the OK response,
        # process the data.
        # print(dir(dlg))
        if dlg.ShowModal() == wx.ID_OK:
            # This returns a Python list of files that were selected.
            paths = dlg.GetPath()
            print(paths)
            self.filepath = paths
            fname = os.path.split(paths)[1]
            
            self.filechosen.SetLabel(fname)
            sizer = self.filechosen.GetContainingSizer()
            sizer.Layout() #call Layout to recalculate the object positions
            
            
        dlg.Destroy()
        
    def OnEnablePlot(self,evt):
        self.log.WriteText("Canvas panel enabled")
        self.panel_manager.downP.Show()
        self.bPlot.Disable()


#%% #----------------------------------------------------------------------  

class testFrame(wx.Frame):    
    def __init__(self, title=None,parent=None):
        wx.Frame.__init__(self,parent= parent, title='Effect of Data Filters', size=(700, 1000)) #super().__init__
        self.Centre()
        self.log = guiLog
        
        splitter = wx.SplitterWindow(self)
        splitter.upP = FileOpenPanel(splitter,self.log) 
        splitter.downP = CanvasPanel(splitter)
        # split the window
        splitter.SplitHorizontally(splitter.upP, splitter.downP,300)
        splitter.SetMinimumPaneSize(20)
        splitter.downP.Hide()
        
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(splitter, 1, wx.EXPAND)
        self.SetSizer(sizer)
        
        # self.panel = MainPanel(self,self.log)      
        self.Show()

frame = testFrame()
app.MainLoop()  

#%%
del app
app = wx.App(False)
#%%


#---------------------------------------------------------------------------
#%%

    
