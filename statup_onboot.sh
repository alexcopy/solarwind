#!/bin/bash

if pgrep -f "python main\.py" > /dev/null
then
    echo "Solar Pond App is running"
else
    echo "The Service is stopped"
    cd /path/to/python/script/ || exit
    python  main.py
    # Start screen session 1 and run custom script
    screen -S info -d -m bash -c 'tail --follow=name logs/main_inf.log'

    # Start screen session 2 and run custom script
    screen -S debug -d -m bash -c 'tail --follow=name logs/info.log'

    # Start screen session 3 and run custom script
    screen -S error -d -m bash -c 'tail --follow=name logs/error.log'
    echo "Three detached screen sessions created and custom scripts started."
fi