import pytest
from nonebug import App


@pytest.mark.asyncio
async def test_word_bank_set(app: App, db):
    """
    测试添加词条 （不知道怎么测）
    """
    from nonebot_plugin_word_bank3 import wb_set_cmd

    from .utils import make_fake_event, make_fake_message

    Message = make_fake_message()

    async with app.test_matcher(wb_set_cmd) as ctx:
        bot = ctx.create_bot()

        msg = Message("问 我是谁 答 我是谁")
        event = make_fake_event(_message=msg, _to_me=True)()

        ctx.receive_event(bot, event)
        ctx.should_call_send(event, "我记住了~", True)
        ctx.should_finished()
