from typing import Set
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

    nonebot.load_plugin("nonebot_plugin_word_bank3")

    import nonebot_plugin_word_bank3

    return App(monkeypatch)


@pytest.fixture
def load_plugins(nonebug_init: None) -> Set["Plugin"]:
    import nonebot  # 这里的导入必须在函数内

    # 加载插件
    return nonebot.load_plugins("awesome_bot/plugins")


@pytest.fixture
async def db():
    from tortoise import Tortoise

    await Tortoise.init(
        db_url="sqlite://db.sqlite3",
        modules={
            "models": [
                "nonebot_plugin_word_bank3.models.word_bank",
                "nonebot_plugin_word_bank3.models.word_bank_data",
            ]
        },
    )
    await Tortoise.generate_schemas()
