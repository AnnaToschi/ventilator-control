TOP=../..

include $(TOP)/configure/CONFIG
#----------------------------------------
#  ADD MACRO DEFINITIONS BELOW HERE

# Use typed rset structure (see 3.16.1 release notes)
USR_CPPFLAGS += -DUSE_TYPED_RSET

# xxxRecord.h will be created from xxxRecord.dbd
DBDINC += xxxRecord

# Install xxxSupport.dbd into <top>/dbd
DBD += xxxSupport.dbd

# Build an IOC support library
LIBRARY_IOC += raspiVentSupport

# Compile and add code to the support library
raspiVentSupport_SRCS += xxxRecord.c
raspiVentSupport_SRCS += devXxxSoft.c

# Link locally-provided code into the support library,
# rather than directly into the IOC application, that
# causes problems on Windows DLL builds
raspiVentSupport_SRCS += dbSubExample.c
raspiVentSupport_SRCS += devraspiVentVersion.c
#raspiVentSupport_SRCS += raspiVentHello.c
raspiVentSupport_SRCS += initTrace.c

raspiVentSupport_LIBS += $(EPICS_BASE_IOC_LIBS)

# Auto-generate a header file containing a version string.
# Version comes from the VCS if available, else date+time.
GENVERSION = raspiVentVersion.h
# Macro name
GENVERSIONMACRO = raspiVentVERSION

# Build the IOC application
PROD_IOC = raspiVent

# raspiVent.dbd will be created and installed
DBD += raspiVent.dbd

# raspiVent.dbd will include these files:
raspiVent_DBD += base.dbd
raspiVent_DBD += xxxSupport.dbd
raspiVent_DBD += dbSubExample.dbd
raspiVent_DBD += devraspiVentVersion.dbd
#raspiVent_DBD += raspiVentHello.dbd
raspiVent_DBD += initTrace.dbd
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
	# Build sncVentilator into raspiVentSupport
	sncVentilator += +r
	#raspiVent_DBD += sncExample.dbd
	raspiVent_DBD += sncVentilator.dbd
    # A .stt sequence program is *not* pre-processed:
	raspiVentSupport_SRCS += sncVentilator.stt
	raspiVentSupport_LIBS += seq pv
	raspiVent_LIBS += seq pv

#     # Build sncProgram as a standalone program
#     PROD_HOST += sncProgram
#     sncProgram_SNCFLAGS += +m
#     # A .st sequence program *is* pre-processed:
#     sncProgram_SRCS += sncProgram.st
#     sncProgram_LIBS += seq pv
#     sncProgram_LIBS += $(EPICS_BASE_HOST_LIBS)
endif

# Link QSRV (pvAccess Server) if available
ifdef EPICS_QSRV_MAJOR_VERSION
    raspiVent_LIBS += qsrv
    raspiVent_LIBS += $(EPICS_BASE_PVA_CORE_LIBS)
    raspiVent_DBD += PVAServerRegister.dbd
    raspiVent_DBD += qsrv.dbd
endif

# Finally link IOC to the EPICS Base libraries
raspiVent_LIBS += $(EPICS_BASE_IOC_LIBS)

include $(TOP)/configure/RULES
#----------------------------------------
#  ADD EXTRA GNUMAKE RULES BELOW HERE

# Explicit dependency needed for generated header file
devraspiVentVersion$(DEP): $(COMMON_DIR)/$(GENVERSION)
