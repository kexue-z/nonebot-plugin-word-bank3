import re
import datetime
import random
from typing import List, Tuple, Optional
from pathlib import Path
import pytz

from nonebot import on_regex, on_command, on_message, get_driver
from nonebot.params import CommandArg, RegexGroup
from nonebot.typing import T_State, T_Handler
from nonebot.matcher import Matcher
from nonebot.permission import SUPERUSER
from nonebot.adapters.onebot.v11 import Bot, Message, MessageEvent, GroupMessageEvent
from nonebot_plugin_tortoise_orm import add_model
from nonebot.adapters.onebot.v11.permission import (
    GROUP_ADMIN,
    GROUP_OWNER,
    PRIVATE_FRIEND,
)

from .config import Config
from .utils import parse_msg, get_index_type, get_session_id, save_and_convert_img
from .models.word_bank import WordBank
from .models.word_bank_data import WordBankData
from .models.typing_models import IndexType, MatchType, WordEntry

add_model("nonebot_plugin_word_bank3.models.word_bank")
add_model("nonebot_plugin_word_bank3.models.word_bank_data")

last_operation_time = Config.parse_obj(get_driver().config.dict()).last_operation_time

img_dir = Path("data/wordbank/img").absolute()
img_dir.mkdir(parents=True, exist_ok=True)

cmd_list = ["-V", "-v", "-r"]


async def special_cmd(
    index_type: IndexType, index_id: str, cmd: str, id: int = 0, key: str = ""
) -> Tuple[str, bool]:
    """cmd判断"""

    # 问题答案回退操作
    if cmd == "-V":
        result = "问答"
        if await WordBank.last_ans_return(index_type, index_id, key) == []:
            return "无该编号问答", False
        for id in await WordBank.last_ans_return(index_type, index_id, key):
            result += id
        result += "已回退完成"
        return result, True

    # 问题近期训练反馈
    if cmd == "-v":
        result = "编号为"
        index = 0
        # 通过问句进行查询
        if id == 0:
            if await WordBank.key_return(index_type, index_id, key) == []:
                return "无该编号问答", False
            for id in await WordBank.key_return(index_type, index_id, key):
                result += f"{id} 的问答信息\n"
                result += f"问题:{key}\n"
                result += "回答:"
                for ans in (await WordBank.match(index_type, index_id, key)).answer:
                    index += 1
                    if ans.answer != ans.last_cmd:
                        result += f"{index}. {ans.answer} [{ans.last_cmd}] "
                    else:
                        result += f"{index}. {ans.answer} "
            return result, True
        # 通过id进行查询
        else:
            if await WordBank.keys_id_return(id) == []:
                return "无该编号问答", False
            for key in await WordBank.keys_id_return(id):
                result += f"{id} 的问答信息\n"
                result += f"问题:{key}\n"
                result += "回答:"
                for ans in (await WordBank.match(index_type, index_id, key)).answer:
                    index += 1
                    if ans.answer != ans.last_cmd:
                        result += f"{index}. {ans.answer} [{ans.last_cmd}] "
                    else:
                        result += f"{index}. {ans.answer} "
            return result, True

    # 问题删除操作
    if cmd == "-r":
        result = "问答"
        # 通过问句进行删除
        if id == 0:
            if await WordBank.key_return(index_type, index_id, key) == []:
                return "该条问答已不存在", False
            for id in await WordBank.key_return(index_type, index_id, key):
                ans_id, bool = await WordBank.delete_by_key(index_type, index_id, key)
                if bool == True:
                    result += f"{id}"
            result += "已成功删除"
            return result, True
        # 通过id进行删除
        else:
            if await WordBank.delete_by_key_id(index_type, index_id, id) == []:
                return "该条问答已不存在", False
            if await WordBank.delete_by_key_id(index_type, index_id, id):
                result += f"{id}"
            result += "已成功删除"
            return result, True

    # 问题迁移操作
    if cmd.startswith("-mg"):
        result = "问题"
        move_id = cmd.replace("-mg", "")
        update_type = IndexType.group
        if move_id != "":
            # 通过问句进行迁移
            if id == 0:
                if await WordBank.key_return(index_type, index_id, key) == []:
                    return f"该条问答不存在无法迁移至{move_id}", False
                for id in await WordBank.key_return(index_type, index_id, key):
                    bool = await WordBank.update_by_key(
                        index_type,
                        index_id,
                        key,
                        update_index_id=move_id,
                        update_index_type=update_type,
                    )
                    if bool == True:
                        result += f"{id}"
                result += f"已成功迁移至{move_id}"
                return result, True
            # 通过id进行迁移
            else:
                if await WordBank.update_by_id(
                    index_type,
                    index_id,
                    id,
                    update_index_id=move_id,
                    update_index_type=update_type,
                ):
                    result += f"{id}"
                else:
                    return f"该条问答不存在无法迁移至{move_id}", False
                result += f"已成功迁移至{move_id}"
                return result, True
    if cmd.startswith("-mp"):
        result = "问题"
        move_id = cmd.replace("-mp", "")
        update_type = IndexType.private
        if move_id != "":
            # 通过问句进行迁移
            if id == 0:
                if await WordBank.key_return(index_type, index_id, key) == []:
                    return f"该条问答不存在无法迁移至{move_id}", False
                for id in await WordBank.key_return(index_type, index_id, key):
                    bool = await WordBank.update_by_key(
                        index_type,
                        index_id,
                        key,
                        update_index_id=move_id,
                        update_index_type=update_type,
                    )
                    if bool == True:
                        result += f"{id}"
                result += f"已成功迁移至{move_id}"
                return result, True
            # 通过id进行迁移
            else:
                if await WordBank.update_by_id(
                    index_type,
                    index_id,
                    id,
                    update_index_id=move_id,
                    update_index_type=update_type,
                ):
                    result += f"{id}"
                else:
                    return f"该条问答不存在无法迁移至{move_id}", False
                result += f"已成功迁移至{move_id}"
                return result, True
    return None, False


async def key_id_list_cmd(
    index_type: IndexType,
    index_id: str,
    list_first: str,
    list_second: str,
    list_third: str = "",
) -> list:
    """范围问句id操作处理"""
    if list_third != "":
        result_list = []
        for i in range(int(list_first), int(list_second) + 1):
            result, bool = await special_cmd(index_type, index_id, list_third, i)
            if bool == True:
                result_list.append(result)
            else:
                result_list = ["范围问句id操作处理错误:" + result]
        return result_list


async def last_cmd_type(cmd: int) -> str:
    if cmd == 1:
        return "添加"
    elif cmd == 2:
        return "修改"
    else:
        return "迁移"


# 教学操作函数
async def last_cmd_bool(event: MessageEvent) -> str:
    index_type = (
        IndexType.group if isinstance(event, GroupMessageEvent) else IndexType.private
    )
    index_id = get_session_id(event)
    data_now = datetime.datetime.now()
    data_now = data_now.replace(tzinfo=pytz.timezone("UTC"))
    data_need = data_now - datetime.timedelta(minutes=float(last_operation_time))
    result = ""
    dict = {}
    time_list, id_key_ans = await WordBank.datetime_return_all(
        index_type=index_type, index_id=index_id
    )
    for time in time_list.keys():
        # print(time_list[time])
        if time_list[time] > data_need - datetime.timedelta(hours=8):
            dict[time] = id_key_ans[time]
            dict[time]["time_distance"] = (
                data_now - time_list[time] - datetime.timedelta(hours=8)
            )
    if dict != {}:
        for time in dict:
            if int(dict[time]["time_distance"].seconds // 60) > 0:
                result += f'{time}.[{await last_cmd_type(dict[time]["last_cmd"])}- {int(dict[time]["time_distance"].seconds//60)} 分前:]问题:{dict[time]["key"]},回答\n'
            else:
                result += f'{time}.[{await last_cmd_type(dict[time]["last_cmd"])}- {int(dict[time]["time_distance"].seconds)} 秒前:]问题:{dict[time]["key"]},回答\n'
            index = 0
            for ans in await WordBankData.id_return(dict[time]["answer_id"]):
                index += 1
                result += f"[{index}]-{ans} \n"
    else:
        result = "近期无教学操作"
    return result


async def search(list: list):
    if "#" in list:
        if len(list) == 3:
            id_list = await WordBankData.ans_return(list[2])
            result = ""
            for id in id_list:
                result += f" {id} "
            return result
    if len(list) == 2:
        if "-v" == list[1]:
            for i in await WordBank.datetime_return(list[0]):
                return isinstance(i, datetime)


# 导入数据库函数
async def add_orm(bot: Bot, index_type, id: int, user_id: str, list: list[str]):
    if "@" in list[0]:
        require_to_me = True
    else:
        for name in bot.config.nickname:
            if list[0].startswith(name):
                key = list[0].replace(name, "", 1)
                require_to_me = True
                break
    require_to_me = False
    key = str(list[0])
    answer = Message(parse_msg(list[1]))  # 替换/at, /self, /atself
    match_type = MatchType.congruence
    await save_and_convert_img(answer, img_dir)  # 保存回答中的图片

    if list[0].startswith("qg"):
        index_type = IndexType._global
        key = key.replace("qg", "")
        if list[0].startswith("zz"):
            match_type = MatchType.regex
            key = key.replace("zz", "")
        elif list[0].startswith("mh"):
            match_type = MatchType.include
            key = key.replace("mh", "")
    elif list[0].startswith("zz"):
        match_type = MatchType.regex
        key = key.replace("zz", "")
    elif list[0].startswith("mh"):
        match_type = MatchType.include
        key = key.replace("mh", "")

    id, created = await WordBank.set(
        index_type=index_type,
        index_id=id,
        match_type=match_type,
        key=key,
        answer=answer,
        creator_id=str(user_id),
        require_to_me=require_to_me,
        weight=10,
    )
    if created:
        return f"问答已添加,编号为{id}。"


# 命令处理函数
async def cmd(bot: Bot, event: MessageEvent, commond: str):
    try:
        index_type = (
            IndexType.group
            if isinstance(event, GroupMessageEvent)
            else IndexType.private
        )
        to_me = False if index_type == IndexType.private else event.is_tome()

        # 空格、换行词条处理
        if '"' in commond:
            list = commond.split('"')
            ex_list: List[str] = []
            for part in list:
                ex_list.append(part)
            ex_list.remove("")
            ex_list.remove(" ")
            result = await add_orm(
                bot, index_type, get_session_id(event), event.user_id, ex_list
            )

        # 正常词条处理
        list = commond.split()

        result = ""
        # 含有‘#’的查询操作处理
        if "#" in list:
            # 由回答查询问句处理
            if len(list) == 3:
                id_list = await WordBankData.ans_return(list[2])
                result = f'回答"{list[2]}"的问题如下:\n'
                key_list = []
                for id in id_list:
                    return_list = await WordBank.ans_id_return(id)
                    key_list.extend(return_list)
                for key in key_list:
                    result += key + "\n"

            elif len(list) == 2:
                # 由问题查询回答处理
                if "-" not in list[1]:
                    id_list = await WordBank.key_return(
                        index_type, get_session_id(event), list[1]
                    )
                    ans_list = []
                    for id in id_list:
                        result = f'问题 {id}."{list[1]}"的回答如下:\n'
                        ans_id_list = await WordBank.keys_id_ans(id)
                        for ans_id in ans_id_list:
                            result_list = await WordBankData.id_return(ans_id)
                            ans_list.extend(result_list)
                        for ans in ans_list:
                            result += ans + "\n"

                # 查询近期全局训练处理
                elif "-v" == list[1]:
                    return await last_cmd_bool(event=event)

        # 其他操作处理
        elif len(list) == 2:
            # 范围问句id操作处理
            if ".." in list[0]:
                id_list = list[0].split("..")
                id_x = id_list[0]
                id_y = id_list[1]
                for i in await key_id_list_cmd(
                    index_type, get_session_id(event), id_x, id_y, list[1]
                ):
                    result += i + "\n"
            elif list[1] in cmd_list or "-mg" in list[1] or "-mp" in list[1]:
                if "id" in list[0]:
                    result, flag = await special_cmd(
                        index_type,
                        get_session_id(event),
                        list[1],
                        list[0].replace("id", ""),
                    )
                elif "key" in list[0]:
                    result, flag = await special_cmd(
                        index_type,
                        get_session_id(event),
                        list[1],
                        key=list[0].replace("key", ""),
                    )
                else:
                    result, flag = await special_cmd(
                        index_type, get_session_id(event), list[1]
                    )
            else:
                result = await add_orm(
                    bot, index_type, get_session_id(event), event.user_id, list
                )
        return result

    except ValueError as e:
        return e


async def wb_match_rule(event: MessageEvent, state: T_State) -> bool:
    index_type = (
        IndexType.group if isinstance(event, GroupMessageEvent) else IndexType.private
    )
    to_me = False if index_type == IndexType.private else event.is_tome()
    word_entry: Optional[WordEntry] = await WordBank.match(
        index_type=index_type,
        index_id=get_session_id(event),
        key=str(event.get_message()),
        to_me=to_me,
    )
    # print(word_entry)
    if word_entry:
        state["replies"] = word_entry
        return True
    return False


wb_matcher = on_message(wb_match_rule, priority=99)


@wb_matcher.handle()
async def handle_wb(event: MessageEvent, state: T_State):
    we: WordEntry = state["replies"]
    choices: List[str] = []
    weights: List[int] = []
    for ans in we.answer:
        choices.append(ans.answer)
        weights.append(ans.weight)
    msg = random.choices(population=choices, weights=weights, k=1)[0]
    msg = Message(msg)
    await wb_matcher.finish(
        Message.template(msg).format(
            nickname=event.sender.card or event.sender.nickname,
            sender_id=event.sender.user_id,
        )
    )


PERM_EDIT = GROUP_ADMIN | GROUP_OWNER | PRIVATE_FRIEND | SUPERUSER
PERM_GLOBAL = SUPERUSER


wb_set_cmd = on_regex(
    r"^((?:模糊|正则|@)*)\s*问\s*(\S+.*?)\s*答$(\d+)\s*(\S+.*?)\s*$",
    flags=re.S,
    block=True,
    priority=11,
    permission=PERM_EDIT,
)

wb_set_cmd_gl = on_regex(
    r"^((?:全局|模糊|正则|@)*)\s*问\s*(\S+.*?)\s*答\s*(\S+.*?)\s*$",
    flags=re.S,
    block=True,
    priority=10,
    permission=PERM_GLOBAL,
)


@wb_set_cmd.handle()
@wb_set_cmd_gl.handle()
async def wb_set(
    bot: Bot,
    event: MessageEvent,
    matcher: Matcher,
    matched: Tuple[str, ...] = RegexGroup(),
):
    flag, key, answer = matched
    match_type = (
        MatchType.regex
        if "正则" in flag
        else MatchType.include
        if "模糊" in flag
        else MatchType.congruence
    )
    require_to_me: bool = False
    if "@" in flag:  # @问需要to_me才会触发
        require_to_me = True
    else:
        # 以昵称开头的词条视为需要to_me
        for name in bot.config.nickname:
            if key.startswith(name):
                key = key.replace(name, "", 1)
                require_to_me = True
                break

    answer = Message(parse_msg(answer))  # 替换/at, /self, /atself
    await save_and_convert_img(answer, img_dir)  # 保存回答中的图片

    index_id = get_session_id(event)
    index_type = get_index_type(event)
    id, created = await WordBank.set(
        index_type=index_type,
        index_id=index_id,
        match_type=match_type,
        key=key,
        answer=str(answer),
        creator_id=str(event.user_id),
        require_to_me=require_to_me,
        weight=10,
    )
    if created:
        await matcher.finish(message=f"问答添加成功编号为: {id}")


wb_del_cmd = on_regex(
    r"^删除\s*((?:模糊|正则|@)*)\s*词条\s*(\S+.*?)\s*$",
    flags=re.S,
    block=True,
    priority=11,
    permission=PERM_EDIT,
)

wb_del_cmd_gl = on_regex(
    r"^删除\s*((?:全局|模糊|正则|@)*)\s*词条\s*(\S+.*?)\s*$",
    flags=re.S,
    block=True,
    priority=10,
    permission=PERM_GLOBAL,
)


@wb_del_cmd.handle()
@wb_del_cmd_gl.handle()
async def _(
    bot: Bot,
    event: MessageEvent,
    matcher: Matcher,
    matched: Tuple[str, ...] = RegexGroup(),
):
    flag, key = matched
    match_type = (
        MatchType.regex
        if "正则" in flag
        else MatchType.include
        if "模糊" in flag
        else MatchType.congruence
    )
    require_to_me: bool = False
    if "@" in flag:
        require_to_me = True
    else:
        for name in bot.config.nickname:
            if key.startswith(name):
                key = key.replace(name, "", 1)
                require_to_me = True
                break

    index_id = get_session_id(event)
    index_type = get_index_type(event)

    # TODO 添加已删除的内容
    res = await WordBank.delete_by_key(
        index_type=index_type,
        index_id=index_id,
        match_type=match_type,
        key=key,
        require_to_me=require_to_me,
    )

    if res:
        await matcher.finish("删除成功~")


def wb_clear(index_type: str = "") -> T_Handler:
    async def wb_clear_(
        event: MessageEvent,
        state: T_State,
        arg: Message = CommandArg(),
        index_type=index_type,
    ):
        msg = arg.extract_plain_text().strip()
        if msg:
            state["is_sure"] = msg

        if not index_type:
            index_id = get_session_id(event)
            index_type = get_index_type(event)
            keyword = "群聊" if isinstance(event, GroupMessageEvent) else "个人"
        elif index_type == "全局":
            index_id = None
            index_type = None
            keyword = index_type
        else:
            # 全部
            index_id = None
            index_type = None
            keyword = index_type
        state["index_id"] = index_id
        state["index_type"] = index_type
        state["keyword"] = keyword

    return wb_clear_


wb_clear_cmd = on_command(
    "删除词库",
    block=True,
    priority=10,
    permission=PERM_EDIT,
    handlers=[wb_clear()],
)
wb_clear_cmd_gl = on_command(
    "删除全局词库", block=True, priority=10, permission=PERM_GLOBAL, handlers=[wb_clear("全局")]
)
wb_clear_bank = on_command(
    "删除全部词库", block=True, priority=10, permission=PERM_GLOBAL, handlers=[wb_clear("全部")]
)


prompt_clear = Message.template("此命令将会清空您的{keyword}词库，确定请发送 yes")


@wb_clear_cmd.got("is_sure", prompt=prompt_clear)
@wb_clear_cmd_gl.got("is_sure", prompt=prompt_clear)
@wb_clear_bank.got("is_sure", prompt=prompt_clear)
async def _(matcher: Matcher, state: T_State):
    is_sure = str(state["is_sure"]).strip()
    index_id = state["index_id"]

    keyword = state["keyword"]

    if is_sure == "yes":
        if keyword == "全部":
            res = await WordBank.clear()
        elif keyword == "全局":
            # TODO
            res = 1
        else:
            res = await WordBank.clear(
                index_type=state["index_type"], index_id=index_id
            )

        if res:
            await matcher.finish(Message.template("删除{keyword}词库成功~"))
    else:
        await matcher.finish("命令取消")


wb_move = on_regex(
    r"^迁移\s*((?:模糊|正则|@)*)\s*词条\s*(\S+.*?)\s*为(\S+.*?)\s*$",
    flags=re.S,
    block=True,
    priority=11,
    permission=PERM_EDIT,
)

wb_move_gl = on_regex(
    r"^迁移\s*((?:模糊|正则|@)*)\s*词条\s*(\S+.*?)\s*为(\S+.*?)\s*$",
    flags=re.S,
    block=True,
    priority=10,
    permission=PERM_EDIT,
)


ans_update = on_regex(
    r"^更改词条答案\s*(\S+.*?)\s*答\s*(\S+.*?)\s*$",
    flags=re.S,
    block=True,
    priority=10,
    permission=PERM_EDIT,
)


@ans_update.handle()
async def _(
    matcher: Matcher,
    matched: Tuple[str, ...] = RegexGroup(),
):
    ans_id_list, update_ans = matched

    ans_id_list = ans_id_list.split("_")

    # TODO 修改内容
    res = await WordBank.update_answer(
        answer_id_list=ans_id_list, update_answer=update_ans
    )

    if res:
        result = ""
        for id in ans_id_list:
            result += f" {id} "
        result += f"已全部修改为{update_ans}"
        await matcher.finish(f"{result}")


wb_cmd = on_command("#", block=True, priority=10, permission=PERM_EDIT)


@wb_cmd.handle()
async def _(
    bot: Bot, event: MessageEvent, matcher: Matcher, arg: Message = CommandArg()
):
    result_list = arg.extract_plain_text().strip().split()
    await wb_cmd.finish(str(await cmd(bot, event, arg.extract_plain_text().strip())))


# wb_search_cmd = on_regex(
#     r"^查询\s*((?:群|用户)*)\s*(\d*)\s*((?:全局)?(?:模糊|正则)?@?)\s*词库\s*(.*?)\s*$",
#     flags=re.S,
#     block=True,
#     priority=10,
#     permission=PERM_GLOBAL,
# )
# wb_search_cmd_user = on_regex(
#     r"^查询\s*((?:模糊|正则)?@?)\s*词库\s*(.*?)\s*$",
#     flags=re.S,
#     block=True,
#     priority=11,
#     permission=PERM_EDIT,
# )


# @wb_search_cmd_user.handle()
# @wb_search_cmd.handle()
# async def wb_search(
#     bot: Bot,
#     event: MessageEvent,
#     matcher: Matcher,
#     matched: Tuple[str, ...] = RegexGroup(),
# ):
#     if len(matched) == 2:
#         type = "群" if isinstance(event, GroupMessageEvent) else "用户"
#         id = event.group_id if isinstance(event, GroupMessageEvent) else event.user_id
#         flag, key = matched
#     else:
#         type, id, flag, key = matched

#     nickname = event.sender.card or event.sender.nickname

#     if type and not id:
#         await matcher.finish(f"请填写{type}ID")

#     index = (
#         "0"
#         if "全局" in flag
#         else get_session_id(event)
#         if not type
#         else {"群": "group", "用户": "private"}[type] + f"_{id}"
#     )
#     type_ = (
#         MatchType.regex
#         if "正则" in flag
#         else MatchType.include
#         if "模糊" in flag
#         else MatchType.congruence
#     )
#     if not (require_to_me := "@" in flag):
#         for name in bot.config.nickname:
#             if key.startswith(name):
#                 key = key.replace(name, "", 1)
#                 require_to_me = True
#                 break

#     entrys = wb.select(index, type_, Message(key), require_to_me)

#     if not entrys:
#         await matcher.finish("词库中未找到词条~")

#     if isinstance(event, GroupMessageEvent):
#         forward_msg: List[Dict] = []
#         for entry in entrys:
#             forward_msg.append(
#                 to_json(
#                     "问: " + entry.key, nickname or "user" + " 答:", str(event.user_id)
#                 )
#             )
#             for value in entry.values:
#                 forward_msg.append(
#                     to_json(
#                         value,
#                         "bot回复",
#                         str(bot.self_id),
#                     )
#                 )
#         await bot.call_api(
#             "send_group_forward_msg", group_id=event.group_id, messages=forward_msg
#         )
#     else:
#         for entry in entrys:
#             msg_temp = "问: " + Message(entry.key) + " 答:"
#             for value in entry.values:
#                 msg_temp += "\n" + Message.template("{value}").format(value=value)
#             await matcher.send(msg_temp)
#             await sleep(1)
