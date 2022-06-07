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
async def db():
    from os import remove

    yield

    remove("db.sqlite3")
