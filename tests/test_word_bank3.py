import pytest
from nonebug import App


@pytest.mark.asyncio
async def test_word_bank_set(app: App, db):
    from nonebot_plugin_word_bank3.models.word_bank import WordBank
    from nonebot_plugin_word_bank3.models.typing_models import IndexType, MatchType

    async with app.test_server():
        res = await WordBank.set(
            index_type=IndexType.group,
            index_id=1,
            match_type=MatchType.congruence,
            key="hello_set_test",
            answer="world_set_test",
            creator_id=1,
            require_to_me=False,
            weight=10,
        )
        assert res


@pytest.mark.asyncio
async def test_word_bank_congruence_match(app: App, db):

    from nonebot_plugin_word_bank3.models.word_bank import WordBank
    from nonebot_plugin_word_bank3.models.typing_models import (
        Answer,
        IndexType,
        MatchType,
        WordEntry,
    )

    async with app.test_server():
        # 添加 全匹配词条
        _, res = await WordBank.set(
            index_type=IndexType.group,
            index_id=1,
            match_type=MatchType.congruence,
            key="hello_match_test",
            answer="world_match_test",
            creator_id=1,
            require_to_me=False,
            weight=10,
        )
        assert res is True

        # 查询
        res = await WordBank.match(
            index_type=IndexType.group,
            index_id=1,
            key="hello_match_test",
            to_me=False,
        )

        assert isinstance(res, WordEntry)
        assert res.key == "hello_match_test"
        assert isinstance(res.answer[0], Answer)
        assert res.answer[0].answer == "world_match_test"

        # 查询无结果
        res = await WordBank.match(
            index_type=IndexType.group,
            index_id=1,
            key="test",
            to_me=False,
        )
        assert not res


@pytest.mark.asyncio
async def test_word_bank_include_match(app: App, db):

    from nonebot_plugin_word_bank3.models.word_bank import WordBank
    from nonebot_plugin_word_bank3.models.typing_models import (
        Answer,
        IndexType,
        MatchType,
        WordEntry,
    )

    async with app.test_server():
        # 添加 模糊匹配词条
        _, res = await WordBank.set(
            index_type=IndexType.group,
            index_id=1,
            match_type=MatchType.include,
            key="include",
            answer="world_match_test_include",
            creator_id=1,
            require_to_me=False,
            weight=10,
        )
        assert res is True

        # 查询
        res = await WordBank.match(
            index_type=IndexType.group,
            index_id=1,
            key="test_include",
            to_me=False,
        )

        assert isinstance(res, WordEntry)
        assert res.key == "test_include"
        assert isinstance(res.answer[0], Answer)
        assert res.answer[0].answer == "world_match_test_include"

        # 查询无结果
        res = await WordBank.match(
            index_type=IndexType.group,
            index_id=1,
            key="wtf",
            to_me=False,
        )
        assert not res


@pytest.mark.asyncio
async def test_word_bank_regex_match(app: App, db):

    from nonebot_plugin_word_bank3.models.word_bank import WordBank
    from nonebot_plugin_word_bank3.models.typing_models import (
        Answer,
        IndexType,
        MatchType,
        WordEntry,
    )

    async with app.test_server():
        # 添加 模糊正则词条
        _, res = await WordBank.set(
            index_type=IndexType.group,
            index_id=1,
            match_type=MatchType.regex,
            key="[你|我|他]好",
            answer="world_match_test_regex",
            creator_id=1,
            require_to_me=False,
            weight=10,
        )
        assert res is True

        # 查询
        res = await WordBank.match(
            index_type=IndexType.group,
            index_id=1,
            key="你好",
            to_me=False,
        )

        assert isinstance(res, WordEntry)
        assert res.key == "你好"
        assert isinstance(res.answer[0], Answer)
        assert res.answer[0].answer == "world_match_test_regex"

        # 查询无结果
        res = await WordBank.match(
            index_type=IndexType.group,
            index_id=1,
            key="谁好",
            to_me=False,
        )
        assert not res


@pytest.mark.asyncio
async def test_word_bank_gl__match(app: App, db):

    from nonebot_plugin_word_bank3.models.word_bank import WordBank
    from nonebot_plugin_word_bank3.models.typing_models import (
        Answer,
        IndexType,
        MatchType,
        WordEntry,
    )

    async with app.test_server():
        # 添加 全局 全匹配词条
        _, res = await WordBank.set(
            index_type=IndexType._global,
            index_id=1,
            match_type=MatchType.congruence,
            key="hello_match_test",
            answer="world_match_test",
            creator_id=1,
            require_to_me=False,
            weight=10,
        )
        assert res is True

        # 查询
        res = await WordBank.match(
            index_type=IndexType._global,
            index_id=1,
            key="hello_match_test",
            to_me=False,
        )

        assert isinstance(res, WordEntry)
        assert res.key == "hello_match_test"
        assert isinstance(res.answer[0], Answer)
        assert res.answer[0].answer == "world_match_test"

        # 查询无结果
        res = await WordBank.match(
            index_type=IndexType._global,
            index_id=1,
            key="test",
            to_me=False,
        )
        assert not res


@pytest.mark.asyncio
async def test_word_bank_gl_include_match(app: App, db):

    from nonebot_plugin_word_bank3.models.word_bank import WordBank
    from nonebot_plugin_word_bank3.models.typing_models import (
        Answer,
        IndexType,
        MatchType,
        WordEntry,
    )

    async with app.test_server():
        # 添加 全局 模糊匹配词条
        _, res = await WordBank.set(
            index_type=IndexType._global,
            index_id=1,
            match_type=MatchType.include,
            key="include",
            answer="world_match_test_include",
            creator_id=1,
            require_to_me=False,
            weight=10,
        )
        assert res is True

        # 查询
        res = await WordBank.match(
            index_type=IndexType._global,
            index_id=1,
            key="test_include",
            to_me=False,
        )

        assert isinstance(res, WordEntry)
        assert res.key == "test_include"
        assert isinstance(res.answer[0], Answer)
        assert res.answer[0].answer == "world_match_test_include"

        # 查询无结果
        res = await WordBank.match(
            index_type=IndexType._global,
            index_id=1,
            key="wtf",
            to_me=False,
        )
        assert not res


@pytest.mark.asyncio
async def test_word_bank_gl_regex_match(app: App, db):

    from nonebot_plugin_word_bank3.models.word_bank import WordBank
    from nonebot_plugin_word_bank3.models.typing_models import (
        Answer,
        IndexType,
        MatchType,
        WordEntry,
    )

    async with app.test_server():
        # 添加 模糊正则词条
        _, res = await WordBank.set(
            index_type=IndexType._global,
            index_id=1,
            match_type=MatchType.regex,
            key="[你|我|他]好",
            answer="world_match_test_regex",
            creator_id=1,
            require_to_me=False,
            weight=10,
        )
        assert res is True

        # 查询
        res = await WordBank.match(
            index_type=IndexType._global,
            index_id=1,
            key="你好",
            to_me=False,
        )

        assert isinstance(res, WordEntry)
        assert res.key == "你好"
        assert isinstance(res.answer[0], Answer)
        assert res.answer[0].answer == "world_match_test_regex"

        # 查询无结果
        res = await WordBank.match(
            index_type=IndexType._global,
            index_id=1,
            key="谁好",
            to_me=False,
        )
        assert not res


@pytest.mark.asyncio
async def test_word_bank_delete_by_key(app: App, db):

    from typing import List

    from nonebot_plugin_word_bank3.models.word_bank import WordBank
    from nonebot_plugin_word_bank3.models.typing_models import IndexType, MatchType

    async with app.test_server():
        # 添加数据
        _, res = await WordBank.set(
            index_type=IndexType.group,
            index_id=114514,
            match_type=MatchType.congruence,
            key="hello_delete_test",
            answer="world_delete_test",
            creator_id=1919810,
            require_to_me=False,
            weight=10,
        )
        assert res

        # 删除 指定词条
        ans_id_list, res = await WordBank.delete_by_key(
            index_type=IndexType.group, index_id=114514, key="hello_delete_test"
        )
        assert isinstance(ans_id_list, List)
        assert res

        # 删除不存在词条
        ans_id_list, res = await WordBank.delete_by_key(
            index_type=IndexType.group, index_id=114514, key="hello_delete_test"
        )
        assert not res


@pytest.mark.asyncio
async def test_word_bank_clear_all(app: App, db):
    from nonebot_plugin_word_bank3.models.word_bank import WordBank
    from nonebot_plugin_word_bank3.models.typing_models import IndexType, MatchType

    async with app.test_server():
        # 添加数据
        for i in range(100):
            _, res = await WordBank.set(
                index_type=IndexType.group,
                index_id=114514 if i >= 50 else 114,
                match_type=MatchType.congruence if i >= 25 else MatchType.include,
                key=f"hello_clear_all_test_{i}",
                answer="hello_clear_all_test_ans_{i}",
                creator_id=1919810,
                require_to_me=False,
                weight=10,
            )
            assert res

        # 清空部分数据
        assert await WordBank.clear(
            index_id=114,
            index_type=IndexType.group,
            match_type=MatchType.include,
        )

        assert await WordBank.clear(
            index_id=114,
            index_type=IndexType.group,
        )

        # 清空所有数据
        assert await WordBank.clear()
