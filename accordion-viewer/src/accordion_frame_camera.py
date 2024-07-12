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
    sig_camera_crop_frame = QtCore.pyqtSignal(np.ndarray)
    sig_finished = QtCore.pyqtSignal()
    sig_update_gui_from_state = QtCore.pyqtSignal(bool)
    sig_status_message = QtCore.pyqtSignal(str)
    sig_framerate = QtCore.pyqtSignal(float)

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

        self.roi_center = [0.5,0.5]
        self.x_roi_pixels = self.cfg.frame_camera_parameters['x_roi_pixels']
        self.y_roi_pixels = self.cfg.frame_camera_parameters['y_roi_pixels']

        self.binning_string = self.cfg.frame_camera_parameters['binning'] # Should return a string in the form '2x4'
        self.x_binning = int(self.binning_string[0])
        self.y_binning = int(self.binning_string[2])

        self.x_pixels = int(self.x_pixels / self.x_binning)
        self.y_pixels = int(self.y_pixels / self.y_binning)

        self.camera_exposure_time = self.cfg.startup['camera_exposure_time']

        self.camera_display_live_subsampling = self.cfg.startup['camera_display_live_subsampling']
        self.camera_display_acquisition_subsampling = self.cfg.startup['camera_display_acquisition_subsampling']
        self.camera_frame_cropping_enabled = self.cfg.startup['camera_frame_cropping_enabled']
        self.display_full_camera_frame = self.cfg.startup['display_full_camera_frame']

        ''' Wiring signals '''
        self.parent.sig_prepare_live.connect(self.prepare_live)
        self.parent.sig_run_live.connect(self.run_live)
        self.parent.sig_end_live.connect(self.end_live)
        self.parent.sig_roi_center.connect(self.update_roi_center)

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

    @QtCore.pyqtSlot(np.ndarray)
    def update_roi_center(self, roi_center):
        self.roi_center = roi_center


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
        self.stopflag = False
       
    def open_camera(self):
        ''' Hamamatsu-specific code '''
        self.camera_id = self.cfg.frame_camera_parameters['camera_id']

        from .devices.frame_cameras.hamamatsu import hamamatsu_camera as cam
        # if self.cfg.camera == 'HamamatsuOrca':
        self.hcam = cam.HamamatsuCameraMR(camera_id=self.camera_id)
        ''' Debbuging information '''
        logger.info(f'Initialized Hamamatsu camera model: {self.hcam.getModelInfo(self.camera_id)}')

        ''' Ideally, the Hamamatsu Camera properties should be set in this order '''

        ''' Accordion mode parameters '''
        self.hcam.setPropertyValue("sensor_mode", self.cfg.frame_camera_parameters['sensor_mode'])

        self.hcam.setPropertyValue("defect_correct_mode", self.cfg.frame_camera_parameters['defect_correct_mode'])
        self.hcam.setPropertyValue("exposure_time", self.camera_exposure_time)
        self.hcam.setPropertyValue("binning", self.cfg.frame_camera_parameters['binning'])
        self.hcam.setPropertyValue("readout_speed", self.cfg.frame_camera_parameters['readout_speed'])

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

    def initialize_live_mode(self):
        self.stopflag = False
        self.hcam.setACQMode(mode = "run_till_abort")
        self.hcam.startAcquisition()

    def run_live_mode(self):
        i = 0

        x_roi_halfwidth = int(self.parent.cfg.frame_camera_parameters['x_roi_pixels']/2)
        y_roi_halfwidth = int(self.parent.cfg.frame_camera_parameters['y_roi_pixels']/2)
        x_pixels = self.parent.cfg.frame_camera_parameters['x_pixels']
        y_pixels = self.parent.cfg.frame_camera_parameters['y_pixels']

        start_time = time.time()
        while self.stopflag is False:
            [frames, dims] = self.hcam.getFrames()

            for aframe in frames:
                image = aframe.getData()
                image = np.reshape(image, (-1, 2048))

                if self.parent.camera_frame_cropping_enabled:
                    x_center = int(self.parent.roi_center[0]*x_pixels)
                    y_center = int(self.parent.roi_center[1]*y_pixels)

                    cropped_frame = image[x_center-x_roi_halfwidth:x_center+x_roi_halfwidth,y_center-y_roi_halfwidth:y_center+y_roi_halfwidth]
                    self.parent.sig_camera_crop_frame.emit(cropped_frame)

                if self.parent.display_full_camera_frame:
                    image = image[::self.parent.camera_display_live_subsampling, ::self.parent.camera_display_live_subsampling]
                    self.parent.sig_camera_frame.emit(image)

                i += 1

                QtWidgets.QApplication.processEvents()

        self.hcam.stopAcquisition()
        end_time = time.time()
        framerate = i/(end_time - start_time)
        print("Framerate :", str(framerate))

    def stop_live_mode(self):
        self.stopflag = True
    



