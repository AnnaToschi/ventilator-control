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
INSPRISETIME_MAX = 20 #percentage
INSPRISETIME_MIN = 0 #percentage
IERATIO_MIN = 1
IERATIO_MAX = 3
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
  
    newSensorSample = QtCore.pyqtSignal(float, float, float)
    afterInspSample = QtCore.pyqtSignal(float, float, float, float, float, float)
    afterExpSample = QtCore.pyqtSignal(float, float, float, float, float)
    PCSettingsSample = QtCore.pyqtSignal(float, float, float, float, float)
    VCSettingsSample = QtCore.pyqtSignal(float, float, float, float, float)
    alarmSettingsSample = QtCore.pyqtSignal(float, float, float, float)
    debugMsgSample = QtCore.pyqtSignal(str)

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
            try:
                dataList = str(data).split('\'')[1].split('\\')[0].split(';')
                msgType = int(dataList[0])
                dataList = dataList[1:]
                if(msgType == 1):
                    print('Received Plot Data Sample')
                    print('Plot: {}'.format(dataList))
                    self.mId = int(dataList[0])
                    self.pressure_now = float(dataList[1])
                    self.flow_now = float(dataList[2])
                    self.vt_now = float(dataList[3])
                    self.newSensorSample.emit(self.pressure_now, \
                        self.flow_now, self.vt_now)
                elif(msgType == 2):
                    print('Received INSP Data Sample')
                    self.mId = int(dataList[0])
                    self.measuredInspirationRiseTimeInSecs = float(dataList[1])
                    self.measuredPIP = float(dataList[2])
                    self.measuredInspirationVolume = float(dataList[3])
                    self.measuredPIF = float(dataList[4])
                    self.measuredFiO2 = float(dataList[5])
                    self.measuredRR = float(dataList[6])
                    self.afterInspSample.emit(self.measuredInspirationRiseTimeInSecs, \
                        self.measuredPIP, self.measuredInspirationVolume, self.measuredPIF, \
                        self.measuredFiO2, self.measuredRR)
                elif(msgType == 3):
                    print('Received EXP Data Sample')
                    self.mId = int(dataList[0])
                    self.measuredPEEP = float(dataList[1])
                    self.measuredExpirationVolume = float(dataList[2])
                    self.measuredPEF = float(dataList[3])
                    self.measuredFiO2 = float(dataList[4])
                    self.measuredRR = float(dataList[5])
                    self.afterExpSample.emit(self.measuredPEEP, \
                        self.measuredExpirationVolume, self.measuredPEF, self.measuredFiO2, self.measuredRR)
                elif(msgType == 4):
                    print('Received PC Settings')
                    print('PC: {}'.format(dataList))
                    self.mId = int(dataList[0])
                    self.targetPEEP = float(dataList[1])
                    self.targetPIP = float(dataList[2])
                    self.targetRR = float(dataList[3])
                    self.targetIERatio = float(dataList[4])
                    self.targetInspirationRiseTime = float(dataList[5])
                    self.PCSettingsSample.emit(self.targetPEEP, self.targetPIP, \
                        self.targetRR, self.targetIERatio, self.targetInspirationRiseTime)
                elif(msgType == 5):
                    print('Received VC Settings')
                    print('VC: {}'.format(dataList))
                    self.mId = int(dataList[0])
                    self.targetPEEP = float(dataList[1])
                    self.targetVt = float(dataList[2])
                    self.targetRR = float(dataList[3])
                    self.targetIERatio = float(dataList[4])
                    self.targetInspPause = float(dataList[5])
                    self.VCSettingsSample.emit(self.targetPEEP, self.targetVt, \
                        self.targetRR, self.targetIERatio, self.targetInspPause)
                elif(msgType == 6):
                    self.mId = int(dataList[0])
                    self.lowerInspirationVolumeThreshold = float(dataList[1])
                    self.upperInspirationVolumeThreshold = float(dataList[2])
                    self.lowerInspirationPressureThreshold = float(dataList[3])
                    self.upperInspirationPressureThreshold = float(dataList[4])
                    self.alarmSettingsSample.emit(self.lowerInspirationVolumeThreshold, \
                        self.upperInspirationVolumeThreshold, self.lowerInspirationPressureThreshold,\
                        self.upperInspirationPressureThreshold)
                elif(msgType == 99):
                    self.debugMsgSample.emit(str(data[1]))
            except:
                print('error in received data: {}'.format(data))
            
    def startRead(self):
        self.loopRun = 1

    def stopRead(self):
        self.loopRun = 0

    def setWrite(self,type,message):
        print('writing to serial' + str(type) + ";" + str(message) + "\n")
        self.ser.write(str.encode(str(type) + ";" + str(message) + "\n"))

    def sendPCSettings(self,mID,targetPEEP,targetPIP,targetRR,targetIERatio,targetInspirationRiseTime):
        message = '4;' + str(mID) + ';' + str(targetPEEP) + ';' + str(targetPIP) + ';' + str(targetRR) + ';' + \
        str(targetIERatio) + ';' + str(targetInspirationRiseTime) + '\n'
        print('writing to serial: ' + message)
        self.ser.write(str.encode(message))

    def sendVCSettings(self,mID,targetPEEP,targetVt,targetRR,targetIERatio,targetInspPause):
        message = '5;' + str(mID) + ';' + str(targetPEEP) + ';' + str(targetVt) + ';' + str(targetRR) + ';' + \
        str(targetIERatio) + ';' + str(targetInspPause) + '\n'
        print('writing to serial: ' + message)
        self.ser.write(str.encode(message))

    def sendAlarmSettings(self,mID,lowerInspirationVolumeThreshold,upperInspirationVolumeThreshold,\
                            lowerInspirationPressureThreshold,upperInspirationPressureThreshold):
        message = '6;' + str(mID) + ';' + str(lowerInspirationVolumeThreshold) + ';' + str(upperInspirationVolumeThreshold) + ';' + \
        str(lowerInspirationPressureThreshold) + ';' + str(upperInspirationPressureThreshold) + '\n'
        print('writing to serial: ' + message)
        self.ser.write(str.encode(message))


class VentilatorWindow(QDialog):
    def __init__(self):
        super(VentilatorWindow, self).__init__()
        uic.loadUi("dashboard_ventilator.ui", self)

        self.initializaValuesFromArduino()

        self.PlotsWidget = PlotsWidget(parent=self)
        self.SettingsWidget_VC = SettingsWidget_VC(parent=self)
        self.SettingsWidget_PC = SettingsWidget_PC(parent=self)
        self.SettingsWidget_PS = SettingsWidget_PS(parent=self)
        self.AlarmsWidget = AlarmsWidget(parent=self)
        
        self.SettingsWidget_VC.readInitialSetValues()

        self.main_stacked_area.addWidget(self.PlotsWidget)
        self.main_stacked_area.addWidget(self.SettingsWidget_VC)
        self.main_stacked_area.addWidget(self.SettingsWidget_PC)
        self.main_stacked_area.addWidget(self.SettingsWidget_PS)
        self.main_stacked_area.addWidget(self.AlarmsWidget)
        self.main_stacked_area.setCurrentWidget(self.PlotsWidget)


        self.BottomAreaVC = BottomAreaVC(parent=self)
        self.BottomAreaPC = BottomAreaPC(parent=self)
        self.BottomAreaPS = BottomAreaPS(parent=self)

        self.bottom_stacked_area.addWidget(self.BottomAreaVC)
        self.bottom_stacked_area.addWidget(self.BottomAreaPC)
        self.bottom_stacked_area.addWidget(self.BottomAreaPS)
        self.bottom_stacked_area.setCurrentWidget(self.BottomAreaVC)

        self.start_timer()



        self.setButton.clicked.connect(self.toggleStackedArea)

        self.alarmsButton.clicked.connect(self.toggleStackedArea)
        self.main_stackedArea_flag = 0
        self.chooseOPMODEbutton.addItem("Volume Control")
        self.chooseOPMODEbutton.addItem("Pressure Control")
        self.chooseOPMODEbutton.addItem("Pressure Support")
        self.chooseOPMODEbutton.currentIndexChanged.connect(self.changeOPMODE)

        self.serialEnabled = True
        self.start_serial()

        self.currentMode = 0#caget('Raspi:central:OPMODE')

        if self.currentMode == 0:
            self.currentModeLabel.setText('Volume Control')
            self.BottomAreaVC.updateBottomBarValues()
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
        serial.afterInspSample.connect(self.updateSideBarValues)
        serial.afterExpSample.connect(self.updateSideBarValues)
        serial.VCSettingsSample.connect(self.updateVCSetValues)
        serial.PCSettingsSample.connect(self.updatePCSetValues)
        # serial.alarmSettingsSample.connect(self.UpdateAlarms.updateSetValues)
        serial.newSensorSample.connect(self.PlotsWidget.updateGraphs)
        self.thread = serial
        serial.start()

    def start_timer(self):
        self.timer = QtCore.QTimer()
        self.timer.setInterval(50)
        self.timer.start()

    def check_alarms(self):
        pass
        #if self.sensorMVvar > caget('Raspi:central:Minute-Volume')

    def changeOPMODE(self, i):
        if i==0:
            self.currentModeLabel.setText('Volume Control')
            self.bottom_stacked_area.setCurrentWidget(self.BottomAreaVC)
            self.BottomAreaVC.updateBottomBarValues()
            self.currentMode = 0
            #caput('Raspi:central:OPMODE',2)
        elif i==1:
            self.currentModeLabel.setText('Pressure Control')
            self.bottom_stacked_area.setCurrentWidget(self.BottomAreaPC)
            self.BottomAreaPC.updateBottomBarValues()
            self.currentMode = 1
            #caput('Raspi:central:OPMODE',3)
        elif i==2:
            self.currentModeLabel.setText('Pressure Support')
            self.bottom_stacked_area.setCurrentWidget(self.BottomAreaPS)
            self.BottomAreaPS.updateBottomBarValues()
            self.currentMode = 2
            #caput('Raspi:central:OPMODE',4)

    def slideroptions(self):
        pass


    def toggleStackedArea(self):
        sending_button = self.sender()
        if sending_button.objectName() == 'alarmsButton':
            self.main_stacked_area.setCurrentWidget(self.AlarmsWidget)
        elif self.main_stackedArea_flag == 1: #I am in the settings view and want to change to show plots
            self.main_stacked_area.setCurrentWidget(self.PlotsWidget)
            self.PlotsWidget.initializeGraphs()
            self.thread.newSensorSample.connect(self.PlotsWidget.updateGraphs)
            try:
                self.timer.timeout.disconnect(self.SettingsWidget_VC.updateSetValues)
            except:
                print('nothing to disconnect VC')
            try:
                self.timer.timeout.disconnect(self.SettingsWidget_PC.updateSetValues)
            except:
                print('nothing to disconnect PC')
            self.main_stackedArea_flag = 0
            if self.chooseOPMODEbutton.currentText()=='Volume Control':
                self.SettingsWidget_VC.commitValueChanges()
                self.BottomAreaVC.updateBottomBarValues()
            elif self.chooseOPMODEbutton.currentText()=='Pressure Control':
                self.SettingsWidget_PC.commitValueChanges()
                self.BottomAreaPC.updateBottomBarValues()
            elif self.chooseOPMODEbutton.currentText()=='Pressure Support':
                self.SettingsWidget_PS.commitValueChanges()
                self.BottomAreaPS.updateBottomBarValues()
            
            self.setButton.setStyleSheet("color: rgb(3, 43, 91);")
            self.setButton.setText('Set\nValues')
        elif self.main_stackedArea_flag == 0 and self.chooseOPMODEbutton.currentText()=='Volume Control': #I am in the plots view and want to change to show VC settings
            self.timer.timeout.connect(self.SettingsWidget_VC.updateSetValues)
            try:
                self.thread.newSensorSample.disconnect(self.PlotsWidget.updateGraphs)
            except:
                print('nothing to disconnect')
            self.main_stacked_area.setCurrentWidget(self.SettingsWidget_VC)
            self.main_stackedArea_flag = 1
            self.setButton.setStyleSheet("background-color: #00e64d;");
        elif self.main_stackedArea_flag == 0 and self.chooseOPMODEbutton.currentText()=='Pressure Control':
            print('Pressure Control')
            self.timer.timeout.connect(self.SettingsWidget_PC.updateSetValues)
            try:
                self.thread.newSensorSample.disconnect(self.PlotsWidget.updateGraphs)
            except:
                print('nothing to disconnect')
            self.main_stacked_area.setCurrentWidget(self.SettingsWidget_PC)
            self.main_stackedArea_flag = 1
            self.setButton.setStyleSheet("background-color: #00e64d;");
        elif self.main_stackedArea_flag == 0 and self.chooseOPMODEbutton.currentText()=='Pressure Support':
            print('Pressure Support')
            try:
                self.thread.newSensorSample.disconnect(self.PlotsWidget.updateGraphs)
            except:
                print('nothing to disconnect')
            self.main_stacked_area.setCurrentWidget(self.SettingsWidget_PS)
            self.main_stackedArea_flag = 1
            self.setButton.setStyleSheet("background-color: #00e64d;");

    def updateSideBarValues(self, *argv):
        if(len(argv) == 6):
            self.sensorInspRiseTime = argv[0]
            self.sensorPIP = argv[1]
            self.sensorVtinsp_max = argv[2]
            self.sensorPIF = argv[3]
            self.sensorFio2 = argv[4]
            self.sensorRR = argv[5]
            self.sensorRiseTimevar.setText("{:.1f}".format(self.sensorInspRiseTime))
            self.sensorVtInspvar.setText("{:.1f}".format(self.sensorVtinsp_max))
            self.sensorFiO2var.setText("{:.1f}".format(self.sensorFio2))
            self.sensorPIPvar.setText("{:.1f}".format(self.sensorPIP))
            self.sensorPIFvar.setText("{:.1f}".format(self.sensorPIF))
            self.sensorRRvar.setText("{:.1f}".format(self.sensorRR))
        elif(len(argv) == 5):
            self.sensorPEEP = argv[0]
            self.sensorVtexp_max = argv[1]
            self.sensorPEF = argv[2]
            self.sensorFiO2 = argv[3]
            self.sensorRR = argv[4]
            self.sensorVtExpvar.setText("{:.1f}".format(self.sensorVtexp_max))
            self.sensorFiO2var.setText("{:.1f}".format(self.sensorFiO2))
            self.sensorPEFvar.setText("{:.1f}".format(self.sensorPEF))
            self.sensorPEEPvar.setText("{:.1f}".format(self.sensorPEEP))
            self.sensorRRvar.setText("{:.1f}".format(self.sensorRR))

    def updatePCSetValues(self, setPEEP, setPIP, setRR, setIERatio, setInspirationRiseTime):
        print('PC set from stream')
        self.setPEEP = setPEEP
        self.setPIP = setPIP
        self.setRR = setRR
        self.setIERatio = setIERatio
        self.setInspirationRiseTime = setInspirationRiseTime
        self.BottomAreaPC.updateBottomBarValues()

    def updateVCSetValues(self, setPEEP, setVt, setRR, setIERatio, setInspPause):
        print('VC set from stream')
        self.setPEEP = setPEEP
        self.setVt = setVt
        self.setRR = setRR
        self.setIERatio = setIERatio
        self.setTplateau = setInspPause
        self.BottomAreaVC.updateBottomBarValues()


    def initializaValuesFromArduino(self):
        self.setTinsp = 1.3
        self.setInspRiseTime = 10 #in percentage
        self.setIERatio = 2
        self.setPIP = 60
        self.valuePIF = 20
        self.valuePEF = 20
        self.setTplateau = 0.0
        self.setRR = 10
        self.setVt = 400
        self.setPEEP = 5
        self.vExp = 0
        self.vInsp = 0
        
    def keyPressEvent(self, event):
        # Did the user press the Escape key?
        if event.key() == QtCore.Qt.Key_Escape: 
          self.app_after_exit = 0
          self.close()


class BottomAreaVC(QWidget):
    def __init__(self, parent=None):
        super(BottomAreaVC, self).__init__(parent)
        uic.loadUi("bottomDisplay_VC.ui", self)

        self.VentilatorMain = self.parent()


    def updateBottomBarValues(self):

        print('Updating VC Bottom')
        self.setVtvar_btm.setText("{:.0f}".format(self.VentilatorMain.setVt))
        self.setRRvar_btm.setText("{:.0f}".format(self.VentilatorMain.setRR))
        self.setTplateauvar_btm.setText("{:.1f}".format(self.VentilatorMain.setTplateau))
        self.setIERatiovar_btm.setText("{:.1f}".format(self.VentilatorMain.setIERatio))
        self.setPEEPvar_btm.setText("{:.0f}".format(self.VentilatorMain.setPEEP))

        #self.check_alarms()

class BottomAreaPC(QWidget):
    def __init__(self, parent=None):
        super(BottomAreaPC, self).__init__(parent)
        uic.loadUi("bottomDisplay_PC.ui", self)

        self.VentilatorMain = self.parent()


    def updateBottomBarValues(self):
        print('Updating PC Bottom')
        self.setPIPvar_btm.setText("{:.0f}".format(self.VentilatorMain.setPIP))
        self.setInspRiseTimevar_btm.setText("{:.0f}".format(self.VentilatorMain.setInspRiseTime))
        self.setRRvar_btm.setText("{:.0f}".format(self.VentilatorMain.setRR))
        self.setIERatiovar_btm.setText("{:.1f}".format(self.VentilatorMain.setIERatio))
        self.setPEEPvar_btm.setText("{:.0f}".format(self.VentilatorMain.setPEEP))

class BottomAreaPS(QWidget):
    def __init__(self, parent=None):
        super(BottomAreaPS, self).__init__(parent)
        uic.loadUi("bottomDisplay_PS.ui", self)

        self.VentilatorMain = self.parent()


    def updateBottomBarValues(self):
        self.setVtvar_btm.setText("{:.0f}".format(self.VentilatorMain.setVt))
        self.setRRvar_btm.setText("{:.0f}".format(self.VentilatorMain.setRR))
        self.setTinspvar_btm.setText("{:.1f}".format(self.VentilatorMain.setTinsp))
        self.setPEEPvar_btm.setText("{:.0f}".format(self.VentilatorMain.setPEEP))



class SettingsWidget_VC(QWidget):
    def __init__(self, parent=None):
        super(SettingsWidget_VC, self).__init__(parent)
        uic.loadUi("settingsWidget_VC.ui", self)

        self.scrollbarSettings = SCROLLBAR_SETTINGS
        self.VentilatorMain = self.parent()

        self.setIERatioScrollBar.setStyleSheet(self.scrollbarSettings)
        self.setTplateauScrollBar.setStyleSheet(self.scrollbarSettings)
        self.setRRScrollBar.setStyleSheet(self.scrollbarSettings)
        self.setPEEPScrollBar.setStyleSheet(self.scrollbarSettings)
        self.setVtScrollBar.setStyleSheet(self.scrollbarSettings)
        
        self.setIERatioScrollBar.setPageStep(1)
        self.setTplateauScrollBar.setPageStep(1)
        self.setRRScrollBar.setPageStep(1)
        self.setPEEPScrollBar.setPageStep(1)
        self.setVtScrollBar.setPageStep(5)

        self.setIERatioScrollBar.setMaximum(IERATIO_MAX*10)
        self.setRRScrollBar.setMaximum(RR_MAX*10)
        self.setPEEPScrollBar.setMaximum(PEEP_MAX)
        self.setVtScrollBar.setMaximum(VT_MAX)
        self.setIERatioScrollBar.setMaximum(TPLATEAU_MAX*10)
        self.setIERatioScrollBar.setMinimum(IERATIO_MIN*10)
        self.setTplateauScrollBar.setMinimum(TPLATEAU_MIN*10)
        self.setRRScrollBar.setMinimum(RR_MIN*10)
        self.setPEEPScrollBar.setMinimum(PEEP_MIN)
        self.setVtScrollBar.setMinimum(VT_MIN)

        self.mID = 0

        self.readInitialSetValues()
        self.updateSetValues()

    def readInitialSetValues(self):
        # TODO: read initial values a file

        self.setIERatio_tmp = self.VentilatorMain.setIERatio
        self.setTplateau_tmp = self.VentilatorMain.setTplateau
        self.setRR_tmp = self.VentilatorMain.setRR
        self.setVt_tmp = self.VentilatorMain.setVt
        self.setPEEP_tmp = self.VentilatorMain.setPEEP

        self.setIERatioScrollBar.setValue(self.setIERatio_tmp * 10)
        self.setTplateauScrollBar.setValue(self.setTplateau_tmp * 10)
        self.setRRScrollBar.setValue(self.setRR_tmp*10)
        self.setPEEPScrollBar.setValue(self.setPEEP_tmp)
        self.setVtScrollBar.setValue(self.setVt_tmp)

    def updateSetValues(self): 

        self.setIERatio_tmp = (self.setIERatioScrollBar.value() / 10)
        self.setTplateau_tmp = (self.setTplateauScrollBar.value() / 10)
        self.setRR_tmp = (self.setRRScrollBar.value() / 10)
        self.setPEEP_tmp = self.setPEEPScrollBar.value()
        self.setVt_tmp = self.setVtScrollBar.value()

        self.setIERatiovar_setting.setText("{:.1f}".format(self.setIERatio_tmp))
        self.setTplateauvar_setting.setText("{:.1f}".format(self.setTplateau_tmp))
        self.setRRvar_setting.setText("{:.1f}".format(self.setRR_tmp))
        self.setVtvar_setting.setText("{:.0f}".format(self.setVt_tmp))
        self.setPEEPvar_setting.setText("{:.0f}".format(self.setPEEP_tmp))


    def commitValueChanges(self):
        print('Commiting values VC')
        self.setIERatio = (self.setIERatioScrollBar.value() / 10)
        self.setTplateau = (self.setTplateauScrollBar.value() / 10)
        self.setRR = (self.setRRScrollBar.value() / 10)
        self.setVt = (self.setVtScrollBar.value())
        self.setPEEP = (self.setPEEPScrollBar.value())

        self.mID += 1 

        self.VentilatorMain.thread.sendVCSettings(self.mID, self.setPEEP, self.setVt,\
                                                self.setRR, self.setIERatio, self.setTplateau)


class SettingsWidget_PC(QWidget):
    def __init__(self, parent=None):
        super(SettingsWidget_PC, self).__init__(parent)
        uic.loadUi("settingsWidget_PC.ui", self)

        self.VentilatorMain = self.parent()

        self.scrollbarSettings = SCROLLBAR_SETTINGS

        self.setIERatioScrollBar.setStyleSheet(self.scrollbarSettings)
        self.setInspRiseTimeScrollBar.setStyleSheet(self.scrollbarSettings)
        self.setRRScrollBar.setStyleSheet(self.scrollbarSettings)
        self.setPEEPScrollBar.setStyleSheet(self.scrollbarSettings)
        self.setPIPScrollBar.setStyleSheet(self.scrollbarSettings)
        
        self.setIERatioScrollBar.setPageStep(1)
        self.setInspRiseTimeScrollBar.setPageStep(1)
        self.setRRScrollBar.setPageStep(1)
        self.setPEEPScrollBar.setPageStep(1)
        self.setPIPScrollBar.setPageStep(5)

        self.setIERatioScrollBar.setMaximum(IERATIO_MAX*10)
        self.setRRScrollBar.setMaximum(RR_MAX*10)
        self.setPEEPScrollBar.setMaximum(PEEP_MAX)
        self.setInspRiseTimeScrollBar.setMaximum(INSPRISETIME_MAX)
        self.setPIPScrollBar.setMaximum(PIP_MAX)

        self.setIERatioScrollBar.setMinimum(IERATIO_MIN*10)
        self.setRRScrollBar.setMinimum(RR_MIN*10)
        self.setPEEPScrollBar.setMinimum(PEEP_MIN)
        self.setPIPScrollBar.setMinimum(PIP_MIN)
        self.setInspRiseTimeScrollBar.setMinimum(INSPRISETIME_MIN)

        self.mID = 0

        self.readInitialSetValues()
        self.updateSetValues()

    def readInitialSetValues(self):
        # TODO: read initial values a file

        self.setIERatio_tmp = self.VentilatorMain.setIERatio
        self.setInspRiseTime_tmp = self.VentilatorMain.setInspRiseTime
        print('insp rise time aa {}'.format(self.setInspRiseTime_tmp))
        self.setRR_tmp = self.VentilatorMain.setRR
        self.setPIP_tmp = self.VentilatorMain.setPIP
        self.setPEEP_tmp = self.VentilatorMain.setPEEP

        self.setIERatioScrollBar.setValue(self.setIERatio_tmp * 10)
        self.setInspRiseTimeScrollBar.setValue(10)
        print('insp rise time bb {}'.format(self.setInspRiseTime_tmp))
        print('insp rise time cc {}'.format(self.setInspRiseTimeScrollBar.value()))

        self.setRRScrollBar.setValue(self.setRR_tmp*10)
        self.setPEEPScrollBar.setValue(self.setPEEP_tmp)
        self.setPIPScrollBar.setValue(self.setPIP_tmp)

    def updateSetValues(self): 

        self.setIERatio_tmp = (self.setIERatioScrollBar.value() / 10)
        self.setInspRiseTime_tmp = (self.setInspRiseTimeScrollBar.value())
        self.setRR_tmp = (self.setRRScrollBar.value() / 10)
        self.setPEEP_tmp = self.setPEEPScrollBar.value()
        self.setPIP_tmp = self.setPIPScrollBar.value()

        self.setIERatiovar_setting.setText("{:.1f}".format(self.setIERatio_tmp))
        self.setInspRiseTimevar_setting.setText("{:.1f}".format(self.setInspRiseTime_tmp))
        self.setRRvar_setting.setText("{:.1f}".format(self.setRR_tmp))
        self.setPIPvar_setting.setText("{:.0f}".format(self.setPIP_tmp))
        self.setPEEPvar_setting.setText("{:.0f}".format(self.setPEEP_tmp))


    def commitValueChanges(self):
        print('Commiting values PC')
        self.setIERatio = (self.setIERatioScrollBar.value() / 10)
        self.setInspRiseTime = (self.setInspRiseTimeScrollBar.value() / 10)
        self.setRR = (self.setRRScrollBar.value() / 10)
        self.setPIP = (self.setPIPScrollBar.value())
        self.setPEEP = (self.setPEEPScrollBar.value())

        self.mID += 1 

        self.VentilatorMain.thread.sendPCSettings(self.mID, self.setPEEP, self.setPIP,\
                                                self.setRR, self.setIERatio, self.setInspRiseTime)


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

        self.VentilatorMain = self.parent()

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

        self.flowData = pg.PlotCurveItem()
        self.pfillX = pg.FillBetweenItem(self.flowData, self.basePlotFlow, brush = self.plotcolor)
        self.graphFlow.addItem(self.flowData)
        self.graphFlow.addItem(self.basePlotFlow)
        self.graphFlow.addItem(self.pfillX)

        self.volumeData = pg.PlotCurveItem()
        self.pfillY = pg.FillBetweenItem(self.volumeData, self.basePlotVol, brush = self.plotcolor)
        self.graphVolume.addItem(self.volumeData)
        self.graphVolume.addItem(self.basePlotVol)
        self.graphVolume.addItem(self.pfillY)
        
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
        self.lastVexp = self.VentilatorMain.vExp
        self.lastVinsp = self.VentilatorMain.vInsp
        self.lastMode = self.VentilatorMain.currentMode
        self.currentMode = 2 #manual
        self.setVinsp = 30
        self.setVexp = 0
        self.VentilatorMain.thread.setWrite(self.currentMode,'0;'+str(self.setVinsp)+';1;'+str(self.setVexp))
        print('Setting Valve Insp at 30')

    def manualVentilationReleased(self):
        self.VentilatorMain.vExp = self.lastVexp
        self.VentilatorMain.vInsp = self.lastVinsp
        self.VentilatorMain.currentMode = self.lastMode
        self.VentilatorMain.thread.setWrite(self.currentMode,'0;'+str(self.setVinsp)+';1;'+str(self.setVexp))
        print('restarting all')

    def manualPausePressed(self):
        self.lastVexp = self.VentilatorMain.vExp
        self.lastVinsp = self.VentilatorMain.vInsp
        self.lastMode = self.VentilatorMain.currentMode
        self.currentMode = 2 #manual
        self.setVinsp = 0
        self.setVexp = 0
        self.VentilatorMain.thread.setWrite(self.currentMode,'0;'+str(self.setVinsp)+';1;'+str(self.setVexp))
        print('Setting Valve Insp at 0')
    def manualPauseReleased(self):
        self.VentilatorMain.vExp = self.lastVexp
        self.VentilatorMain.vInsp = self.lastVinsp
        self.VentilatorMain.currentMode = self.lastMode
        self.VentilatorMain.thread.setWrite(self.currentMode,'0;'+str(self.setVinsp)+';1;'+str(self.setVexp))
        print('restarting all')

    def initializeGraphs(self):
        self.channelFlow = [0]*X_AXIS_LENGTH
        self.channelVolume = [0]*X_AXIS_LENGTH
        self.channelPressure = [0]*X_AXIS_LENGTH
        self.counterPlots = 0


    def updateGraphs(self, pressure, flow, vt):

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