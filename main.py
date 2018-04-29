import machine
import utime as time
import ujson as json

import mywifi
from mymqtt import MyMQTT
from mysensors import MySensor

with open('config.json') as configfile:
    CONFIG = json.load(configfile)


def main():

    mywifi.init(CONFIG['wifi'])

    mqttcli = MyMQTT(CONFIG['mqtt'])

    mysensor = MySensor(mqttcli)

    errcnt = 0

    while True:

        try:
            mysensor.send_mqtt_data()
            errcnt = 0
        except Exception:
            errcnt += 1
            if errcnt > 2:
                machine.reset()

        # Retry quickly in case of error
        if errcnt > 0:
            time.sleep(10)
        # Send data once a minute otherwise
        else:
            time.sleep(60)

if __name__ == '__main__':
    main()
