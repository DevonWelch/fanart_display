#!/bin/bash

mkdir -p "$HOME/tmp"
PIDFILE="$HOME/tmp/run_display.pid"

if [ -e "${PIDFILE}" ] && (ps -u $(whoami) -opid= |
                           grep -P "^\s*$(cat ${PIDFILE})$" &> /dev/null); then
  if ps -o etimes= -p "$$" > 86400; then
    echo "Process has been running for more than 24 hours, restarting."
    rm -f "${PIDFILE}"
    kill -9 $(cat "${PIDFILE}") &> /dev/null
  else
    echo "Already running."
    exit 99
  fi
fi

# /path/to/myprogram > $HOME/tmp/myprogram.log &
source /home/devon/kivy_venv/bin/activate
cd /home/devon/fanart_display
python /home/devon/fanart_display/fanart_display_v2.py &
echo $! > "${PIDFILE}"
chmod 644 "${PIDFILE}"

# if line endings are bad, run:
# sed -i -e 's/\r$//' run_display.sh