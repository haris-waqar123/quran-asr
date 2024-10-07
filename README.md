## Strarting of Gunicorn Background Services
### 1. Verify the Path to Gunicorn

*First, ensure that the path to the gunicorn executable is correct. You can check the path by running:*

```sh
which gunicorn
```
If gunicorn is not found, you may need to install it in your virtual environment:

```sh
source /sdb-disk/9D-Muslim-Ai/Production/Production/.venv/bin/activate
pip install gunicorn
```

### 2. Update the gunicorn.service File

Open the gunicorn.service file:

```sh
sudo nano /etc/systemd/system/gunicorn.service
```
Update the ExecStart line to use the correct path to the gunicorn executable. Assuming gunicorn is installed in your virtual environment, the path should be something like this:

```sh
[Unit]
Description=Gunicorn instance to serve myapp
After=network.target

[Service]
ExecStart=/path/to/your/gunicorn -w 4 -b your_ip_address:8000 app:app
WorkingDirectory=/path/to/your/working_directory
Restart=always
User=administrator
Group=administrator
Environment="PATH=/path/to/.venv/bin"

[Install]
WantedBy=multi-user.target
```

### 3. Reload the Systemd Daemon and Restart the Service

After updating the service file, reload the systemd daemon,enable the service, start the service, and check its status:

```sh
sudo systemctl daemon-reload
sudo systemctl enable gunicorn.service
sudo systemctl start gunicorn.service
sudo systemctl status gunicorn.service
```


## Starting of Websocket Background Service
### 1. Update the websocket.service File

Open the websocket.service file:

```sh
sudo nano /etc/systemd/system/websocket.service
```
Update the ExecStart line to use the correct path to the python executable. Assuming python is in your virtual environment, the path should be something like this:

```sh
[Unit]
Description=WebSocket server for myapp
After=network.target

[Service]
ExecStart=/path/to/your/.venv/bin/python /path/to/your/websocket_server.py
WorkingDirectory=/path/to/your/working_directory
Restart=always
User=administrator
Group=administrator
Environment="PATH=/path/to/your/.venv/bin"

[Install]
WantedBy=multi-user.target

```

### 2. Reload the Systemd Daemon and Restart the Service

After updating the service file, reload the systemd daemon, enable the service, start the service, and check its status:

```sh
sudo systemctl daemon-reload
sudo systemctl enable websocket.service
sudo systemctl start websocket.service
sudo systemctl status websocket.service
```
