'''
Accordion Camera class, intended to run in its own thread
'''

import time
import numpy as np
from numba import jit
from PyQt5 import QtCore, QtWidgets, QtGui

from .accordion_state import AccordionSingletonStateObject

import logging
logger = logging.getLogger(__name__)

class AccordionEventCamera(QtCore.QObject):
    '''Top-level class for all cameras'''
    sig_camera_datachunk = QtCore.pyqtSignal(np.ndarray)
    sig_finished = QtCore.pyqtSignal()
    sig_update_gui_from_state = QtCore.pyqtSignal(bool)
    sig_status_message = QtCore.pyqtSignal(str)
    sig_roi_center = QtCore.pyqtSignal(np.ndarray)

    def __init__(self, parent = None):
        super().__init__()

        self.parent = parent # a AccordionCore() object
        self.cfg = parent.cfg

        self.state = AccordionSingletonStateObject()
                
        self.parent.sig_prepare_live.connect(self.prepare_live_mode)
        self.parent.sig_run_live.connect(self.start_live_mode)
        self.parent.sig_end_live.connect(self.end_live_mode)
                
        ''' Set up the camera '''
        if self.cfg.event_camera == 'DemoEventCamera':
            self.camera = AccordionDemoEventCamera(self)
        elif self.cfg.event_camera == 'PropheseeEventCamera':
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
    def end_live_mode(self):
        ''' Stops acquisition '''
        self.camera.stopflag = True
        self.camera.end_live_mode()

    @QtCore.pyqtSlot()
    def start_live_mode(self):
        self.camera.run_live_mode()

    @QtCore.pyqtSlot()
    def prepare_live_mode(self):
        print('Preparing live mode')
        logger.info('Camera: Preparing Live Mode')
        print('Camera Thread ID during prep live: '+str(int(QtCore.QThread.currentThreadId())))
        self.camera.prepare_live_mode()
    
class AccordionGenericEventCamera(QtCore.QObject):
    ''' Generic Accordion camera class meant for subclassing.'''

    def __init__(self, parent = None):
        super().__init__()
        self.parent = parent
        self.cfg = parent.cfg
        self.state = AccordionSingletonStateObject()

        self.eventcount = 0
        self.stopflag = False

        self.x_pixels = self.cfg.event_camera_parameters['x_pixels']
        self.y_pixels = self.cfg.event_camera_parameters['y_pixels']
        self.x_pixel_size_in_microns = self.cfg.event_camera_parameters['x_pixel_size_in_microns']
        self.y_pixel_size_in_microns = self.cfg.event_camera_parameters['y_pixel_size_in_microns']
        
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

        # self.eventcount = 0
        self.parent = parent
        self.cfg = parent.cfg

        self.event_processing_enabled = self.cfg.startup['event_processing_enabled']

        self.events_per_chunk = self.cfg.event_camera_parameters['events_per_chunk']
        self.chunk_frequency = self.cfg.event_camera_parameters['chunk_frequency_in_Hz']
        self.timer_interval_in_ms = int(np.divide(1,self.chunk_frequency)*1000)
        self.timer_interval_in_us = self.timer_interval_in_ms * 1000

        self.demo_type = self.cfg.event_camera_parameters['demo_type']

        self.timer_initialized = False

        self.initialize_camera()

    def initialize_camera(self):
        logger.info('Initialized Demo Event Camera')

    def close_camera(self):
        logger.info('Closed Demo Event Camera')

    def prepare_live_mode(self):
        if not self.timer_initialized:
            self.timer = QtCore.QTimer(self)
            self.timer.timeout.connect(self.send_demo_data)
            self.timer_initialized = True

        self.stopflag = False

    def run_live_mode(self):
        self.eventcount = 0
        self.timer.start(self.timer_interval_in_ms)

    def end_live_mode(self):
        self.stopflag = True
        self.timer.stop()
    
    def process_data(self):
        pass

    def send_demo_data(self):
        if self.stopflag is not True:
            datachunk = self._create_random_datachunk()
            if self.event_processing_enabled == True:
                roi_center = datachunk_to_normalized_roi(datachunk, self.x_pixels, self.y_pixels)
                self.parent.sig_roi_center.emit(roi_center)
            self.parent.sig_camera_datachunk.emit(datachunk)
        else: 
            pass

    def _create_random_datachunk(self, ):
        start_time = time.time()*1E6 # Time in us
        if self.demo_type == 'random':
            datachunk = create_random_datachunk(start_time, self.x_pixels, self.y_pixels, self.events_per_chunk, self.timer_interval_in_us)
        elif self.demo_type == 'spiral':
            datachunk = create_spiral_datachunk(start_time, self.x_pixels, self.y_pixels, self.events_per_chunk, self.timer_interval_in_us)
               
        return datachunk

    def get_image(self):
        return self._create_random_image()
    
class AccordionPropheseeEventCamera(AccordionGenericEventCamera):
    def __init__(self, parent=None):
        super().__init__(parent)

        from metavision_core.event_io.raw_reader import RawReader
        from metavision_core.event_io.py_reader import EventDatReader
        from metavision_core.event_io import EventsIterator


class AccordionEventProcessor(QtCore.QObject):
    def __init__(self, parent=None):
        super().__init__(parent)

    def datachunk_to_roi(self, datachunk):


        pass
        

@jit(nopython=True)    
def create_random_datachunk(start_time, x_pixels, y_pixels, events_per_chunk, timer_interval_in_us):
    event_x_coordinates = np.random.randint(0,x_pixels, events_per_chunk)
    event_y_coordinates = np.random.randint(0,y_pixels, events_per_chunk)
    event_type = np.random.randint(0,2,events_per_chunk)
    event_times = np.sort(np.random.randint(0,timer_interval_in_us,events_per_chunk))
    event_times = start_time + event_times
    return np.stack((event_x_coordinates, event_y_coordinates, event_type, event_times)).T

@jit(nopython=True)    
def create_spiral_datachunk(start_time, x_pixels, y_pixels, events_per_chunk, timer_interval_in_us):
    x_center = int(x_pixels/2)
    y_center = int(y_pixels/2)
    radius = x_pixels/4
    x_offset = int(radius*np.sin(start_time/500000))
    y_offset = int(radius*np.cos(start_time/500000))
    event_x_coordinates = x_center + x_offset + np.random.normal(0, 30, events_per_chunk)
    event_y_coordinates = y_center + y_offset + np.random.normal(0, 30, events_per_chunk)
    event_type = np.random.randint(0,2,events_per_chunk)
    event_times = np.sort(np.random.randint(0, timer_interval_in_us, events_per_chunk))
    event_times = start_time + event_times
    return np.stack((event_x_coordinates, event_y_coordinates, event_type, event_times)).T


def datachunk_to_normalized_roi(datachunk,x_pixels, y_pixels):
    ''' Calculates the x and y mean of the event datachunk and divides it by the image size to get 
        a relative measure
    '''
    x_and_y_positions = datachunk[:,0:2]
    norm_roi = np.divide(np.mean(x_and_y_positions, axis=0),[x_pixels,y_pixels])
    return norm_roi
