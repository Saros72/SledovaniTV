#-*-coding:utf8;-*-
#v0.2.0


#účet
username = ""
password = ""
pin = ""


# Nastavení EPG
# Počet dní (0-15)
days = 3
# Počet dní zpětně (0-7)
days_back = 1


# Seznam vlastních kanálů
# Seznam id kanálů oddělené čárkou (např.: "ct1,ct2")
# Pro všechny kanály ponechte prázdné ("")
ids =""


import requests
import json
import uuid
import os
import sys
import xmltv
from urllib.parse import urlencode, quote, urlparse, parse_qsl
import colors
from datetime import datetime, timedelta, date


product_list = ["Xiaomi Redmi Note 7", "iPhone Plus", "Samsung TV", "LG TV"]
dev_list = ["androidportable", "ios", "samsungtv", "lgtv"]
headers = {"User-Agent": "okhttp/3.12.12"}


#select device
if not os.path.exists("data.json"):
    try:
        os.system('cls||clear')
        i = 1
        for x in product_list:
            print('{:30s} {:1s} '.format(x, str(i)))
            i+=1
        l = int(input("\nVyberte zařízení: "))
        product = product_list[l - 1]
        dev = dev_list[l - 1]
    except:
        input("\nPro ukončení stiskněte libovolnou klávesu")
        sys.exit(0)


#pairing
    os.system('cls||clear')
    print("Login: ", end="", flush=True)
    mac_num = hex(uuid.getnode()).replace('0x', '').upper()
    mac = ':'.join(mac_num[i : i + 2] for i in range(0, 11, 2))
    data = requests.get("https://sledovanitv.cz/api/create-pairing?username=" + quote(username) + "&password=" + quote(password) + "&type=" + quote(dev) + "&product=" + quote(product) + "&serial=" + mac, headers = headers).json()
    if data["status"] == 1:
        deviceId = data["deviceId"]
        passwordId = data["password"]
        json_object = json.dumps(data, indent=4)
        with open("data.json", "w") as outfile:
            outfile.write(json_object)
        print(colors.green("OK"))
    else:
        print(colors.red(data["error"]))
        input("\nPro ukončení stiskněte libovolnou klávesu")
        sys.exit(0)
else:
    with open('data.json', 'r') as openfile:
        data = json.load(openfile)
    deviceId = data["deviceId"]
    passwordId = data["password"]


#phpsessid
data = requests.get("https://sledovanitv.cz/api/device-login?deviceId=" + str(deviceId) + "&password=" + str(passwordId) + "&version=2.44.16&lang=cs&unit=default&capabilities=clientvast%2Cvast%2Cadaptive2%2Cwebvtt", headers = headers).json()
if data["status"] == 1:
    phpsessid = data["PHPSESSID"]
    print("PHPSessid: " + colors.green("OK"), end="", flush=True)
    pin = requests.get("http://sledovanitv.cz/api/pin-unlock?pin=" + pin + "&PHPSESSID=" + phpsessid, headers = headers).json()
    print("\nPin: ", end="", flush=True)
    if pin["status"] == 1:
        print(colors.green("OK"))
    else:
        print(colors.red(pin["error"]))
else:
    print("PHPSessid: ", end="", flush=True)
    print(colors.red(data["error"]))
    input("\nPro ukončení stiskněte libovolnou klávesu")
    sys.exit(0)


#quality
try:
    with open('data.json', 'r') as openfile:
        data = json.load(openfile)
    if "quality" in data:
        quality = data["quality"]
    else:
        print("\n")
        req = requests.get("https://sledovanitv.cz/api/get-stream-qualities?PHPSESSID=" + phpsessid, headers = headers).json()
        if req["status"] == 1:
            i = 1
            for x in req["qualities"]:
                if x["allowed"] == 1:
                    print('{:30s} {:1s} '.format(x["name"], str(i)))
                    i+=1
            l = int(input("\nKvalita videa: "))
            quality = req["qualities"][l - 1]["id"]
            data["quality"]  = quality
            json_object = json.dumps(data, indent=4)
            with open("data.json", "w") as outfile:
                outfile.write(json_object)
        else:
            quality = 20
except:
    input("\nPro ukončení stiskněte libovolnou klávesu")
    sys.exit(0)


#playlist
print("\n\nPlaylist: ", end="", flush=True)
req = requests.get("https://sledovanitv.cz/api/playlist?quality=" + str(quality) + "&capabilities=h265%2Cvast%2Cclientvast%2Cadaptive2%2Cwebvtt&force=true&format=m3u8&logosize=96&whitelogo=true&drm=&subtitles=1&PHPSESSID=" + phpsessid, headers = headers).json()
ch = []
channels = []
if req["status"] == 1:
    f = open("playlist.m3u", "w", encoding="utf-8")
    f.write("#EXTM3U\n")
    groups = req["groups"]
    data = req["channels"]
    if ids == "":
        for i in data:
            ch.append(i["id"])
    else:
        ch = ids.split(",")
    for d in data:
        if d["locked"] == "none":
            if d["type"] == "radio":
                radio = ' radio="true" '
            else:
                radio = ' '
            group = 'group-title="' + groups[d["group"]] + '"'
            if d["id"] in ch:
                f.write('#EXTINF:-1 ' + group + radio 
 + 'tvg-logo="' + d["logoUrl"] + '" tvg-id="stv-' + d["id"] + '",'+ d["name"] +'\n' + d["url"] + '\n')
                channels.append({'display-name': [(d["name"], u'cs')], 'id': 'stv-' + d["id"],'icon': [{'src': 'https://sledovanitv.cz/cache/biglogos/' + d["id"] + '.png'}]})
    f.close()
    print(colors.green("OK"))
else:
    print(colors.red(data["error"]))
    input("\nPro ukončení stiskněte libovolnou klávesu")
    sys.exit(0)


#EPG
if days > 0:
    programmes = []
    print("\n\nGeneruji EPG...\n", end="", flush=True)
    now = datetime.now()
    local_now = now.astimezone()
    TS = " " + str(local_now)[-6:].replace(":", "")
    for i in range(days_back*-1, days):
        next_day = now + timedelta(days = i)
        date_from = next_day.strftime("%Y-%m-%d")
        date_ = next_day.strftime("%d.%m.%Y")
        print(date_ + "  ", end="", flush=True)
        req = requests.get("https://sledovanitv.cz/api/epg?time=" + date_from + "+00%3A44&duration=1439&detail=description,poster&posterSize=234&channels=" + ",".join(ch) + "&PHPSESSID=" + phpsessid, headers = headers).json()["channels"]
        for k in req.keys():
            for x in req[k]:
                programm = {'channel': "stv-" + k, 'start': x["startTime"].replace("-", "").replace(" ", "").replace(":", "") + "00" + TS, 'stop': x["endTime"].replace("-", "").replace(" ", "").replace(":", "") + "00" + TS, 'title': [(x["title"], u'')], 'desc': [(x["description"], u'')]}
                try:
                    icon = x["poster"]
                except:
                    icon = None
                if icon != None:
                    programm['icon'] = [{"src": icon}]
                if programm not in programmes:
                    programmes.append(programm)
        print(colors.green("OK"))
    print("\nEPG: ", end="", flush=True)
    w = xmltv.Writer(encoding="utf-8", source_info_url="http://www.funktronics.ca/python-xmltv", source_info_name="Funktronics", generator_info_name="python-xmltv", generator_info_url="http://www.funktronics.ca/python-xmltv")
    for c in channels:
        w.addChannel(c)
    for p in programmes:
        w.addProgramme(p)
    w.write("epg.xml", pretty_print=True)
    print(colors.green("OK"))
    input("\nPro ukončení stiskněte libovolnou klávesu")
    sys.exit(0)
else:
    input("\nPro ukončení stiskněte libovolnou klávesu")
    sys.exit(0)
