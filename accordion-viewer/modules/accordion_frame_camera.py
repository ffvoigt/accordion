'''
Accordion Camera class, intended to run in its own thread
'''

import time
import numpy as np
from PyQt5 import QtCore, QtWidgets, QtGui

import logging
logger = logging.getLogger(__name__)

from .accordion_state import AccordionSingletonStateObject

class AccordionFrameCamera(QtCore.QObject):
    '''Top-level class for all cameras'''
    sig_camera_frame = QtCore.pyqtSignal(np.ndarray)
    sig_finished = QtCore.pyqtSignal()
    sig_update_gui_from_state = QtCore.pyqtSignal(bool)
    sig_status_message = QtCore.pyqtSignal(str)

    def __init__(self, parent = None):
        super().__init__()

        self.parent = parent # a Accordion_Core() object
        self.cfg = parent.cfg

        self.state = AccordionSingletonStateObject()
        #self.image_writer = Accordion_ImageWriter(self)
        self.stopflag = False

        self.x_pixels = self.cfg.frame_camera_parameters['x_pixels']
        self.y_pixels = self.cfg.frame_camera_parameters['y_pixels']
        self.x_pixel_size_in_microns = self.cfg.frame_camera_parameters['x_pixel_size_in_microns']
        self.y_pixel_size_in_microns = self.cfg.frame_camera_parameters['y_pixel_size_in_microns']

        self.binning_string = self.cfg.frame_camera_parameters['binning'] # Should return a string in the form '2x4'
        self.x_binning = int(self.binning_string[0])
        self.y_binning = int(self.binning_string[2])

        self.x_pixels = int(self.x_pixels / self.x_binning)
        self.y_pixels = int(self.y_pixels / self.y_binning)

        self.camera_exposure_time = self.cfg.startup['camera_exposure_time']

        self.camera_display_live_subsampling = self.cfg.startup['camera_display_live_subsampling']
        self.camera_display_acquisition_subsampling = self.cfg.startup['camera_display_acquisition_subsampling']

        ''' Wiring signals '''
        
        '''
        self.parent.sig_state_request.connect(self.state_request_handler) # from Accordion_Core() to Accordion_Camera()
        self.parent.sig_prepare_image_series.connect(self.prepare_image_series, type=QtCore.Qt.BlockingQueuedConnection)
        self.parent.sig_add_images_to_image_series.connect(self.add_images_to_series)
        self.parent.sig_add_images_to_image_series_and_wait_until_done.connect(self.add_images_to_series, type=QtCore.Qt.BlockingQueuedConnection)
        self.parent.sig_write_metadata.connect(self.image_writer.write_metadata, type=QtCore.Qt.QueuedConnection)
        # The following connection can cause problems when disk is too slow (e.g. writing TIFF files on HDD drive):
        self.parent.sig_end_image_series.connect(self.end_image_series, type=QtCore.Qt.BlockingQueuedConnection)
        '''

        self.parent.sig_prepare_live.connect(self.prepare_live)
        self.parent.sig_run_live.connect(self.run_live)
        self.parent.sig_end_live.connect(self.end_live)

        ''' Set up the camera '''
        if self.cfg.frame_camera == 'HamamatsuOrca':
            self.camera = AccordionHamamatsuCamera(self)
        elif self.cfg.frame_camera == 'DemoFrameCamera':
            self.camera = AccordionDemoFrameCamera(self)

        self.camera.open_camera()

    def __del__(self):
        try:
            self.camera.close_camera()
        except:
            pass

    def set_camera_exposure_time(self, time):
        '''
        Sets the exposure time in seconds

        Args:
            time (float): exposure time to set
        '''
        self.camera.set_exposure_time(time)
        self.camera_exposure_time = time
        self.sig_update_gui_from_state.emit(True)
        self.state['camera_exposure_time'] = time
        self.sig_update_gui_from_state.emit(False)

    def set_camera_line_interval(self, time):
        '''
        Sets the line interval in seconds

        Args:
            time (float): interval time to set
        '''
        self.camera.set_line_interval(time)
        self.camera_line_interval = time
        self.sig_update_gui_from_state.emit(True)
        self.state['camera_line_interval'] = time
        self.sig_update_gui_from_state.emit(False)

    def set_camera_display_live_subsampling(self, factor):
        self.camera_display_live_subsampling = factor
        self.state['camera_display_live_subsampling'] = factor

    def set_camera_display_acquisition_subsampling(self, factor):
        self.camera_display_acquisition_subsampling = factor
        self.state['camera_display_acquisition_subsampling'] = factor

    def set_camera_binning(self, value):
        print('Setting camera binning: '+value)
        self.camera.set_binning(value)
        self.state['camera_binning'] = value
    '''
    @QtCore.pyqtSlot(Acquisition, AcquisitionList)
    def prepare_image_series(self, acq, acq_list):
        
        #Row is a row in a AcquisitionList
        
        logger.info('Camera: Preparing Image Series')
        self.stopflag = False

        self.image_writer.prepare_acquisition(acq, acq_list)

        self.max_frame = acq.get_image_count()
        self.processing_options_string = acq['processing']

        self.camera.initialize_image_series()
        self.cur_image = 0
        logger.info(f'Camera: Finished Preparing Image Series')
        self.start_time = time.time()

    @QtCore.pyqtSlot(Acquisition, AcquisitionList)
    def add_images_to_series(self, acq, acq_list):
        if self.cur_image == 0:
            logger.debug('Thread ID during add images: '+str(int(QtCore.QThread.currentThreadId())))

        if self.stopflag is False:
            if self.cur_image < self.max_frame:
                images = self.camera.get_images_in_series()
                for image in images:
                    image = np.rot90(image)
                    self.sig_camera_frame.emit(image[0:self.x_pixels:self.camera_display_acquisition_subsampling,
                                               0:self.y_pixels:self.camera_display_acquisition_subsampling])
                    self.image_writer.write_image(image, acq, acq_list)
                    self.cur_image += 1

    @QtCore.pyqtSlot(Acquisition, AcquisitionList)
    def end_image_series(self, acq, acq_list):
        logger.info("end_image_series() started")
        try:
            self.camera.close_image_series()
            logger.info("self.camera.close_image_series()")
        except Exception as e:
            logger.error(f'Camera: Image Series could not be closed: {e}')

        self.image_writer.end_acquisition(acq, acq_list)

        self.end_time = time.time()
        framerate = (self.cur_image + 1)/(self.end_time - self.start_time)
        logger.info(f'Camera: Framerate: {framerate:.2f}')
        self.sig_finished.emit()

    @QtCore.pyqtSlot(bool)
    def snap_image(self, write_flag=True):
        """"Snap an image and display it"""
        image = self.camera.get_image()
        image = np.rot90(image)[::self.camera_display_acquisition_subsampling, ::self.camera_display_acquisition_subsampling]
        self.sig_camera_frame.emit(image)
        if write_flag:
            self.image_writer.write_snap_image(image)
    '''

    @QtCore.pyqtSlot()
    def prepare_live(self):
        self.camera.initialize_live_mode()
        self.live_image_count = 0
        self.start_time = time.time()
        logger.info('Camera: Preparing Live Mode')

    @QtCore.pyqtSlot()
    def run_live(self):
        self.camera.run_live_mode()

    @QtCore.pyqtSlot()
    def end_live(self):
        self.camera.stop_live_mode()
        self.end_time = time.time()
        framerate = (self.live_image_count + 1)/(self.end_time - self.start_time)
        logger.info(f'Camera: Finished Live Mode: Framerate: {framerate:.2f}')


class AccordionGenericFrameCamera(QtCore.QObject):
    ''' Generic Accordion camera class meant for subclassing.'''

    def __init__(self, parent = None):
        super().__init__()
        self.parent = parent
        self.cfg = parent.cfg

        self.state = AccordionSingletonStateObject()

        self.stopflag = False

        self.x_pixels = self.cfg.frame_camera_parameters['x_pixels']
        self.y_pixels = self.cfg.frame_camera_parameters['y_pixels']
        self.x_pixel_size_in_microns = self.cfg.frame_camera_parameters['x_pixel_size_in_microns']
        self.y_pixel_size_in_microns = self.cfg.frame_camera_parameters['y_pixel_size_in_microns']

        self.binning_string = self.cfg.frame_camera_parameters['binning'] # Should return a string in the form '2x4'
        self.x_binning = int(self.binning_string[0])
        self.y_binning = int(self.binning_string[2])

        self.x_pixels = int(self.x_pixels / self.x_binning)
        self.y_pixels = int(self.y_pixels / self.y_binning)

        # self.camera_line_interval = self.cfg.startup['camera_line_interval']
        self.camera_exposure_time = self.cfg.startup['camera_exposure_time']

    def open_camera(self):
        pass

    def close_camera(self):
        pass

    def set_exposure_time(self, time):
        self.camera_exposure_time = time

    def set_line_interval(self, time):
        pass

    def set_binning(self, binning_string):
        self.x_binning = int(binning_string[0])
        self.y_binning = int(binning_string[2])
        self.x_pixels = int(self.x_pixels / self.x_binning)
        self.y_pixels = int(self.y_pixels / self.y_binning)
        self.state['camera_binning'] = str(self.x_binning)+'x'+str(self.y_binning)

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

class AccordionDemoFrameCamera(AccordionGenericFrameCamera):
    def __init__(self, parent = None):
        super().__init__(parent)

        self.count = 0

        self.line = np.linspace(0,6*np.pi,self.x_pixels)
        self.line = 400*np.sin(self.line)+1200

        self.timer_initialized = False

        self.timer_interval_in_ms = 50

    def open_camera(self):
        logger.info('Initialized Demo Camera')

    def close_camera(self):
        logger.info('Closed Demo Camera')
    
    def set_binning(self, binning_string):
        self.x_binning = int(binning_string[0])
        self.y_binning = int(binning_string[2])
        self.x_pixels = int(self.x_pixels / self.x_binning)
        self.y_pixels = int(self.y_pixels / self.y_binning)
        ''' Changing the number of pixels also affects the random image, so we need to update self.line '''
        self.line = np.linspace(0,6*np.pi,self.x_pixels)
        self.line = 400*np.sin(self.line)+1200
        self.state['camera_binning'] = str(self.x_binning)+'x'+str(self.y_binning)

    def _create_random_image(self):
        data = np.array([np.roll(self.line, 4*i+self.count) for i in range(0, self.y_pixels)], dtype='uint16')
        data = data + (np.random.normal(size=(self.x_pixels, self.y_pixels))*100)
        data = np.around(data).astype('uint16')
        self.count += 20
        return data

    def get_images_in_series(self):
        return [self._create_random_image()]

    def get_image(self):
        return self._create_random_image()
    
    @QtCore.pyqtSlot()
    def send_live_image(self):
        if self.stopflag is not True:
            image = np.rot90(self._create_random_image())
            # image = np.rot90([self._create_random_image()])
            self.parent.sig_camera_frame.emit(image[0:self.x_pixels:self.parent.camera_display_live_subsampling,
                                        0:self.y_pixels:self.parent.camera_display_live_subsampling])
            self.parent.live_image_count += 1
    
    @QtCore.pyqtSlot()
    def initialize_live_mode(self):
        if not self.timer_initialized:
            self.timer = QtCore.QTimer(self)
            self.timer.timeout.connect(self.send_live_image)
            self.timer_initialized = True

        self.stopflag = False
        
    @QtCore.pyqtSlot()
    def run_live_mode(self):
        self.timer.start(self.timer_interval_in_ms)

    @QtCore.pyqtSlot()
    def stop_live_mode(self):
        self.stopflag = True
        self.timer.stop()

class AccordionHamamatsuCamera(AccordionGenericFrameCamera):
    def __init__(self, parent = None):
        super().__init__(parent)

    def open_camera(self):
        ''' Hamamatsu-specific code '''
        self.camera_id = self.cfg.camera_parameters['camera_id']

        from .devices.cameras.hamamatsu import hamamatsu_camera as cam
        # if self.cfg.camera == 'HamamatsuOrca':
        self.hcam = cam.HamamatsuCameraMR(camera_id=self.camera_id)
        ''' Debbuging information '''
        logger.info(f'Initialized Hamamatsu camera model: {self.hcam.getModelInfo(self.camera_id)}')

        ''' Ideally, the Hamamatsu Camera properties should be set in this order '''

        ''' Accordion mode parameters '''
        self.hcam.setPropertyValue("sensor_mode", self.cfg.camera_parameters['sensor_mode'])

        self.hcam.setPropertyValue("defect_correct_mode", self.cfg.camera_parameters['defect_correct_mode'])
        self.hcam.setPropertyValue("exposure_time", self.camera_exposure_time)
        self.hcam.setPropertyValue("binning", self.cfg.camera_parameters['binning'])
        self.hcam.setPropertyValue("readout_speed", self.cfg.camera_parameters['readout_speed'])

        #self.hcam.setPropertyValue("trigger_active", self.cfg.camera_parameters['trigger_active'])
        #self.hcam.setPropertyValue("trigger_mode", self.cfg.camera_parameters['trigger_mode']) # it is unclear if this is the external lightsheeet mode - how to check this?
        #self.hcam.setPropertyValue("trigger_polarity", self.cfg.camera_parameters['trigger_polarity']) # positive pulse
        #self.hcam.setPropertyValue("trigger_source", self.cfg.camera_parameters['trigger_source']) # external
        #self.hcam.setPropertyValue("internal_line_interval",self.camera_line_interval)

    def close_camera(self):
        self.hcam.shutdown()

    def set_camera_sensor_mode(self, mode):
        if mode == 'Area':
            self.hcam.setPropertyValue("sensor_mode", 1)
        elif mode == 'ASLM':
            self.hcam.setPropertyValue("sensor_mode", 12)
        else:
            print('Camera mode not supported')

    def set_exposure_time(self, time):
        self.hcam.setPropertyValue("exposure_time", time)

    def set_line_interval(self, time):
        self.hcam.setPropertyValue("internal_line_interval",self.camera_line_interval)

    def set_binning(self, binningstring):
        self.hcam.setPropertyValue("binning", binningstring)
        self.x_binning = int(binning_string[0])
        self.y_binning = int(binning_string[2])
        self.x_pixels = int(self.x_pixels / self.x_binning)
        self.y_pixels = int(self.y_pixels / self.y_binning)
        self.state['camera_binning'] = str(self.x_binning)+'x'+str(self.y_binning)

    def initialize_image_series(self):
        self.hcam.startAcquisition()

    def get_images_in_series(self):
        [frames, _] = self.hcam.getFrames()
        images = [np.reshape(aframe.getData(), (-1,self.x_pixels)) for aframe in frames]
        return images

    def close_image_series(self):
        self.hcam.stopAcquisition()

    def get_image(self):
        [frames, _] = self.hcam.getFrames()
        images = [np.reshape(aframe.getData(), (-1,self.x_pixels)) for aframe in frames]
        return images[0]

    def initialize_live_mode(self):
        self.hcam.setACQMode(mode = "run_till_abort")
        self.hcam.startAcquisition()

    def get_live_image(self):
        [frames, _] = self.hcam.getFrames()
        images = [np.reshape(aframe.getData(), (-1,self.x_pixels)) for aframe in frames]
        return images

    def close_live_mode(self):
        self.hcam.stopAcquisition()

