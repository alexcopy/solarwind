#!/bin/bash

SESSION_NAMES=("info" "debug" "error" "warning")

start_screen_session() {
    screen -S "$1" -d -m bash -c "tail --follow=name logs/$1.log"
    echo "Detached screen session created: $1."
}

start_python_script() {
    if pgrep -f "python main\.py" >/dev/null; then
        echo "Solar Pond App is running"
    else
        echo "The Service is stopped"
        nohup python main.py >logs/run.log &
    fi
}

# Check if Python script is running
start_python_script

# Check if existing screen sessions are running with the same names
for SESSION_NAME in "${SESSION_NAMES[@]}"; do
    if ! screen -list | grep -q "$SESSION_NAME"; then
        start_screen_session "$SESSION_NAME"
    else
        echo "Screen session already running: $SESSION_NAME."
    fi
done