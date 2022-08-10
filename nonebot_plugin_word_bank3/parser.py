# from nonebot.rule import ArgumentParser
from argparse import ArgumentParser

wb_parser = ArgumentParser("wb", description="wordbank")

wb_subparsers = wb_parser.add_subparsers(title="子命令")


# 添加词条
wb_add_parser = wb_subparsers.add_parser(
    "add", aliases="a", help="添加词条", description="添加词条"
)

qa_group = wb_add_parser.add_argument_group(
    title="问答",
    description="问答组,必须按照格式填入. 如果问题或回答中包含空白字符（空格, 换行等）, 应该将对应的部分用引号包裹起来",
)
qa_group.add_argument("-q", "--question", nargs="*", help="问题")
qa_group.add_argument("-a", "--answer", nargs="*", help="回答")

# 备选 1
# match_group = wb_add_parser.add_mutually_exclusive_group()
# match_group.add_argument("-s", "--strict", action="store_true", help="使用全匹配")
# match_group.add_argument("-r", "--regex", action="store_true", help="使用正则匹配")
# match_group.add_argument("-f", "--fuzzy", action="store_true", help="使用模糊匹配")
# 备选 2
wb_add_parser.add_argument(
    "-t",
    "--type",
    type=str,
    choices=("strict", "fuzzy", "regex"),
    help="匹配方式(全匹配, 模糊匹配, 正则匹配)",
    dest="match_type",
    default="strict",
)

wb_add_parser.add_argument("-g", action="store_true", help="使用全局匹配", dest="global")
wb_add_parser.add_argument(
    "-P",
    help="问答触发概率（默认1.0)",
    type=float,
    default=1.0,
    dest="probability",
)
wb_add_parser.add_argument(
    "-p",
    help="答句触发概率（默认1.0)",
    type=float,
    default=1.0,
    dest="probability",
)


# 搜索问答
wb_search_parser = wb_subparsers.add_parser(
    "search",
    aliases="s",
    help="搜索问答",
    description="搜索问答, 如果只搜索特定问题的所有回答, 回答可以为空. 如果只搜索特定回答的所有问题, 问题用 ~ 占位",
)

wb_search_parser.add_argument("question", nargs="+", help="问题")
wb_search_parser.add_argument("answer", nargs="+", help="回答")


# 删除/禁用词条
wb_del_parser = wb_subparsers.add_parser(
    "delete", aliases="d", help="删除/禁用词条", description="删除/禁用词条"
)

wb_del_parser.add_argument("id", nargs="+", help="词条id, 多个以空格隔开")
wb_del_parser.add_argument("-f", help="彻底删除词条", action="store_true")


# 清空词库
wb_clear_parser = wb_subparsers.add_parser(
    "clear", aliases="c", help="清空词库", description="清空词库"
)

clear_group = wb_clear_parser.add_mutually_exclusive_group()
clear_group.add_argument("-ffff", help="清空所有对话中所有词库（超管）", action="store_true")
clear_group.add_argument("-fff", help="清空所有对话中指定词库（超管）", action="store_true")
clear_group.add_argument("-ff", help="清空对话中所有词库", action="store_true")
clear_group.add_argument("-f", help="清空对话中指定词库", action="store_true")

clear_id_group = wb_clear_parser.add_mutually_exclusive_group()
clear_id_group.add_argument("-u", "--user", help="指定用户的词库", nargs="*")
clear_id_group.add_argument("-g", "--group", help="指定群聊的词库", nargs="*")
wb_clear_parser.add_argument(
    "-t",
    "--type",
    type=str,
    choices=("strict", "fuzzy", "regex"),
    help="匹配方式(全匹配, 模糊匹配, 正则匹配)",
    dest="match_type",
    default="strict",
)

if __name__ == "__main__":
    wb_parser.print_help()
    print("=" * 30)
    wb_add_parser.print_help()
    print("=" * 30)
    wb_search_parser.print_help()
    print("=" * 30)
    wb_del_parser.print_help()
    print("=" * 30)
    wb_clear_parser.print_help()
