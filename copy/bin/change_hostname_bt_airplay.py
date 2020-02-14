import subprocess

name = subprocess.check_output(["cat", "/etc/machine-info"])
name = name.decode().strip()

serial_last_four = subprocess.check_output(['cat', '/proc/cpuinfo'])[-42:-38].decode('utf-8')
hostname = "PRETTY_HOSTNAME=Octavio_" + serial_last_four
name_bluetooth = "Octavio_" + serial_last_four
name_airplay = "\"" +  'Octavio_' + serial_last_four + "\""
airplay = "general = {name = "+ name_airplay +" };"

if name == 'PRETTY_HOSTNAME=Octavio':
    #HOSTNAME
    fichier = open("/etc/machine-info", "w")
    fichier.write(hostname)
    fichier.close()

    #BLUETOOTH
    subprocess.call(["sudo", "hciconfig", "hci0", "name", name_bluetooth])
    subprocess.call(["sudo", "hciconfig", "hci0", "down"])
    subprocess.call(["sudo", "hciconfig", "hci0", "up"])

    fichier = open("/usr/local/etc/shairport-sync.conf", "a")
    fichier.write(airplay)
    fichier.close()
    subprocess.call(["sudo", "service", "shairport-sync", "restart"])
    print('HOSTNAME CHANGED')
else :
    print('HOSTNAME ALREADY CHANGED')
