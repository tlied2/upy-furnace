#!/bin/sh

PORT="/dev/ttyUSB0"

FILES="\
config.json \
main.py \
mysensors.py \
upy-mylib/mywifi.py \
upy-mylib/mymqtt.py \
mpy_bme280_esp8266/bme280.py \
micropython-tmp102/tmp102 \
"

for FILE in $FILES; do
echo ampy -p $PORT put $FILE ;
ampy -p $PORT put $FILE ;
done
