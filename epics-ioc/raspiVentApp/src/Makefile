TOP=../..

include $(TOP)/configure/CONFIG
#----------------------------------------
#  ADD MACRO DEFINITIONS BELOW HERE

# xxxRecord.h will be created from xxxRecord.dbd
DBDINC += xxxRecord

# Install xxxSupport.dbd into <top>/dbd
DBD += xxxSupport.dbd

# Build an IOC support library
LIBRARY_IOC += raspiVentSupport

# Compile and add the code to the support library
#raspiVentSupport_SRCS += xxxRecord.c
#raspiVentSupport_SRCS += devXxxSoft.c

# Link locally-provided code into the support library,
# rather than directly into the IOC application.
# This is required for Windows DLL builds.
raspiVentSupport_SRCS += dbSubExample.c
#raspiVentSupport_SRCS += raspiVentHello.c
raspiVentSupport_SRCS += initTrace.c

raspiVentSupport_LIBS += $(EPICS_BASE_IOC_LIBS)


# Build the IOC application
PROD_IOC = raspiVent

# raspiVent.dbd will be created and installed
DBD += raspiVent.dbd

# raspiVent.dbd will include these files:
raspiVent_DBD += base.dbd
#raspiVent_DBD += xxxSupport.dbd
raspiVent_DBD += dbSubExample.dbd
#raspiVent_DBD += raspiVentHello.dbd
#raspiVent_DBD += initTrace.dbd
raspiVent_DBD += asyn.dbd
raspiVent_DBD += stream.dbd
raspiVent_DBD += drvAsynSerialPort.dbd
raspiVent_DBD += epidRecord.dbd
raspiVent_DBD += asSupport.dbd

# raspiVent_registerRecordDeviceDriver.cpp derives from raspiVent.dbd
raspiVent_SRCS += raspiVent_registerRecordDeviceDriver.cpp

# Build the main IOC entry point where needed
raspiVent_SRCS_DEFAULT += raspiVentMain.cpp
raspiVent_SRCS_vxWorks += -nil-

# Link in the code from our support library
raspiVent_LIBS += raspiVentSupport
# Add all the support libraries needed by this IOC
raspiVent_LIBS += asyn
raspiVent_LIBS += stream
raspiVent_LIBS += std
raspiVent_LIBS += autosave

# To build SNL programs, SNCSEQ must be defined
# in the <top>/configure/RELEASE file
ifneq ($(SNCSEQ),)
    # Build sncExample into raspiVentSupport
    sncVentilator_SNCFLAGS  += +r
    #sncExample_SNCFLAGS += +r
    raspiVent_DBD += sncVentilator.dbd
    # A .stt sequence program is *not* pre-processed:
    raspiVentSupport_SRCS += sncVentilator.stt
    raspiVentSupport_LIBS += seq pv
    raspiVent_LIBS += seq pv

    # Build sncProgram as a standalone program
    #PROD_HOST += sncProgram
    #sncProgram_SNCFLAGS += +m
    # A .st sequence program *is* pre-processed:
    #sncProgram_SRCS += sncProgram.st
    #sncProgram_LIBS += seq pv
    #sncProgram_LIBS += $(EPICS_BASE_HOST_LIBS)
endif

# Finally link IOC to the EPICS Base libraries
raspiVent_LIBS += $(EPICS_BASE_IOC_LIBS)

include $(TOP)/configure/RULES
#----------------------------------------
#  ADD EXTRA GNUMAKE RULES BELOW HERE

