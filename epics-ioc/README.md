# EPICS ioc controller for Ventilator Support

## Install Steps
### EPICS, ASYN, StreamDevice, SEQ, and STD

1. Install EPICS [https://docs.epics-controls.org/projects/how-tos/en/latest/getting-started/installation.html]
2. Install also `ASYN` and `StreamDevice` Packages according to Steps 6. and 7. of previous link.
3. The EPICS sequencer needs the `re2c` package
  * `sudo apt-get install re2c` or `brew install re2c`
  * `cd [..]/EPICS/support`
  * Create a file  `RELEASE.local` (not versioned) with your installation details
```
   EPICS_BASE = ...
```
  * `wget https://www-csr.bessy.de/control/SoftDist/sequencer/releases/seq-2.2.8.tar.gz`
  * `tar zxf seq-x.y.z.tar.gz`
  * `cd  seq-x.y.z`
  * `make `
4. Install STD
  * `cd [..]/EPICS/support`
```bash
git clone https://github.com/epics-modules/std
```
  * edit configure/RELEASE
  * `make `

## Get and build IOC application
1. goto to `EPICS` folder:
```bash
git clone https://gitlab.com/air4all-portugal/ventilator-control
```
2. Create a file  `ventilator-control/RELEASE.local` (not versioned) with your installation details
```
EPICS_BASE = [/../EPICS/epics-base]
MODULES = [/..]/EPICS/support
SNCSEQ = $(MODULES)/seq-2.2.8
ASYN = $(MODULES)/asyn
STREAM = $(MODULES)/stream
STD = $(MODULES)/std
```
3. Build IOC
```
cd ventilator-control/epics-ioc
source ./epicsenv.sh
make
cd iocBoot/iocraspiVent
```
4. On file `st.cmd` or `stMac.cmd`
    check the executable name on the first line
    and Run:
```
./st.cmd
```

5. To run as deamon install `screen` and include this on `/etc/rc.local`
```
screen -dm bash -c "cd /..../ventilator-control/epics-ioc/iocBoot/iocraspiVent; ../../bin/linux-arm/raspiVent st.cmd"
```
