# Lcd

/etc/systemd/system/lcd.service

```bash
[Unit]
Description=Unit to run python script for lcd display
After=multi-user.target

[Service]
Type=idle
ExecStart=/usr/bin/python3 /home/jd/lcd/display.py
Restart=always

[Install]
WantedBy=multi-user.target
```

**start deamon**
```bash
sudo systemctl daemon-reload
sudo systemctl enable lcd.service
sudo systemctl start lcd.service
```