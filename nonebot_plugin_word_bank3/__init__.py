import re
import random
from typing import List, Tuple, Optional
from pathlib import Path

from nonebot import on_regex, on_command, on_message
from nonebot.params import State, CommandArg, RegexGroup
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

from .utils import parse_msg, get_index_type, get_session_id, save_and_convert_img
from .models.word_bank import WordBank
from .models.typing_models import IndexType, MatchType, WordEntry

add_model("nonebot_plugin_word_bank3.models.word_bank")
add_model("nonebot_plugin_word_bank3.models.word_bank_data")

img_dir = Path("data/wordbank/img").absolute()
img_dir.mkdir(parents=True, exist_ok=True)


async def wb_match_rule(event: MessageEvent, state: T_State = State()) -> bool:
    index_type = (
        IndexType.group if isinstance(event, GroupMessageEvent) else IndexType.private
    )

    word_entry: Optional[WordEntry] = await WordBank.match(
        index_type=index_type,
        index_id=get_session_id(event),
        key=str(event.get_message()),
        to_me=event.is_tome(),
    )
    if word_entry:
        state["replies"] = word_entry
        return True
    return False


wb_matcher = on_message(wb_match_rule, priority=99)


@wb_matcher.handle()
async def handle_wb(event: MessageEvent, state: T_State = State()):
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
    r"^((?:??????|??????|@)*)\s*???\s*(\S+.*?)\s*???$(\d+)\s*(\S+.*?)\s*$",
    flags=re.S,
    block=True,
    priority=11,
    permission=PERM_EDIT,
)

wb_set_cmd_gl = on_regex(
    r"^((?:??????|??????|??????|@)*)\s*???\s*(\S+.*?)\s*???\s*(\S+.*?)\s*$",
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
        if "??????" in flag
        else MatchType.include
        if "??????" in flag
        else MatchType.congruence
    )
    require_to_me: bool = False
    if "@" in flag:  # @?????????to_me????????????
        require_to_me = True
    else:
        # ????????????????????????????????????to_me
        for name in bot.config.nickname:
            if key.startswith(name):
                key = key.replace(name, "", 1)
                require_to_me = True
                break

    answer = Message(parse_msg(answer))  # ??????/at, /self, /atself
    await save_and_convert_img(answer, img_dir)  # ????????????????????????

    index_id = get_session_id(event)
    index_type = get_index_type(event)

    id, created = await WordBank.set(
        index_type=index_type,
        index_id=index_id,
        match_type=match_type,
        key=key,
        answer=str(answer),
        creator_id=event.user_id,
        require_to_me=require_to_me,
        weight=10,
    )
    if created:
        await matcher.finish(message=f"???????????????????????????: {id}")


wb_del_cmd = on_regex(
    r"^??????\s*((?:??????|??????|@)*)\s*??????\s*(\S+.*?)\s*$",
    flags=re.S,
    block=True,
    priority=11,
    permission=PERM_EDIT,
)

wb_del_cmd_gl = on_regex(
    r"^??????\s*((?:??????|??????|??????|@)*)\s*??????\s*(\S+.*?)\s*$",
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
        if "??????" in flag
        else MatchType.include
        if "??????" in flag
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

    # TODO ????????????????????????
    res = await WordBank.delete_by_key(
        index_type=index_type,
        index_id=index_id,
        match_type=match_type,
        key=key,
        require_to_me=require_to_me,
    )

    if res:
        await matcher.finish("????????????~")


def wb_clear(index_type: str = "") -> T_Handler:
    async def wb_clear_(
        event: MessageEvent,
        arg: Message = CommandArg(),
        state: T_State = State(),
        index_type=index_type,
    ):
        msg = arg.extract_plain_text().strip()
        if msg:
            state["is_sure"] = msg

        if not index_type:
            index_id = get_session_id(event)
            index_type = get_index_type(event)
            keyword = "??????" if isinstance(event, GroupMessageEvent) else "??????"
        elif index_type == "??????":
            index_id = None
            index_type = None
            keyword = index_type
        else:
            # ??????
            index_id = None
            index_type = None
            keyword = index_type
        state["index_id"] = index_id
        state["index_type"] = index_type
        state["keyword"] = keyword

    return wb_clear_


wb_clear_cmd = on_command(
    "????????????",
    block=True,
    priority=10,
    permission=PERM_EDIT,
    handlers=[wb_clear()],
)
wb_clear_cmd_gl = on_command(
    "??????????????????", block=True, priority=10, permission=PERM_GLOBAL, handlers=[wb_clear("??????")]
)
wb_clear_bank = on_command(
    "??????????????????", block=True, priority=10, permission=PERM_GLOBAL, handlers=[wb_clear("??????")]
)


prompt_clear = Message.template("???????????????????????????{keyword}???????????????????????? yes")


@wb_clear_cmd.got("is_sure", prompt=prompt_clear)
@wb_clear_cmd_gl.got("is_sure", prompt=prompt_clear)
@wb_clear_bank.got("is_sure", prompt=prompt_clear)
async def _(matcher: Matcher, state: T_State = State()):
    is_sure = str(state["is_sure"]).strip()
    index_id = state["index_id"]

    keyword = state["keyword"]

    if is_sure == "yes":

        if keyword == "??????":
            res = await WordBank.clear()
        elif keyword == "??????":
            # TODO
            res = 1
        else:
            res = await WordBank.clear(
                index_type=state["index_type"], index_id=index_id
            )

        if res:
            await matcher.finish(Message.template("??????{keyword}????????????~"))
    else:
        await matcher.finish("????????????")


# wb_search_cmd = on_regex(
#     r"^??????\s*((?:???|??????)*)\s*(\d*)\s*((?:??????)?(?:??????|??????)?@?)\s*??????\s*(.*?)\s*$",
#     flags=re.S,
#     block=True,
#     priority=10,
#     permission=PERM_GLOBAL,
# )
# wb_search_cmd_user = on_regex(
#     r"^??????\s*((?:??????|??????)?@?)\s*??????\s*(.*?)\s*$",
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
#         type = "???" if isinstance(event, GroupMessageEvent) else "??????"
#         id = event.group_id if isinstance(event, GroupMessageEvent) else event.user_id
#         flag, key = matched
#     else:
#         type, id, flag, key = matched

#     nickname = event.sender.card or event.sender.nickname

#     if type and not id:
#         await matcher.finish(f"?????????{type}ID")

#     index = (
#         "0"
#         if "??????" in flag
#         else get_session_id(event)
#         if not type
#         else {"???": "group", "??????": "private"}[type] + f"_{id}"
#     )
#     type_ = (
#         MatchType.regex
#         if "??????" in flag
#         else MatchType.include
#         if "??????" in flag
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
#         await matcher.finish("????????????????????????~")

#     if isinstance(event, GroupMessageEvent):
#         forward_msg: List[Dict] = []
#         for entry in entrys:
#             forward_msg.append(
#                 to_json(
#                     "???: " + entry.key, nickname or "user" + " ???:", str(event.user_id)
#                 )
#             )
#             for value in entry.values:
#                 forward_msg.append(
#                     to_json(
#                         value,
#                         "bot??????",
#                         str(bot.self_id),
#                     )
#                 )
#         await bot.call_api(
#             "send_group_forward_msg", group_id=event.group_id, messages=forward_msg
#         )
#     else:
#         for entry in entrys:
#             msg_temp = "???: " + Message(entry.key) + " ???:"
#             for value in entry.values:
#                 msg_temp += "\n" + Message.template("{value}").format(value=value)
#             await matcher.send(msg_temp)
#             await sleep(1)
