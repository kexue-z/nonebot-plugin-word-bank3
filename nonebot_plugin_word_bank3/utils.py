import re


def regex_match(regex: str, text: str) -> bool:
    try:
        return bool(re.search(regex, text, re.S))
    except re.error:
        return False
