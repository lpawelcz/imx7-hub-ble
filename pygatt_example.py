import time
import pygatt

adapter = pygatt.backends.GATTToolBackend()

try:
    adapter.start()
    device = adapter.connect('A4:CF:12:75:BB:66')
    print("connected")

    while True:
        chrc_temp = device.char_read("00002a6e-0000-1000-8000-00805f9b34fb")
        int_temp = int.from_bytes(chrc_temp, byteorder='little', signed=True)
        float_temp = float(int_temp) / 100;
        print("chrc_temp: {} deg C".format(float_temp))
        time.sleep(10);
finally:
    adapter.stop()
