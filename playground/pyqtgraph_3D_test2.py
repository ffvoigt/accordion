"""
Demonstrates use of GLScatterPlotItem with rapidly-updating plots.
"""

import numpy as np

import pyqtgraph as pg
import pyqtgraph.opengl as gl
from pyqtgraph import functions as fn
from pyqtgraph.Qt import QtCore

app = pg.mkQApp("GLScatterPlotItem Example")
w = gl.GLViewWidget()
w.show()
w.setWindowTitle('pyqtgraph example: GLScatterPlotItem')
w.setCameraPosition(distance=20)

g = gl.GLGridItem()
w.addItem(g)

##
##  Second example shows a volume of points with rapidly updating color
##  and pxMode=True
##

pos = np.random.random(size=(1000000,3))
pos -= 0.5
pos *= [20,20,20]
pos[0] = (0,0,0)
color = np.ones((pos.shape[0], 4))
d2 = (pos**2).sum(axis=1)**0.5
size = np.random.random(size=pos.shape[0])*10
sp2 = gl.GLScatterPlotItem(pos=pos, color=(1,1,1,0.5), size=size)
phase = 0.

w.addItem(sp2)

##
##  Third example shows a grid of points with rapidly updating position
##  and pxMode = False
##

def update():
    ## update volume colors
    pos = np.random.random(size=(1000000,3))
    pos -= 0.5
    pos *= [20,20,20]
    sp2.setData(pos=pos)
    
    '''
    global phase, sp2, d2
    s = -np.cos(d2*2+phase)
    color = np.empty((len(d2),4), dtype=np.float32)
    color[:,3] = fn.clip_array(s * 0.1, 0., 1.)
    color[:,0] = fn.clip_array(s * 3.0, 0., 1.)
    color[:,1] = fn.clip_array(s * 1.0, 0., 1.)
    color[:,2] = fn.clip_array(s ** 3, 0., 1.)
    sp2.setData(color=color)
    phase -= 0.1
    '''
    
    ## update surface positions and colors
    '''
    global sp3, d3, pos3
    z = -np.cos(d3*2+phase)
    pos3[:,2] = z
    color = np.empty((len(d3),4), dtype=np.float32)
    color[:,3] = 0.3
    color[:,0] = np.clip(z * 3.0, 0, 1)
    color[:,1] = np.clip(z * 1.0, 0, 1)
    color[:,2] = np.clip(z ** 3, 0, 1)
    sp3.setData(pos=pos3, color=color)
    '''

t = QtCore.QTimer()
t.timeout.connect(update)
t.start(25)

if __name__ == '__main__':
    pg.exec()
