from typing import List, Union, Optional

from tortoise import fields
from tortoise.models import Model

from .typing_models import IndexType, MatchType, WordEntry


class WordBankData(Model):
    id = fields.IntField(pk=True)
    answer = fields.TextField()

    class Meta:
        table = "wordbank3_data"
        table_description = "wordbank3 答句数据库"


class WordBank(Model):
    index_type = fields.SmallIntField(default=1)
    """索引类型"""
    index_id = fields.IntField(pk=True)
    """索引ID"""
    match_type = fields.SmallIntField(default=1)
    """类型"""
    key = fields.TextField()
    """问句"""
    answer_id = fields.IntField()
    """答句ID"""
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

    @staticmethod
    async def match(
        index_type: IndexType,
        key: str,
        match_type: Optional[MatchType] = None,
        to_me: bool = False,
    ) -> Optional[WordEntry]:

        """
        :说明: `match`
        > 匹配词库

        :参数:
          * `index_type: IndexType`: 索引类型: IndexType.group 群聊, IndexType.private 私聊
          * `key: str`: 问句

        :可选参数:
          * `match_type: Optional[MatchType] = None`: 匹配类型, 如果为None则匹配所有类型
          * `to_me: bool = False`: 是否需要@

        :返回:
          - `Optional[WordEntry]`: 如匹配到词条则返回结果
        """

        if wb_list := await WordBank.filter(
            index_type=index_type, key=key, match_type=match_type, require_to_me=to_me
        ):
            # TODO 测试是否可用
            answers = await WordBankData.filter(id=[wb.answer_id for wb in wb_list])
            return WordEntry(key=key, answer=answers, require_to_me=to_me)

        return None

    @staticmethod
    async def set(
        index_type: IndexType,
        index_id: int,
        match_type: MatchType,
        key: str,
        answer: str,
        creator_id: int,
        require_to_me: bool = False,
        weight: int = 10,
    ) -> bool:
        """
        :说明: `set`
        > 添加词条

        :参数:
          * `index_type: IndexType`: 索引类型: IndexType.group 群聊, IndexType.private 私聊
          * `index_id: int`: 索引ID
          * `match_type: MatchType`: 匹配类型: MatchType.congruence 全匹配, MatchType.include
                模糊匹配, MatchType.regex 正则匹配, MatchType.at @匹配
          * `key: str`: 问句
          * `answer: str`: 答句
          * `creator_id: int`: 创建人ID

        :可选参数:
          * `require_to_me: bool = False`: 是否需要@
          * `weight: int = 10`: 权重 1~10

        :返回:
          - `bool`: 是否添加成功
        """
        pass

    @staticmethod
    async def keys(index_type: IndexType, index_id: int) -> List[str]:
        """
        :说明: `keys`
        > 获取索引下的所有问句

        :参数:
          * `index_type: IndexType`: 索引类型: IndexType.group 群聊, IndexType.private 私聊
          * `index_id: int`: 索引ID

        :返回:
          - `List[str]`: 问句列表
        """
        pass

    @staticmethod
    async def delete(
        index_type: IndexType,
        index_id: int,
        match_type: Optional[MatchType] = None,
        key: Optional[str] = None,
        creator_id: Optional[int] = None,
        answer_id: Optional[int] = None,
        require_to_me: bool = False,
    ) -> bool:
        """
        :说明: `delete`
        > 删除指定问答词条 (可以指定 `问句` 或 `创建者ID` 或 `答句ID`)

        :参数:
          * `index_type: IndexType`: 索引类型: IndexType.group 群聊, IndexType.private 私聊
          * `index_id: int`: 索引ID

        :可选参数:
          * `match_type: Optional[MatchType] = None`: 配类型: MatchType.congruence 全匹配,
                MatchType.include
          * `key: Optional[str] = None`: 问句
          * `creator_id: Optional[int] = None`: 创建人ID
          * `answer_id: Optional[int] = None`: 答句ID
          * `require_to_me: bool = False`: 是否需要@

        :返回:
          - `bool`: 是否删除成功
        """
        pass

    @staticmethod
    async def delete_ans_id(ans_id: Union[int, List[int]]) -> bool:
        """
        :说明: `delete_ans_id`
        > 删除指定答句ID

        :参数:
          * `ans_id: Union[int, List[int]]`: 答句ID 或 答句ID 列表

        :返回:
          - `bool`: 是否删除成功
        """
        pass

    @staticmethod
    async def clear(
        index_type: IndexType,
        index_id: int,
        creator_id: Optional[int] = None,
    ) -> bool:
        """
        :说明: `clear`
        > 清空索引下的所有问答词条

        :参数:
          * `index_type: IndexType`: 索引类型: IndexType.group 群聊, IndexType.private 私聊
          * `index_id: int`: 索引ID

        :可选参数:
          * `creator_id: Optional[int] = None`: 创建人ID

        :返回:
          - `bool`: 是否清空成功
        """
        pass
