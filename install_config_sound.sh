#!/bin/bash -e
# Installation Snapcast et Snapserver
SNAPCLIENT_VERSION=0.15.0
SNAPSERVER_VERSION=0.15.0

echo -n "Snapcast deja install? (snapclient v${SNAPCLIENT_VERSION}) (snapserver v${SNAPSERVER_VERSION})? [y/N] "
read REPLY
if [[ ! "$REPLY" =~ ^(yes|y|Y)$ ]]; then exit 1; fi


# Config fichiers audio

cat <<'EOF' > /etc/asound.conf
pcm.hifiberry {
    type softvol
    slave.pcm "plughw:0"
    control.name "Master"
    control.card 0
}
pcm.!default {
    type             plug
    slave.pcm       "hifiberry"
}
EOF

sudo mkdir /home/btspeaker

cat <<'EOF' > /home/btspeaker/.asoundrc
pcm.!default {
        type plug
        slave.pcm rate48000Hz
}

pcm.rate48000Hz {
        type rate
        slave {
                pcm writeFile
                format S16_LE
                rate 48000
        }
}

pcm.writeFile {
        type file
        slave.pcm null
        file "/tmp/bluesnapfifo"
        format "raw"
}
EOF
