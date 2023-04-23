import datetime
from typing import List, Tuple
from pathlib import Path

import pytz
from nonebot import get_driver
from nonebot.adapters.onebot.v11 import Bot, Message, MessageEvent, GroupMessageEvent
from nonebot_plugin_tortoise_orm import add_model

from .utils import parse_msg, get_session_id, save_and_convert_img
from .config import Config
from .models.word_bank import WordBank
from .models.typing_models import IndexType, MatchType
from .models.word_bank_data import WordBankData

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
            result += str(id)
        result += "已回退完成"
        return result, True

    # 问题近期训练反馈
    try:
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
    except AttributeError:
        pass

    # 问题删除操作
    if cmd == "-r":
        result = "问答"
        # 通过问句进行删除
        if id == 0:
            if await WordBank.key_return(index_type, index_id, key) == []:
                return "该条问答已不存在", False
            for id in await WordBank.key_return(index_type, index_id, key):
                ans_id, flag = await WordBank.delete_by_key(index_type, index_id, key)
                if flag:
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
                    if bool:
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
                    if bool:
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
    return "", False


async def key_id_list_cmd(
    index_type: IndexType,
    index_id: str,
    list_first: str,
    list_second: str,
    list_third: str = "",
):
    """范围问句id操作处理"""
    if list_third != "":
        result_list = []
        for i in range(int(list_first), int(list_second) + 1):
            result, bool = await special_cmd(index_type, index_id, list_third, i)
            if bool:
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
                result += f"""{time}.[{await last_cmd_type(dict[time]["last_cmd"])}- {int(dict[time]["time_distance"].seconds//60)} 分前:]问题:{dict[time]["key"]},回答\n"""
            else:
                result += f"""{time}.[{await last_cmd_type(dict[time]["last_cmd"])}- {int(dict[time]["time_distance"].seconds)} 秒前:]问题:{dict[time]["key"]},回答\n"""
            index = 0
            for ans in await WordBankData.id_return(dict[time]["answer_id"]):
                index += 1
                result += f"[{index}]-{ans} \n"
    else:
        result = "近期无教学操作"
    return result


# 导入数据库函数
async def add_orm(
    bot: Bot, index_type: IndexType, id: int, user_id: str, list: list[str]
):
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
        index_id=str(id),
        match_type=match_type,
        key=key,
        answer=answer.extract_plain_text(),
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
        # to_me = False if index_type == IndexType.private else event.is_tome()

        # 空格、换行词条处理
        if '"' in commond:
            list = commond.split('"')
            ex_list: List[str] = []
            for part in list:
                ex_list.append(part)
            ex_list.remove("")
            ex_list.remove(" ")
            result = await add_orm(
                bot, index_type, int(get_session_id(event)), str(event.user_id), ex_list
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
                try:
                    for i in await key_id_list_cmd(
                        index_type, get_session_id(event), id_x, id_y, list[1]
                    ):
                        result += i + "\n"
                except TypeError:
                    pass
            elif list[1] in cmd_list or "-mg" in list[1] or "-mp" in list[1]:
                if "id" in list[0]:
                    result, flag = await special_cmd(
                        index_type,
                        get_session_id(event),
                        list[1],
                        int(list[0].replace("id", "")),
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
                    bot,
                    index_type,
                    int(get_session_id(event)),
                    str(event.user_id),
                    list,
                )
        return result

    except ValueError as e:
        return e
