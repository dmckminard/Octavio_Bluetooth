if avahi-browse -atl | grep -q '_octavio._tcp'; then
    echo "OCTAVIO DEVICE FOUND, LETS CHECK IP"
    python3 /home/config/bin/scan_octavio.py
    exit 0
else
    echo "NO OCTAVIO DEVICE FOUND"
    python3 /home/config/bin/server.py
    exit 0
fi
exit 0
