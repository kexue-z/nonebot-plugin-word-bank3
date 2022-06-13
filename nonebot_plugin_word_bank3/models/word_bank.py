import re
from typing import List, Tuple, Union, Optional
from xml.sax import parseString
from datetime import datetime

from tortoise import fields
from tortoise.models import Model

from ..utils import regex_match
from .typing_models import Answer, IndexType, MatchType, WordEntry
from .word_bank_data import WordBankData


class WordBank(Model):
    index_type = fields.SmallIntField(default=1)
    """索引类型"""
    index_id = fields.IntField()
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
    create_time = fields.DatetimeField(auto_now_add=True)
    """添加时间"""

    class Meta:
        table = "wordbank3"
        table_description = "wordbank3 数据库"

    @staticmethod
    async def match(
        index_type: IndexType,
        index_id: int,
        key: str,
        to_me: bool = False,
    ) -> Optional[WordEntry]:
        """
        :说明: `match`
        > 匹配词库

        :参数:
          * `index_type: IndexType`: 索引类型: IndexType.group 群聊, IndexType.private 私聊
          * `index_id: IndexType`: 索引ID: 群聊ID, 私聊ID
          * `key: str`: 问句

        :可选参数:
          * `to_me: bool = False`: 是否需要@

        :返回:
          - `Optional[WordEntry]`: 如匹配到词条则返回结果
        """
        answers: List[Answer] = []
        # 下面这个尝试用for来遍历, 但是有问题 >_<
        # for mt in MatchType:
        #     if wb_list := await WordBank.filter(
        #         index_type=index_type.value,
        #         index_id=index_id,
        #         match_type=mt.value,
        #         require_to_me=to_me,
        #     ):
        #         for wb_ans in wb_list:
        #             if mt == MatchType.congruence and wb_ans.key == key:
        #                 pass
        #             elif mt == MatchType.include and (wb_ans.key in key):
        #                 pass
        #             elif mt == MatchType.regex and regex_match(wb_ans.key, key):
        #                 pass
        #             else:
        #                 continue
        #             data = await WordBankData.get(id=wb_ans.answer_id)
        #             answers.append(Answer(answer=data.answer, weight=wb_ans.weight))

        #     return (
        #         WordEntry(key=key, answer=answers, require_to_me=to_me)
        #         if answers
        #         else None
        #     )

        # 下面把每个类型都查询一下
        if wb_list := await WordBank.filter(
            index_type=index_type.value,
            index_id=index_id,
            key=key,
            match_type=MatchType.congruence.value,
            require_to_me=to_me,
        ):

            for wb_ans in wb_list:
                data = await WordBankData.get(id=wb_ans.answer_id)
                answers.append(Answer(answer=data.answer, weight=wb_ans.weight))

        if wb_list := await WordBank.filter(
            index_type=index_type.value,
            index_id=index_id,
            match_type=MatchType.include.value,
            require_to_me=to_me,
        ):
            for wb in wb_list:
                if wb.key in key:
                    data = await WordBankData.get(id=wb.answer_id)
                    answers.append(Answer(answer=data.answer, weight=wb.weight))

        if wb_list := await WordBank.filter(
            index_type=index_type.value,
            index_id=index_id,
            match_type=MatchType.regex.value,
            require_to_me=to_me,
        ):
            for wb in wb_list:
                try:
                    if bool(re.search(wb.key, key, re.S)):
                        data = await WordBankData.get(id=wb.answer_id)
                        answers.append(Answer(answer=data.answer, weight=wb.weight))
                except re.error:
                    continue

        we = WordEntry(key=key, answer=answers, require_to_me=to_me)
        return we

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
                模糊匹配, MatchType.regex 正则匹配
          * `key: str`: 问句
          * `answer: str`: 答句
          * `creator_id: int`: 创建人ID

        :可选参数:
          * `require_to_me: bool = False`: 是否需要@
          * `weight: int = 10`: 权重 1~10

        :返回:
          - `bool`: 是否添加成功
        """
        if weight < 1 or weight > 10:
            raise ValueError("权重必须为 1~10 的整数")

        ans = await WordBankData.create(answer=answer)
        _, created = await WordBank.get_or_create(
            index_type=index_type.value,
            index_id=index_id,
            match_type=match_type.value,
            key=key,
            answer_id=ans.id,
            require_to_me=require_to_me,
            creator_id=creator_id,
            weight=weight,
        )
        return created

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
        keys: List[str] = []
        wb_list = await WordBank.filter(index_type=index_type, index_id=index_id).all()
        for wb in wb_list:
            keys.append(wb.key)
        return keys

    @staticmethod
    async def delete_by_key(
        index_type: IndexType,
        index_id: int,
        key: str,
        match_type: MatchType = MatchType.congruence,
        require_to_me: bool = False,
    ) -> Tuple[List[int], bool]:

        """
        :说明: `delete`
        > 删除指定问答词条 (可以指定 `问句`)

        :参数:
          * `index_type: IndexType`: 索引类型: IndexType.group 群聊, IndexType.private 私聊
          * `index_id: int`: 索引ID
          * `key: str`: 问句

        :可选参数:
          * `match_type: Optional[MatchType] = None`: 匹配类型: MatchType.congruence 全匹配,
                MatchType.include
          * `require_to_me: bool = False`: 是否需要@

        :返回:
          - `Tuple[List[int], bool]`: 已删除的答句ID列表, 是否删除成功
        """
        match = await WordBank.filter(
            index_type=index_type.value,
            index_id=index_id,
            match_type=match_type.value,
            key=key,
            require_to_me=require_to_me,
        )
        ans_id_list = [ans.answer_id for ans in match]
        for id in ans_id_list:
            await WordBankData.filter(id=id).delete()

        await WordBank.filter(
            index_type=index_type.value,
            index_id=index_id,
            match_type=match_type.value,
            key=key,
            require_to_me=require_to_me,
        ).delete()

        return ans_id_list, True

    @staticmethod
    async def delete_by_answer_id(
        answer_id_list: List[int],
    ) -> Tuple[List[int], bool]:
        """
        :说明: `delete_by_answer_id`
        > 删除指定答句ID对应的词条

        :参数:
          * `answer_id: Union[int, List[int]]`: 答句ID列表

        :返回:
          - `Tuple[List[int], bool]`: 已删除的答句ID列表, 是否删除成功
        """
        for id in answer_id_list:
            await WordBank.filter(answer_id=id).delete()
            await WordBankData.filter(id=id).delete()
        return answer_id_list, True

    @staticmethod
    async def clear(
        index_id: Optional[int] = None,
        index_type: Optional[IndexType] = None,
        match_type: Optional[MatchType] = None,
    ) -> bool:
        """
        :说明: `clear`
        > 清空词库

        若为参数均为空则清空所有词库

        :可选参数:
          * `index_id: Optional[int] = None`: 索引ID
          * `index_type: Optional[IndexType] = None`: 索引类型: IndexType.group 群聊,
                IndexType.private 私聊
          * `match_type: Optional[MatchType] = None`: 匹配类型: MatchType.congruence 全匹配,
                MatchType.include 模糊匹配, MatchType.regex 正则匹配

        :返回:
          - `bool`: 是否删除成功
        """

        if index_id is None and index_type is None and match_type is None:
            await WordBank.all().delete()
            await WordBankData.all().delete()
            return True

        if index_id and index_type:
            match = await WordBank.filter(
                index_id=index_id,
                index_type=index_type.value,
                match_type=match_type.value if match_type else None,
            )
            ans_id_list = [ans.answer_id for ans in match]
            for id in ans_id_list:
                await WordBankData.filter(id=id).delete()

            await WordBank.filter(
                index_id=index_id,
                index_type=index_type.value,
            ).delete()

            return True

        return False
