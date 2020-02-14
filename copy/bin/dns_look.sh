if avahi-browse -at | grep -q 'Snapcast'; then
    echo "SNAPCAST ALREADY LAUNCHED"
else
    echo "SNAPCAST NOT LAUNCHED"
fi
exit 0
