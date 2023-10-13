'''
Tiny example GUI as a threading example
'''

import sys
import time
import logging
import qdarkstyle

from PyQt5 import QtWidgets

from modules.accordion_main_window import AccordionMainWindow
import config.config as cfg

timestr = time.strftime("%Y%m%d-%H%M%S")
logging_filename = timestr + '.log'
logging.basicConfig(filename='log/'+logging_filename, level=logging.INFO, format='%(asctime)-8s:%(levelname)s:%(threadName)s:%(thread)d:%(module)s:%(name)s:%(message)s')
logger = logging.getLogger(__name__)
logger.info('Accordion started')

def main():
    app = QtWidgets.QApplication(sys.argv)
    app.setStyleSheet(qdarkstyle.load_stylesheet(qt_api='pyqt5'))
    ex = AccordionMainWindow(cfg)
    ex.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()
