#!/usr/bin/env python3

import dbus
try:
  from gi.repository import GObject
except ImportError:
  import gobject as GObject
import sys

from dbus.mainloop.glib import DBusGMainLoop

bus = None
mainloop = None

BLUEZ_SERVICE_NAME = 'org.bluez'
DBUS_OM_IFACE =      'org.freedesktop.DBus.ObjectManager'
DBUS_PROP_IFACE =    'org.freedesktop.DBus.Properties'

GATT_SERVICE_IFACE = 'org.bluez.GattService1'
GATT_CHRC_IFACE =    'org.bluez.GattCharacteristic1'

ENV_SENS_SVC_UUID =	'0000181a-0000-1000-8000-00805f9b34fb'
TEMP_UUID =		'00002a6e-0000-1000-8000-00805f9b34fb'
HUM_UUID =		'00002a6f-0000-1000-8000-00805f9b34fb'
PRESS_UUID =		'00002a6d-0000-1000-8000-00805f9b34fb'
UVI_UUID =		'00002a76-0000-1000-8000-00805f9b34fb'

# The objects that we interact with.
es_service = None
es_temp_chrc = None
es_hum_chrc = None
es_press_chrc = None
es_uvi_chrc = None

def generic_error_cb(error):
    print('D-Bus call failed: ' + str(error))
    mainloop.quit()


def body_sensor_val_to_str(val):
    if val == 0:
        return 'Other'
    if val == 1:
        return 'Chest'
    if val == 2:
        return 'Wrist'
    if val == 3:
        return 'Finger'
    if val == 4:
        return 'Hand'
    if val == 5:
        return 'Ear Lobe'
    if val == 6:
        return 'Foot'

    return 'Reserved value'


def sensor_contact_val_to_str(val):
    if val == 0 or val == 1:
        return 'not supported'
    if val == 2:
        return 'no contact detected'
    if val == 3:
        return 'contact detected'

    return 'invalid value'


def body_sensor_val_cb(value):
    if len(value) != 1:
        print('Invalid body sensor location value: ' + repr(value))
        return

    print('Body sensor location value: ' + body_sensor_val_to_str(value[0]))


def hr_msrmt_start_notify_cb():
    print('HR Measurement notifications enabled')


def hr_msrmt_changed_cb(iface, changed_props, invalidated_props):
    if iface != GATT_CHRC_IFACE:
        return

    if not len(changed_props):
        return

    value = changed_props.get('Value', None)
    if not value:
        return

    print('New HR Measurement')

    flags = value[0]
    value_format = flags & 0x01
    sc_status = (flags >> 1) & 0x03
    ee_status = flags & 0x08

    if value_format == 0x00:
        hr_msrmt = value[1]
        next_ind = 2
    else:
        hr_msrmt = value[1] | (value[2] << 8)
        next_ind = 3

    print('\tHR: ' + str(int(hr_msrmt)))
    print('\tSensor Contact status: ' +
          sensor_contact_val_to_str(sc_status))

    if ee_status:
        print('\tEnergy Expended: ' + str(int(value[next_ind])))


def start_client():
    # Read the Temperature Sensor value and print it asynchronously.
    es_temp_chrc[0].ReadValue({}, reply_handler=temp_val_cb,
                                    error_handler=generic_error_cb,
                                    dbus_interface=GATT_CHRC_IFACE)

    # Read the Humidity Sensor value and print it asynchronously.
    es_hum_chrc[0].ReadValue({}, reply_handler=hum_val_cb,
                                    error_handler=generic_error_cb,
                                    dbus_interface=GATT_CHRC_IFACE)

    # Read the Pressure Sensor value and print it asynchronously.
    es_press_chrc[0].ReadValue({}, reply_handler=press_val_cb,
                                    error_handler=generic_error_cb,
                                    dbus_interface=GATT_CHRC_IFACE)

    # Read the UVI Sensor value and print it asynchronously.
    es_uvi_chrc[0].ReadValue({}, reply_handler=uvi_val_cb,
                                    error_handler=generic_error_cb,
                                    dbus_interface=GATT_CHRC_IFACE)

    # # Listen to PropertiesChanged signals from the Heart Measurement
    # # Characteristic.
    # hr_msrmt_prop_iface = dbus.Interface(hr_msrmt_chrc[0], DBUS_PROP_IFACE)
    # hr_msrmt_prop_iface.connect_to_signal("PropertiesChanged",
                                          # hr_msrmt_changed_cb)

    # # Subscribe to Heart Rate Measurement notifications.
    # hr_msrmt_chrc[0].StartNotify(reply_handler=hr_msrmt_start_notify_cb,
                                 # error_handler=generic_error_cb,
                                 # dbus_interface=GATT_CHRC_IFACE)

def process_chrc(chrc_path):
    chrc = bus.get_object(BLUEZ_SERVICE_NAME, chrc_path)
    chrc_props = chrc.GetAll(GATT_CHRC_IFACE,
                             dbus_interface=DBUS_PROP_IFACE)

    uuid = chrc_props['UUID']

    if uuid == TEMP_UUID:
        global es_temp_chrc
        es_temp_chrc = (chrc, chrc_props)
    elif uuid == HUM_UUID:
        global es_hum_chrc
        es_hum_chrc = (chrc, chrc_props)
    elif uuid == PRESS_UUID:
        global es_press_chrc
        es_press_chrc = (chrc, chrc_props)
    elif uuid == UVI_UUID:
	global es_uvi_chrc
	es_uvi_chrc = (chrc, chrc_props)
    else:
        print('Unrecognized characteristic: ' + uuid)

    return True


def process_es_service(service_path, chrc_paths):
    service = bus.get_object(BLUEZ_SERVICE_NAME, service_path)
    service_props = service.GetAll(GATT_SERVICE_IFACE,
                                   dbus_interface=DBUS_PROP_IFACE)

    uuid = service_props['UUID']

    if uuid != ENV_SENS_SVC_UUID:
        return False

    print('Environment Sensing Service found: ' + service_path)

    # Process the characteristics.
    for chrc_path in chrc_paths:
        process_chrc(chrc_path)

    global es_service
    es_service = (service, service_props, service_path)

    return True


def interfaces_removed_cb(object_path, interfaces):
    if not es_service:
        return

    if object_path == es_service[2]:
        print('Service was removed')
        mainloop.quit()


def main():
    # Set up the main loop.
    DBusGMainLoop(set_as_default=True)
    global bus
    bus = dbus.SystemBus()
    global mainloop
    mainloop = GObject.MainLoop()

    om = dbus.Interface(bus.get_object(BLUEZ_SERVICE_NAME, '/'), DBUS_OM_IFACE)
    om.connect_to_signal('InterfacesRemoved', interfaces_removed_cb)

    print('Getting objects...')
    objects = om.GetManagedObjects()
    chrcs = []

    # List characteristics found
    for path, interfaces in objects.items():
        if GATT_CHRC_IFACE not in interfaces.keys():
            continue
        chrcs.append(path)

    # List sevices found
    for path, interfaces in objects.items():
        if GATT_SERVICE_IFACE not in interfaces.keys():
            continue

        chrc_paths = [d for d in chrcs if d.startswith(path + "/")]

        if process_es_service(path, chrc_paths):
            break

    if not es_service:
        print('No Environment Sensing Service found')
        sys.exit(1)

    start_client()

    mainloop.run()


if __name__ == '__main__':
    main()
