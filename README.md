# solarwind Project 
Automation between Solar Pannels and consumer (any loads). The script is using 2 relay modules (Keyes 5V 1 Channel Relay Module
Keyes and 5V 2 Channel Relay Module Shield for Arduino). The double channel module is relay for switching on/off mains the  single
way relay is for switching on/off power inverter. The idea is to switch power consumer to solar source when bat is ready 
and fully charged (approx 26V and over). And switch back to mains when battery is drained  (approx 20 V and lower). 
To control the power is used INA3221 module with customised 100A shunts. The Raspberry Pi Zero is used as central control 
and send for reports to remote server. 
The INA3221 board connected to the Raspberry PI module via I2C Bus. Power Inverter with wired remote control and button 
on/off which is used for switching and checking inverter status.  

# P
