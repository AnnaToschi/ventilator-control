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

from epics import caget

#os.environ['EPICS_CA_ADDR_LIST'] = 'localhost'
#os.environ['EPICS_CA_AUTO_ADDR_LIST'] = 'NO'


class VentilatorWindow(QtGui.QTabWidget):
  
  def __init__(self, parent = None):

    super(VentilatorWindow, self).__init__(parent)
    
    self.accelBufferX = (0,0)

    self.BGCOLOR = pg.mkColor(220,220,220)
    self.FGCOLOR = pg.mkColor(100,100,100)
    self.plotcolor = QtGui.QColor(76,100,230)
    self.PLTWIDTH = 2

    self.activeTab = 1
    self.activeChannel = 1

    self.channelAccelX = [0]*600
    self.channelAccelY = [0]*600
    self.channelAccelZ = [0]*600

    pg.setConfigOption('background', self.BGCOLOR)
    pg.setConfigOption('foreground', self.FGCOLOR)
    pg.setConfigOptions(useOpenGL=True)
   
    pen = pg.mkPen(color = self.plotcolor, width = 3)
    
    self.basePlot = pg.PlotCurveItem([0]*600, pen = self.plotcolor) 
    self.basePlotX = pg.PlotCurveItem([0]*600, pen = self.plotcolor) 

    self.graphFlow = pg.PlotWidget()
    self.flowData = pg.PlotCurveItem()
    self.pfillX = pg.FillBetweenItem(self.flowData, self.basePlotX, brush = self.plotcolor)
    self.graphFlow.addItem(self.flowData)
    self.graphFlow.addItem(self.basePlotX)
    self.graphFlow.addItem(self.pfillX)

    self.graphVolume = pg.PlotWidget()
    self.volumeData = pg.PlotCurveItem()
    self.pfillY = pg.FillBetweenItem(self.volumeData, self.basePlot, brush = self.plotcolor)
    self.graphVolume.addItem(self.volumeData)
    self.graphVolume.addItem(self.basePlot)
    self.graphVolume.addItem(self.pfillY)
    
    self.graphPressure = pg.PlotWidget()
    self.pressureData = pg.PlotCurveItem()
    self.pfillZ = pg.FillBetweenItem(self.pressureData, self.basePlot, brush = self.plotcolor)
    self.graphPressure.addItem(self.pressureData)
    self.graphPressure.addItem(self.basePlot)
    self.graphPressure.addItem(self.pfillZ)

    self.graphFlow.setLabel('left', "Flow", "L/min")
    self.graphFlow.setLabel('bottom', "Number of points")
    self.graphFlow.setTitle("Flow ")

    self.graphVolume.setLabel('left', "Volume", "mL")
    self.graphVolume.setLabel('bottom', "Number of points")
    self.graphVolume.setTitle("Volume ")

    self.graphPressure.setLabel('left', "Pressure", "cmH20")
    self.graphPressure.setLabel('bottom', "Number of points")
    self.graphPressure.setTitle("Pressure ")
    
    self.tabConnect = QtGui.QWidget()	#connect
    self.tabAccel = QtGui.QWidget() #accel
    self.connectTabIndex = self.addTab(self.tabConnect,"Connect") + 1
    self.plotTabIndex = self.addTab(self.tabAccel,"Accel Data") + 1

    self.connectTabUI()
    self.accelTabUI()
    self.connectTabs()
    
    self.setWindowTitle("Ventilator")
    self.start_plotting()
  
    
  def connectTabUI(self):
    layout = QtGui.QVBoxLayout()
    self.tabConnect.setLayout(layout)

  def tabChanged(self):
    lastActiveTab = self.activeTab
    print("lastActive:", lastActiveTab)
    self.activeTab = self.currentIndex() + 1
    print("Active:", self.activeTab)
    

    if(self.activeTab == self.plotTabIndex):
      print("tab tabAccel")
      self.channelFlow = [0]*600
      self.channelVolume = [0]*600
      self.channelPressure = [0]*600
      self.counterPlots = 0

    
  def connectTabs(self):
    self.currentChanged.connect(self.tabChanged)
    
  def updateGraphs(self):
    if(self.activeTab == self.plotTabIndex): #accel

        self.channelFlow[self.counterPlots] = caget('Raspi:central:Sensor-Finsp') - 50
        self.channelVolume[self.counterPlots] = caget('Raspi:central:Sensor-Vt')
        self.channelPressure[self.counterPlots] = caget('Raspi:central:Sensor-Pinsp')
        self.counterPlots += 1
        if(self.counterPlots == 600):
          self.counterPlots = 0
        self.flowData.setData(self.channelFlow,pen= self.plotcolor)
        self.volumeData.setData(self.channelVolume,pen= self.plotcolor)
        self.pressureData.setData(self.channelPressure,pen= self.plotcolor)

  def accelTabUI(self):
    layoutAccel = QtGui.QVBoxLayout()
    layoutAccel.addWidget(self.graphFlow)
    layoutAccel.addWidget(self.graphVolume)
    layoutAccel.addWidget(self.graphPressure)
    self.tabAccel.setLayout(layoutAccel)
    self.updateGraphs()

  def keyPressEvent(self, event):
    # Did the user press the Escape key?
    if event.key() == QtCore.Qt.Key_Escape: # QtCore.Qt.Key_Escape is a value that equates to what the operating system passes to python from the keyboard when the escape key is pressed.
      self.app_after_exit = 0
      self.close()

  def start(self):
    if (sys.flags.interactive != 1) or not hasattr(QtCore, 'PYQT_VERSION'):
        QtGui.QApplication.instance().exec_()
  
  def start_plotting(self):
    self.timer = QtCore.QTimer()
    self.timer.setInterval(10)
    self.timer.timeout.connect(self.updateGraphs)
    self.timer.start()

def main():
  app = QtGui.QApplication(sys.argv)
  win = VentilatorWindow()
  win.show()
  sys.exit(app.exec_())

if __name__ == '__main__':
  main()
