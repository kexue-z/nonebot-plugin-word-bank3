import re
from typing import Optional
from pathlib import Path

import httpx
from nonebot.log import logger
from nonebot.adapters.onebot.v11 import Message, MessageEvent, GroupMessageEvent

from .models.typing_models import IndexType


def regex_match(regex: str, text: str) -> bool:
    try:
        return bool(re.search(regex, text, re.S))
    except re.error:
        return False


def get_session_id(event: MessageEvent) -> int:
    if isinstance(event, GroupMessageEvent):
        return event.group_id
    else:
        return event.user_id


def get_index_type(event: MessageEvent) -> IndexType:
    if isinstance(event, GroupMessageEvent):
        return IndexType.group
    else:
        return IndexType.private


def save_img(img: bytes, filepath: Path):
    with filepath.open("wb") as f:
        f.write(img)


def parse_msg(msg: str) -> str:
    """
    :说明: `parse_msg`
    > 替换回答中的 `/at`, `/self`, `/atself`

    :参数:
      * `msg: str`: 待处理的消息

    :返回:
      - `str`: 消息
    """
    msg = re.sub(r"{", "{{", msg)
    msg = re.sub(r"}", "}}", msg)
    msg = re.sub(r"/at\s*(\d+)", lambda s: f"[CQ:at,qq={s.group(1)}]", msg)
    msg = re.sub(r"/self", "{nickname}", msg)
    msg = re.sub(r"/atself", "{sender_id:at}", msg)
    return msg


async def get_img(url: str) -> Optional[bytes]:
    headers = {
        "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9",  # noqa
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/95.0.4638.69 Safari/537.36 Edg/95.0.1020.53",  # noqa
    }
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get(url, headers=headers)
            return resp.content
    except httpx.TimeoutException:
        logger.warning(f"图片下载失败：{url}")
        return None


async def save_and_convert_img(msg: Message, img_dir: Path):
    """
    :说明: `save_and_convert_img`
    > 保存消息中的图片，并替换 `file` 中的文件名为本地路径

    :参数:
      * `msg: Message`: 待处理的消息
      * `img_dir: Path`: 图片保存路径
    """
    for msg_seg in msg:
        if msg_seg.type == "image":
            filename = msg_seg.data.get("file", "")
            if not filename:
                continue
            # 检查图片文件夹中有无同名文件
            images = [f.name for f in img_dir.iterdir() if f.is_file()]
            filepath = img_dir / filename
            if filename not in images:
                url = msg_seg.data.get("url", "")
                if not url:
                    continue
                data = await get_img(url)
                if not data:
                    continue
                save_img(data, filepath)
            msg_seg.data["file"] = f"file:///{filepath.resolve()}"
