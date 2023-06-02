# How to deploy nesquic server with systemd

## Nesquic part

You just have to put a new file `/usr/lib/systemd/system/nesquic.service` with a content like this :

```systemd
[Unit]
Description=Nesquic server
After=multi-user.target

[Service]
Type=simple
Environment="NESQUIC_SERVER_QLOG_DIR=/home/ubuntu/nesquic_tests/server/qlogs"
ExecStart=/home/ubuntu/nesquic/nesquic server -P 4442 -C /home/ubuntu/nesquic/deps/picoquic/certs/cert.pem -K /home/ubuntu/nesquic/deps/picoquic/certs/key.pem
User=ubuntu

[Install]
WantedBy=multi-user.target
```

Then enable the new service

```bash
sudo systemctl enable nesquic.service
```

Then start it

```bash
sudo systemctl start nesquic.service
```

## Python Flask server to get qlogs

Like before a file `/usr/lib/systemd/system/nesquic_flask.service` with content :

```systemctl
[Unit]
Description="flask-nesquic"
After=multi-user.target

[Service]
User=root
WorkingDirectory=/home/ubuntu/nesquic_tests/server
ExecStart=flask run --host=0.0.0.0
Restart=on-failure

[Install]
WantedBy=multi-user.target
```

And do :

```bash
sudo systemctl enable nesquic_flask.service
```

Then start it

```bash
sudo systemctl start nesquic_flask.service
```
