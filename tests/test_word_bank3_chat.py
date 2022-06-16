import pytest
from nonebug import App


@pytest.mark.asyncio
async def test_word_bank_set(app: App, db):
    """
    测试添加词条 （不知道怎么测）
    """
    import nonebot
    from nonebot_plugin_word_bank3 import wb_set_cmd
    from nonebot.adapters.onebot.v11 import Bot, Adapter, Message
    from nonebot.adapters.onebot.v11.event import Sender, PrivateMessageEvent

    driver = nonebot.get_driver()

    async with app.test_matcher(wb_set_cmd) as ctx:
        adapter = ctx.create_adapter(base=Adapter)
        bot = ctx.create_bot(base=Bot, adapter=adapter)

        event = PrivateMessageEvent(
            time=0,
            self_id=0,
            post_type="message",
            sub_type="friend",
            user_id=123,
            message_type="private",
            message_id=0,
            message=Message("问1答114514"),
            raw_message="问1答114514",
            font=0,
            sender=Sender(),
        )
        ctx.receive_event(bot, event)
        ctx.should_call_send(event, "我记住了~", True)
