from calendar import prcal
import json
from msilib.schema import File
import os
import re
import time
import random
import requests
import threading
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

class Watcher:
    def __init__(self, directory=".", handler=FileSystemEventHandler()):
        self.observer = Observer()
        self.handler = handler
        self.directory = directory

    def run(self):
        self.observer.schedule(self.handler, self.directory, recursive=True)
        self.observer.start()
        print("\nWatcher Running in {}/\n".format(self.directory))
        try:
            while True:
                time.sleep(1)
        except:
            self.observer.stop()
        self.observer.join()
        print("\nWatcher Terminated\n")

class MyHandler(FileSystemEventHandler):
    def __init__(self,directory,file,discordwebhook,steam_api_dev_key):
        self.directory = directory
        self.file = file
        self.discordwebhook = discordwebhook
        self.steam_api_dev_key = steam_api_dev_key
        self.drop_path = os.path.join(self.directory,self.file)

    def _read_file(self,file_name=None,jfile=False):
        if not jfile:
            with open(self.drop_path, encoding = 'utf-8') as f:
                rfile = f.read()
        else:
            with open(file_name, encoding = 'utf-8') as f:
                rfile = json.load(f)
        return rfile

    def _check_case_availability(self,case_index,jcase):
        if case_index in jcase:
            case_name = jcase[case_index]["eng_case_name"]
            case_url = jcase[case_index]["image_url"]
            if case_index in Price_Cases:
                text_price = "Цена: `{}`".format(Price_Cases[case_index])
            else:
                text_price = "Цена: `Неизвестна`"
            market_url = ("https://steamcommunity.com/market/listings/730/" + case_name).replace(" ","%20")
        else:
            case_name = "Неизвестный кейс"
            case_url = None
            text_price = "Цена: `Неизвестна`"
            market_url = None
        return case_name,case_url,market_url,text_price

    def _parser_logs(self,line):
        os.remove(self.drop_path)
        with open(self.drop_path, mode='a'): pass
        result = re.findall(r'^L ([0-9\/]*) - ([0-9]{2}:[0-9]{2}:[0-9]{2}).*Игроку (.*)<[0-9]{1,5}><(.*)><.*> выпало \[?([0-9]*)', line)[0]
        data_time = result[0] + " " + result[1]
        user_login = result[2]
        user_steamid = int(result[3].split(":")[2])*2+int(result[3].split(":")[1])+76561197960265728
        case_index = result[4]
        user_avatar = self._get_api_user(user_steamid)
        user_profile = "https://steamcommunity.com/profiles/" + str(user_steamid)
        return data_time,user_login,user_avatar,user_steamid,case_index,user_profile

    def _discord_id_alert(self,jdiscord,user_steamid,text_price):
        for id in jdiscord:
            if id != "_comment":
                if user_steamid in jdiscord[id]:
                    if text_price != None:
                        text_price += " <@{}>".format(id)
                    else:
                        text_price = "<@{}>".format(id)
        return text_price

    def _get_api_user(self,user_steamid):
        api_user = "https://api.steampowered.com/ISteamUser/GetPlayerSummaries/v2/?key={}&steamids={}".format(self.steam_api_dev_key,user_steamid)
        try:
            user_avatar = requests.get(api_user).json()['response']['players'][0]['avatarfull']
        except:
            user_avatar = None
        return user_avatar

    def _request_post_generation(self,case_name,text_price,market_url,user_profile,data_time,user_login,user_avatar,case_url):
        data = {
            "username" : "Drops_Cases",
            "embeds": [
                {
                "title": case_name,
                "description": text_price,
                "url": market_url,
                "color": random.randint(0, 0xffffff),
                "fields": [
                    {
                    "name": "ᅠ ᅠ",
                    "value": "[`Профиль`]({}) [`Инвентарь`]({}) [`Маркет`]({})".format(user_profile,user_profile+"/inventory/#730",market_url) \
                    +"\n\n :hourglass_flowing_sand:" + data_time + ":hourglass:",
                    }
                ],
                "author": {
                    "name": user_login,
                    "url": user_profile,
                    "icon_url": user_avatar
                },
                "thumbnail": {
                    "url": case_url
                }
                }
            ],
            "attachments": []
            }
        resp = requests.post(self.discordwebhook, json=data)
        if resp.status_code == 204:
            print("\nSuccessfully sent to Discord\n")
        else:
            print("\nError sending to Discord\n")
        return resp

    def on_modified(self, event):
        if event.src_path == self.drop_path:
            queue = self._read_file()
            for line in queue.splitlines():
                data_time,user_login,user_avatar,user_steamid,case_index,user_profile = self._parser_logs(line)
                jcase = self._read_file("Case.json",True)
                case_name,case_url,market_url,text_price = self._check_case_availability(case_index,jcase)
                jdiscord = self._read_file("Discord.json",True)
                text_price = self._discord_id_alert(jdiscord,user_steamid,text_price)
                self._request_post_generation(case_name,text_price,market_url,user_profile,data_time,user_login,user_avatar,case_url)

    def Price_parser(self):
        jcase = self._read_file("Case.json",True)
        while True:
            for num in jcase:
                try:
                    api_price = "https://steamcommunity.com/market/priceoverview/?currency=5&appid=730&market_hash_name=" + jcase[num]["eng_case_name"].replace("&","%26")
                    api_price = requests.get(api_price).json()
                    try:
                        price = api_price['lowest_price']
                    except:
                        price = api_price['median_price']
                    Price_Cases.update({num: price})
                    print(num, jcase[num]["ru_case_name"], price)
                    time.sleep(6)
                except Exception as e:
                    print(e)
                    time.sleep(60*60) #1 час
            time.sleep(6*60*60) #12 часов

def main():
    directory = r"C:\SteamCMD\steamapps\common\Counter-Strike Global Offensive Beta - Dedicated Server\csgo\addons\sourcemod\logs"
    file = r"DropsSummoner.log"
    discordwebhook = ""
    steam_api_dev_key = ""
    My = MyHandler(directory,file,discordwebhook,steam_api_dev_key)
    threading.Thread(target=My.Price_parser).start()
    w = Watcher(directory, My)
    w.run()

if __name__=="__main__":
    Price_Cases = {}
    main()