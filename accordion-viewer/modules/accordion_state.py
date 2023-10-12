'''
State singleton example 
'''
import time

from PyQt5 import QtCore

class AccordionSingletonStateObject():
    instance = None

    def __new__(cls):
        if not SingletonStateObject.instance:
            SingletonStateObject.instance = SingletonStateObject.__StateObject()

        return SingletonStateObject.instance

    def __getattr__(self, name):
        print('getattr called')
        return getattr(self.instance, name)

    def __setattr__(self, name):
        print('setattr called')
        return setattr(self.instance, name)

    class __StateObject(QtCore.QObject):
        state_updated = QtCore.pyqtSignal(str)
        mutex = QtCore.QMutex()

        def __init__(self):
            super().__init__()
            self.spam = None
                      
            print('State ID:', id(self))
            print('Mutex ID: ', id(self.mutex))

            self.state_updated.connect(lambda string: print('StateObject: ', string))

        def set_state(self, spam, wait_until_done=False):
            print('set state called')
            with QtCore.QMutexLocker(self.mutex):
                starttime = time.time() 
                self.spam = spam
                self.state_updated.emit('State is now: ' + str(spam))
                if wait_until_done:
                    time.sleep(2)
                endtime = time.time() 
                print('Delta t: ', endtime-starttime)

        def get_state(self):
            with QtCore.QMutexLocker(self.mutex): 
                return self.spam