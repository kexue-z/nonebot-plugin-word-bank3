from pathlib import Path

import pytest
from nonebug.app import App
from nonebot.plugin import Plugin


@pytest.fixture
async def app(
    nonebug_init: None,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> App:
    import nonebot
    from nonebot.adapters.onebot.v11 import Adapter as ONEBOT_V11_Adapter

    driver = nonebot.get_driver()
    driver.register_adapter(ONEBOT_V11_Adapter)
    nonebot.load_plugin("nonebot_plugin_word_bank3")

    config = driver.config

    import nonebot_plugin_word_bank3

    return App(monkeypatch)


@pytest.fixture
async def db():
    from os import remove

    yield

    remove("db.sqlite3")
