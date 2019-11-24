# Definition of ble-hub service

## How to enable service

Set Your path to `ble-hub.py` script in `repo-dir/systemd/ble-hub.service`:
```
ExecStart=/usr/bin/python3 path-to-script/ble-hub.py
```

Put `ble-hub.service` in `/etc/systemd/system/`:
```
sudo cp repo-dir/systemd/ble-hub.service /etc/systemd/system
```

Enable auto start of service on boot:
```
sudo systemctl enable ble-hub.service
```

Start service immediately:
```
sudo systemctl start ble-hub.service
```

Check service status:
```
systemctl status ble-hub.service
```

## How to disable service:

Disable auto start of service on boot:
```
sudo systemctl disable ble-hub.service
```

Stop service immediately:
```
sudo systemctl stop ble-hub.service
```

Check service status:
```
systemctl status ble-hub.service
```

## Logging

Logs are created in `repo-dir/logs`
