from enum import Enum

from tortoise import fields
from tortoise.models import Model


class MatchType(Enum):
    congruence = 1
    """全匹配(==)"""
    include = 2
    """模糊匹配(in)"""
    regex = 3
    """正则匹配(regex)"""


class IndexType(Enum):
    group = 1
    """群聊"""
    private = 2
    """私聊"""


class WordBank(Model):
    index_type = fields.SmallIntField(default=1)
    """索引类型"""
    index_id = fields.IntField(pk=True)
    """索引ID"""
    match_type = fields.SmallIntField(default=1)
    """类型"""
    key = fields.TextField()
    """问句"""
    value = fields.TextField()
    """答句"""
    require_to_me = fields.BooleanField(default=False)
    """是否需要@"""
    creator_id = fields.IntField()
    """创建者ID"""
    weight = fields.SmallIntField(default=10)
    """权重"""
    creater_time = fields.DatetimeField()
    """添加时间"""

    class Meta:
        table = "wordbank3"
        table_description = "wordbank3 数据库"
