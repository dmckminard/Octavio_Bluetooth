#!/usr/bin/env python3.5

import subprocess

check = subprocess.check_output(["avahi-browse", "-at"]).strip().decode()
print(check)


if ("Snapcast") in check :
    print('Snapcast already launched')
else :
    print('Snapcast not launched')
