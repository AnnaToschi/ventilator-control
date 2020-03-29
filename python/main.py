import sys
from pyqtgraph.Qt import QtGui, QtCore
import pyqtgraph as pg
import numpy as np
import math

import struct
import numpy

import os
import re
import pickle

os.environ['EPICS_CA_ADDR_LIST'] = 'localhost'
os.environ['EPICS_CA_AUTO_ADDR_LIST'] = 'NO'


class tabdemo(QtGui.QTabWidget):
  
  def __init__(self, parent = None):

    self.accelBufferX = (0,0)

    self.BGCOLOR = pg.mkColor(220,220,220)
    self.FGCOLOR = pg.mkColor(100,100,100)
    self.plotcolor = QtGui.QColor(76,100,230)
    self.PLTWIDTH = 2

    super(tabdemo, self).__init__(parent)
    
    self.activeTab = 1
    self.activeChannel = 1

    self.channelAccelX = [0]*1000
    self.channelAccelY = [0]*1000
    self.channelAccelZ = [0]*1000

    pg.setConfigOption('background', self.BGCOLOR)
    pg.setConfigOption('foreground', self.FGCOLOR)
    pg.setConfigOptions(useOpenGL=True)
   
    pen = pg.mkPen(color = self.plotcolor, width = 3)
    
    self.graphAccel_x = pg.PlotWidget()
    self.accelDataX = pg.PlotCurveItem()
    self.graphAccel_x.addItem(self.accelDataX)
    self.graphAccel_y = pg.PlotWidget()
    self.accelDataY = pg.PlotCurveItem()
    self.graphAccel_y.addItem(self.accelDataY)
    self.graphAccel_z = pg.PlotWidget()
    self.accelDataZ = pg.PlotCurveItem()
    self.graphAccel_z.addItem(self.accelDataZ)

    self.graphAccel_x.setLabel('left', "Flow", "L/min")
    self.graphAccel_x.setLabel('bottom', "Number of points")
    self.graphAccel_x.setTitle("Flow ")

    self.graphAccel_y.setLabel('left', "Volume", "mL")
    self.graphAccel_y.setLabel('bottom', "Number of points")
    self.graphAccel_y.setTitle("Volume ")

    self.graphAccel_z.setLabel('left', "Pressure", "cmH20")
    self.graphAccel_z.setLabel('bottom', "Number of points")
    self.graphAccel_z.setTitle("Pressure ")
    
    self.tabConnect = QtGui.QWidget()	#connect
    self.tabAccel = QtGui.QWidget() #accel
    self.connectTabIndex = self.addTab(self.tabConnect,"Connect") + 1
    self.accelTabIndex = self.addTab(self.tabAccel,"Accel Data") + 1

    self.connectTabUI()
    self.accelTabUI()
    self.connectTabs()
    
    self.setWindowTitle("Ventilator")
  
    
  def connectTabUI(self):
    layout = QtGui.QVBoxLayout()
    self.tabConnect.setLayout(layout)

  def changeDDMenu(self):
    self.activeChannel = self.ddMenu.currentIndex() + 1
    self.counter = 0
    self.channeldata = [0]*5000


  def tabChanged(self):
    lastActiveTab = self.activeTab
    print("lastActive:", lastActiveTab)
    self.activeTab = self.currentIndex() + 1
    print("Active:", self.activeTab)
    

    if(self.activeTab == self.accelTabIndex):
      print("tab tabAccel")
      self.channelAccelX = [0]*1000
      self.channelAccelY = [0]*1000
      self.channelAccelZ = [0]*1000
      self.counterAccel = 0
    else:
      self.counter = 0

    
  def connectTabs(self):
    self.currentChanged.connect(self.tabChanged)
    
  def updateGraphs(self):

    if(self.activeTab == self.accelTabIndex): #accel

        accelBufferX[2] = caget('Raspi:central:Sensor-Pinsp')
        accelBufferX[0] = caget('Raspi:central:Sensor-TotalFlow')
        accelBufferX[1] = caget('Raspi:central:Sensor-Vt')

        self.channelAccelX[self.counterAccel] = accelBufferX[0]
        self.channelAccelY[self.counterAccel] = accelBufferX[1]
        self.channelAccelZ[self.counterAccel] = accelBufferX[2]
        self.counterAccel += 1
        if(self.counterAccel == 1000):
          self.counterAccel = 0
        self.accelDataX.setData(self.channelAccelX,pen= self.plotcolor)
        self.accelDataY.setData(self.channelAccelY,pen= self.plotcolor)
        self.accelDataZ.setData(self.channelAccelZ,pen= self.plotcolor)

    else: # game
      channel = self.activeChannel

  def accelTabUI(self):
    layoutAccel = QtGui.QVBoxLayout()
    layoutAccel.addWidget(self.graphAccel_x)
    layoutAccel.addWidget(self.graphAccel_y)
    layoutAccel.addWidget(self.graphAccel_z)
    self.tabAccel.setLayout(layoutAccel)
    self.updateGraphs()

  def keyPressEvent(self, event):
    # Did the user press the Escape key?
    if event.key() == QtCore.Qt.Key_Escape: # QtCore.Qt.Key_Escape is a value that equates to what the operating system passes to python from the keyboard when the escape key is pressed.
      # Yes: Close the window
      self.app_after_exit = 0
      self.close()
  
  def start_plotting(self):
    timer = QtCore.QTimer()
    timer.timeout.connect(self.updateGraphs)
    self.start()


def main():
  app = QtGui.QApplication(sys.argv)
  ex = tabdemo()
  ex.show()
  sys.exit(app.exec_())

if __name__ == '__main__':
  main()
