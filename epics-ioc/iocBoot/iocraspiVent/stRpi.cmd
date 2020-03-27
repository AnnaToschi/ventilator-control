#!../../bin/linux-arm/raspiVent

#- You may have to change raspiVent to something else
#- everywhere it appears in this file

< envPaths

epicsEnvSet ("STREAM_PROTOCOL_PATH","$(TOP)/db")

cd "${TOP}"

## Register all support components
dbLoadDatabase "dbd/raspiVent.dbd"
raspiVent_registerRecordDeviceDriver pdbbase

## Load record instances
dbLoadRecords "db/raspiVentVersion.db", "user=pi"
dbLoadRecords "db/rpiControl.db", "P=Raspi:,R=central:"
#dbLoadRecords "db/rpiSensors-arduino.db", "P=Raspi:,R=central:"
#dbLoadRecords "db/dbSubExample.db", "user=pi"
#dbLoadTemplate "db/user.substitutions"

## Load Serial drivers
#drvAsynSerialPortConfigure("RS0","/dev/ttyUSB0")
#drvAsynSerialPortConfigure("RS0","/dev/ttyAMA0")
drvAsynSerialPortConfigure("RS0","/dev/ttyUSB0")
#drvAsynSerialPortConfigure("RS0","/dev/ttys022")

asynSetOption("RS0", 0, "baud", "115200")
asynSetOption("RS0", 0, "bits", "8")
asynSetOption("RS0", 0, "parity", "none")
asynSetOption("RS0", 0, "stop", "1")
asynSetOption("RS0", 0, "clocal", "Y")
asynSetOption("RS0", 0, "crtscts", "N")

dbLoadRecords "db/rpiSensors-arduino.db", "P=Raspi:,R=central:,PORT=RS0")

# Stream DEBUG
var streamError 1
var streamDebug 1
streamSetLogfile("logfile.txt")

#- Set this to see messages from mySub
#var mySubDebug 1

#- Run this to trace the stages of iocInit
#traceIocInit

cd "${TOP}/iocBoot/${IOC}"
iocInit

## Start any sequence programs
seq sncVentilator, "user=Raspi:central"
#seq sncExample, "user=Raspi:central"
