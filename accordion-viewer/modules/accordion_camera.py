'''
Accordion Camera class, intended to run in its own thread
'''

import time
import numpy as np
from PyQt5 import QtCore, QtWidgets, QtGui

from .accordion_state import AccordionSingletonStateObject

import logging
logger = logging.getLogger(__name__)

class AccordionCamera(QtCore.QObject):
    '''Top-level class for all cameras'''
    sig_camera_datachunk = QtCore.pyqtSignal(np.ndarray)
    sig_finished = QtCore.pyqtSignal()
    sig_update_gui_from_state = QtCore.pyqtSignal(bool)
    sig_status_message = QtCore.pyqtSignal(str)

    def __init__(self, parent = None):
        super().__init__()

        self.parent = parent # a AccordionCore() object
        self.cfg = parent.cfg

        self.state = AccordionSingletonStateObject()
                
        self.parent.sig_prepare_live.connect(self.prepare_live_mode)
        self.parent.sig_run_live.connect(self.start_live_mode)
        self.parent.sig_stop.connect(self.stop)
                
        ''' Set up the camera '''
        if self.cfg.camera == 'DemoEventCamera':
            self.camera = AccordionDemoEventCamera(self)
        elif self.cfg.camera == 'PropheseeEventCamera':
            self.camera = AccordionPropheseeEventCamera(self)

    def __del__(self):
        try:
            self.camera.close_camera()
        except:
            pass

    @QtCore.pyqtSlot(dict)
    def state_request_handler(self, dict):
        '''The request handling is done with exec() to write fewer lines of code. '''
        for key, value in zip(dict.keys(), dict.values()):
            if key in ('camera_exposure_time',
                        'camera_line_interval',
                        'state',
                        'camera_display_live_subsampling',
                        'camera_display_acquisition_subsampling',
                        'camera_binning'):
                exec('self.set_'+key+'(value)')
            elif key == 'state':
                if value == 'live':
                    logger.debug('Thread ID during live: '+str(int(QtCore.QThread.currentThreadId())))

    def set_state(self, value):
        pass

    @QtCore.pyqtSlot()
    def stop(self):
        ''' Stops acquisition '''
        self.camera.stopflag = True

    @QtCore.pyqtSlot()
    def start_live_mode(self):
        self.camera.run_live_mode()

    @QtCore.pyqtSlot()
    def prepare_live_mode(self):
        print('Preparing live mode')
        logger.info('Camera: Preparing Live Mode')
        print('Camera Thread ID during prep live: '+str(int(QtCore.QThread.currentThreadId())))
        self.camera.prepare_live_mode()

    @QtCore.pyqtSlot(bool)
    def snap_image(self, write_flag=True):
        """"Snap an image and display it"""
        image = self.camera.get_image()
        self.sig_camera_frame.emit(image)
        if write_flag:
            self.image_writer.write_snap_image(image)

class AccordionGenericEventCamera(QtCore.QObject):
    ''' Generic Accordion camera class meant for subclassing.'''

    def __init__(self, parent = None):
        super().__init__()
        self.parent = parent
        self.cfg = parent.cfg
        self.state = AccordionSingletonStateObject()

        self.eventcount = 0
        self.stopflag = False

        self.x_pixels = self.cfg.camera_parameters['x_pixels']
        self.y_pixels = self.cfg.camera_parameters['y_pixels']
        self.x_pixel_size_in_microns = self.cfg.camera_parameters['x_pixel_size_in_microns']
        self.y_pixel_size_in_microns = self.cfg.camera_parameters['y_pixel_size_in_microns']
        
    def initialize_camera(self):
        pass

    def close_camera(self):
        pass

    def prepare_live_mode(self):
        pass

    def run_live_mode(self):
        pass

    def end_live_mode(self):
        pass

    def stop(self):
        self.stopflag = True

class AccordionDemoEventCamera(AccordionGenericEventCamera):
    def __init__(self, parent = None):
        super().__init__(parent)

        self.eventcount = 0
        self.parent = parent

        self.events_per_chunk = self.cfg.camera_parameters['events_per_chunk']
        self.chunk_frequency = self.cfg.camera_parameters['chunk_frequency_in_Hz']
        self.timer_interval_in_ms = int(np.divide(1,self.chunk_frequency)*1000)
        self.timer_interval_in_us = self.timer_interval_in_ms * 1000

        self.initialize_camera()

    def initialize_camera(self):
        logger.info('Initialized Demo Event Camera')

    def close_camera(self):
        logger.info('Closed Demo Event Camera')

    def prepare_live_mode(self):
        self.timer = QtCore.QTimer(self)
        self.timer.timeout.connect(self.send_demo_data)

    def run_live_mode(self):
        self.eventcount = 0
        self.timer.start(self.timer_interval_in_ms)
    
    def process_data(self):
        pass

    def send_demo_data(self):
        if self.stopflag is not True:
            datachunk = self._create_random_datachunk()
            self.parent.sig_camera_datachunk.emit(datachunk)
        else: 
            self.timer.stop()
            self.stopflag = False
    
    def _create_random_datachunk(self):
        self.start_time = time.time()*1E6 # Time in us
        
        event_x_coordinates = np.random.randint(0,self.x_pixels, self.events_per_chunk)
        event_y_coordinates = np.random.randint(0,self.y_pixels, self.events_per_chunk)
        # 0 = OFF, 1= ON
        event_type = np.random.randint(0,2,self.events_per_chunk)
        event_times = np.sort(np.random.randint(0,self.timer_interval_in_us,self.events_per_chunk))
        event_times = self.start_time + event_times

        datachunk = np.stack((event_x_coordinates, event_y_coordinates, event_type, event_times)).T
        self.eventcount += self.events_per_chunk
        return datachunk

    def get_image(self):
        return self._create_random_image()
    
class AccordionPropheseeEventCamera(AccordionGenericEventCamera):
    def __init__(self, parent=None):
        super().__init__(parent)

        from metavision_core.event_io.raw_reader import RawReader
        from metavision_core.event_io.py_reader import EventDatReader
        from metavision_core.event_io import EventsIterator

    



    