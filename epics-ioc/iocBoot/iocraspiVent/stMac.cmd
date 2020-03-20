#!../../bin/darwin-x86/raspiVent

#- You may have to change raspiVent to something else
#- everywhere it appears in this file

< envPaths

cd "${TOP}"

## Register all support components
dbLoadDatabase "dbd/raspiVent.dbd"
raspiVent_registerRecordDeviceDriver pdbbase

## Load record instances
#dbLoadTemplate "db/user.substitutions"
dbLoadRecords "db/raspiVentVersion.db", "user=pi"
dbLoadRecords "db/rpiControl.db", "P=Raspi:,R=central:"
dbLoadRecords "db/rpiSensors-simul.db", "P=Raspi:,R=central:"
#dbLoadRecords "db/dbSubExample.db", "user=pi"

#- Set this to see messages from mySub
#var mySubDebug 1

#- Run this to trace the stages of iocInit
#traceIocInit

cd "${TOP}/iocBoot/${IOC}"
iocInit

## Start any sequence programs
#seq sncExample, "user=pi"
