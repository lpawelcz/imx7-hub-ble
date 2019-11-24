import requests
import time
import pygatt
import os
import sys
import subprocess
from datetime import datetime

adapter = pygatt.backends.GATTToolBackend()

temp_min = -4000
temp_max = 8500
temp_error_val = 0
hum_min = 0
hum_max = 10000
hum_error_val = 0
press_min = 300000
press_max = 1100000
uvi_min = 0
uvi_max = 45

node1_addr = 'A4:CF:12:75:BB:66'
node1_temp = 4
node1_hum = 3
node1_press = 2
node1_uv = 1

url = 'http://192.168.100.101:8080'
json = '/json.htm?type=command&param=udevice&idx='
nvalue = '&nvalue='
svalue = '&svalue='

temp_service = "00002a6e-0000-1000-8000-00805f9b34fb"
hum_service = "00002a6f-0000-1000-8000-00805f9b34fb"
press_service = "00002a6d-0000-1000-8000-00805f9b34fb"
uvi_service = "00002a76-0000-1000-8000-00805f9b34fb"

log_dir = os.path.dirname(os.path.realpath(__file__))
temp_file = log_dir + "/log/temperature.log"
hum_file = log_dir + "/log/humidity.log"
press_file = log_dir + "/log/pressure.log"
uvi_file = log_dir + "/log/uvi.log"
dump_file = log_dir + "/log/stdout.dump"

def read_val(device, service_id, filename, min_val, max_val, prev_val, error_val = -999):
    "read characteristic and perform sanity check, returns values as specified in Bluetooth characteristics specification"
    timeout = 3
    condition = True
    while condition:
        timeout -= 1
        charac = device.char_read(service_id)
        int_val = int.from_bytes(charac, byteorder='little', signed=True)
        condition = (not (int_val >= min_val and int_val <= max_val and int_val != error_val)) and timeout
        if condition:
            f = open(filename, "a")
            date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            f.write("{}	{}\n".format(date, int_val))
            f.close()
    if int_val == error_val:
        f = open(filename, "a")
        date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        f.write("{}	error value {} is real value\n".format(date, int_val))
        f.close()
    elif not timeout:
        f = open(filename, "a")
        date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        f.write("{}	value out of sensor scope {}, previous value {} as result \n".format(date, int_val, prev_val))
        f.close()
        int_val = prev_val

    return int_val


try:
    tee = subprocess.Popen(["tee", dump_file], stdin=subprocess.PIPE)
    os.dup2(tee.stdin.fileno(), sys.stdout.fileno())
    os.dup2(tee.stdin.fileno(), sys.stderr.fileno())

    adapter.start()

    device = adapter.connect(node1_addr)
    date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    print("{}	Connected to {}".format(date, node1_addr))

    temp_prev = 0
    hum_prev = 0
    press_prev = 0
    uvi_prev = 0

    while True:
        int_temp = read_val(device, temp_service, temp_file, temp_min, temp_max, temp_prev, temp_error_val)
        temp_prev = int_temp
        int_hum = read_val(device, hum_service, hum_file, hum_min, hum_max, hum_prev, hum_error_val)
        hum_prev = int_hum
        int_press = read_val(device, press_service, press_file, press_min, press_max, press_prev)
        press_prev = int_press
        int_uvi = read_val(device, uvi_service, uvi_file, uvi_min, uvi_max, uvi_prev)
        uvi_prev = int_uvi

        float_temp = float(int_temp) / 100;
        float_hum = float(int_hum) / 100;
        float_press = float(int_press) / 1000;

        date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        print("{}	Temperature: {} deg C".format(date, float_temp))
        print("{}	Humidity:    {} %".format(date, float_hum))
        print("{}	Pressure:    {} hPa".format(date, float_press))
        print("{}	UV Index:    {}".format(date, int_uvi))

        final_url = url + json + str(node1_temp) + nvalue + '0' + svalue + str(float_temp)
        requests.get(final_url)

        final_url = url + json + str(node1_hum) + nvalue + str(float_hum) + svalue + '0'
        requests.get(final_url)

        final_url = url + json + str(node1_press) + nvalue + '0' + svalue + str(float_press) + ';0'
        requests.get(final_url)

        final_url = url + json + str(node1_uv) + nvalue + '0' + svalue + str(int_uvi) + ';0'
        requests.get(final_url)

        time.sleep(5);

finally:
    device.disconnect()
    adapter.stop()
