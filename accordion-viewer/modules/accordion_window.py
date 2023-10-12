
from PyQt5 import QtWidgets, QtCore

from PyQt5.uic import loadUi
import qdarkstyle

# from .worker import WorkerObject, AnotherWorkerObject
from .accordion_state import AccordionSingletonStateObject
from .accordion_camera import AccordionCamera

import pyqtgraph as pg
import numpy as np

from metavision_core.event_io.raw_reader import RawReader
from metavision_core.event_io.py_reader import EventDatReader
from metavision_core.event_io import EventsIterator

import logging
logger = logging.getLogger(__name__)

class AccordionMainWindow(QtWidgets.QMainWindow):
    '''
    Main application window which instantiates worker objects and moves them
    to a thread.
    '''
    sig_start = QtCore.pyqtSignal()
    sig_run_live = QtCore.pyqtSignal()
    sig_end_live = QtCore.pyqtSignal()
    sig_stop = QtCore.pyqtSignal()

    def __init__(self, config):
        super().__init__()

        self.cfg = config
        
        logger.info('Window thread ID at Startup: '+str(int(QtCore.QThread.currentThreadId())))
        logger.info('Ideal thread count: '+str(int(QtCore.QThread.idealThreadCount())))
        
        ''' Set up the UI '''
        loadUi('gui/accordion_gui.ui', self)
        self.setWindowTitle('Accordion')

        self.initialize_and_connect_menubar()

        ''' Set up the basic slots '''
        self.startButton.clicked.connect(self.start)
        self.stopButton.clicked.connect(self.stop)

        ''' Setting up the state '''
        self.state = SingletonStateObject()
        #print('Window State ID:', id(self.state))
        #print('Window Mutex ID: ', id(self.state.mutex))
        self.state.state_updated.connect(lambda string: print('Window thread received state update: ',string))
        # self.logger = SingletonLoggerObject('my_log_file.txt')
        # print('ID Window Logger: ', id(self.logger))

        print(type(self.graphicsView))

        self.XY_plot_layout = self.graphicsView.addLayout(row=0, col=0, rowspan=2, colspan=1, border=(50,50,0))
        self.XY_plot = self.XY_plot_layout.addPlot()
        # self.ET_plot = self.graphicsView.addPlot(row=2, col=0, rowspan=1, colspan=1, border=(50,50,0))
        # self.ET_region_selection_plot = self.graphicsView.addPlot(row=3, col=0, rowspan=1, colspan=1, border=(50,50,0))
        self.XY_plot.setAspectLocked(True, ratio=1.77)

        # self.ET_region = pg.LinearRegionItem(values=[1000,2000])
        # self.ET_region.setZValue(10) # Move item up 

        # self.ET_region_selection_plot.addItem(self.ET_region, ignoreBounds = True)
        # self.ET_plot.setAutoVisible(y=True)

        #data1 = 10000 + 15000 * pg.gaussianFilter(np.random.random(size=10000), 10) + 3000 * np.random.random(size=10000)
        #data2 = 15000 + 15000 * pg.gaussianFilter(np.random.random(size=10000), 10) + 3000 * np.random.random(size=10000)

        #self.ET_plot.plot(data1, pen="r")
        #self.ET_region_selection_plot.plot(data1, pen="r")

        #self.ET_region.sigRegionChanged.connect(self.update)

        self.s4 = pg.ScatterPlotItem(
                    size=3,
                    pen=pg.mkPen(None),
                    brush=pg.mkBrush(255, 255, 255, 20),
                    hoverable=False,
                    hoverSymbol='s',
                    hoverSize=15,
                    hoverPen=pg.mkPen('r', width=2),
                    hoverBrush=pg.mkBrush('g'),
                    )
        
        self.n = 10000
        self.pos = np.random.normal(size=(2, self.n), scale=1e-9)

        self.s4.addPoints(x=self.pos[0],
                          y=self.pos[1],
                            # size=(np.random.random(n) * 20.).astype(int),
                            # brush=[pg.mkBrush(x) for x in np.random.randint(0, 256, (n, 3))],
                            data=np.arange(self.n)
                            )
        
        self.XY_plot.addItem(self.s4)

        self.clickedPen = pg.mkPen('b', width=2)
        self.lastClicked = []    

        # self.s4.sigClicked.connect(self.clicked)

        ''' Set the thread up '''
        self.camera_thread = QtCore.QThread()
        self.camera_worker = AccordionCamera(self)
        self.camera_worker.moveToThread(self.camera_thread)

        ''' Create the connections '''
        self.camera_worker.sig_camera_datachunk.connect(self.update_display)

        '''Start the thread'''
        self.camera_thread.start()
        
    def __del__(self):
        '''Cleans the thread up after deletion, waits until the thread
        has truly finished its life.

        Uses "try" in case things crash before the thread was even started.
        '''
        try:
            self.self.camera_thread.quit()
            self.self.camera_thread.wait()
        except:
            pass
    
    @QtCore.pyqtSlot(np.ndarray)
    def update_display(self, datachunk):
        print('updating display')
        pass
        '''
        self.ET_region.setZValue(10)
        minX, maxX = self.ET_region.getRegion()
        self.ET_plot.setXRange(minX, maxX, padding=0)
        '''

    def initialize_and_connect_menubar(self):
        self.actionExit_2.triggered.connect(self.close_app)
        self.actionOpen_File.triggered.connect(self.load_dataset)
    
    def close_app(self):
        self.__del__()
        self.close()

    def clicked(self, plot, points):
        for p in self.lastClicked:
            p.resetPen()
        print("clicked points", points)
        for p in points:
            p.setPen(self.clickedPen)
        self.lastClicked = points
          
    def print_sth(self, string):
        print(string)

    def update_progressbar(self,value):
        self.progressBar.setValue(value)

    def start(self):
        self.sig_start.emit()
        self.sig_run_live.emit()

    def stop(self):
        self.sig_stop.emit()


