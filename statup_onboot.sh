#!/bin/bash
SERVICE= "^python\d?\s+main\.py"
path_to_service= "/"
if pgrep -f "$SERVICE" > /dev/null
then
    echo "Solar Pond App is running"
else
    echo "$SERVICE stopped"
    exec python  "$path_to_service"
    # mail
fi