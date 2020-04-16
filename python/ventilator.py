from PyQt5.QtWidgets import QMainWindow, QApplication, QPushButton, QTextEdit, QDialog, QWidget, QMessageBox
from PyQt5 import uic, QtGui, QtCore, QtWidgets
import pyqtgraph as pg
import sys
#from epics import caget, caput
import numpy as np
from qrangesliderhorizontal import QRangeSliderHorizontal

import serial
import sys

VT_MIN = 100
VT_MAX = 1300
PIP_MIN = 5
PIP_MAX = 120
TINSP_MIN = 0.1
TINSP_MAX = 20
RR_MIN = 1
RR_MAX = 30
TPLATEAU_MIN = 0
TPLATEAU_MAX=10
PEEP_MIN = 0
PEEP_MAX = 50

SCROLLBAR_SETTINGS = """
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


X_AXIS_LENGTH = 200;


class serialReceiver(QtCore.QThread):
  
    newSample = QtCore.pyqtSignal(int,float, float, float, float)

    def __init__(self, serialEnabled, loopRun):
        QtCore.QThread.__init__(self)

        self.loopRun = loopRun
        self.serialEnabled = serialEnabled

        self.ser = serial.Serial()

        self.ser.baudrate = 115200
        try:
            self.ser.port = str(sys.argv[1])
        except:
            print('ERROR, NO PORT SELECTED, going to default port')
            self.ser.port = '/dev/cu.usbmodem14201'
        self.ser.open()

    def run(self):
        while self.loopRun:
            data = self.ser.readline()
            data = str(data).split('\'')[1].split('\\')[0].split(';')
            try:
                self.mId = int(data[0])
                self.fio2 = float(data[1])
                self.pressure = float(data[2])
                self.flow = float(data[3])
                self.vt = float(data[4])
                self.newSample.emit(self.mId, self.fio2, self.pressure, self.flow, self.vt)
            except:
                print('error in received data: {}'.format(data))
            
    def setRead(self):
        self.loopRun = 1

    def stopRead(self):
        self.loopRun = 0

    def setWrite(self,type,message):
        print('writing to serial' + str(type) + ";" + str(message) + "\n")
        self.ser.write(str.encode(str(type) + ";" + str(message) + "\n"))


class VentilatorWindow(QDialog):
    def __init__(self):
        super(VentilatorWindow, self).__init__()
        uic.loadUi("dashboard_ventilator.ui", self)


        self.initializaValuesFromArduino()
        self.start_timer()

        self.PlotsWidget = PlotsWidget(parent=self)
        self.SettingsWidget_VC = SettingsWidget_VC(parent=self)
        self.SettingsWidget_PC = SettingsWidget_PC(parent=self)
        self.SettingsWidget_PS = SettingsWidget_PS(parent=self)
        self.AlarmsWidget = AlarmsWidget(parent=self)
        self.stacked_area.addWidget(self.PlotsWidget)
        self.SettingsWidget_VC.readInitialSetValues()
        self.stacked_area.addWidget(self.SettingsWidget_VC)
        self.stacked_area.addWidget(self.SettingsWidget_PC)
        self.stacked_area.addWidget(self.SettingsWidget_PS)
        self.stacked_area.addWidget(self.AlarmsWidget)
        self.stacked_area.setCurrentWidget(self.PlotsWidget)

        self.setButton.clicked.connect(self.toggleStackedArea)

        self.alarmsButton.clicked.connect(self.toggleStackedArea)
        self.stackedArea_flag = 0
        self.chooseOPMODEbutton.addItem("Volume Control")
        self.chooseOPMODEbutton.addItem("Pressure Control")
        self.chooseOPMODEbutton.addItem("Pressure Support")
        self.chooseOPMODEbutton.currentIndexChanged.connect(self.changeOPMODE)

        self.serialEnabled = True
        self.start_serial()

        self.currentMode = 0#caget('Raspi:central:OPMODE')

        if self.currentMode == 0:
            self.currentModeLabel.setText('Volume Control')
        elif self.currentMode == 1:
            self.currentModeLabel.setText('Pressure Control')
        elif self.currentMode == 2: 
            self.currentModeLabel.setText('Pressure Support')
        else:   
            self.currentModeLabel.setText('No mode Selected')

        self.msg = QMessageBox()
        self.setWindowTitle("Ventilator")

    def start_serial(self):
        serial = serialReceiver(self.serialEnabled, True)
        serial.newSample.connect(self.updateSideBarValues)
        serial.newSample.connect(self.PlotsWidget.updateGraphs)
        self.thread = serial
        serial.start()

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
            self.currentMode = 0
            #caput('Raspi:central:OPMODE',2)
        elif i==1:
            self.currentModeLabel.setText('Pressure Control')
            self.currentMode = 1
            #caput('Raspi:central:OPMODE',3)
        elif i==2:
            self.currentModeLabel.setText('Pressure Support')
            self.currentMode = 2
            #caput('Raspi:central:OPMODE',4)

    def slideroptions(self):
        pass


    def toggleStackedArea(self):
        sending_button = self.sender()
        if sending_button.objectName() == 'alarmsButton':
            self.stacked_area.setCurrentWidget(self.AlarmsWidget)
        elif self.stackedArea_flag == 1: #I am in the settings view and want to change to show plots
            self.stacked_area.setCurrentWidget(self.PlotsWidget)
            self.PlotsWidget.initializeGraphs()
            self.updateBottomBarValues()
            self.thread.newSample.connect(self.PlotsWidget.updateGraphs)
            try:
                self.timer.timeout.disconnect(self.SettingsWidget_VC.updateSetValues)
            except:
                print('nothing to disconnect')
            try:
                self.timer.timeout.disconnect(self.SettingsWidget_PC.updateSetValues)
            except:
                print('nothing to disconnect')
            self.stackedArea_flag = 0
            if self.chooseOPMODEbutton.currentText()=='Volume Control':
                self.SettingsWidget_VC.commitValueChanges()
            elif self.chooseOPMODEbutton.currentText()=='Pressure Control':
                self.SettingsWidget_PC.commitValueChanges()
            self.setButton.setStyleSheet("color: rgb(3, 43, 91);")
            self.setButton.setText('Set\nValues')
        elif self.stackedArea_flag == 0 and self.chooseOPMODEbutton.currentText()=='Volume Control': #I am in the plots view and want to change to show VC settings
            self.timer.timeout.connect(self.SettingsWidget_VC.updateSetValues)
            try:
                self.thread.newSample.disconnect(self.PlotsWidget.updateGraphs)
            except:
                print('nothing to disconnect')
            self.stacked_area.setCurrentWidget(self.SettingsWidget_VC)
            self.stackedArea_flag = 1
            self.setButton.setStyleSheet("background-color: #00e64d;");
        elif self.stackedArea_flag == 0 and self.chooseOPMODEbutton.currentText()=='Pressure Control':
            print('Pressure Control')
            self.timer.timeout.connect(self.SettingsWidget_PC.updateSetValues)
            try:
                self.thread.newSample.disconnect(self.PlotsWidget.updateGraphs)
            except:
                print('nothing to disconnect')
            self.stacked_area.setCurrentWidget(self.SettingsWidget_PC)
            self.stackedArea_flag = 1
            self.setButton.setStyleSheet("background-color: #00e64d;");
        elif self.stackedArea_flag == 0 and self.chooseOPMODEbutton.currentText()=='Pressure Support':
            print('Pressure Support')
            try:
                self.thread.newSample.disconnect(self.PlotsWidget.updateGraphs)
            except:
                print('nothing to disconnect')
            self.stacked_area.setCurrentWidget(self.SettingsWidget_PS)
            self.stackedArea_flag = 1
            self.setButton.setStyleSheet("background-color: #00e64d;");

    def updateSideBarValues(self, mId, fio2, pressure, flow, vt):
        self.sensorFio2 = fio2
        self.sensorPressure = pressure
        self.sensorFlow = flow
        self.sensorVt = vt
        self.sensorVtvar.setText("{:.1f}".format(self.sensorVt))
        self.sensorFiO2var.setText("{:.1f}".format(self.sensorFio2))
        self.sensorPIPvar.setText("{:.1f}".format(self.sensorPressure))
        self.sensorPEEPvar.setText("{:.1f}".format(self.sensorFlow))

    def initializaValuesFromArduino(self):
        self.valueTinsp = 1.3
        self.valueTplateau = 0.0
        self.valueRR = 10
        self.valueVt = 400
        self.valuePEEP = 5
        self.valuePIP = 30
        self.vExp = 0
        self.vInsp = 0
        

    def updateBottomBarValues(self):
        self.setVtvar_btm.setText("{:.0f}".format(self.valueVt))
        self.setRRvar_btm.setText("{:.0f}".format(self.valueRR))
        self.setTinspvar_btm.setText("{:.1f}".format(self.valueTinsp))
        self.setPEEPvar_btm.setText("{:.0f}".format(self.valuePEEP))

        self.check_alarms()

    def keyPressEvent(self, event):
        # Did the user press the Escape key?
        if event.key() == QtCore.Qt.Key_Escape: 
          self.app_after_exit = 0
          self.close()

class SettingsWidget_VC(QWidget):
    def __init__(self, parent=None):
        super(SettingsWidget_VC, self).__init__(parent)
        uic.loadUi("settingsWidget_VC.ui", self)

        self.scrollbarSettings = SCROLLBAR_SETTINGS

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

        self.setTinspScrollBar.setMaximum(TINSP_MAX*10)
        self.setRRScrollBar.setMaximum(RR_MAX*10)
        self.setPEEPScrollBar.setMaximum(PEEP_MAX)
        self.setVtScrollBar.setMaximum(VT_MAX)
        self.setTplateauScrollBar.setMaximum(TPLATEAU_MAX*10)
        self.setTinspScrollBar.setMinimum(TINSP_MIN*10)
        self.setTplateauScrollBar.setMinimum(TPLATEAU_MIN*10)
        self.setRRScrollBar.setMinimum(RR_MIN*10)
        self.setPEEPScrollBar.setMinimum(PEEP_MIN)
        self.setVtScrollBar.setMinimum(VT_MIN)

        self.readInitialSetValues()
        self.updateSetValues()

    def readInitialSetValues(self):
        # TODO: read initial values a file

        self.valueTinsp_tmp = self.parent().valueTinsp
        self.valueTplateau_tmp = self.parent().valueTplateau
        self.valueRR_tmp = self.parent().valueRR
        self.valueVt_tmp = self.parent().valueVt
        self.valuePEEP_tmp = self.parent().valuePEEP

        self.setTinspScrollBar.setValue(self.valueTinsp_tmp * 10)
        self.setTplateauScrollBar.setValue(self.valueTplateau_tmp * 10)
        self.setRRScrollBar.setValue(self.valueRR_tmp*10)
        self.setPEEPScrollBar.setValue(self.valuePEEP_tmp)
        self.setVtScrollBar.setValue(self.valueVt_tmp)

    def updateSetValues(self): 

        self.valueTinsp_tmp = (self.setTinspScrollBar.value() / 10)
        self.valueTplateau_tmp = (self.setTplateauScrollBar.value() / 10)
        self.valueRR_tmp = (self.setRRScrollBar.value() / 10)
        self.valuePEEP_tmp = self.setPEEPScrollBar.value()
        self.valueVt_tmp = self.setVtScrollBar.value()

        self.setTinspvar_setting.setText("{:.1f}".format(self.valueTinsp_tmp))
        self.setTplateauvar_setting.setText("{:.1f}".format(self.valueTplateau_tmp))
        self.setRRvar_setting.setText("{:.1f}".format(self.valueRR_tmp))
        self.setVtvar_setting.setText("{:.0f}".format(self.valueVt_tmp))
        self.setPEEPvar_setting.setText("{:.0f}".format(self.valuePEEP_tmp))


    def commitValueChanges(self):
        print('Commiting values')
        self.valueTinsp_tmp = (self.setTinspScrollBar.value() / 10)
        self.valueTplateau_tmp = (self.setTplateauScrollBar.value() / 10)
        self.valueRR_tmp = (self.setRRScrollBar.value() / 10)
        
        if((self.valueTinsp_tmp+self.valueTplateau_tmp)>(60/self.valueRR_tmp - 0.3)):
            self.parent().parent().msg.setText('Values of RR and Tinsp do not match. RR was corrected to maximum value allowed.')
            self.parent().parent().msg.setIcon(QMessageBox.Warning)
            self.parent().parent().msg.exec_()


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

            self.valueTinsp = self.valueTinsp_tmp
            self.valueTplateau = self.valueTplateau_tmp
            self.valueRR = self.valueRR_tmp
            self.valueVt = self.valueVt_tmp
            self.valuePEEP = self.valuePEEP_tmp

            self.parent().parent().valueTinsp =self.valueTinsp 
            self.parent().parent().valueTplateau = self.valueTplateau 
            self.parent().parent().valueRR = self.valueRR
            self.parent().parent().valueVt = self.valueVt 
            self.parent().parent().valuePEEP = self.valuePEEP

            self.valueTinsp_tmp = self.parent().parent().valueTinsp
            self.valueTplateau_tmp = self.parent().parent().valueTplateau
            self.valueRR_tmp = self.parent().parent().valueRR
            self.valueVt_tmp = self.parent().parent().valueVt
            self.valuePEEP_tmp = self.parent().parent().valuePEEP

            self.setTinspScrollBar.setValue(self.valueTinsp_tmp * 10)
            self.setTplateauScrollBar.setValue(self.valueTplateau_tmp * 10)
            self.setRRScrollBar.setValue(self.valueRR_tmp*10)
            self.setPEEPScrollBar.setValue(self.valuePEEP_tmp)
            self.setVtScrollBar.setValue(self.valueVt_tmp)

            self.parent().parent().updateBottomBarValues()

class SettingsWidget_PC(QWidget):
    def __init__(self, parent=None):
        super(SettingsWidget_PC, self).__init__(parent)
        uic.loadUi("settingsWidget_PC.ui", self)


        self.scrollbarSettings = SCROLLBAR_SETTINGS

        self.setTinspScrollBar.setStyleSheet(self.scrollbarSettings)
        self.setTplateauScrollBar.setStyleSheet(self.scrollbarSettings)
        self.setRRScrollBar.setStyleSheet(self.scrollbarSettings)
        self.setPEEPScrollBar.setStyleSheet(self.scrollbarSettings)
        self.setPIPScrollBar.setStyleSheet(self.scrollbarSettings)
        
        self.setTinspScrollBar.setPageStep(1)
        self.setTplateauScrollBar.setPageStep(1)
        self.setTinspScrollBar.setSingleStep(1)
        self.setRRScrollBar.setPageStep(1)
        self.setPEEPScrollBar.setPageStep(1)
        self.setPIPScrollBar.setPageStep(5)

        self.setTinspScrollBar.setMaximum(TINSP_MAX*10)
        self.setRRScrollBar.setMaximum(RR_MAX*10)
        self.setPEEPScrollBar.setMaximum(PEEP_MAX)
        self.setPIPScrollBar.setMaximum(VT_MAX)
        self.setTplateauScrollBar.setMaximum(TPLATEAU_MAX*10)
        self.setTinspScrollBar.setMinimum(TINSP_MIN*10)
        self.setTplateauScrollBar.setMinimum(TPLATEAU_MIN*10)
        self.setRRScrollBar.setMinimum(RR_MIN*10)
        self.setPEEPScrollBar.setMinimum(PEEP_MIN)
        self.setPIPScrollBar.setMinimum(VT_MIN)

        self.readInitialSetValues()
        self.updateSetValues()

    def readInitialSetValues(self):
        # TODO: read initial values a file

        self.valueTinsp_tmp = self.parent().valueTinsp
        self.valueTplateau_tmp = self.parent().valueTplateau
        self.valueRR_tmp = self.parent().valueRR
        self.valuePIP_tmp = self.parent().valuePIP
        self.valuePEEP_tmp = self.parent().valuePEEP

        self.setTinspScrollBar.setValue(self.valueTinsp_tmp * 10)
        self.setTplateauScrollBar.setValue(self.valueTplateau_tmp * 10)
        self.setRRScrollBar.setValue(self.valueRR_tmp*10)
        self.setPEEPScrollBar.setValue(self.valuePEEP_tmp)
        self.setPIPScrollBar.setValue(self.valuePIP_tmp)

    def updateSetValues(self): 

        self.valueTinsp_tmp = (self.setTinspScrollBar.value() / 10)
        self.valueTplateau_tmp = (self.setTplateauScrollBar.value() / 10)
        self.valueRR_tmp = (self.setRRScrollBar.value() / 10)
        self.valuePEEP_tmp = self.setPEEPScrollBar.value()
        self.valuePIP_tmp = self.setPIPScrollBar.value()

        self.setTinspvar_setting.setText("{:.1f}".format(self.valueTinsp_tmp))
        self.setTplateauvar_setting.setText("{:.1f}".format(self.valueTplateau_tmp))
        self.setRRvar_setting.setText("{:.1f}".format(self.valueRR_tmp))
        self.setPIPvar_setting.setText("{:.0f}".format(self.valuePIP_tmp))
        self.setPEEPvar_setting.setText("{:.0f}".format(self.valuePEEP_tmp))


    def commitValueChanges(self):
        print('Commiting values PC')
        self.valueTinsp_tmp = (self.setTinspScrollBar.value() / 10)
        self.valueTplateau_tmp = (self.setTplateauScrollBar.value() / 10)
        self.valueRR_tmp = (self.setRRScrollBar.value() / 10)
        
        if((self.valueTinsp_tmp+self.valueTplateau_tmp)>(60/self.valueRR_tmp - 0.3)):
            self.parent().parent().msg.setText('Values of RR and Tinsp do not match. RR was corrected to maximum value allowed.')
            self.parent().parent().msg.setIcon(QMessageBox.Warning)
            self.parent().parent().msg.exec_()


            self.setTinspScrollBar.setValue(self.valueTinsp * 10)
            self.setTplateauScrollBar.setValue(self.valueTplateau * 10)
            self.setRRScrollBar.setValue(self.valueRR*10)
            self.setPEEPScrollBar.setValue(self.valuePEEP)
            self.setPIPScrollBar.setValue(self.valuePIP)

            self.setTinspvar_setting.setText("{:.1f}".format(self.valueTinsp))
            self.setTplateauvar_setting.setText("{:.1f}".format(self.valueTplateau))
            self.setRRvar_setting.setText("{:.1f}".format(self.valueRR))
            self.setPIPvar_setting.setText("{:.0f}".format(self.valuePIP))
            self.setPEEPvar_setting.setText("{:.0f}".format(self.valuePEEP))

        else:

            print('settings...')

            self.valueTinsp = self.valueTinsp_tmp
            self.valueTplateau = self.valueTplateau_tmp
            self.valueRR = self.valueRR_tmp
            self.valuePIP = self.valuePIP_tmp
            self.valuePEEP = self.valuePEEP_tmp

            print(self.valueTinsp_tmp)

            self.parent().parent().valueTinsp =self.valueTinsp 
            self.parent().parent().valueTplateau = self.valueTplateau 
            self.parent().parent().valueRR = self.valueRR
            self.parent().parent().valuePIP = self.valuePIP 
            self.parent().parent().valuePEEP = self.valuePEEP

            self.valueTinsp_tmp = self.parent().parent().valueTinsp
            self.valueTplateau_tmp = self.parent().parent().valueTplateau
            self.valueRR_tmp = self.parent().parent().valueRR
            self.valuePIP_tmp = self.parent().parent().valuePIP
            self.valuePEEP_tmp = self.parent().parent().valuePEEP

            self.setTinspScrollBar.setValue(self.valueTinsp_tmp * 10)
            self.setTplateauScrollBar.setValue(self.valueTplateau_tmp * 10)
            self.setRRScrollBar.setValue(self.valueRR_tmp*10)
            self.setPEEPScrollBar.setValue(self.valuePEEP_tmp)
            self.setPIPScrollBar.setValue(self.valuePIP_tmp)

            self.parent().parent().updateBottomBarValues()


class SettingsWidget_PS(QWidget):
    def __init__(self, parent=None):
        super(SettingsWidget_PS, self).__init__(parent)
        uic.loadUi("settingsWidget_PS.ui", self)
        

class AlarmsWidget(QWidget):
    def __init__(self, parent=None):
        super(AlarmsWidget, self).__init__(parent)
        uic.loadUi("alarmsWidget.ui", self)
            

        # self.alarmVtMaxRange=caget('Raspi:central:Set-Vt.DRVH')
        # self.alarmVtMinRange=caget('Raspi:central:Set-Vt.DRVL')

        # self.alarmVtHIGH=caget('Raspi:central:Set-Vt.HIGH')
        # self.alarmVtLOW=caget('Raspi:central:Set-Vt.LOW')

        # self.alarmPIPMaxRange=caget('Raspi:central:Set-Vt.DRVH')
        # self.alarmPIPMinRange=caget('Raspi:central:Set-Vt.DRVL')

        # #self.setAlarmVtSlider.SetRange(self.alarmVtMinRange, self.alarmVtMaxRange)
        # self.setAlarmVtSlider.setMin(self.alarmVtMinRange)
        # self.setAlarmVtSlider.setMax(self.alarmVtMaxRange)

        # self.setAlarmVtSlider.setStart(self.alarmVtMinRange)
        # self.setAlarmVtSlider.setEnd(self.alarmVtMaxRange)


        # # self.setAlarmPIPSlider.setMin(0)
        # # self.setAlarmPIPSlider.setMax(99)
        # # self.setAlarmPIPSlider.setStart(10)
        # # self.setAlarmPIPSlider.setEnd(40)
        # #self.setAlarmPIPSlider.SetRange(self.alarmPIPMinRange, self.alarmPIPMaxRange)

        # self.maxAlarmVt.setText("{:.0f}".format(caget('Raspi:central:Set-Vt.HIGH')))
        # self.minAlarmVt.setText("{:.0f}".format(caget('Raspi:central:Set-Vt.LOW')))
        # self.maxAlarmPIP.setText("{:.0f}".format(caget('Raspi:central:Set-Ppeak.HIGH')))
        # self.minAlarmPIP.setText("{:.0f}".format(caget('Raspi:central:Set-Ppeak.LOW')))
        



class PlotsWidget(QWidget):
    def __init__(self, parent=None):
        super(PlotsWidget, self).__init__(parent)
        uic.loadUi("plotsWidget.ui", self)

        self.manualVentButton.pressed.connect(self.manualVentilationPressed)
        self.manualVentButton.released.connect(self.manualVentilationReleased)
        self.manualPauseButton.pressed.connect(self.manualPausePressed)
        self.manualPauseButton.released.connect(self.manualVentilationReleased)

        self.accelBufferX = (0,0)

        self.BGCOLOR = QtGui.QColor(220,220,220)
        self.FGCOLOR = QtGui.QColor(255,0,0)
        self.plotcolor = QtGui.QColor(26, 76, 156)
        self.PLTWIDTH = 2

        self.basePlotFlow = pg.PlotCurveItem([0]*X_AXIS_LENGTH, pen = self.plotcolor)
        self.basePlotVol = pg.PlotCurveItem([0]*X_AXIS_LENGTH, pen = self.plotcolor) 
        self.basePlotPres = pg.PlotCurveItem([0]*X_AXIS_LENGTH, pen = self.plotcolor)

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
        tticks = (np.array(range(0,X_AXIS_LENGTH+1,20))/20)
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
        
        self.basePlot = pg.PlotCurveItem([0]*X_AXIS_LENGTH, pen = self.plotcolor) 
        self.basePlotX = pg.PlotCurveItem([0]*X_AXIS_LENGTH, pen = self.plotcolor)
        
        self.initializeGraphs()

    def manualVentilationPressed(self):
        self.lastVexp = self.parent().parent().vExp
        self.lastVinsp = self.parent().parent().vInsp
        self.lastMode = self.parent().parent().currentMode
        self.currentMode = 2 #manual
        self.setVinsp = 30
        self.setVexp = 0
        self.parent().parent().thread.setWrite(self.currentMode,'0;'+str(self.setVinsp)+';1;'+str(self.setVexp))
        print('Setting Valve Insp at 30')

    def manualVentilationReleased(self):
        self.parent().parent().vExp = self.lastVexp
        self.parent().parent().vInsp = self.lastVinsp
        self.parent().parent().currentMode = self.lastMode
        self.parent().parent().thread.setWrite(self.currentMode,'0;'+str(self.setVinsp)+';1;'+str(self.setVexp))
        print('restarting all')

    def manualPausePressed(self):
        self.lastVexp = self.parent().parent().vExp
        self.lastVinsp = self.parent().parent().vInsp
        self.lastMode = self.parent().parent().currentMode
        self.currentMode = 2 #manual
        self.setVinsp = 0
        self.setVexp = 0
        self.parent().parent().thread.setWrite(self.currentMode,'0;'+str(self.setVinsp)+';1;'+str(self.setVexp))
        print('Setting Valve Insp at 0')
    def manualPauseReleased(self):
        self.parent().parent().vExp = self.lastVexp
        self.parent().parent().vInsp = self.lastVinsp
        self.parent().parent().currentMode = self.lastMode
        self.parent().parent().thread.setWrite(self.currentMode,'0;'+str(self.setVinsp)+';1;'+str(self.setVexp))
        print('restarting all')

    def initializeGraphs(self):
        self.channelFlow = [0]*X_AXIS_LENGTH
        self.channelVolume = [0]*X_AXIS_LENGTH
        self.channelPressure = [0]*X_AXIS_LENGTH
        self.counterPlots = 0


    def updateGraphs(self, mId, fio2, pressure, flow, vt):

        self.channelFlow[self.counterPlots] = flow
        self.channelVolume[self.counterPlots] = vt
        self.channelPressure[self.counterPlots] = pressure
        self.counterPlots += 1
        if(self.counterPlots == X_AXIS_LENGTH):
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