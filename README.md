# Strarting of  Background Services
## Gunicorn (For Single GPU)

### 1. First Configure nginx.conf

```sh
sudo nano /etc/nginx/nginx.conf
```

then add the following code just below the include statements in http block:

```sh
upstream backend {
        server <your-server-ipaddress>:8000;
    }

    server {
        listen 80;
        server_name <your-server-ipaddress>;

    location / {
        proxy_pass http://backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        }

    location /ws/ {
        proxy_pass http://<your-server-ipaddress>:5000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "Upgrade";
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
        }
    }
```

and the reload the nginx:

```sh
sudo systemctl nginx reload
```

### 2. Verify the Path to Gunicorn

First, ensure that the path to the gunicorn executable is correct. You can check the path by running:

```sh
which gunicorn
```
If gunicorn is not found, you may need to install it in your virtual environment:

```sh
source /sdb-disk/9D-Muslim-Ai/Production/Production/.venv/bin/activate
pip install gunicorn
pip install uvicorn
```

### 3. Update the gunicorn.service File

Open the gunicorn.service file:

```sh
sudo nano /etc/systemd/system/gunicorn.service
```
Update the ExecStart line to use the correct path to the start_gunicorn.sh executable. Assuming start_gunicorn.sh is in your working directory, the ***ExecStart*** path should be something like this:

```sh
[Unit]
Description=Gunicorn instance to serve myapp
After=network.target

[Service]
ExecStart=/path/to/your/gunicorn app:app -k uvicorn.workers.UvicornWorker -b <your_ip_address>:8000 -w 3
WorkingDirectory=/path/to/your/working_directory
Restart=always
User=administrator
Group=administrator
Environment="PATH=/path/to/.venv/bin"

[Install]
WantedBy=multi-user.target
```

### 4. Reload the Systemd Daemon and Restart the Service

After updating the service file, reload the systemd daemon,enable the service, start the service, and check its status:

```sh
sudo systemctl daemon-reload
sudo systemctl enable gunicorn.service
sudo systemctl start gunicorn.service
sudo systemctl status gunicorn.service
```


## Websocket


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


## Multi-GPU
### 1. First Configure nginx 
For Multi-GPU and Port handling paste the *nginx.conf* file to the below path:

```sh
etc/nginx/nginx.conf
```

And add the below code just below the include statements in http block:


```sh
    upstream backend {
        server <your-server-ipaddress>:8000;
	    server <your-server-ipaddress>:8001;
	    server <your-server-ipaddress>:8002;
    }

    server {
        listen 80;
        server_name <your-server-ipaddress>;

    location / {
        proxy_pass http://backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        }

    location /ws/ {
        proxy_pass <your-server-ipaddress>:5000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "Upgrade";
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
        }
    }
```


and the reload the nginx and daemon and restart the gunicorn service using below commands:

~~~sh
sudo systemctl nginx reload
~~~
and for gunicorn
~~~sh
sudo systemctl daemon-reload

sudo systemctl restart gunicorn.service

#check status
sudo systemctl status gunicorn.service
~~~

### 1. Verify the Path to Gunicorn

First, ensure that the path to the gunicorn executable is correct. You can check the path by running:

```sh
which gunicorn
```
If gunicorn is not found, you may need to install it in your virtual environment:

```sh
source /sdb-disk/9D-Muslim-Ai/Production/Production/.venv/bin/activate
pip install gunicorn
pip install uvicorn
```

### 2. Update the start_gunicorn.sh file

First edit the start_gunicorn.sh file by adding your own ip address and path to gunicorn

```sh
#!/bin/bash

CUDA_VISIBLE_DEVICES=0 path/to/your//gunicorn app:app -k uvicorn.workers.UvicornWorker -b <your_ip_address>:8000 -w 3 &
CUDA_VISIBLE_DEVICES=1 path/to/your//gunicorn app:app -k uvicorn.workers.UvicornWorker -b <your_ip_address>:8001 -w 3 &
CUDA_VISIBLE_DEVICES=2 path/to/your//gunicorn app:app -k uvicorn.workers.UvicornWorker -b <your_ip_address>:8002 -w 3
```

You can update 

### 3. Update the gunicorn.service File

Open the gunicorn.service file:

```sh
sudo nano /etc/systemd/system/gunicorn.service
```
Update the ExecStart line to use the correct path to the start_gunicorn.sh executable. Assuming start_gunicorn.sh is in your working directory, the ***ExecStart*** path should be something like this:

```sh
[Unit]
Description=Gunicorn instance to serve myapp
After=network.target

[Service]
User=administrator
Group=www-data
WorkingDirectory=/path/to/your/working/directory
ExecStart=/path/to/your/start_gunicorn.sh
StandardOutput=append:/path/to/your/gunicorn.log
StandardError=append:/path/to/your/gunicorn_error.log
Restart=always

[Install]
WantedBy=multi-user.target
```

**OR** 

Just rename the gunicorn_new.service file to gunicorn.service and place it to the below path

```sh
/etc/systemd/system/<your-gunicorn.service-file>
```

After updating or placing the service files, reload the systemd daemon,enable the service, start the service, and check its status:

```sh
sudo systemctl daemon-reload
sudo systemctl enable gunicorn.service
sudo systemctl start gunicorn.service
sudo systemctl status gunicorn.service
```

### **Note That For Multi-GPU websocket.service will remain same.**