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
        assert res is True


@pytest.mark.asyncio
async def test_word_bank_match(app: App, db):

    from nonebot_plugin_word_bank3.models.word_bank import WordBank
    from nonebot_plugin_word_bank3.models.typing_models import (
        Answer,
        IndexType,
        MatchType,
        WordEntry,
    )

    async with app.test_server():
        # 添加一条数据
        res = await WordBank.set(
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
            match_type=MatchType.congruence,
            key="hello_match_test",
            to_me=False,
        )

        assert isinstance(res, WordEntry)
        assert res.key == "hello_match_test"
        assert isinstance(res.answer[0], Answer)
        assert res.answer[0].answer == "world_match_test"
