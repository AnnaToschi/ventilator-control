# EPICS ioc controller for Ventilator Support

## Install Steps

1. Install EPICS [https://docs.epics-controls.org/projects/how-tos/en/latest/getting-started/installation.html]
2. Install also `ASYN` and `StreamDevice` according to Steps 6. and 7. of previous link.
3. The EPICS sequencer needs the re2c package
  * `sudo apt-get install re2c` or `brew install re2c`
  * `cd [..]/EPICS/support`
  * `https://www-csr.bessy.de/control/SoftDist/sequencer/releases/seq-2.2.8.tar.gz`
  * ` `
3. mkdir folder and do:
```bash 
git clone https://gitlab.com/air4all-portugal/ventilator-control
```
4. Create a file  `ventilator-control/RELEASE.local` (not versioned) with your installation details
```
   EPICS_BASE = ...
```
5. On file `iocBoot/iocraspiVent/st.cmd`
    check the executable name on the first line 
```
cd ventilator-control/epics-ioc
source ./epicsenv.sh
make
cd iocBoot/iocraspiVent
./st.cmd
```

6. To run as deamon install `screen` and include this on `/etc/rc.local`
```
screen -dm bash -c "cd /..../ventilator-control/epics-ioc/iocBoot/iocraspiVent; ../../bin/linux-arm/raspiVent st.cmd"
```
