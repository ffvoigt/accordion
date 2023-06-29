
from PyQt5 import QtWidgets, QtCore

from PyQt5.uic import loadUi
import qdarkstyle

from .worker import WorkerObject, AnotherWorkerObject
from .state import SingletonStateObject

import pyqtgraph as pg
import numpy as np

from metavision_core.event_io.raw_reader import RawReader
from metavision_core.event_io.py_reader import EventDatReader
from metavision_core.event_io import EventsIterator

import logging
logger = logging.getLogger(__name__)

class Window(QtWidgets.QMainWindow):
    '''
    Main application window which instantiates worker objects and moves them
    to a thread.
    '''
    sig_start = QtCore.pyqtSignal()

    def __init__(self, config):
        super().__init__()

        self.cfg = config
        
        logger.info('Window thread ID at Startup: '+str(int(QtCore.QThread.currentThreadId())))
        logger.info('Ideal thread count: '+str(int(QtCore.QThread.idealThreadCount())))
        
        ''' Set up the UI '''
        loadUi('gui/accordion_gui.ui', self)
        self.setWindowTitle('Accordion Event Browser')

        self.initialize_and_connect_menubar()

        ''' Set up the basic slots '''
        self.startButton.clicked.connect(self.start)

        ''' Setting up the state '''
        self.state = SingletonStateObject()
        print('Window State ID:', id(self.state))
        print('Window Mutex ID: ', id(self.state.mutex))
        self.state.state_updated.connect(lambda string: print('Window thread received state update: ',string))
        # self.logger = SingletonLoggerObject('my_log_file.txt')
        # print('ID Window Logger: ', id(self.logger))

        self.w1 = self.graphicsView.addPlot()

        self.s4 = pg.ScatterPlotItem(
                    size=10,
                    pen=pg.mkPen(None),
                    brush=pg.mkBrush(255, 255, 255, 20),
                    hoverable=True,
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
        self.w1.addItem(self.s4)

        self.clickedPen = pg.mkPen('b', width=2)
        self.lastClicked = []    

        self.s4.sigClicked.connect(self.clicked)

        ''' Set the thread up '''
        self.my_thread = QtCore.QThread()
        self.my_worker = WorkerObject(self)
        self.my_worker.moveToThread(self.my_thread)

        ''' Setting another thread up '''
        self.my_thread1 = QtCore.QThread()
        self.my_worker1 = AnotherWorkerObject(self)
        self.my_worker1.moveToThread(self.my_thread1)

        ''' Create the connections '''
        self.my_worker.status.connect(self.update_progressbar)

        ''' The Signal Switchboard '''
        self.my_worker.started.connect(self.test1)
        self.my_worker.finished.connect(self.test2)

        '''Start the thread'''
        self.my_thread.start()
        self.my_thread1.start()

    def __del__(self):
        '''Cleans the thread up after deletion, waits until the thread
        has truly finished its life.

        Uses "try" in case things crash before the thread was even started.
        '''
        try:
            self.my_thread.quit()
            self.my_thread1.quit()
            self.my_thread.wait()
            self.my_thread1.wait()
        except:
            pass

    def initialize_and_connect_menubar(self):
        self.actionExit_2.triggered.connect(self.close_app)
        self.actionOpen_File.triggered.connect(self.load_dataset)
    
    def close_app(self):
        self.__del__()
        self.close()

    def load_dataset(self):
        path , _ = QtWidgets.QFileDialog.getOpenFileName(self, 'Open File')

        ''' To avoid crashes, only set the cfg file when a file has been selected:'''
        if path:
            path = path.decode('ascii')
            print(path)
            logger.info(f'Main Window: Chosen File: {path}')
            self.record_raw = RawReader(path)
            print(record_raw)
            self.events = self.record_raw.load_n_events(10000)

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

    def test1(self):
        print('Start signal received')

    def test2(self):
        print('Finished signal received')
