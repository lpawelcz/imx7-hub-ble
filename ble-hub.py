import requests
import time
import pygatt
import os
import sys
import subprocess
from datetime import datetime

adapter = pygatt.backends.GATTToolBackend()

cycle_time = 5

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
node1_uv = 5
node1_temp = 6
node1_hum = 7
node1_press = 8

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

def read_val(device, characteristic_uuid, filename, min_val, max_val, prev_val, error_val = -999):
    "read characteristic and perform sanity check, returns values as specified in Bluetooth characteristics specification"
    timeout = 3
    condition = True
    # Do while result is not in range of sensor or has value that can be an error or 3 attempts pass
    while condition:
        timeout -= 1
        # Read characteristic
        try:
            charac = device.char_read(characteristic_uuid)
        except:
            date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            condition = timeout
            print("{}	Failed to read characteristic {}".format(date, characteristic_uuid))
            if not condition:
                return -1
            else:
                continue

        int_val = int.from_bytes(charac, byteorder='little', signed=True)
        # Check if there is need for second characteristic readout
        condition = (not (int_val >= min_val and int_val <= max_val and int_val != error_val)) and timeout
        if condition:
            f = open(filename, "a")
            date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            f.write("{}	{}\n".format(date, int_val))
            f.close()
    # Value is still possible error after 3 characteristic readouts - consider as correct measurement
    if int_val == error_val:
        f = open(filename, "a")
        date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        f.write("{}	error value {} is real value\n".format(date, int_val))
        f.close()
    # Several readouts in wrong range - take previous correct measurement
    elif not timeout:
        f = open(filename, "a")
        date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        f.write("{}	value out of sensor scope {}, previous value {} as result \n".format(date, int_val, prev_val))
        f.close()
        int_val = prev_val

    return int_val

def main():
    try:
        # write stdout also to log
        tee = subprocess.Popen(["tee", dump_file], stdin=subprocess.PIPE)
        os.dup2(tee.stdin.fileno(), sys.stdout.fileno())
        os.dup2(tee.stdin.fileno(), sys.stderr.fileno())

        adapter.start()

        while True:
            try:
                date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                device = adapter.connect(node1_addr)
                print("{}	Connected to {}".format(date, node1_addr))
            except:
                print("{}	Timeout when connecting to {}".format(date, node1_addr))
                continue

            temp_prev = 0
            hum_prev = 0
            press_prev = 0
            uvi_prev = 0

            # Read measurements from node
            int_temp = read_val(device, temp_service, temp_file, temp_min, temp_max, temp_prev, temp_error_val)
            if int_temp == -1:
                # return -1
                continue
            temp_prev = int_temp
            int_hum = read_val(device, hum_service, hum_file, hum_min, hum_max, hum_prev, hum_error_val)
            if int_hum == -1:
                # return -1
                continue
            hum_prev = int_hum
            int_press = read_val(device, press_service, press_file, press_min, press_max, press_prev)
            if int_press == -1:
                # return -1
                continue
            press_prev = int_press
            int_uvi = read_val(device, uvi_service, uvi_file, uvi_min, uvi_max, uvi_prev)
            if int_uvi == -1:
                # return -1
                continue
            uvi_prev = int_uvi

            date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            try:
                device.disconnect()
                print("{}	Disconnected from {}".format(date, node1_addr))
            except:
                print("{}	Already disconnected from {}".format(date, node1_addr))

            # Convert measurements to correct format according to BT spec - characteristics
            float_temp = float(int_temp) / 100;
            float_hum = float(int_hum) / 100;
            float_press = float(int_press) / 1000;

            date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            print("{}	Temperature: {} deg C".format(date, float_temp))
            print("{}	Humidity:    {} %".format(date, float_hum))
            print("{}	Pressure:    {} hPa".format(date, float_press))
            print("{}	UV Index:    {}".format(date, int_uvi))

            # Prepare and send data to Domoticz
            final_url = url + json + str(node1_temp) + nvalue + '0' + svalue + str(float_temp)
            requests.get(final_url)
            final_url = url + json + str(node1_hum) + nvalue + str(float_hum) + svalue + '0'
            requests.get(final_url)
            final_url = url + json + str(node1_press) + nvalue + '0' + svalue + str(float_press) + ';0'
            requests.get(final_url)
            final_url = url + json + str(node1_uv) + nvalue + '0' + svalue + str(int_uvi) + ';0'
            requests.get(final_url)


            time.sleep(cycle_time);

    finally:
        try:
            device.disconnect()
            print("{}	Disconnected from {}".format(date, node1_addr))
        except:
            print("{}	Already disconnected from {}".format(date, node1_addr))
        adapter.stop()

main()
