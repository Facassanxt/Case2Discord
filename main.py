import json
import re
import time
import random
import requests
import threading
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from discord_webhook import DiscordEmbed, DiscordWebhook

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

    def on_any_event(self, event):
        if event.src_path[2:] == "text.txt":
            print(event)
            with open("text.txt", encoding = 'utf-8') as f:
                last_line = f.readlines()[-1]
            result = re.findall(r'^L ([0-9\/]*) - ([0-9]{2}:[0-9]{2}:[0-9]{2}).*Игроку (.*)<[0-9]{1,5}><(.*)><.*> выпало \[?([0-9]*)', last_line)[0]
            user_steamid = int(result[3].split(":")[2])*2+int(result[3].split(":")[1])+76561197960265728
            api_user = "https://api.steampowered.com/ISteamUser/GetPlayerSummaries/v2/?key={}&steamids={}".format("",user_steamid)
            try:
                rq = requests.get(api_user).json()
                user_avatar = rq['response']['players'][0]['avatarfull']
            except:
                user_avatar = None

            with open("Case.json", encoding = 'utf-8') as f:
                jcase = json.load(f)

            num = result[4]
            discordwebhook = "https://discord.com/api/webhooks/996905511519780964/JnhHM8OOfaemo4cmoG1QfTTp-hM2lGP8MrpjZlYeHZpkTH_gg96OKOBsLx8TOjv4pQ1f"
            lang = "eng_case_name"
            data_time = result[0] + " " + result[1]
            user_login = result[2]
            user_profile = "https://steamcommunity.com/profiles/" + str(user_steamid)
            try:
                case_name = jcase[num][lang]
                market_case = jcase[num]["eng_case_name"]
                case_url = jcase[num]["image_url"]
                text_price = "Цена: `{}`".format(Price_Cases[num])
                market_url = ("https://steamcommunity.com/market/listings/730/" + market_case).replace(" ","%20")
            except:
                case_name = "Неизвестный кейс"
                market_url = None
                case_url = None
                text_price = None
            with open("Discord.json", encoding = 'utf-8') as f:
                discord = json.load(f)
            for id in discord:
                if id != "_comment":
                    if user_steamid in discord[id]:
                        if text_price != None:
                            text_price += " <@{}>".format(id)
                        else:
                            text_price = "<@{}>".format(id)
            Random_color = ''.join([random.choice('0123456789ABCDEF') for i in range(6)])
            print(case_name,case_url,market_url,text_price)
            data = {
                "username" : "Drops_Cases",
                "embeds": [
                    {
                    "title": case_name,
                    "description": text_price,
                    "url": market_url,
                    "color": int(Random_color,16),
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
            resp = requests.post(discordwebhook, json=data)
            print(resp)

Price_Cases = {}
def Price_parser():
    with open("Case.json", encoding = 'utf-8') as f:
        json_case = json.load(f)
    while True:
        for num in json_case:
            try:
                api_price = "https://steamcommunity.com/market/priceoverview/?currency=5&appid=730&market_hash_name=" + json_case[num]["eng_case_name"].replace("&","%26")
                api_price = requests.get(api_price).json()
                try:
                    price = api_price['lowest_price']
                except:
                    price = api_price['median_price']
                Price_Cases.update({num: price})
                print(num, json_case[num]["ru_case_name"], price)
                time.sleep(6)
            except Exception as e:
                print(e)
                time.sleep(60*60) #1 час
        time.sleep(6*60*60) #12 часов

if __name__=="__main__":
    #threading.Thread(target=Price_parser).start()
    w = Watcher(".", MyHandler())
    w.run()