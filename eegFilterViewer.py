# -*- coding: utf-8 -*-
"""
Created on Tue Oct 18 12:59:18 2022
_______________________________________________________________________________

EEG waveform viewer like EDF browser
Widgets: Bandpass filter - low and high freq, Order of filter, Window Size
Data: Synthetic/ recorded data
EDF browser - min filter order is 2

To Do:
- Try more filters
_______________________________________________________________________________

"""

import time
import wx

import os
import pyedflib
import numpy as np
from matplotlib.figure import Figure
from matplotlib.backends.backend_wxagg \
    import FigureCanvasWxAgg as FigureCanvas, \
    NavigationToolbar2WxAgg as NavigationToolbar
# from brainflow.board_shim import BoardShim, BrainFlowInputParams, LogLevels, BoardIds
from brainflow.data_filter import DataFilter, FilterTypes, DetrendOperations 
import mne

mainfolder = './eeg_test/'
defaultfile = "eeg_synthetic_data.edf"
os.chdir(mainfolder)

class guiLog:
    
    def WriteText(string):
        print(string)
    
    def write(string):
        print(string)

app = wx.App(False)

choices = ['1','2','3']   #channels


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
        self.figure = Figure() #figsize=(5,3) # Figure((5.0, 4.0), dpi=100)
        self.canvas = FigureCanvas(self, -1, self.figure)
        self.axes = self.figure.add_subplot(111)
        self.toolbar = NavigationToolbar(self.canvas)
        
        #for clicking on data
        self.canvas.mpl_connect('pick_event', self.on_pick)
        
        drawBtn = wx.Button(self, label='Plot raw data ', name="raw")
        drawFilteredBtn = wx.Button(self, label='Plot with Brainflow filter ', name="brainflow")
        drawFilteredBrevBtn = wx.Button(self, label='Plot with Brainflow filter - reversed', name="reversedbrainflow")        
        drawFilteredFIRBtn = wx.Button(self, label='Plot with mne FIR filter ', name="mneFIR")
        drawFilteredIIRBtn = wx.Button(self, label='Plot with mne IIR filter ', name="mneIIR")
        
        claBtn = wx.Button(self, label='Clear plot ')
        self.Bind(wx.EVT_BUTTON, self.drawclear, claBtn)
        
        buttons = [drawBtn, drawFilteredBtn, drawFilteredBrevBtn, 
                   drawFilteredFIRBtn, drawFilteredIIRBtn]
        
        sizer = wx.BoxSizer(wx.VERTICAL)
        for button in buttons:
            self.buildButtons(button, sizer)
        sizer.Add(claBtn,  1, wx.ALL | wx.CENTER, 3)     
        # sizer.Add(flexsizer, flag=wx.ALL | wx.CENTER , border=1)
        sizer.Add(self.canvas, 1, wx.LEFT | wx.TOP | wx.GROW) 
        sizer.Add(self.toolbar, 0, wx.EXPAND)
        self.SetSizer(sizer)
        self.Fit()
    
    
    def on_pick(self, event):
        box_points = event.artist.get_bbox().get_points()
        msg = "You've clicked on coords:\n %s" % box_points
        dlg = wx.MessageDialog( self, msg, "Click!",
            wx.OK | wx.ICON_INFORMATION)
        dlg.ShowModal()
        dlg.Destroy()

    def buildButtons(self, btn, sizer):
        """"""
        btn.Bind(wx.EVT_BUTTON, self.getDataandPlot)
        sizer.Add(btn,  1, wx.ALL | wx.CENTER, 2)
        
    def drawclear(self,evt):
        if DEBUG:
            print("Drawing canvas cleared")
        self.axes.clear()
        self.canvas.draw()
     
    def getDataandPlot(self,event):
        
        edf_file = self.panel_manager.upP.filepath
        print(edf_file)
        try:
            header_info = pyedflib.highlevel.read_edf_header(edf_file, read_annotations=False)
            n_signals = len(header_info['channels'])
            sf = int(header_info['SignalHeaders'][0]['sample_frequency'])   
            duration = header_info['Duration']
            print(header_info['equipment']," data with {} channels".format(n_signals))
            print(duration," seconds")
            
            chan_sel = self.panel_manager.upP.chan_selected
            channel = chan_sel.GetString(chan_sel.GetSelection())
            start_sec = self.panel_manager.upP.start_time.GetValue()
            win_sec = self.panel_manager.upP.window_size.GetValue()
            if DEBUG:
                print("Channel: ",channel," , Window size: ",win_sec)
            if not win_sec.isnumeric() or (int(win_sec)+int(start_sec)) not in np.arange(1,duration):
                wx.MessageBox("Check if you have entered window size > {} (file duration):/"
                              .format(duration),"Error",
                              wx.OK|wx.ICON_INFORMATION)
            else:
                if DEBUG:
                    print("Getting data")
                win_sec = int(win_sec)
                start_sec = float(start_sec)
                raw_data_chan = pyedflib.highlevel.read_edf(edf_file, ch_names=channel, digital=False, verbose=False)
                raw_data = raw_data_chan[0][0, int(start_sec*sf): int((start_sec+win_sec)*sf)]
                times = np.linspace(start_sec,start_sec+win_sec,int(sf)*win_sec)
                print(times[0],times[-1])
                filterOrder = int(self.panel_manager.upP.bandorder.GetValue())
                filterLow = int(self.panel_manager.upP.bandlow.GetValue())
                filterHigh = int(self.panel_manager.upP.bandhigh.GetValue())
                if DEBUG:
                    print("Getting data done")
        except:
            wx.MessageBox("Couldn't get data - ensure file and channel are selected","Error",
                          wx.OK|wx.ICON_INFORMATION)
        
        # Check which button was pressed - to filter accordingly
        button = event.GetEventObject().GetName()
        
        match button:
            case 'raw':                      
                    if DEBUG:
                        print("Drawing canvas raw")
                    self.axes.plot(times,raw_data, color='tab:blue', label='raw')
            
            case 'brainflow':               
                    if DEBUG:
                        print("filter: brainflow")
                        print(sf,filterOrder,filterLow,filterHigh,type(filterOrder))
                    filter_data = raw_data.copy()
                    #Brainflow filters - buttreworth, chebyshev - IIR filters
                    # DataFilter.detrend(filter_data, DetrendOperations.CONSTANT.value)
                    # DataFilter.perform_bandstop(filter_data, sf, 48, 50, 2,FilterTypes.BUTTERWORTH.value, 0)
                    DataFilter.perform_bandpass(filter_data, sf, filterLow, filterHigh, filterOrder,
                                                FilterTypes.BUTTERWORTH.value, 0)
                    
                    self.axes.plot(times,filter_data, color='tab:green',label='brainflow')
            
            case 'reversedbrainflow':       
                    if DEBUG:
                        print("filter: brainflow reversed")
                        print(sf,filterOrder,filterLow,filterHigh,type(filterOrder))
                    filter_data = raw_data.copy()
                    # For brainflow filtering (to look similar to mne IIR filter)
                    # - reverse data, then filter, then reverse back and filter
                    filter_data = np.ascontiguousarray(np.flip(filter_data))  #filter_data[::-1]
                    DataFilter.perform_bandpass(filter_data, sf, filterLow, filterHigh, filterOrder,
                                                FilterTypes.BUTTERWORTH.value, 0)
                    filter_data = np.ascontiguousarray(np.flip(filter_data))
                    DataFilter.perform_bandpass(filter_data, sf, filterLow, filterHigh, filterOrder,
                                                FilterTypes.BUTTERWORTH.value, 0)
                    self.axes.plot(times,filter_data, color='tab:red',label='reversedbrainflow')
            
            case 'mneFIR':                  
                    if DEBUG:
                        print("filter: mne FIR")
                        print(sf,filterOrder,filterLow,filterHigh,type(filterOrder))
                    filter_data = raw_data.copy()
                    filter_data = mne.filter.filter_data(filter_data,  sfreq= sf,
                                                     l_freq = filterLow, h_freq = filterHigh, 
                                                     filter_length='auto', method='fir', 
                                                     iir_params=None, copy=True, 
                                                     phase='zero', fir_window='hamming', 
                                                     fir_design='firwin', pad='reflect_limited', 
                                                     verbose=None)
                    self.axes.plot(times,filter_data, color='tab:pink',label='mne FIR')
                    
            case 'mneIIR':                  
                    if DEBUG:
                        print("filter: mne IIR")
                        print(sf,filterOrder,filterLow,filterHigh,type(filterOrder))
                    filter_data = raw_data.copy()
                    iir_params = dict(order=filterOrder, ftype='butter', output='sos')
                    filter_data = mne.filter.filter_data(filter_data,  sfreq= sf, 
                                                    l_freq = filterLow, h_freq = filterHigh, 
                                                    filter_length='auto', method='iir', 
                                                    iir_params=iir_params,copy=True, 
                                                    phase='zero', fir_window='hamming', 
                                                    fir_design='firwin', pad='reflect_limited', 
                                                    verbose=None)
                    self.axes.plot(times,filter_data, color='tab:orange',label='mne IIR')
            case _:
                    pass
        
        self.axes.set_xlabel('time')
        self.axes.set_ylabel('volts')
        self.axes.set_title('Explore EEG filters')
        self.axes.legend(loc='upper right')
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
        # self.chan_selected =  wx.TextCtrl(self,value='5')  #make dropdown instead
        self.chan_selected   = wx.Choice(self, choices = choices)
        
        window_size_label = wx.StaticText(self, label="Window size :")
        self.window_size =  wx.TextCtrl(self,value='2')     
        start_time_label = wx.StaticText(self, label="Start time (in s) :")
        self.start_time =  wx.TextCtrl(self,value='2') 
        # hbox1 = wx.BoxSizer(wx.HORIZONTAL)
        # hbox1.Add(channelstatic, flag=wx.RIGHT, border=8)  
        # hbox1.Add(self.chan_selected, proportion=1)          
        
        bandlow_label = wx.StaticText(self, label="Bandpass Freq Low :")
        self.bandlow =  wx.TextCtrl(self,value='4')
        bandhigh_label = wx.StaticText(self, label="Bandpass Freq High :")
        self.bandhigh =  wx.TextCtrl(self,value='8')
        bandorder_label = wx.StaticText(self, label="Bandpass Filter order :")
        self.bandorder =  wx.TextCtrl(self,value='2')
        
        flexsizer = wx.FlexGridSizer(cols = 2, hgap = 6, vgap = 6)
        flexsizer.AddMany([ chan_selected_label, self.chan_selected , 
                           start_time_label, self.start_time ,
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
        # Show the dialog and retrieve the user response, If OK, process the data.
        # print(dir(dlg))
        if dlg.ShowModal() == wx.ID_OK:
            edf_file = dlg.GetPath()
            print(edf_file)
            self.filepath = edf_file
            fname = os.path.split(edf_file)[1]
            self.filechosen.SetLabel(fname)
            
            header_info = pyedflib.highlevel.read_edf_header(edf_file, read_annotations=False)
            signal_labels = header_info['channels']
            self.chan_selected.SetItems(signal_labels) #choices = signal_labels
            
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
        wx.Frame.__init__(self,parent= parent, title='Effect of Data Filters', size=(700, 1100)) #super().__init__
        self.Centre()
        self.log = guiLog
        
        splitter = wx.SplitterWindow(self)
        splitter.upP = FileOpenPanel(splitter,self.log) 
        splitter.downP = CanvasPanel(splitter)
        splitter.SplitHorizontally(splitter.upP, splitter.downP,300)
        splitter.downP.Hide()
        
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(splitter, 1, wx.EXPAND)
        self.SetSizer(sizer)
        
        self.Show()

frame = testFrame()
app.MainLoop()  

#%%
del app


#---------------------------------------------------------------------------------------
#%% explore time taken for the filters
''' keep taking data from a synthetic stream - instead of a stream, from a prerecorded file?
     filter it and then only take next data from buffer
----- or just run the filter on same piece of data 100 times - check time
Current problem 
- Time -If we use higher order filters, more complex - so more time?
- We want filter to update in real time based on our data
'''





    
