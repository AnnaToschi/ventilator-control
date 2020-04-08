#!../../bin/darwin-x86/raspiVent

#- You may have to change raspiVent to something else
#- everywhere it appears in this file

< envPaths

epicsEnvSet ("STREAM_PROTOCOL_PATH","$(TOP)/db")
epicsEnvSet( "SAVE_DIR", "$(TOP)/iocBoot/$(IOC)" )

cd "${TOP}"

## Register all support components
dbLoadDatabase "dbd/raspiVent.dbd"
raspiVent_registerRecordDeviceDriver pdbbase

## Load record instances
dbLoadRecords "db/raspiVentVersion.db", "user=pi"
dbLoadRecords "db/rpiControl.db", "P=Raspi:,R=central:"
#dbLoadRecords "db/rpiSensors-simul.db", "P=Raspi:,R=central:"
#dbLoadRecords "db/dbSubExample.db", "user=pi"
#dbLoadTemplate "db/user.substitutions"

## Load Serial drivers
#drvAsynSerialPortConfigure("RS0","/dev/ttyUSB0")
#drvAsynSerialPortConfigure("RS0","/dev/ttyAMA0")
#drvAsynSerialPortConfigure("RS0","/dev/ttyUSB0")
drvAsynSerialPortConfigure("RS0","/dev/cu.usbmodem14201")

asynSetOption("RS0", 0, "baud", "115200")
asynSetOption("RS0", 0, "bits", "8")
asynSetOption("RS0", 0, "parity", "none")
asynSetOption("RS0", 0, "stop", "1")
asynSetOption("RS0", 0, "clocal", "Y")
asynSetOption("RS0", 0, "crtscts", "N")

dbLoadRecords "db/rpiSensors-arduino.db", "P=Raspi:,R=central:,PORT=RS0")
#dbLoadRecords "db/rpiControl-arduino.db", "P=Raspi:,R=central:,PORT=RS0")
# Stream DEBUG
var streamError 1
var streamDebug 1
streamSetLogfile("logfile.txt")

#- Set this to see messages from mySub
#var mySubDebug 1

#- Run this to trace the stages of iocInit
#traceIocInit

# Autosave configuration
save_restoreSet_status_prefix("Raspi:")
set_requestfile_path("$(SAVE_DIR)")
set_savefile_path("$(SAVE_DIR)/save")
save_restoreSet_NumSeqFiles(3)
#save_restoreSet_SeqPeriodInSeconds(600)
set_pass0_restoreFile("$(IOC).sav")
set_pass1_restoreFile("$(IOC).sav")
dbLoadRecords("$(AUTOSAVE)/asApp/Db/save_restoreStatus.db", "P=Raspi:")

cd "${TOP}/iocBoot/${IOC}"
iocInit

# Create request file and start periodic 'save’
create_monitor_set("$(IOC).req", 30)

## Start any sequence programs
seq sncVentilator, "user=Raspi:central"
#seq sncExample, "user=Raspi:central"

