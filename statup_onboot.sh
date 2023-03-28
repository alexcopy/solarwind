#!/bin/bash

cd /path/to/python/script/ || exit
SESSION_NAMES=("info" "debug" "error", "warning")
if pgrep -f "python main\.py" > /dev/null
  then
      echo "Solar Pond App is running"
else
    echo "The Service is stopped"
    nohup python  main.py > logs/run.log &
    # Start screen session 1 and run custom script
    screen -S info -d -m bash -c 'tail --follow=name logs/main_inf.log'

    # Start screen session 2 and run custom script
    screen -S debug -d -m bash -c 'tail --follow=name logs/info.log'

    # Start screen session 3 and run custom script
    screen -S error -d -m bash -c 'tail --follow=name logs/error.log'
    echo "Three detached screen sessions created and custom scripts started."

    # Start screen session 3 and run custom script
    screen -S warning -d -m bash -c 'tail --follow=name logs/warning.log'
    echo "Three detached screen sessions created and custom scripts started."
fi

      # Loop through the session names and check if each one is still running
for SESSION_NAME in "${SESSION_NAMES[@]}"
  do
      if ! screen -list | grep -q "$SESSION_NAME"; then
            # If the screen session has been terminated, restart it
            screen -S "$SESSION_NAME" -d -m bash -c "tail --follow=name logs/$SESSION_NAME.log"
            echo "Detached screen sessions created: $SESSION_NAME."
      fi
  done