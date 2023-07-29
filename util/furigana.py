import re

HIRAGANA_RE = re.compile(r"[\u3040-\u309F]")
KATAKANA_RE = re.compile(r"[\u30A0-\u30FF\u31F0-\u31FF]")
KANJI_RE = re.compile(r"[\u3400-\u4DBF\u4E00-\u9FFF\uF900-\uFAFF]")

# this doesn't use the same kanji range as above because the "kanji" here might
# be not literally be kanji (e.g. fullwidth numerals or other symbols)
FURIGANA_RE = re.compile(r" ?(?P<kanji>[^ >]+?)\[(?P<kana>.+?)\]")


def furigana_to_kanji(furigana: str) -> str:
    return FURIGANA_RE.sub(r"\g<kanji>", furigana)


def furigana_to_kana(furigana: str) -> str:
    return FURIGANA_RE.sub(r"\g<kana>", furigana)
