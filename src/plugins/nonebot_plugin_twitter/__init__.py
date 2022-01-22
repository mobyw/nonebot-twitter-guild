from dataclasses import MISSING
from nonebot import on_command
from nonebot import rule
from nonebot import on_request
from nonebot import on_notice
from nonebot.adapters import Bot, Event
from nonebot.adapters.cqhttp.event import MessageEvent, Status
from nonebot.rule import to_me
from nonebot.adapters.cqhttp.permission import GROUP_ADMIN, GROUP_OWNER, PRIVATE_FRIEND
from nonebot.permission import SUPERUSER
from nonebot.typing import T_State
from nonebot.adapters.cqhttp import (
    Bot,
    Message,
    GroupMessageEvent,
    bot,
    FriendRequestEvent,
    GroupRequestEvent,
    GroupDecreaseNoticeEvent,
)
from nonebot.adapters.cqhttp.message import MessageSegment
from nonebot import require
from nonebot.log import logger
from . import data_source
from . import model
from . import config
import asyncio
import nonebot
import httpx

from .nonebot_guild_patch import GuildMessageEvent, ChannelDestoryedNoticeEvent

model.Init()
tweet_index = 0

if config.api_url == "":
    raise Exception("这可能是您第一次运行本插件，请按照文档填写config.json后重新运行！")
try:
    response = httpx.get(url=config.api_url)
    config.token = response.json()["value"]
except:
    raise Exception("token初始化失败，请检查网络设置或API地址是否正确！")


scheduler = require("nonebot_plugin_apscheduler").scheduler


# 定时任务：刷新 Token
@scheduler.scheduled_job("interval", minutes=5, id="flush_token")
async def flush():
    logger.info("开始刷新token")
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(url=config.api_url)
            config.token = response.json()["value"]
            logger.info("token更新成功！")
    except:
        logger.error("token更新失败！")


# 定时任务：推送推文
@scheduler.scheduled_job("interval", seconds=15, id="tweet")
async def tweet():
    if model.Empty():
        return

    (schedBot,) = nonebot.get_bots().values()
    global tweet_index
    users = model.GetUserList()
    tweet_index %= len(users)
    tweet_id, data = await data_source.get_latest_tweet(
        users[tweet_index][2], config.token
    )

    if tweet_id == "" or users[tweet_index][3] == tweet_id:
        tweet_index += 1
        return

    logger.info("检测到 %s 的推特已更新" % (users[tweet_index][1]))
    model.UpdateTweet(users[tweet_index][0], tweet_id)
    text, translate, media_list, url = data_source.get_tweet_details(data)
    translate = await data_source.baidu_translate(
        config.appid, translate, config.baidu_token
    )
    media = ""

    for item in media_list:
        media += MessageSegment.image(item) + "\n"

    cards = model.GetALLCard(users[tweet_index][0])

    for card in cards:

        if card[2] == 1:  # 翻译
            msg = text + translate + media + url
        else:
            msg = text + media + url

        if int(card[1]) > 1:  # 子频道
            await schedBot.call_api(
                "send_guild_channel_msg",
                **{"message": msg, "guild_id": card[0], "channel_id": str(card[1])}
            )
        elif int(card[1]) == 1:  # 群聊
            await schedBot.call_api("send_msg", **{"message": msg, "group_id": card[0]})
        else:  # 私聊
            await schedBot.call_api("send_msg", **{"message": msg, "user_id": card[0]})
    tweet_index += 1


adduser = on_command(
    "推特关注",
    priority=5,
    permission=GROUP_ADMIN | GROUP_OWNER | PRIVATE_FRIEND | SUPERUSER,
)


@adduser.handle()  # 添加用户
async def handle(bot: Bot, event: MessageEvent, state: T_State):
    if isinstance(event, GuildMessageEvent):
        id = event.guild_id
        id2 = event.channel_id
    else:
        id = event.get_session_id()
        if not id.isdigit():
            id = id.split("_")[1]
        if isinstance(event, GroupMessageEvent):
            id2 = 1
        else:
            id2 = 0

    args = str(event.get_message()).strip()
    msg = "指令格式错误！请按照：推特关注 推特ID"

    if args != "":
        user = model.GetUserInfo(args)
        if len(user) != 0:
            status = model.AddCard(args, id, id2)
            if status == 0:
                msg = "{}({})添加成功！".format(user[1], args)  # 待测试
            else:
                msg = "{}({})已存在！".format(user[1], args)  # 待测试
        else:
            user_name, user_id = await data_source.get_user_info(args, config.token)
            if user_id != "":
                model.AddNewUser(args, user_name, user_id)
                model.AddCard(args, id, id2)
                msg = "{}({})添加成功！".format(user_name, args)  # 待测试
            else:
                msg = "{} 推特ID不存在或网络错误！".format(args)
    Msg = Message(msg)
    await bot.send(message=Msg, event=event)


removeuser = on_command(
    "推特取关",
    priority=5,
    permission=GROUP_ADMIN | GROUP_OWNER | PRIVATE_FRIEND | SUPERUSER,
)


@removeuser.handle()  # 取关用户
async def handle(bot: Bot, event: MessageEvent, state: T_State):
    if isinstance(event, GuildMessageEvent):
        id = event.guild_id
        id2 = event.channel_id
    else:
        id = event.get_session_id()
        if not id.isdigit():
            id = id.split("_")[1]
        if isinstance(event, GroupMessageEvent):
            id2 = 1
        else:
            id2 = 0

    args = str(event.get_message()).strip()
    msg = "指令格式错误！请按照：推特取关 UID"

    if args != "":
        user = model.GetUserInfo(args)
        if len(user) == 0:
            msg = "{} 用户不存在！请检查推特ID是否错误".format(args)
        else:
            status = model.DeleteCard(args, id, id2)
            if status != 0:
                msg = "{}({})不在当前子频道关注列表".format(user[1], args)
            else:
                msg = "{}({})删除成功！".format(user[1], args)
    Msg = Message(msg)
    await bot.send(message=Msg, event=event)


alllist = on_command(
    "推特列表",
    priority=5,
    permission=GROUP_ADMIN | GROUP_OWNER | PRIVATE_FRIEND | SUPERUSER,
)


@alllist.handle()  # 显示当前群聊/私聊/子频道中的关注列表
async def handle(bot: Bot, event: MessageEvent, state: T_State):
    if isinstance(event, GuildMessageEvent):
        id = event.guild_id
        id2 = event.channel_id
    else:
        id = event.get_session_id()
        if not id.isdigit():
            id = id.split("_")[1]
        if isinstance(event, GroupMessageEvent):
            id2 = 1
        else:
            id2 = 0

    msg = "用户名(推特ID)\n"
    content = ""

    user = model.GetUserList()
    for index in user:
        card = model.GetCard(index[0], id, id2)
        if len(card) != 0:
            content += "{}({})\n{}\n".format(
                index[1],
                index[0],
                str(card[2]).replace("1", "推文翻译：开").replace("0", "推文翻译：关"),
            )
    if content == "":
        msg = "当前关注列表为空！"
    else:
        msg = msg + content
    Msg = Message(msg)
    await bot.send(message=Msg, event=event)


ontranslate = on_command(
    "开启翻译",
    priority=5,
    permission=GROUP_ADMIN | GROUP_OWNER | PRIVATE_FRIEND | SUPERUSER,
)


@ontranslate.handle()  # 开启推文翻译
async def handle(bot: Bot, event: MessageEvent, state: T_State):
    if isinstance(event, GuildMessageEvent):
        id = event.guild_id
        id2 = event.channel_id
    else:
        id = event.get_session_id()
        if not id.isdigit():
            id = id.split("_")[1]
        if isinstance(event, GroupMessageEvent):
            id2 = 1
        else:
            id2 = 0

    args = str(event.get_message()).strip()
    msg = "指令格式错误！请按照：开启翻译 推特ID"

    if args != "":
        user = model.GetUserInfo(args)
        if len(user) == 0:
            msg = "{} 用户不存在！请检查UID是否错误".format(args)
        else:
            card = model.GetCard(args, id, id2)
            if len(card) == 0:
                msg = "{}({})不在当前子频道关注列表！".format(user[1], args)
            else:
                model.TranslateON(args, id, id2)
                msg = "{}({})开启推文翻译！".format(user[1], args)
    Msg = Message(msg)
    await bot.send(message=Msg, event=event)


offtranslate = on_command(
    "关闭翻译",
    priority=5,
    permission=GROUP_ADMIN | GROUP_OWNER | PRIVATE_FRIEND | SUPERUSER,
)


@offtranslate.handle()  # 关闭推文翻译
async def handle(bot: Bot, event: MessageEvent, state: T_State):
    if isinstance(event, GuildMessageEvent):
        id = event.guild_id
        id2 = event.channel_id
    else:
        id = event.get_session_id()
        if not id.isdigit():
            id = id.split("_")[1]
        if isinstance(event, GroupMessageEvent):
            id2 = 1
        else:
            id2 = 0

    args = str(event.get_message()).strip()
    msg = "指令格式错误！请按照：关闭翻译 推特ID"

    if args != "":
        user = model.GetUserInfo(args)
        if len(user) == 0:
            msg = "{} 用户不存在！请检查UID是否错误".format(args)
        else:
            card = model.GetCard(args, id, id2)
            if len(card) == 0:
                msg = "{}({})不在当前子频道关注列表！".format(user[1], args)
            else:
                model.TranslateOFF(args, id, id2)
                msg = "{}({})关闭推文翻译！".format(user[1], args)
    Msg = Message(msg)
    await bot.send(message=Msg, event=event)


help = on_command(
    "推特帮助",
    priority=5,
    permission=GROUP_ADMIN | GROUP_OWNER | PRIVATE_FRIEND | SUPERUSER,
)


@help.handle()
async def handle(bot: Bot, event: MessageEvent, state: T_State):
    menu = """HanayoriBot目前支持的功能：
    (ID为推特ID\'@\'后面的名称)
    推特关注 ID
    推特取关 ID
    推特列表
    开启翻译 ID
    关闭翻译 ID
    推特帮助
"""

    info = "当前版本：v1.2"

    msg = menu + info
    Msg = Message(msg)
    await bot.send(message=Msg, event=event)


group_decrease = on_notice(priority=5)


@group_decrease.handle()
async def handle(bot: Bot, event: GroupDecreaseNoticeEvent, state: T_State):
    id = event.get_session_id()
    if not id.isdigit():
        id = id.split("_")[1]
    if event.self_id == event.user_id:
        model.DeleteGroupCard(id)


channel_decrease = on_notice(priority=5)


@channel_decrease.handle()
async def handle(bot: Bot, event: ChannelDestoryedNoticeEvent, state: T_State):
    id = event.channel_info.owner_guild_id
    cid = event.channel_info.channel_id
    model.DeleteChannelCard(id, cid)
