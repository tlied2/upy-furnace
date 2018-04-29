import network
import esp
import machine
import utime as time
import ujson

from tmp102 import Tmp102
import tmp102.shutdown
import tmp102.oneshot  # lint:ok
import bme280


class MySensor(object):

    def __init__(self, mqttcli):
        self.mqttcli = mqttcli
        self.tmp102_failed = True
        self.bme_failed = True

        I2C_BUS = machine.I2C(
            scl=machine.Pin(5),
            sda=machine.Pin(4),
            freq=100000)
        #print(("I2C Devices Found: {}".format([hex(tmp) for tmp in I2C_BUS.scan()])))
        if len(I2C_BUS.scan()) > 10:
            print("I2C Bus Error. Might be disconnected, please check cable")

        try:
            self.BME = bme280.BME280(i2c=I2C_BUS,
                address=bme280.BME280_I2CADDR + 1,
                mode=bme280.BME280_OSAMPLE_8)
            self.bme_failed = False
        except OSError:
            self.bme_failed = True

        try:
            self.TMP102 = Tmp102(I2C_BUS, 0x48, shutdown=True)
            self.tmp102_failed = False
        except OSError:
            self.tmp102_failed = True

    def send_mqtt_data(self):
        ''' Collects all sensors, and sends MQTT packets for each '''

        sysdat = self.sysinfo()
        self.mqttcli.pub(b"test-furnace/system", ujson.dumps(sysdat))

        if not self.bme_failed:
            bmedat = self.bme2dict()
            self.mqttcli.pub(b"test-furnace/bme280", ujson.dumps(bmedat))
        else:
            self.mqttcli.pub(b"test-furnace/bme280", ujson.dumps({'failed': True}))

        if not self.tmp102_failed:
            self.mqttcli.pub(b"test-furnace/tmp102", ujson.dumps(self.tmp102_get()))
        else:
            self.mqttcli.pub(b"test-furnace/tmp102", ujson.dumps({"failed": True}))

    def tmp102_get(self):
        ''' Returns dict of tmp102 values '''
        try:
            self.TMP102.initiate_conversion()
            while not self.TMP102.conversion_ready:
                time.sleep_ms(10)
            address = self.TMP102.address
            temperature = "{0:0.2f}".format(self.TMP102.temperature)
        except RuntimeError as tmpex:
            print(tmpex)
            address = None
            temperature = 0.0
        except OSError:
            self.tmp102_failed = True

        tmp102dat = {
            'address': address,
            'temp': temperature
        }

        print(tmp102dat)
        return tmp102dat

    def bme2dict(self):
        ''' Returns dict of bme280 values '''
        # Pack BME values into dict
        keys = ["temp", "pressure", "humidity"]
        bmedat = dict(list(zip(keys, self.BME.values)))
        #bmedat['timestamp'] = utime.time()

        # Convert to numeric
        bmedat['temp'] = "{0:0.2f}".format(float(bmedat['temp'][:-1]))  # DegC
        bmedat['humidity'] = "{0:0.2f}".format(float(bmedat['humidity'][:-1]))  # %
        bmedat['pressure'] = "{0:0.2f}".format(float(bmedat['pressure'][:-3]))  # hPa

        print(bmedat)
        return bmedat

    @staticmethod
    def sysinfo():
        ''' Returns dict of some system info '''
        calib_add_mV = 308
        mV = machine.ADC(1).read() + calib_add_mV

        voltage = "{0:0.2f}".format(mV / 1000.0)
        sysinfo = {
            'ipaddr': network.WLAN(network.STA_IF).ifconfig()[0],
            'freemem': esp.freemem(),
            'voltage': voltage,
        }

        return sysinfo
