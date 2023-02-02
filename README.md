# solarwind
Automation between Solar Pannels and consumer (any loads). The script is using 2 relay modules (Keyes 5V 1 Channel Relay Module
Keyes and 5V 2 Channel Relay Module Shield for Arduino). The double channel module is relay for switching on/off mains the  single
way relay is for switching on/off power inverter. The idea is to switch power consumer to solar source when bat is ready and fully charged. And switch off to mains when bat is drained.
To control the power is used INA3221 module with customised 100A shunts. The Raspberry Pi Zero is used as central control and send for reports to remote server.

# P
