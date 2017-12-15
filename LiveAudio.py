import numpy as np
from PyQt5 import QtCore, QtGui, QtWidgets
from pyqtgraph.Qt import QtGui, QtCore
import pyqtgraph as pg
import struct
import pyaudio
from scipy.fftpack import fft
import peakutils
import padasip as pa

#separate timer class to handle 'multi-threading'
class Thread(QtCore.QThread):
    def __init__(self):
        QtCore.QThread.__init__(self)
        self.stream = AudioStream()

    def run(self):
        self.thread_func()
        self.exec_()

    def stop(self):
        self.timer.stop()

    def thread_func(self):
        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.stream.update)
        self.timer.start(0.022)

class AudioStream(object):
    def __init__(self):
        # pyqtgraph stuff
        pg.setConfigOptions(antialias=True)
        self.traces = dict()
        self.win = pg.GraphicsLayoutWidget()
        self.notebox = QtWidgets.QPlainTextEdit()

        self.wf_xlabels = [(0, '0'), (2048, '2048'), (4096, '4096')]
        self.wf_xaxis = pg.AxisItem(orientation='bottom')
        self.wf_xaxis.setTicks([self.wf_xlabels])

        self.wf_ylabels = [(0, '0'), (127, '128'), (255, '255')]
        self.wf_yaxis = pg.AxisItem(orientation='left')
        self.wf_yaxis.setTicks([self.wf_ylabels])

        self.sp_xlabels = [
            (0, '0'),(2000,'2000'),(4000,'4000'),(6000,'6000'),(8000,'8000'),(10000,'1000'),(12000,'12000'),
        ]
        self.sp_xaxis = pg.AxisItem(orientation='bottom')
        self.sp_xaxis.setTicks([self.sp_xlabels])

        self.waveform = self.win.addPlot(
            title='WAVEFORM', row=1, col=1, axisItems={'bottom': self.wf_xaxis, 'left': self.wf_yaxis},
        )
        self.spectrum = self.win.addPlot(
            title='SPECTRUM', row=2, col=1, axisItems={'bottom': self.sp_xaxis},
        )

        #create dicionary of notes all the way to the limit of human hearing
        self.letters = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
        self.count = 1
        self.notecount = 0
        self.octave = 1
        self.notes = {}
        self.fund = 32.703
        self.freq = self.fund
        while self.freq < 21000:
            self.notes[round(self.freq, 2)] = self.letters[self.notecount] + str(self.octave)
            #print(str(self.notes[round(self.freq, 2)]) + ' ' + str(round(self.freq, 2)))
            self.step = (2 ** (self.count / 12))
            self.freq = self.fund * self.step
            if self.notecount == 11:
                self.notecount = 0
                self.octave += 1
            else:
                self.notecount += 1
            self.count += 1



        # pyaudio stuff
        self.FORMAT = pyaudio.paInt16
        self.CHANNELS = 1
        self.RATE = 44100
        self.CHUNK = 1024 * 2

        self.p = pyaudio.PyAudio()
        self.stream = self.p.open(
            format=self.FORMAT,
            channels=self.CHANNELS,
            rate=self.RATE,
            input=True,
            output=True,
            frames_per_buffer=self.CHUNK,
        )
        # waveform and spectrum x points
        self.x = np.arange(0, 2 * self.CHUNK, 2)
        self.f = np.linspace(0, self.RATE / 2, self.CHUNK / 2)

    def set_plotdata(self, name, data_x, data_y):
        if name in self.traces:
            self.traces[name].setData(data_x, data_y)
        else:
            if name == 'waveform':
                self.traces[name] = self.waveform.plot(pen='c', width=3)
                self.waveform.setYRange(0, 255, padding=0)
                self.waveform.setXRange(0, 2 * self.CHUNK, padding=0.005)
            if name == 'spectrum':
                self.traces[name] = self.spectrum.plot(pen='m', width=3)
                self.spectrum.setLogMode(x=False, y=False)
                self.spectrum.setYRange(-0.8, 0.8, padding=0)
                self.spectrum.setXRange(0, self.RATE / 2, padding=0.005)

    def update(self):
        #read raw data from PyAudio object
        self.wf_data = self.stream.read(self.CHUNK+8)

        #turn raw data into binary
        self.wf_data = struct.unpack(str(2 * (self.CHUNK+8)) + 'B', self.wf_data)
        #turn binary into integer array
        self.wf_data = np.array(self.wf_data, dtype='b')[::2] + 128

        #get data ready for filtering
        self.wf_data = pa.input_from_history(self.wf_data,9)

        #create target array (zero noise plot)
        self.d = np.ones(2048)
        self.d[:] = [x * 128 for x in self.d]

        #create adaptive filter object with parameters
        self.filter = pa.filters.AdaptiveFilter(model="NLMS", n=9, mu=0.9, w="random")

        #run filter on collected data
        self.wf_data, e, w = self.filter.run(self.d,self.wf_data)

        #plot waveform data
        self.set_plotdata(name='waveform', data_x=self.x, data_y=self.wf_data,)
        self.sp_data = fft(np.array(self.wf_data, dtype='int8') - 128)

        #getting first half of fft output
        self.sp_data = np.abs(self.sp_data[0:int(self.CHUNK / 2)]
                         ) * 2 / (128 * self.CHUNK)
        #removing first element of array, some error
        self.sp_data[0] = 0

        #plot spectrum data
        self.set_plotdata(name='spectrum', data_x=self.f, data_y=self.sp_data)

        #get indices of the peaks of the spectrum data
        self.indexes = peakutils.indexes(self.sp_data, thres=0.2/max(self.sp_data))

        #convert array indices to frequency values (multiply by 21.533) 22050/1024 = 21.533. 1024 is length of
        self.indexes[:] = [index * 21.533 for index in self.indexes]
        if len(self.indexes) != 0:
            #print(type(self.indexes))
            self.noteSelect(self.indexes[0])

    def noteSelect(self, value):
        self.keys = self.notes.keys()
        self.nearest = self.find_nearest(self.keys,value)
        self.note = self.notes[self.nearest]
        #print(str(self.note) + ' ' + str(self.nearest))
        self.notebox.setPlainText(self.note)

    def find_nearest(self, array, value):
        return min(array, key=lambda x: abs(x - value))




