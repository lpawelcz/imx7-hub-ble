import pygatt

# adapter = pygatt.GATTToolBackend()
# adapter = pygatt.BGAPIBackend()
adapter = pygatt.backends.GATTToolBackend()

try:
    adapter.start()
    device = adapter.connect('A4:CF:12:75:BB:66')
    print("connected")
    value = device.char_read("00002a6e-0000-1000-8000-00805f9b34fb")
    print("value: {}".format(value))
finally:
    adapter.stop()
