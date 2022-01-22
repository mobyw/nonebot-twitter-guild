import nonebot
import httpx

from nonebot.adapters.onebot.v11 import (
    Bot,
    Message,
    GroupMessageEvent,
    GroupDecreaseNoticeEvent,
)
from nonebot.adapters.onebot.v11.event import MessageEvent
from nonebot.adapters.onebot.v11.message import MessageSegment
from nonebot.adapters.onebot.v11.permission import (
    GROUP_ADMIN,
    GROUP_OWNER,
    PRIVATE_FRIEND,
)

from nonebot.log import logger
from nonebot.params import CommandArg
from nonebot.plugin import require, on_notice, on_command
from nonebot.permission import SUPERUSER

from . import data_source
from . import model
from . import config

from .nonebot_guild_patch import GuildMessageEvent, ChannelDestoryedNoticeEvent

model.Init()
tweet_index = 0

if config.api_url == "":
    raise Exception("这可能是您第一次运行本插件，请按照文档填写 config.json 后重新运行！")
try:
    response = httpx.get(url=config.api_url)
    config.token = response.json()["value"]
except:
    raise Exception("token初始化失败，请检查网络设置或API地址是否正确！")


scheduler = require("nonebot_plugin_apscheduler").scheduler


# 定时任务：刷新 Token
@scheduler.scheduled_job("interval", minutes=5, id="twitter_flush_token")
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
@scheduler.scheduled_job("interval", minutes=1, id="twitter_tweet")
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

    logger.info(f"检测到 {users[tweet_index][1]} 的推特已更新")
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
                **{"message": msg, "guild_id": card[0], "channel_id": str(card[1])},
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
async def handle(bot: Bot, event: MessageEvent, message: Message = CommandArg()):
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

    args = str(message)
    msg = "指令格式错误！请按照：推特关注 推特ID"

    if args != "":
        user = model.GetUserInfo(args)
        if len(user) != 0:
            status = model.AddCard(args, id, id2)
            if status == 0:
                msg = f"{user[1]}({args})添加成功！"
            else:
                msg = f"{user[1]}({args})已存在！"
        else:
            user_name, user_id = await data_source.get_user_info(args, config.token)
            if user_id != "":
                model.AddNewUser(args, user_name, user_id)
                model.AddCard(args, id, id2)
                msg = f"{user_name}({args})添加成功！"
            else:
                msg = f"{args} 推特ID不存在或网络错误！"

    await adduser.finish(msg)


removeuser = on_command(
    "推特取关",
    priority=5,
    permission=GROUP_ADMIN | GROUP_OWNER | PRIVATE_FRIEND | SUPERUSER,
)


@removeuser.handle()  # 取关用户
async def handle(bot: Bot, event: MessageEvent, message: Message = CommandArg()):
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

    args = str(message)
    msg = "指令格式错误！请按照：推特取关 UID"

    if args != "":
        user = model.GetUserInfo(args)
        if len(user) == 0:
            msg = f"{args} 用户不存在！请检查推特ID是否错误"
        else:
            status = model.DeleteCard(args, id, id2)
            if status != 0:
                msg = f"{user[1]}({args})不在当前关注列表"
            else:
                msg = f"{user[1]}({args})删除成功！"

    await removeuser.finish(msg)


alllist = on_command(
    "推特列表",
    priority=5,
    permission=GROUP_ADMIN | GROUP_OWNER | PRIVATE_FRIEND | SUPERUSER,
)


@alllist.handle()  # 显示当前群聊/私聊/子频道中的关注列表
async def handle(bot: Bot, event: MessageEvent):
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
            trans = str(card[2]).replace("1", "推文翻译：开").replace("0", "推文翻译：关")
            content += f"{index[1]}({index[0]})\n{trans}"

    if content == "":
        msg = "当前关注列表为空！"
    else:
        msg = msg + content

    await alllist.finish(msg)


ontranslate = on_command(
    "开启翻译",
    priority=5,
    permission=GROUP_ADMIN | GROUP_OWNER | PRIVATE_FRIEND | SUPERUSER,
)


@ontranslate.handle()  # 开启推文翻译
async def handle(bot: Bot, event: MessageEvent, message: Message = CommandArg()):
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

    args = str(message)
    msg = "指令格式错误！请按照：开启翻译 推特ID"

    if args != "":
        user = model.GetUserInfo(args)
        if len(user) == 0:
            msg = f"{args} 用户不存在！请检查UID是否错误"
        else:
            card = model.GetCard(args, id, id2)
            if len(card) == 0:
                msg = f"{user[1]}({args})不在当前子频道关注列表！"
            else:
                model.TranslateON(args, id, id2)
                msg = f"{user[1]}({args})开启推文翻译！"

    await ontranslate.finish(msg)


offtranslate = on_command(
    "关闭翻译",
    priority=5,
    permission=GROUP_ADMIN | GROUP_OWNER | PRIVATE_FRIEND | SUPERUSER,
)


@offtranslate.handle()  # 关闭推文翻译
async def handle(bot: Bot, event: MessageEvent, message: Message = CommandArg()):
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

    args = str(message)
    msg = "指令格式错误！请按照：关闭翻译 推特ID"

    if args != "":
        user = model.GetUserInfo(args)
        if len(user) == 0:
            msg = f"{args} 用户不存在！请检查UID是否错误"
        else:
            card = model.GetCard(args, id, id2)
            if len(card) == 0:
                msg = f"{user[1]}({args})不在当前子频道关注列表！"
            else:
                model.TranslateOFF(args, id, id2)
                msg = f"{user[1]}({args})关闭推文翻译！"

    await offtranslate.finish(msg)


help = on_command(
    "推特帮助",
    priority=5,
    permission=GROUP_ADMIN | GROUP_OWNER | PRIVATE_FRIEND | SUPERUSER,
)


@help.handle()
async def handle():
    menu = """\
HanayoriBot目前支持的功能：
(ID为推特ID\'@\'后面的名称)
    推特关注 ID
    推特取关 ID
    推特列表
    开启翻译 ID
    关闭翻译 ID
    推特帮助
"""

    info = "当前版本：v2.1"

    msg = menu + info

    await help.finish(msg)


group_decrease = on_notice(priority=5)


@group_decrease.handle()
async def handle(bot: Bot, event: GroupDecreaseNoticeEvent):
    id = event.get_session_id()
    if not id.isdigit():
        id = id.split("_")[1]
    if event.self_id == event.user_id:
        model.DeleteGroupCard(id)


channel_decrease = on_notice(priority=5)


@channel_decrease.handle()
async def handle(bot: Bot, event: ChannelDestoryedNoticeEvent):
    id = event.channel_info.owner_guild_id
    cid = event.channel_info.channel_id
    model.DeleteChannelCard(id, cid)
