# CS-STUDIO to design the dashboard of the ventilator

## Install Steps

### CS-Studio Version 4.5.9 (Stable with BOY GUIs)
1. Download and install Java JDK version 1.8.0_241.jdk (make sure the folder is int the path /Library/Java/JavaVirtualMachines/)
```https://www.oracle.com/java/technologies/javase-downloads.html#JDK8```
2. For Windows Use [MEGA](https://mega.nz/#F!EolCyShY!D0QUZdcafG1mUXbqWywFsg)

3. Download latest version of CS-Studio for your OS:
```http://download.controlsystemstudio.org/release/4.5/```

### CS-Studio Version 4.6.x (IN DEVELOPMENT - With *Display Builder* GUIs)
#### MACos Instalation
1.  Install java
[Java
14](https://www.oracle.com/java/technologies/javase-jdk14-downloads.html?fbclid=IwAR1Y75ohFxV7Qo0-v6Ue13KiLVWdGqx-Ij6AddHdJsaIK1_nIj-Yl4Zg2sU)
2. Untar to /Library/Java/JavaVirtualMachines
3. Get CS-Studio
[CS-Studio 4.6.1](https://controlssoftware.sns.ornl.gov/css_phoebus/)
4. Edit phoebus.sh , to be something like
```
#!/bin/sh
#
# Phoebus launcher for Linux or Mac OS X

# When deploying, change "TOP"
# to the absolute installation path
TOP="/Users/xxxxxxx/EPICS/phoebus-4.6.1/"
#THIS_SCRIPT="$(realpath "$0")";
#TOP="${THIS_SCRIPT%/*}";

# Ideally, assert that Java is found
export JAVA_HOME=/Library/Java/JavaVirtualMachines/jdk-14.jdk/Contents/Home
export PATH="$JAVA_HOME/bin:$PATH"

```

#### Raspian Instalation
```bash
sudo apt install maven openjfx libopenjfx-java default-jdk
```
/usr/libexec/java_home -V
