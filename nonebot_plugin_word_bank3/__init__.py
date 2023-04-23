import re
import html
import random
from typing import List, Tuple, Optional
from pathlib import Path

from nonebot import on_regex, get_driver, on_command, on_message, on_startswith
from nonebot.params import CommandArg, RegexGroup
from nonebot.typing import T_State, T_Handler
from nonebot.matcher import Matcher
from nonebot.permission import SUPERUSER
from nonebot.adapters.onebot.v11 import Bot, Message, MessageEvent, GroupMessageEvent
from nonebot.adapters.onebot.v11.permission import (
    GROUP_ADMIN,
    GROUP_OWNER,
    PRIVATE_FRIEND,
)

from .utils import parse_msg, get_index_type, get_session_id, save_and_convert_img
from .config import Config
from .data_source import cmd
from .models.word_bank import WordBank
from .models.typing_models import IndexType, MatchType, WordEntry

last_operation_time = Config.parse_obj(get_driver().config.dict()).last_operation_time

img_dir = Path("data/wordbank/img").absolute()
img_dir.mkdir(parents=True, exist_ok=True)

cmd_list = ["-V", "-v", "-r"]


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
    msg = html.unescape(msg)
    await wb_matcher.finish(Message(msg))


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

    ans_id_list_ = []

    for ans in ans_id_list:
        ans_id_list_.append(int(ans))
    # TODO 修改内容
    res = await WordBank.update_answer(
        answer_id_list=ans_id_list_, update_answer=update_ans
    )

    if res:
        result = ""
        for id in ans_id_list:
            result += f" {id} "
        result += f"已全部修改为{update_ans}"
        await matcher.finish(f"{result}")


wb_cmd = on_startswith("#", block=True, priority=10, permission=PERM_EDIT)


@wb_cmd.handle()
async def _(
    bot: Bot, event: MessageEvent, matcher: Matcher, arg: Message = CommandArg()
):
    await wb_cmd.finish(str(await cmd(bot, event, str(arg).strip())))


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
