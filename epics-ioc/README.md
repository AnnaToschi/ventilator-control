# EPICS ioc controller for Ventilator Support

## Install Steps

1. Install EPICS [https://docs.epics-controls.org/projects/how-tos/en/latest/getting-started/installation.html]
2. mkdir folder and do:
```
git clone https://gitlab.com/air4all-portugal/ventilator-control
cd ventilator-control/epics-ioc
```
3. Adjust file `configure/RELEASE` 
   `EPICS_BASE =`
4. On file `iocBoot/iocraspiVent/st.cmd`
    check the executable name on the first line 
```
source ./epicsenv.sh
make
cd iocBoot/iocraspiVent
./st.cmd
```

6. To run as deamon install `screen` and include this on `/etc/rc.local`
```
screen -dm bash -c "cd /..../ventilator-control/epics-ioc/iocBoot/iocraspiVent; ../../bin/linux-arm/raspiVent st.cmd"
```
