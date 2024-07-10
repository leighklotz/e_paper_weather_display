#!/bin/bash

YMD=$(date --iso-8601=date)

cd ~pi

exec &>> epaper-weather-kiosk.$YMD.log

echo "Checking for /home/pi/kiosk.off..."

while [ ! -f /home/pi/kiosk.off ]
do
  echo "* Starting $(date)"
  echo "* touch /home/pi/kiosk.off to stop"
  echo "* resetting screen"
  /home/pi/epd clear
  echo "* EPD done $(date)"
  /home/pi/epaper-weather
  echo "* FAIL! epaper-weather exited $(date)"
  echo "* sleeping 60s before restart"
  sleep 60
done

exit 0
