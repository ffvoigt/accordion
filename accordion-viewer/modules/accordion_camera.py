'''
Accordion Camera class, intended to run in its own thread
'''

import time
import numpy as np
from PyQt5 import QtCore, QtWidgets, QtGui

from metavision_core.event_io.raw_reader import RawReader
from metavision_core.event_io.py_reader import EventDatReader
from metavision_core.event_io import EventsIterator

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

        self.state = AccordionStateSingleton()
                
        #self.parent.sig_prepare_live.connect(self.prepare_live, type=QtCore.Qt.BlockingQueuedConnection)
        self.parent.sig_run_live.connect(self.run_live)
        self.parent.sig_stop.connect(self.end_live, type=QtCore.Qt.BlockingQueuedConnection)
        #self.parent.sig_get_snap_image.connect(self.snap_image)

                
        ''' Set up the camera '''
        if self.cfg.camera == 'DemoEventCamera':
            self.camera = AccordionDemoEventCamera(self)

        self.camera.initialize_camera()

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
        self.stopflag = True


    @QtCore.pyqtSlot()
    def prepare_live(self):
        self.camera.initialize_live_mode()
        self.live_image_count = 0
        self.start_time = time.time()
        logger.info('Camera: Preparing Live Mode')

    @QtCore.pyqtSlot()
    def get_live_image(self):
        images = self.camera.get_live_image()

        for image in images:
            image = np.rot90(image)

            self.sig_camera_frame.emit(image[0:self.x_pixels:self.camera_display_live_subsampling,
                                       0:self.y_pixels:self.camera_display_live_subsampling])
            self.live_image_count += 1
            #self.sig_camera_status.emit(str(self.live_image_count))

    @QtCore.pyqtSlot()
    def end_live(self):
        self.camera.close_live_mode()
        self.end_time = time.time()
        framerate = (self.live_image_count + 1)/(self.end_time - self.start_time)
        logger.info(f'Camera: Finished Live Mode: Framerate: {framerate:.2f}')

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

        #self.state = AccordionStateSingleton()

        self.stopflag = False

        self.x_pixels = self.cfg.camera_parameters['x_pixels']
        self.y_pixels = self.cfg.camera_parameters['y_pixels']
        self.x_pixel_size_in_microns = self.cfg.camera_parameters['x_pixel_size_in_microns']
        self.y_pixel_size_in_microns = self.cfg.camera_parameters['y_pixel_size_in_microns']
        
    def open_camera(self):
        pass

    def close_camera(self):
        pass

    def initialize_image_series(self):
        pass

    def get_images_in_series(self):
        '''Should return a single numpy array'''
        pass

    def close_image_series(self):
        pass

    def get_image(self):
        '''Should return a single numpy array'''
        pass

    def initialize_live_mode(self):
        pass

    def get_live_image(self):
        pass

    def close_live_mode(self):
        pass

class AccordionDemoEventCamera(AccordionGenericEventCamera):
    def __init__(self, parent = None):
        super().__init__(parent)

        self.eventcount = 0

        self.events_per_chunk = self.cfg.camera_parameters['events_per_chunk']
        self.chunk_frequency = self.cfg.camera_parameters['chunk_frequency_in_Hz']
        timer_interval = int(np.divide(1,self.chunk_frequency)*1000)

        self.timer = QtCore.QTimer(self)
        self.timer.timeout.connect(self.process_data)

    def open_camera(self):
        logger.info('Initialized Demo Camera')

    def close_camera(self):
        logger.info('Closed Demo Camera')

    def initialize_live_mode(self):
        self.timer.start(timer_interval)

    def process_data(self):
        pass
    
    def _create_random_datachunk(self):
        # move this to numba

        self.start_time = time.time()*1E6 # Time in us
        event_coordinates = np.random.randint(500,2)
        data = 

        self.x_pixels
        self.y_pixels

        data = np.array([np.roll(self.line, 4*i+self.count) for i in range(0, self.y_pixels)], dtype='uint16')
        data = data + (np.random.normal(size=(self.x_pixels, self.y_pixels))*100)
        data = np.around(data).astype('uint16')
        self.count += 20
        return data

    def get_image(self):
        return self._create_random_image()

    



    