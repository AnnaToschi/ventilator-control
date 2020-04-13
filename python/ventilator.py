from PyQt5.QtWidgets import QMainWindow, QApplication, QPushButton, QTextEdit, QDialog, QWidget, QMessageBox
from PyQt5 import uic, QtGui, QtCore, QtWidgets
import pyqtgraph as pg
import sys
from epics import caget, caput
import numpy as np

x_axis_length = 200;
MAXVAL = 650000

class RangeSliderClass(QtWidgets.QWidget):

    def __init__(self):
        super().__init__()

        self.minTime = 0
        self.maxTime = 0
        self.minRangeTime = 0
        self.maxRangeTime = 0

        self.sliderMin = MAXVAL
        self.sliderMax = MAXVAL

        self.setupUi(self)

    def setupUi(self, RangeSlider):
        RangeSlider.setObjectName("RangeSlider")
        RangeSlider.resize(1000, 65)
        RangeSlider.setMaximumSize(QtCore.QSize(16777215, 65))
        self.RangeBarVLayout = QtWidgets.QVBoxLayout(RangeSlider)
        self.RangeBarVLayout.setContentsMargins(5, 0, 5, 0)
        self.RangeBarVLayout.setSpacing(0)
        self.RangeBarVLayout.setObjectName("RangeBarVLayout")

        self.slidersFrame = QtWidgets.QFrame(RangeSlider)
        self.slidersFrame.setMaximumSize(QtCore.QSize(16777215, 25))
        self.slidersFrame.setFrameShape(QtWidgets.QFrame.StyledPanel)
        self.slidersFrame.setFrameShadow(QtWidgets.QFrame.Raised)
        self.slidersFrame.setObjectName("slidersFrame")
        self.horizontalLayout = QtWidgets.QHBoxLayout(self.slidersFrame)
        self.horizontalLayout.setSizeConstraint(QtWidgets.QLayout.SetMinimumSize)
        self.horizontalLayout.setContentsMargins(5, 2, 5, 2)
        self.horizontalLayout.setSpacing(0)
        self.horizontalLayout.setObjectName("horizontalLayout")

        ## Start Slider Widget
        self.startSlider = QtWidgets.QSlider(self.slidersFrame)
        self.startSlider.setMaximum(self.sliderMin)
        self.startSlider.setMinimumSize(QtCore.QSize(100, 5))
        self.startSlider.setMaximumSize(QtCore.QSize(16777215, 10))

        font = QtGui.QFont()
        font.setKerning(True)

        self.startSlider.setFont(font)
        self.startSlider.setAcceptDrops(False)
        self.startSlider.setAutoFillBackground(False)
        self.startSlider.setOrientation(QtCore.Qt.Horizontal)
        self.startSlider.setInvertedAppearance(True)
        self.startSlider.setObjectName("startSlider")
        self.startSlider.setValue(MAXVAL)
        self.startSlider.valueChanged.connect(self.handleStartSliderValueChange)
        self.horizontalLayout.addWidget(self.startSlider)

        ## End Slider Widget
        self.endSlider = QtWidgets.QSlider(self.slidersFrame)
        self.endSlider.setMaximum(MAXVAL)
        self.endSlider.setMinimumSize(QtCore.QSize(100, 5))
        self.endSlider.setMaximumSize(QtCore.QSize(16777215, 10))
        self.endSlider.setTracking(True)
        self.endSlider.setOrientation(QtCore.Qt.Horizontal)
        self.endSlider.setObjectName("endSlider")
        self.endSlider.setValue(self.sliderMax)
        self.endSlider.valueChanged.connect(self.handleEndSliderValueChange)

        #self.endSlider.sliderReleased.connect(self.handleEndSliderValueChange)

        self.horizontalLayout.addWidget(self.endSlider)

        self.RangeBarVLayout.addWidget(self.slidersFrame)

        #self.retranslateUi(RangeSlider)
        QtCore.QMetaObject.connectSlotsByName(RangeSlider)

        self.show()

    @QtCore.pyqtSlot(int)
    def handleStartSliderValueChange(self, value):
        self.startSlider.setValue(value)

    @QtCore.pyqtSlot(int)
    def handleEndSliderValueChange(self, value):
        self.endSlider.setValue(value)


class VentilatorWindow(QDialog):
    def __init__(self):
        super(VentilatorWindow, self).__init__()
        uic.loadUi("dashboard_ventilator.ui", self)

        self.start_timer()

        self.PlotsWidget = PlotsWidget(parent=self)
        self.SettingsWidget_VC = SettingsWidget_VC(parent=self)
        self.stacked_area.addWidget(self.PlotsWidget)
        self.SettingsWidget_VC.readInitialValues()
        self.stacked_area.addWidget(self.SettingsWidget_VC)
        self.stacked_area.setCurrentWidget(self.PlotsWidget)
        self.timer.timeout.connect(self.PlotsWidget.updateGraphs)
        self.setButton.clicked.connect(self.toggleStackedArea)
        self.stackedArea_flag = 0
        self.chooseOPMODEbutton.addItem("Volume Control")
        self.chooseOPMODEbutton.addItem("Pressure Control")
        self.chooseOPMODEbutton.addItem("Pressure Support")
        self.chooseOPMODEbutton.currentIndexChanged.connect(self.changeOPMODE)

        self.currentMode = caget('Raspi:central:OPMODE')
        if self.currentMode == 2:
            self.currentModeLabel.setText('Volume Control')
        elif self.currentMode == 3:
            self.currentModeLabel.setText('Pressure Control')
        elif self.currentMode == 4: 
            self.currentModeLabel.setText('Pressure Support')
        else:   
            self.currentModeLabel.setText('No mode Selected')


        self.msg = QMessageBox()
        awindow = RangeSliderClass()

        self.setWindowTitle("Ventilator")

    def start_timer(self):
        self.timer = QtCore.QTimer()
        self.timer.setInterval(50)
        self.timer.timeout.connect(self.updateBottomBarValues)
        self.timer.start()

    def check_alarms(self):
        pass
        #if self.sensorMVvar > caget('Raspi:central:Minute-Volume')

    def changeOPMODE(self, i):
        if i==0:
            self.currentModeLabel.setText('Volume Control')
            caput('Raspi:central:OPMODE',2)
        elif i==1:
            self.currentModeLabel.setText('Pressure Control')
            caput('Raspi:central:OPMODE',3)
        elif i==2:
            self.currentModeLabel.setText('Pressure Support')
            caput('Raspi:central:OPMODE',4)


    def toggleStackedArea(self):
        if self.stackedArea_flag == 1: #I am in the settings view and want to change to show plots
            self.stacked_area.setCurrentWidget(self.PlotsWidget)
            self.PlotsWidget.initializeGraphs()
            self.timer.timeout.connect(self.PlotsWidget.updateGraphs)
            try:
                self.timer.timeout.disconnect(self.SettingsWidget_VC.updateValues)
            except:
                print('nothing to disconnect')
            self.stackedArea_flag = 0
            print('here')
            self.SettingsWidget_VC.commitValueChanges()
            self.setButton.setStyleSheet("color: rgb(3, 43, 91);")
            self.setButton.setText('Set\nValues')
        elif self.stackedArea_flag == 0 and self.chooseOPMODEbutton.currentText()=='Volume Control': #I am in the plots view and want to change to show VC settings
            self.timer.timeout.connect(self.SettingsWidget_VC.updateValues)
            try:
                self.timer.timeout.disconnect(self.PlotsWidget.updateGraphs)
            except:
                print('nothing to disconnect')
            self.stacked_area.setCurrentWidget(self.SettingsWidget_VC)
            self.stackedArea_flag = 1
            self.setButton.setStyleSheet("background-color: #00e64d;");
        elif self.stackedArea_flag == 0 and self.chooseOPMODEbutton.currentText()=='Pressure Control':
            print('Pressure Control')
        elif self.stackedArea_flag == 0 and self.chooseOPMODEbutton.currentText()=='Pressure Support':
            print('Pressure Support')

    def updateBottomBarValues(self):
        self.sensorMVvar.setText("{:.1f}".format(caget('Raspi:central:Minute-Volume')))
        self.sensorVtvar.setText("{:.1f}".format(caget('Raspi:central:Sensor-Max-Vol')))
        self.sensorRRvar.setText("{:.1f}".format(caget('Raspi:central:Sensor-RR')))
        self.sensorFiO2var.setText("{:.1f}".format(caget('Raspi:central:Sensor-FiO2')))
        self.sensorPIPvar.setText("{:.1f}".format(caget('Raspi:central:Sensor-Ppeak')))
        self.sensorPEEPvar.setText("{:.1f}".format(caget('Raspi:central:Sensor-PEEP')))
        self.sensorIEvar.setText("{:.1f}".format(caget('Raspi:central:Sensor-RR')))

        self.setVtvar_btm.setText("{:.0f}".format(caget('Raspi:central:Set-Vt')))
        self.setRRvar_btm.setText("{:.0f}".format(caget('Raspi:central:Set-RespRate')))
        self.setTinspvar_btm.setText("{:.1f}".format(caget('Raspi:central:Set-Tinsp')))
        self.setPEEPvar_btm.setText("{:.0f}".format(caget('Raspi:central:Set-PEEP')))

        self.check_alarms()

    def keyPressEvent(self, event):
        # Did the user press the Escape key?
        if event.key() == QtCore.Qt.Key_Escape: # QtCore.Qt.Key_Escape is a value that equates to what the operating system passes to python from the keyboard when the escape key is pressed.
          self.app_after_exit = 0
          self.close()

class SettingsWidget_VC(QWidget):
    def __init__(self, parent=None):
        super(SettingsWidget_VC, self).__init__(parent)
        uic.loadUi("settingsWidget_VC.ui", self)

        self.scrollbarSettings = """
                QScrollArea {
                    border: none;
                }
                QScrollBar {
                    background: gray;
                    border-radius: 3px;
                    min-height: 40px;
                }
                QScrollBar:horizontal {
                    height: 13px;
                }
                QScrollBar::handle:horizontal {
                    background: #285ec9;
                    min-width: 50px;
                    border-radius: 3px;
                }
                QScrollBar::handle:horizontal:hover{
                    background: #ebb028
                }
                QScrollBar::add-line {
                    border-left: -20px;
                    background: none;
                }
                QScrollBar::sub-line {
                    border-right: -20px;
                    background: none;
                }
            """

        self.setTinspScrollBar.setStyleSheet(self.scrollbarSettings)
        self.setTplateauScrollBar.setStyleSheet(self.scrollbarSettings)
        self.setRRScrollBar.setStyleSheet(self.scrollbarSettings)
        self.setPEEPScrollBar.setStyleSheet(self.scrollbarSettings)
        self.setVtScrollBar.setStyleSheet(self.scrollbarSettings)
        
        self.setTinspScrollBar.setPageStep(1)
        self.setTplateauScrollBar.setPageStep(1)
        self.setTinspScrollBar.setSingleStep(1)
        self.setRRScrollBar.setPageStep(1)
        self.setPEEPScrollBar.setPageStep(1)
        self.setVtScrollBar.setPageStep(5)


        self.setTinspScrollBar.setMaximum(caget('Raspi:central:Set-Tinsp.DRVH')*10)
        self.setRRScrollBar.setMaximum(30*10)
        self.setPEEPScrollBar.setMaximum(caget('Raspi:central:Set-PEEP.DRVH'))
        self.setVtScrollBar.setMaximum(caget('Raspi:central:Set-Vt.DRVH'))
        self.setTplateauScrollBar.setMaximum(caget('Raspi:central:Set-Tinsp.DRVH')*10)


        self.setTinspScrollBar.setMinimum(caget('Raspi:central:Set-Tinsp.DRVL')*10)
        self.setTplateauScrollBar.setMinimum(caget('Raspi:central:Set-Tinsp.DRVL')*10)
        self.setRRScrollBar.setMinimum(caget('Raspi:central:Set-RespRate.DRVL')*10)
        self.setPEEPScrollBar.setMinimum(caget('Raspi:central:Set-PEEP.DRVL'))
        self.setVtScrollBar.setMinimum(caget('Raspi:central:Set-Vt.DRVL'))
        self.readInitialValues()
        self.updateValues()

    def readInitialValues(self):

        self.valueTinsp = caget('Raspi:central:Set-Tinsp')
        self.valueTplateau = caget('Raspi:central:Set-Tplateau')
        self.valueRR = caget('Raspi:central:Set-RespRate')
        self.valueVt = caget('Raspi:central:Set-Vt')
        self.valuePEEP = caget('Raspi:central:Set-PEEP')


        self.setTinspScrollBar.setValue(self.valueTinsp * 10)
        self.setTplateauScrollBar.setValue(self.valueTplateau * 10)
        self.setRRScrollBar.setValue(self.valueRR*10)
        self.setPEEPScrollBar.setValue(self.valuePEEP)
        self.setVtScrollBar.setValue(self.valueVt)

    def updateValues(self): 

        self.setTinspvar_setting.setText("{:.1f}".format(self.valueTinsp))
        self.setTplateauvar_setting.setText("{:.1f}".format(self.valueTplateau))
        self.setRRvar_setting.setText("{:.1f}".format(self.valueRR))
        self.setVtvar_setting.setText("{:.0f}".format(self.valueVt))
        self.setPEEPvar_setting.setText("{:.0f}".format(self.valuePEEP))

        self.valueTinsp = (self.setTinspScrollBar.value() / 10)
        self.valueTplateau = (self.setTplateauScrollBar.value() / 10)
        self.valueRR = (self.setRRScrollBar.value() / 10)
        self.valuePEEP = self.setPEEPScrollBar.value()
        self.valueVt = self.setVtScrollBar.value()


    def commitValueChanges(self):
        print('Commiting values')
        self.valueTinsp = (self.setTinspScrollBar.value() / 10)
        self.valueTplateau = (self.setTplateauScrollBar.value() / 10)
        self.valueRR = (self.setRRScrollBar.value() / 10)
        
        if((self.valueTinsp+self.valueTplateau)>(60/self.valueRR - 0.3)):
            self.parent().parent().msg.setText('Values of RR and Tinsp do not match. RR was corrected to maximum value allowed.')
            self.parent().parent().msg.setIcon(QMessageBox.Warning)
            self.parent().parent().msg.exec_()
            self.valueTinsp = caget('Raspi:central:Set-Tinsp')
            self.valueTplateau = caget('Raspi:central:Set-Tplateau')
            self.valueRR = caget('Raspi:central:Set-RespRate')
            self.valueVt = caget('Raspi:central:Set-Vt')
            self.valuePEEP = caget('Raspi:central:Set-PEEP')


            self.setTinspScrollBar.setValue(self.valueTinsp * 10)
            self.setTplateauScrollBar.setValue(self.valueTplateau * 10)
            self.setRRScrollBar.setValue(self.valueRR*10)
            self.setPEEPScrollBar.setValue(self.valuePEEP)
            self.setVtScrollBar.setValue(self.valueVt)

            self.setTinspvar_setting.setText("{:.1f}".format(self.valueTinsp))
            self.setTplateauvar_setting.setText("{:.1f}".format(self.valueTplateau))
            self.setRRvar_setting.setText("{:.1f}".format(self.valueRR))
            self.setVtvar_setting.setText("{:.0f}".format(self.valueVt))
            self.setPEEPvar_setting.setText("{:.0f}".format(self.valuePEEP))

        else:
            caput('Raspi:central:Set-Tinsp', self.valueTinsp)
            self.setTinspvar_setting.setText("{:.1f}".format(self.valueTinsp))
            caput('Raspi:central:Set-Tplateau', self.valueTplateau)
            self.setTplateauvar_setting.setText("{:.1f}".format(self.valueTplateau))
            caput('Raspi:central:Set-RespRate',self.valueRR)
            self.setRRvar_setting.setText("{:.1f}".format(self.valueRR))

            self.valueVt = self.setVtScrollBar.value()
            caput('Raspi:central:Set-Vt',self.valueVt)
            self.setVtvar_setting.setText("{:.0f}".format(self.valueVt))

            self.valuePEEP = self.setPEEPScrollBar.value()
            caput('Raspi:central:Set-PEEP',self.valuePEEP)
            self.setPEEPvar_setting.setText("{:.0f}".format(self.valuePEEP))


        






    #     self.setValuesTinsp()
    #     self.setValuesTplateau()
    #     self.setValuesRR()
    #     self.setValuesVt()
    #     self.setValuesPEEP()

    # def setValuesTinsp(self):
    #     self.valueTinsp = (self.setTinspScrollBar.value() / 10)
    #     caput('Raspi:central:Set-Tinsp', self.valueTinsp)
    #     self.setTinspvar_setting.setText("{:.1f}".format(self.valueTinsp))

    # def setValuesTplateau(self):
    #     self.valueTplateau = (self.setTplateauScrollBar.value() / 10)
    #     caput('Raspi:central:Set-Tplateau', self.valueTplateau)
    #     self.setTplateauvar_setting.setText("{:.1f}".format(self.valueTplateau))


    # def setValuesRR(self):
    #     self.valueRR = (self.setRRScrollBar.value() / 10)
    #     if((self.valueTinsp+self.valueTplateau)>(60/self.valueRR - 0.3)):
    #         self.parent().parent().msg.setText('Values of RR and Tinsp do not match. RR was corrected to maximum value allowed.')
    #         self.parent().parent().msg.setIcon(QMessageBox.Warning)
    #         self.parent().parent().msg.exec_()
    #     else:       
    #         caput('Raspi:central:Set-RespRate',self.valueRR)
    #         self.valueRR = (caget('Raspi:central:Set-RespRate') )
    #         #print(self.valueRR )
    #         self.setRRvar_setting.setText("{:.1f}".format(self.valueRR))
        
    # def setValuesVt(self):
    #     self.valueVt = self.setVtScrollBar.value()
    #     caput('Raspi:central:Set-Vt',self.valueVt)
    #     self.setVtvar_setting.setText("{:.0f}".format(self.valueVt))

    # def setValuesPEEP(self):
    #     self.valuePEEP = self.setPEEPScrollBar.value()
    #     caput('Raspi:central:Set-PEEP',self.valuePEEP)
    #     self.setPEEPvar_setting.setText("{:.0f}".format(self.valuePEEP))


class PlotsWidget(QWidget):
    def __init__(self, parent=None):
        super(PlotsWidget, self).__init__(parent)
        uic.loadUi("plotsWidget.ui", self)

        #self.manualVentButton.setCheckable(True)
        #self.manualVentButton.toggle()
        self.manualVentButton.pressed.connect(self.manualVentilationPressed)
        self.manualVentButton.released.connect(self.manualVentilationReleased)


        #self.manualPauseButton.setCheckable(True)
        #self.manualPauseButton.toggle()
        self.manualPauseButton.pressed.connect(self.manualPausePressed)
        self.manualPauseButton.released.connect(self.manualVentilationReleased)

        self.accelBufferX = (0,0)

        self.BGCOLOR = QtGui.QColor(220,220,220)
        self.FGCOLOR = QtGui.QColor(255,0,0)
        self.plotcolor = QtGui.QColor(26, 76, 156)
        self.PLTWIDTH = 2

        self.basePlotFlow = pg.PlotCurveItem([0]*x_axis_length, pen = self.plotcolor)
        self.basePlotVol = pg.PlotCurveItem([0]*x_axis_length, pen = self.plotcolor) 
        self.basePlotPres = pg.PlotCurveItem([0]*x_axis_length, pen = self.plotcolor)

        #self.graphFlow = pg.PlotWidget()
        self.flowData = pg.PlotCurveItem()
        self.pfillX = pg.FillBetweenItem(self.flowData, self.basePlotFlow, brush = self.plotcolor)
        self.graphFlow.addItem(self.flowData)
        self.graphFlow.addItem(self.basePlotFlow)
        self.graphFlow.addItem(self.pfillX)

        #self.graphVolume = pg.PlotWidget()
        self.volumeData = pg.PlotCurveItem()
        self.pfillY = pg.FillBetweenItem(self.volumeData, self.basePlotVol, brush = self.plotcolor)
        self.graphVolume.addItem(self.volumeData)
        self.graphVolume.addItem(self.basePlotVol)
        self.graphVolume.addItem(self.pfillY)
        
        #self.graphPressure = pg.PlotWidget()
        self.pressureData = pg.PlotCurveItem()
        self.pfillZ = pg.FillBetweenItem(self.pressureData, self.basePlotPres, brush = self.plotcolor)
        self.graphPressure.addItem(self.pressureData)
        self.graphPressure.addItem(self.basePlotPres)
        self.graphPressure.addItem(self.pfillZ)

        self.graphFlow.setLabel('left', "<span style=\"color:black;font-size:16px\">Flow (L/min)</span>")
        self.graphVolume.setLabel('left', "<span style=\"color:black;font-size:16px\">Volume (mL)</span>")
        self.graphPressure.setLabel('left', "<span style=\"color:black;font-size:16px\">Pressure (cmH2O)</span>")
        self.graphPressure.setLabel('bottom', "<span style=\"color:black;font-size:16px\">Time (sec)</span>")
        self.graphFlow.setYRange(-60, 60) 
        self.graphVolume.setYRange(0, 160) 
        self.graphPressure.setYRange(0, 10) 
        tticks = (np.array(range(0,x_axis_length+1,20))/20)
        ax=self.graphFlow.getAxis('bottom')    #This is the trick  
        ax.setTicks([[(v*20, '') for v in tticks ]])
        
        ax=self.graphVolume.getAxis('bottom')    #This is the trick  
        ax.setTicks([[(v*20, '') for v in tticks ]])
        
        ax=self.graphPressure.getAxis('bottom')    #This is the trick  
        ax.setTicks([[(v*20, '{:.0f}'.format(v)) for v in tticks ]])

        self.graphFlow.showGrid(x=True, y=True)
        self.graphVolume.showGrid(x=True, y=True)
        self.graphPressure.showGrid(x=True, y=True)

        pg.setConfigOption('background', self.BGCOLOR)
        pg.setConfigOption('foreground', self.FGCOLOR)
        pg.setConfigOptions(useOpenGL=True)
       
        pen = pg.mkPen(color = self.plotcolor, width = 3)
        
        self.basePlot = pg.PlotCurveItem([0]*x_axis_length, pen = self.plotcolor) 
        self.basePlotX = pg.PlotCurveItem([0]*x_axis_length, pen = self.plotcolor)
        
        self.initializeGraphs()
        self.updateGraphs()

    def manualVentilationPressed(self):
        self.currentTime = caget('Raspi:central:TIME-COUNTER')
        self.currentVinsp = caget('Raspi:central:Set-Vinsp')
        self.currentVexp = caget('Raspi:central:Set-Vexp')
        caput('Raspi:central:Set-Vinsp', 30)
        caput('Raspi:central:Set-Vexp', 0)
        print('Setting Valve Insp at 30')
    def manualVentilationReleased(self):
        caput('Raspi:central:Set-Vinsp', self.currentVinsp)
        caput('Raspi:central:Set-Vexp', self.currentVexp)
        caput('Raspi:central:TIME-COUNTER', self.currentTime)
        print('restarting all')

    def manualPausePressed(self):
        self.currentTime = caget('Raspi:central:TIME-COUNTER')
        self.currentVinsp = caget('Raspi:central:Set-Vinsp')
        self.currentVexp = caget('Raspi:central:Set-Vexp')
        caput('Raspi:central:Set-Vinsp', 0)
        caput('Raspi:central:Set-Vexp', 0)
        print('Setting Valve Insp at 0')
    def manualPauseReleased(self):
        caput('Raspi:central:Set-Vinsp', self.currentVinsp)
        caput('Raspi:central:Set-Vexp', self.currentVexp)
        caput('Raspi:central:TIME-COUNTER', self.currentTime)
        print('restarting all')

    def initializeGraphs(self):
        self.channelFlow = [0]*x_axis_length
        self.channelVolume = [0]*x_axis_length
        self.channelPressure = [0]*x_axis_length
        self.counterPlots = 0


    def updateGraphs(self):
        self.channelFlow[self.counterPlots] = caget('Raspi:central:Sensor-Finsp')
        self.channelVolume[self.counterPlots] = caget('Raspi:central:Calibrated-Vt')
        self.channelPressure[self.counterPlots] = caget('Raspi:central:Sensor-Pinsp')
        self.counterPlots += 1
        if(self.counterPlots == x_axis_length):
            self.initializeGraphs()
        self.flowData.setData(self.channelFlow,pen= self.plotcolor)
        self.volumeData.setData(self.channelVolume,pen= self.plotcolor)
        self.pressureData.setData(self.channelPressure,pen= self.plotcolor)


def main():
  app = QApplication(sys.argv)
  win = VentilatorWindow()
  win.show()
  sys.exit(app.exec_())

if __name__ == '__main__':
  main()