#!/bin/bash -e

if [ ! -f /usr/local/share/sounds/octavio/connect.ogg ]; then
    curl -so /usr/local/share/sounds/octavio/connect.ogg https://raw.githubusercontent.com/dmckminard/Octavio_Bluetooth/blob/master/connect.ogg
fi

cat <<'EOF' > /etc/systemd/system/startup-sound.service
[Unit]
Description=Startup sound
After=multi-user.target

[Service]
Type=simple
ExecStart=/usr/bin/ogg123 -q /usr/local/share/sounds/octavio/connect.ogg

[Install]
WantedBy=multi-user.target
EOF
systemctl enable startup-sound.service

echo -n "Reboot now ? [y/N] "
read REPLY
if [[ ! "$REPLY" =~ ^(yes|y|Y)$ ]]; then exit 0; fi

sudo reboot
