from astrbot.api.event import filter, AstrMessageEvent
from astrbot.api.star import Context, Star, register
from astrbot.api import logger
import requests
import re
from datetime import datetime
from bs4 import BeautifulSoup

def get_url_info():
    url = "https://indienova.com/gamedb/list/121/p/1"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.72 Safari/537.36 Edg/90.0.818.41",
    }
    try:
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        data = response.text
    except Exception as e:
        return None    
    return data

def parse_game_data(data):
    dict_info = {}
    game = BeautifulSoup(data, "html.parser")
    game_all_info = game.find(name='h4')
    game_name_zh = game_all_info.find_all(name='a')
    game_name_en = game_all_info.find_all(name='small')
    game_name_zh = re.findall(r'>(.+?)<', str(game_name_zh))
    game_name_en = re.findall(r'>(.+?)<', str(game_name_en))
    game_start_end = game.find(name='p', attrs={"class": "intro"})
    game_start_end_new = game_start_end.find_all(name='span')
    game_edit_time = game.find(name='p', attrs={"class": "text-date"})
    game_edit_time_new = game_edit_time.find_all(name='small')
    game_edit_time_new = str(game_edit_time_new).replace(" ", "").replace("\n", " ")
    game_start_end_new = re.findall(r'>(.+?)<', str(game_start_end_new))
    game_edit_time_new = re.findall(r'>(.+?)<', str(game_edit_time_new))
    dict_info["game_zh"] = game_name_zh
    dict_info["game_en"] = game_name_en
    dict_info["game_start"] = game_start_end_new
    dict_info["game_time"] = game_edit_time_new
    return dict_info

def parse_web_data(data):
    soup = BeautifulSoup(data, "html.parser")
    data.encode("UTF-8").decode("UTF-8")
    div_class = soup.find(name="div", attrs={"id": "portfolioList"})
    game_name = div_class.find_all(name="div", attrs={"class": "col-xs-12 col-sm-6 col-md-4 user-game-list-item"})
    list_game = str(game_name).split('<div class="col-xs-12 col-sm-6 col-md-4 user-game-list-item">')
    game_info_list = []
    for i in list_game[1:]:
        game_info_list.append(parse_game_data(i))
    return game_info_list

def filter_game_data(data_list):
    list_content = []
    for i in data_list:
        game_time = i["game_start"][0]
        time = str.split(game_time, "-")
        try:
            canGet = False
            nowTime = datetime.now()
            timeLength = len(time)
            if timeLength == 1:
                start_time = str.strip(time[0])
                start_time = datetime.strptime(start_time, "%Y/%m/%d")
                canGet = start_time.date() == nowTime.date()
            elif timeLength > 1:
                start_time = str.strip(time[0])
                start_time = datetime.strptime(start_time, "%Y/%m/%d")
                end_time = str.strip(time[1])
                end_time = datetime.strptime(end_time, "%Y/%m/%d")
                canGet = start_time <= nowTime and end_time >= nowTime
            if canGet:                
                list_content.append(i)            
        except ValueError:
            continue
    return list_content

@register("Epic喜加一", "EndlessAttackUnderMoon", "获取本周Epic的周免游戏。", "1.1")
class PluginFreeEpicGame(Star):
    def __init__(self, context: Context):
        super().__init__(context)

    async def initialize(self):
        """可选择实现异步的插件初始化方法，当实例化该插件类之后会自动调用该方法。"""
    
    async def terminate(self):
        """可选择实现异步的插件销毁方法，当插件被卸载/停用时会调用。"""

    @filter.command("Epic喜加一")
    async def get_free_epic_games(self, event: AstrMessageEvent):
        """这是一个AstrBot的 Epic喜加一 指令，可获取本周Epic的周免游戏。""" # handler描述
        message_chain = event.get_messages() # 用户所发的消息的消息链 # from astrbot.api.message_components import *
        logger.info(message_chain)

        text = ""
        try:
            resp_data = get_url_info()
            if resp_data == None:
                text = "请求失败呀，等会儿再试试吧!"
            else:
                game_data_list = parse_web_data(resp_data)
                free_game_list = filter_game_data(game_data_list)
                if bool(free_game_list) == False:        
                    text = "没有免费游戏可以领取哦，明天再来看看吧!"
                else:
                    text = "查到周免信息了哦\n"
                    length = len(free_game_list)
                    for i in range(length):
                        game_data = free_game_list[i]
                        text = text + str(i + 1) + ": 《" + game_data["game_zh"][0] + "》\n领取时间: " + game_data["game_start"][0]
                        if i < length - 1:
                            text = text + "\n\n"
        except Exception as e:
            logger.error(f"请求失败: {str(e)}")
            text = "请求失败!"

        yield event.plain_result(text) # 发送一条纯文本消息
