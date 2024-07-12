from PyQt5 import QtWidgets, QtCore

from PyQt5.uic import loadUi
import qdarkstyle

# from .worker import WorkerObject, AnotherWorkerObject
from .accordion_state import AccordionSingletonStateObject
from .accordion_event_camera import AccordionEventCamera
from .accordion_frame_camera import AccordionFrameCamera

import pyqtgraph as pg
import numpy as np

import logging
logger = logging.getLogger(__name__)

class AccordionMainWindow(QtWidgets.QMainWindow):
    '''
    Main application window which instantiates worker objects and moves them
    to a thread.
    '''
    sig_prepare_live = QtCore.pyqtSignal()
    sig_prepare_acq = QtCore.pyqtSignal()
    sig_run_live = QtCore.pyqtSignal()
    sig_run_acq = QtCore.pyqtSignal()
    sig_end_live = QtCore.pyqtSignal()
    sig_stop = QtCore.pyqtSignal()
    sig_roi_center = QtCore.pyqtSignal(np.ndarray)

    def __init__(self, config):
        super().__init__()

        self.cfg = config
        
        logger.info('Window thread ID at Startup: '+str(int(QtCore.QThread.currentThreadId())))
        print('Window thread ID at Startup: '+str(int(QtCore.QThread.currentThreadId())))
        logger.info('Ideal thread count: '+str(int(QtCore.QThread.idealThreadCount())))
        print('Ideal thread count: '+str(int(QtCore.QThread.idealThreadCount())))
        
        ''' Set up the UI '''
        loadUi('gui/accordion_gui2.ui', self)
        self.setWindowTitle('Accordion')

        self.initialize_and_connect_menubar()

        ''' Set up the basic slots '''
        self.startButton.clicked.connect(self.start)
        self.stopButton.clicked.connect(self.stop)

        ''' Setting up the state '''
        self.state = AccordionSingletonStateObject()
        self.state.state_updated.connect(lambda string: print('Window thread received state update: ',string))
        

        self.XY_plot_layout = self.eventCameraView.addLayout(row=0, col=0, rowspan=2, colspan=1, border=(50,50,0))
        self.XY_plot = self.XY_plot_layout.addPlot()
        # self.ET_plot = self.graphicsView.addPlot(row=2, col=0, rowspan=1, colspan=1, border=(50,50,0))
        # self.ET_region_selection_plot = self.graphicsView.addPlot(row=3, col=0, rowspan=1, colspan=1, border=(50,50,0))
        self.XY_plot.setAspectLocked(True, ratio=1.77)

        ''' Modify Frame Camera View '''
        self.frame_camera_image_item = self.frameCameraView.getImageItem()
        self.frameCameraView.setLevels(100,600)
        self.frameCameraView.setMinimumWidth(1000)
         # Hide Histogram if camera image isn't displayed
        if not self.cfg.startup['display_full_camera_frame']:
            self.frameCameraView.ui.histogram.hide()
        # Hide the buttons below the histogram
        self.frameCameraView.ui.roiBtn.hide()     
        self.frameCameraView.ui.menuBtn.hide()     
        self.frameCameraViewHistogram = self.frameCameraView.getHistogramWidget()
        self.frameCameraViewHistogram.setMinimumWidth(200)
        self.frameCameraViewHistogram.item.vb.setMaximumWidth(200)

        ''' Modify Crop View '''
        self.frame_camera_crop_image_item = self.frameCameraCropView.getImageItem()
        self.frameCameraCropView.setLevels(100,600)
        self.frameCameraCropView.setMinimumWidth(1000)
        # self.frameCameraCropView.ui.histogram.hide() # Hide Histogram if necessary
        # Hide the buttons below the histogram
        self.frameCameraCropView.ui.roiBtn.hide()     
        self.frameCameraCropView.ui.menuBtn.hide()    
        self.frameCameraCropViewHistogram = self.frameCameraView.getHistogramWidget()
        self.frameCameraCropViewHistogram.setMinimumWidth(200)
        self.frameCameraCropViewHistogram.item.vb.setMaximumWidth(200)


        # ON Plot?
        self.s4 = pg.ScatterPlotItem(
                    size=3,
                    pen=pg.mkPen(None),
                    brush=pg.mkBrush(255, 255, 255, 255),
                    hoverable=False,
                    hoverSymbol='s',
                    hoverSize=15,
                    hoverPen=pg.mkPen('r', width=2),
                    hoverBrush=pg.mkBrush('g'),
                    )
        
        # OFF Plot?
        self.s5 = pg.ScatterPlotItem(
                    size=3,
                    pen=pg.mkPen(None),
                    brush=pg.mkBrush(255, 255, 128, 128),
                    hoverable=False,
                    hoverSymbol='s',
                    hoverSize=15,
                    hoverPen=pg.mkPen('r', width=2),
                    hoverBrush=pg.mkBrush('g'),
                    )
        
        self.XY_plot.addItem(self.s4)
        self.XY_plot.addItem(self.s5)

        self.initialize_crosshairs()
        
        ''' Set the thread up '''
        self.event_camera_thread = QtCore.QThread()
        self.event_camera_worker = AccordionEventCamera(self)
        self.event_camera_worker.moveToThread(self.event_camera_thread)

        ''' Set the thread up '''
        self.frame_camera_thread = QtCore.QThread()
        self.frame_camera_worker = AccordionFrameCamera(self)
        self.frame_camera_worker.moveToThread(self.frame_camera_thread)

        ''' Create the connections / signal switchboard '''
        self.event_camera_worker.sig_camera_datachunk.connect(self.update_event_display)
        self.event_camera_worker.sig_roi_center.connect(self.update_roi_center)
        self.frame_camera_worker.sig_camera_frame.connect(self.update_frame_display)
        self.frame_camera_worker.sig_camera_crop_frame.connect(self.update_frame_crop_display)
        
        '''Start the thread'''
        self.event_camera_thread.start()
        self.frame_camera_thread.start()
        
    def __del__(self):
        '''Cleans the thread up after deletion, waits until the thread
        has truly finished its life.

        Uses "try" in case things crash before the thread was even started.
        '''
        try:
            self.event_camera_thread.quit()
            self.event_camera_thread.wait()
        except:
            pass

        try:
            self.frame_camera_thread.quit()
            self.frame_camera_thread.wait()
        except:
            pass
    
    @QtCore.pyqtSlot(np.ndarray)
    def update_event_display(self, datachunk):
        self.s4.clear()
        self.s4.setData(datachunk[:,0],datachunk[:,1])
        self.s5.clear()
        self.s5.setData(datachunk[:,0]+1,datachunk[:,1]+1)

    @QtCore.pyqtSlot(np.ndarray)
    def update_roi_center(self, roi_center):
        self.sig_roi_center.emit(roi_center)
        self.update_crosshairs(roi_center)

    @QtCore.pyqtSlot(np.ndarray)
    def update_frame_display(self, image):
        self.frameCameraView.setImage(image, autoLevels=False, autoHistogramRange=False, autoRange=False)

    @QtCore.pyqtSlot(np.ndarray)
    def update_frame_crop_display(self, image):
        self.frameCameraCropView.setImage(image, autoLevels=False, autoHistogramRange=False, autoRange=False)

    def initialize_and_connect_menubar(self):
        self.actionExit_2.triggered.connect(self.close_app)
        # self.actionOpen_File.triggered.connect(self.load_dataset)

    def initialize_crosshairs(self):
        self.crosspen = pg.mkPen({'color': "r", 'width': 1})
        x_image_width = self.cfg.frame_camera_parameters['x_pixels']/self.cfg.startup['camera_display_live_subsampling']
        y_image_width = self.cfg.frame_camera_parameters['y_pixels']/self.cfg.startup['camera_display_live_subsampling']
        x_center = x_image_width/2
        y_center = y_image_width/2
        self.vLine = pg.InfiniteLine(pos=x_center, angle=90, movable=False, pen=self.crosspen)
        self.hLine = pg.InfiniteLine(pos=y_center, angle=0, movable=False, pen=self.crosspen)
        self.frameCameraView.addItem(self.vLine, ignoreBounds=True)
        self.frameCameraView.addItem(self.hLine, ignoreBounds=True)

        ''' Draw bounding rectangle as well '''

        self.rect = pg.RectROI([0, 0], [x_image_width, y_image_width],pen=self.crosspen,movable=False, rotatable=False, resizable=False)
        self.rect.translatable = False
        for handle in self.rect.getHandles():
            handle.pen.setWidth(0)  # Making handles invisible
        self.frameCameraView.addItem(self.rect, ignoreBounds=True)

    def update_crosshairs(self, roi_center):
        x_image_width = self.cfg.frame_camera_parameters['x_pixels']/self.cfg.startup['camera_display_live_subsampling']
        y_image_width = self.cfg.frame_camera_parameters['y_pixels']/self.cfg.startup['camera_display_live_subsampling']
        self.vLine.setValue(roi_center[0]*x_image_width)
        self.hLine.setValue(roi_center[1]*y_image_width)
    
    def close_app(self):
        self.__del__()
        self.close()

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
        # self.sig_start.emit()
        self.sig_prepare_live.emit()
        self.sig_run_live.emit()

    def stop(self):
        # self.sig_stop.emit()
        self.sig_end_live.emit()


