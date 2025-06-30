#!/bin/bash

mkdir -p "$HOME/tmp"
PIDFILE="$HOME/tmp/run_display.pid"

if [ -e "${PIDFILE}" ] && (ps -u $(whoami) -opid= |
                           grep -P "^\s*$(cat ${PIDFILE})$" &> /dev/null); then
  echo "Already running."
  exit 99
fi

# /path/to/myprogram > $HOME/tmp/myprogram.log &
source /home/devon/kivy_venv/bin/activate
cd /home/devon/fanart_display
python /home/devon/fanart_display/fanart_display_v2.py &
echo $! > "${PIDFILE}"
chmod 644 "${PIDFILE}"