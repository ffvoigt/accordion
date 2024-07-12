'''
State singleton example 
'''
import time

from PyQt5 import QtCore

class AccordionSingletonStateObject():
    instance = None

    def __new__(cls):
        if not AccordionSingletonStateObject.instance:
            AccordionSingletonStateObject.instance = AccordionSingletonStateObject.__StateObject()

        return AccordionSingletonStateObject.instance

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
            self._state_dict = {
                            'state' : 'init', # 'init', 'idle' , 'live', 'snap', 'running_script'
                            'camera_exposure_time':0.02,
                            'camera_line_interval':0.000075,
                            'camera_display_live_subsampling': 1,
                            'camera_display_acquisition_subsampling': 2,
                            'camera_binning':'1x1',
                            'camera_sensor_mode':'ASLM',
                            'current_framerate':3.8,
                                 }
            
        def __len__(self):
            return len(self._state_dict) 
        
        def __setitem__(self, key, value):
            '''
            Custom __setitem__ method to allow mutexed access to 
            a state parameter. 

            After the state has been changed, the updated signal is emitted.
            '''
            with QtCore.QMutexLocker(self.mutex):
                self._state_dict.__setitem__(key, value)
            self.sig_updated.emit()

        def __getitem__(self, key):
            '''
            Custom __getitem__ method to allow mutexed access to 
            a state parameter.

            To avoid the state being updated while a parameter is read.
            '''

            with QtCore.QMutexLocker(self.mutex):
                return self._state_dict.__getitem__(key)
            
        def set_parameters(self, dict):
            '''
            Sometimes, several parameters should be set at once 
            without allowing the state being updated while a parameter is read.
            '''
            with QtCore.QMutexLocker(self.mutex):
                for key, value in dict.items():
                    self._state_dict.__setitem__(key, value)
            self.sig_updated.emit()

        def get_parameter_dict(self, list):
            '''
            For a list of keys, get a state dict with the current values back.

            All the values are read out under a QMutexLocker so that 
            the state cannot be updated at the same time.
            '''
            return_dict = {}

            with QtCore.QMutexLocker(self.mutex):
                for key in list:
                    return_dict[key] = self._state_dict.__getitem__(key)
            
            return return_dict

        def get_parameter_list(self, list):
            '''
            For a list of keys, get a state list with the current values back.

            This is especially useful for unpacking.

            All the values are read out under a QMutexLocker so that 
            the state cannot be updated at the same time.
            '''
            return_list = []

            with QtCore.QMutexLocker(self.mutex):
                for key in list:
                    return_list.append(self._state_dict.__getitem__(key))
            
            return return_list

        def block_signals(self, boolean):
            self.blockSignals(boolean)
