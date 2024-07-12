import sys
from PyQt5 import QtWidgets
import pyqtgraph as pg
import numpy as np

class CustomImageView(pg.ImageView):
    def __init__(self, *args, **kwargs):
        super(CustomImageView, self).__init__(*args, **kwargs)
        # Remove the default histogram
        self.ui.histogram.hide()
        self.ui.histogram.setParent(None)
        
        # Create a new histogram
        self.histogram = pg.HistogramLUTItem()
        
        # Add the new histogram to a different position
        # For example, position it below the image
        self.ui.gridLayout.addWidget(self.histogram, 2, 1, 1, 1)
        
        # Link the histogram to the image data
        self.histogram.setImageItem(self.imageItem)
        
def main():
    app = QtWidgets.QApplication(sys.argv)
    
    win = CustomImageView()
    win.show()
    
    # Generate a random image for demonstration
    img = np.random.normal(size=(100, 100))
    win.setImage(img)
    
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()
