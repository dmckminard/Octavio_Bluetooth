#!/bin/bash -e

HOSTNAME="Octavio_SetupNeeded"
PRETTY_HOSTNAME="Octavio_SetupNeeded"
sudo raspi-config nonint do_hostname ${HOSTNAME:-$(hostname)}

CURRENT_PRETTY_HOSTNAME=$(hostnamectl status --pretty)
sudo hostnamectl set-hostname --pretty "${PRETTY_HOSTNAME:-${CURRENT_PRETTY_HOSTNAME:-Raspberry Pi}}"

echo "Updating packages"
sudo apt update
sudo apt upgrade -y

echo "Installing components"
sudo ./install-bluetooth.sh
sudo ./install_config_sound.sh
sudo ./install-startup-sound.sh
