# solarwind
AUtomation between Solar Pannels and consumer (any loads). The script is using 2 relay blocks. THe firs block is double relay for mains switching on/off the second one is single
pole relay for switching on/off power inverter. The idea is to switch power consumer to solar when bat is ready and almost fully charged. And switch off when bat is drained.
To control power is used INA3221 module with customised 100A shunts. The Raspberry Pi Zero is used to control and send reports to remote server.

# P
