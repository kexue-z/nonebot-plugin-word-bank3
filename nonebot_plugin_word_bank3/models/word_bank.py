import re
from typing import List, Tuple, Optional
from datetime import datetime

from tortoise import fields
from tortoise.models import Model
from nonebot.adapters.onebot.v11.utils import unescape

from .typing_models import Answer, CmdType, IndexType, MatchType, WordEntry
from .word_bank_data import WordBankData


class WordBank(Model):
    id = fields.BigIntField(pk=True)
    """问答ID"""
    index_type = fields.SmallIntField(default=1)
    """索引类型"""
    index_id = fields.TextField()
    """索引ID"""
    match_type = fields.SmallIntField(default=1)
    """类型"""
    key = fields.TextField()
    """问句"""
    answer_id = fields.IntField()
    """答句ID"""
    require_to_me = fields.BooleanField(default=False)
    """是否需要@"""
    creator_id = fields.TextField()
    """创建者ID"""
    weight = fields.SmallIntField(default=10)
    """权重"""
    create_time = fields.DatetimeField(auto_now_add=True)
    """添加时间"""
    last_ans = fields.TextField()
    """最近回退问句"""
    last_cmd = fields.SmallIntField(default=1)
    """最近操作"""
    update_time = fields.DatetimeField(auto_now_add=True)
    """添加时间"""
    block = fields.BooleanField(default=False)
    """词条是否被停用"""

    class Meta:
        table = "wordbank3"
        table_description = "wordbank3 数据库"

    @staticmethod
    async def match(
        index_type: IndexType,
        index_id: str,
        key: str,
        to_me: bool = False,
    ) -> Optional[WordEntry]:
        """
        :说明: `match`
        > 匹配词库

        :参数:
          * `index_type: IndexType`: 索引类型: IndexType.group 群聊, IndexType.private 私聊
          * `index_id: str`: 索引ID: 群聊ID, 私聊ID
          * `key: str`: 问句

        :可选参数:
          * `to_me: bool = False`: 是否需要@

        :返回:
          - `Optional[WordEntry]`: 如匹配到词条则返回结果
        """
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
        async def _match(index_type: IndexType) -> WordEntry:
            answers: List[Answer] = []
            if wb_list := await WordBank.filter(
                index_type=index_type.value,
                index_id=index_id,
                key=key,
                match_type=MatchType.congruence.value,
                require_to_me=to_me,
            ):
                for wb in wb_list:
                    data = await WordBankData.get(id=wb.answer_id)
                    answers.append(
                        Answer(
                            answer=data.answer,
                            weight=wb.weight,
                            last_cmd=wb.last_cmd,
                            id=wb.id,
                        )
                    )

            if wb_list := await WordBank.filter(
                index_type=index_type.value,
                index_id=index_id,
                match_type=MatchType.include.value,
                require_to_me=to_me,
            ):
                for wb in wb_list:
                    if wb.key in key:
                        data = await WordBankData.get(id=wb.answer_id)
                        answers.append(
                            Answer(
                                answer=data.answer,
                                weight=wb.weight,
                                last_cmd=wb.last_cmd,
                                id=wb.id,
                            )
                        )

            if wb_list := await WordBank.filter(
                index_type=index_type.value,
                index_id=index_id,
                match_type=MatchType.regex.value,
                require_to_me=to_me,
            ):
                for wb in wb_list:
                    try:
                        _wb_key = unescape(wb.key)
                        _key = unescape(key)
                        if bool(re.search(_wb_key, _key, re.S)):
                            data = await WordBankData.get(id=wb.answer_id)
                            answers.append(
                                Answer(
                                    answer=data.answer,
                                    weight=wb.weight,
                                    last_cmd=wb.last_cmd,
                                    id=wb.id,
                                )
                            )
                    except re.error:
                        continue

            we = WordEntry(key=key, answer=answers, require_to_me=to_me)
            return we

        _we = await _match(index_type=index_type)
        _gl_we = await _match(index_type=IndexType._global)
        _we.answer += _gl_we.answer
        return _we if _we.answer else None

    @staticmethod
    async def set(
        index_type: IndexType,
        index_id: str,
        match_type: MatchType,
        key: str,
        answer: str,
        creator_id: str,
        require_to_me: bool = False,
        weight: int = 10,
    ) -> Tuple[int, bool]:
        """
        :说明: `set`
        > 添加词条

        :参数:
          * `index_type: IndexType`: 索引类型: IndexType.group 群聊, IndexType.private 私聊
                IndexType._global 全局
          * `index_id: str`: 索引ID
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
        wb, created = await WordBank.get_or_create(
            index_type=index_type.value,
            index_id=index_id,
            match_type=match_type.value,
            key=key,
            answer_id=ans.id,
            require_to_me=require_to_me,
            creator_id=creator_id,
            last_ans=answer,
            last_cmd=CmdType.add.value,
            weight=weight,
        )
        return wb.id, created

    @staticmethod
    async def keys(index_type: IndexType, index_id: str) -> List[str]:
        """
        :说明: `keys`
        > 获取索引下的所有问句

        :参数:
          * `index_type: IndexType`: 索引类型: IndexType.group 群聊, IndexType.private 私聊
                IndexType._global 全局
          * `index_id: str`: 索引ID

        :返回:
          - `List[str]`: 问句列表
        """
        keys: List[str] = []
        wb_list = await WordBank.filter(
            index_type=index_type.value, index_id=index_id
        ).all()
        for wb in wb_list:
            keys.append(wb.key)
        return keys

    @staticmethod
    async def delete_by_key(
        index_type: IndexType,
        index_id: str,
        key: str,
        match_type: MatchType = MatchType.congruence,
        require_to_me: bool = False,
    ) -> Tuple[List[int], bool]:
        """
        :说明: `delete`
        > 删除指定问答词条 (可以指定 `问句`)

        :参数:
          * `index_type: IndexType`: 索引类型: IndexType.group 群聊, IndexType.private 私聊
                IndexType._global 全局
          * `index_id: str`: 索引ID
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
        if not match:
            return [], False
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
    async def delete_by_key_id(
        index_type: IndexType,
        index_id: str,
        key_id: int,
        match_type: MatchType = MatchType.congruence,
        require_to_me: bool = False,
    ) -> bool:
        """
        :说明: `delete_by_key_id`
        > 删除指定问句ID对应的词条

        :参数:
          * `index_type: IndexType`: 索引类型: IndexType.group 群聊, IndexType.private 私聊
                IndexType._global 全局
          * `index_id: str`: 索引ID
          * `key: str`: 问句

        :可选参数:
          * `match_type: Optional[MatchType] = None`: 匹配类型: MatchType.congruence 全匹配,
                MatchType.include
          * `require_to_me: bool = False`: 是否需要@

        :返回:
          - `bool: 是否删除成功
        """
        key = await WordBank.filter(id=key_id).values()
        for ans in key:
            ans_id = ans["answer_id"]
            await WordBankData.filter(id=ans_id).delete()
        await WordBank.filter(
            index_type=index_type.value,
            index_id=index_id,
            id=key_id,
            match_type=match_type.value,
            require_to_me=require_to_me,
        ).delete()
        return True

    @staticmethod
    async def clear(
        index_id: Optional[str] = None,
        index_type: Optional[IndexType] = None,
        match_type: Optional[MatchType] = None,
    ) -> bool:
        """
        :说明: `clear`
        > 清空词库

        若为参数均为空则清空所有词库

        :可选参数:
          * `index_id: Optional[str] = None`: 索引ID
          * `index_type: IndexType`: 索引类型: IndexType.group 群聊, IndexType.private 私聊
                IndexType._global 全局
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

    @staticmethod
    async def update_by_key(
        index_type: IndexType,
        index_id: str,
        key: str,
        update_index_id: str,
        update_index_type: IndexType = IndexType.group,
        match_type: MatchType = MatchType.congruence,
        update_match_type: MatchType = MatchType.congruence,
        require_to_me: bool = False,
        update_require_to_me: bool = False,
    ) -> bool:
        """
        :说明: `move`
        > 迁移指定问答词条 (可以指定 `问句`)

        :参数:
            * `index_type: IndexType`: 索引类型: IndexType.group 群聊, IndexType.private 私聊
                IndexType._global 全局
            * `index_id: str`: 索引ID
            * `key: str`: 问句

        :可选参数:
            * `update_index_type: IndexType`: 更改索引类型: IndexType.group 群聊, IndexType.private 私聊
                IndexType._global 全局
            * `update_index_id: str`: 更改索引ID(用于转交至群或其他私聊会话)
            * `match_type: Optional[MatchType] = None`: 匹配类型: MatchType.congruence 全匹配,
                MatchType.include 模糊匹配 MatchType.regex 正则匹配
            * `update_match_type: Optional[MatchType] = match_type`: 更改匹配类型: MatchType.congruence 全匹配,
                MatchType.include 模糊匹配 MatchType.regex 正则匹配
            * `require_to_me: bool = False`: 是否需要@
            * `update_require_to_me: bool = require_to_me`: 更改是否需要@

        :返回:
          - bool`: 是否迁移成功
        """
        match = await WordBank.filter(
            index_type=index_type.value,
            index_id=index_id,
            match_type=match_type.value,
            key=key,
            require_to_me=require_to_me,
        )
        if not match:
            return False
        await WordBank.filter(
            index_type=index_type.value,
            index_id=index_id,
            match_type=match_type.value,
            key=key,
            require_to_me=require_to_me,
        ).update(
            index_type=update_index_type.value,
            index_id=update_index_id,
            match_type=update_match_type.value,
            last_cmd=CmdType.move.value,
            update_time=datetime.now(),
            require_to_me=update_require_to_me,
        )

        return True

    @staticmethod
    async def update_by_id(
        index_type: IndexType,
        index_id: str,
        id: int,
        update_index_id: str,
        update_index_type: IndexType = IndexType.group,
        match_type: MatchType = MatchType.congruence,
        update_match_type: MatchType = MatchType.congruence,
        require_to_me: bool = False,
        update_require_to_me: bool = False,
    ) -> bool:
        """
        :说明: `move`
        > 迁移指定问答词条 (可以指定 `问句`)

        :参数:
            * `index_type: IndexType`: 索引类型: IndexType.group 群聊, IndexType.private 私聊
                IndexType._global 全局
            * `index_id: str`: 索引ID
            * `id: int`: 问句id

        :可选参数:
            * `update_index_type: IndexType`: 更改索引类型: IndexType.group 群聊, IndexType.private 私聊
                IndexType._global 全局
            * `update_index_id: str`: 更改索引ID(用于转交至群或其他私聊会话)
            * `match_type: Optional[MatchType] = None`: 匹配类型: MatchType.congruence 全匹配,
                MatchType.include 模糊匹配 MatchType.regex 正则匹配
            * `update_match_type: Optional[MatchType] = match_type`: 更改匹配类型: MatchType.congruence 全匹配,
                MatchType.include 模糊匹配 MatchType.regex 正则匹配
            * `require_to_me: bool = False`: 是否需要@
            * `update_require_to_me: bool = require_to_me`: 更改是否需要@

        :返回:
          - bool`: 是否迁移成功
        """
        match = await WordBank.filter(
            index_type=index_type.value,
            index_id=index_id,
            match_type=match_type.value,
            id=id,
            require_to_me=require_to_me,
        )
        if not match:
            return False
        await WordBank.filter(
            index_type=index_type.value,
            index_id=index_id,
            match_type=match_type.value,
            id=id,
            require_to_me=require_to_me,
        ).update(
            index_type=update_index_type.value,
            index_id=update_index_id,
            match_type=update_match_type.value,
            last_cmd=CmdType.move.value,
            update_time=datetime.now(),
            require_to_me=update_require_to_me,
        )

        return True

    @staticmethod
    async def update_answer(
        answer_id_list: List[int],
        update_answer: str,
    ) -> Tuple[List[int], bool]:
        """
        :说明: `update_answer`
        > 修改指定答句ID对应的答句

        :参数:
          * `answer_id: Union[int, List[int]]`: 答句ID列表
          * `update_answer: str`: 更新答句

        :返回:
          - `Tuple[List[int], bool]`: 已修改的答句ID列表, 是否修改成功
        """
        try:
            for id in answer_id_list:
                for origin_ans in await WordBank.filter(answer_id=id).values():
                    origin_answer: str = origin_ans["answer"]
                await WordBankData.filter(id=id).update(answer=update_answer)
                await WordBank.filter(answer_id=id).update(
                    update_time=datetime.now(),
                    last_key=origin_answer,
                    last_cmd=CmdType.update,
                )
            return answer_id_list, True
        except UnboundLocalError:
            return [], False

    @staticmethod
    async def key_return(index_type: IndexType, index_id: str, key: str) -> List[int]:
        """
        :说明: `keys`
        > 获取索引下的所有问句id

        :参数:
          * `index_type: IndexType`: 索引类型: IndexType.group 群聊, IndexType.private 私聊
                IndexType._global 全局
          * `index_id: str`: 索引ID
          * `key: str`: 问句s

        :返回:
          - `List[int]`: 问句id列表
        """
        ids: List[int] = []
        wb_list = await WordBank.filter(
            index_type=index_type.value, index_id=index_id, key=key
        ).all()
        for wb in wb_list:
            ids.append(wb.id)
        return ids

    @staticmethod
    async def ans_id_return(ans_id: int) -> List[str]:
        keys: List[str] = []
        wb_list = await WordBank.filter(answer_id=ans_id).values()
        for wb in wb_list:
            key = ""
            key += str(wb["id"])
            key += "."
            key += wb["key"]
            keys.append(key)
        return keys

    @staticmethod
    async def datetime_return(ans_id: int) -> List[datetime]:
        keys = []
        wb_list = await WordBank.filter(answer_id=ans_id).values()
        for wb in wb_list:
            keys.append(wb["create_time"])
        return keys

    @staticmethod
    async def datetime_return_all(
        index_type: IndexType, index_id: str
    ) -> Tuple[dict, dict]:
        keys = {}
        id_key_ans = {}
        wb_list = await WordBank.filter(
            index_type=index_type.value, index_id=index_id
        ).all()
        for wb in wb_list:
            print(wb.create_time)
            keys[wb.id] = wb.create_time
            id_key_ans[wb.id] = {
                "key": wb.key,
                "answer_id": wb.answer_id,
                "last_cmd": wb.last_cmd,
            }
        return keys, id_key_ans

    @staticmethod
    async def last_ans_return(
        index_type: IndexType, index_id: str, key: str
    ) -> List[int]:
        """回退最近操作"""
        ids: List[int] = []
        wb_list = await WordBank.filter(
            index_type=index_type.value, index_id=index_id, key=key
        ).all()
        for wb in wb_list:
            await WordBankData.filter(id=wb.answer_id).update(answer=wb["last_key"])  # type: ignore
            await WordBank.filter(id=wb.id).update(
                update_time=datetime.now(), last_key=wb.key, last_cmd=2
            )
            ids.append(wb.answer_id)
        return ids

    @staticmethod
    async def keys_id_return(id: int) -> List[str]:
        keys: List[str] = []
        wb_list = await WordBank.filter(id=id).values()
        for wb in wb_list:
            keys.append(wb["key"])
        return keys

    @staticmethod
    async def keys_id_ans(id: int) -> List[int]:
        ans_id: List[int] = []
        wb_list = await WordBank.filter(id=id).values()
        for wb in wb_list:
            ans_id.append(wb["answer_id"])
        return ans_id
