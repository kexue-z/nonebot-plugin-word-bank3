from enum import Enum
from typing import List

from pydantic import BaseModel


class MatchType(Enum):
    """匹配类型 全匹配(1) 模糊匹配(2) 正则匹配(3)"""

    congruence = 1
    """全匹配(==)"""
    include = 2
    """模糊匹配(in)"""
    regex = 3
    """正则匹配(regex)"""


class IndexType(Enum):
    """索引类型 群聊(1) 私聊(2)"""

    group = 1
    """群聊"""
    private = 2
    """私聊"""
    _global = 3

class CmdType(Enum):
    """操作类型 添加(1) 修改(2) 迁移(3)"""

    add = 1
    """添加"""
    update = 2
    """修改""" 
    move = 3
    """迁移"""


class Answer(BaseModel):
    answer: str
    weight: int
    last_cmd:int
    id: int


class WordEntry(BaseModel):
    key: str
    answer: List[Answer]
    require_to_me: bool
