import requests
import time
import pygatt

adapter = pygatt.backends.GATTToolBackend()

node1_temp = 4
node1_hum = 3
node1_press = 2
node1_uv = 1

url = 'http://192.168.100.101:8080'
json = '/json.htm?type=command&param=udevice&idx='
nvalue = '&nvalue='
svalue = '&svalue='

try:
    adapter.start()
    device = adapter.connect('A4:CF:12:75:BB:66')
    print("connected")

    while True:
        chrc_temp = device.char_read("00002a6e-0000-1000-8000-00805f9b34fb")
        chrc_hum = device.char_read("00002a6f-0000-1000-8000-00805f9b34fb")
        chrc_press = device.char_read("00002a6d-0000-1000-8000-00805f9b34fb")
        chrc_uvi = device.char_read("00002a76-0000-1000-8000-00805f9b34fb")

        int_temp = int.from_bytes(chrc_temp, byteorder='little', signed=True)
        int_hum = int.from_bytes(chrc_hum, byteorder='little', signed=True)
        int_press = int.from_bytes(chrc_press, byteorder='little', signed=True)
        int_uvi = int.from_bytes(chrc_uvi, byteorder='little', signed=True)

        float_temp = float(int_temp) / 100;
        float_hum = float(int_hum) / 100;
        float_press = float(int_press) / 1000;

        print("Temperature: {} deg C".format(float_temp))
        print("Humidity: {}%".format(float_hum))
        print("Pressure: {} Pa".format(float_press))
        print("UV Index: {}".format(int_uvi))

        final_url = url + json + str(node1_temp) + nvalue + '0' + svalue + str(float_temp)
        requests.get(final_url)

        final_url = url + json + str(node1_hum) + nvalue + str(float_hum) + svalue + '0'
        requests.get(final_url)

        final_url = url + json + str(node1_press) + nvalue + '0' + svalue + str(float_press) + ';0'
        requests.get(final_url)

        final_url = url + json + str(node1_uv) + nvalue + '0' + svalue + str(int_uvi) + ';0'
        requests.get(final_url)

        time.sleep(10);

finally:
    adapter.stop()
