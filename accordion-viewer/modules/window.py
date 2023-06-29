
from PyQt5 import QtWidgets, QtCore

from PyQt5.uic import loadUi
import qdarkstyle

from .worker import WorkerObject, AnotherWorkerObject
from .state import SingletonStateObject

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
        self.setWindowTitle('Thread Template')

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
        self.actionExit.triggered.connect(self.close_app)

    def close_app(self):
        self.__del__()
        self.close()
        
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
