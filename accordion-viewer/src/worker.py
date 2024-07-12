''' Worker object in a separate file '''

import time
import copy
import random

from PyQt5 import QtWidgets, QtCore
from .state import SingletonStateObject

class WorkerObject(QtCore.QObject):
    '''
    Worker object which has a few time-intensive methods, can signal
    its status and is able to listen to stop events.
    '''
    started = QtCore.pyqtSignal()
    finished = QtCore.pyqtSignal()
    status = QtCore.pyqtSignal(int)

    def __init__(self, parent):
        super().__init__()

        ''' Here, I'm referencing the parent '''
        # print(id(parent))
        self.parent = parent
        # print(id(self.parent))
        ''' The IDs are the same'''

        ''' Here, I can connect signals from the parent in the child

        This is a form of callbacks
        '''
        self.state = SingletonStateObject()
        #print('Worker State ID:', id(self.state))
        #print('Worker Mutex ID: ', id(self.state.mutex))

        self.parent.sig_start.connect(self.start)

        self.cfg = copy.deepcopy(self.parent.cfg)

        self.stop_index = 10

        # print(id(self.parent.cfg))
        # print(id(self.cfg))

    @QtCore.pyqtSlot()
    def start(self):
        '''
        Execute some time intensive (sleepy) operation.
        '''
        self.started.emit()
        for i in range(0,101):
            time.sleep(0.02)
            QtWidgets.QApplication.processEvents()
            if i==self.stop_index:
                self.state.set_state('working',wait_until_done=True)
            self.status.emit(i)
        self.finished.emit()

        self.parent.print_sth('hi from your thread')

class AnotherWorkerObject(WorkerObject):
    ''' Another, simpler worker object '''

    def __init__(self, parent):
        super().__init__(parent)
        

        self.stop_index = 10

    @QtCore.pyqtSlot()
    def start(self):
        for i in range(0,101):
            time.sleep(0.02)
            if i==self.stop_index:
                print(i)
                self.state.set_state('working',wait_until_done=True)
            if i % 10 == 0:
                print(i)
