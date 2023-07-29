# adapted from https://github.com/birchill/normal-jp/tree/v1.4.0
NON_MORAIC_KANA = {
    "ぁ", "ぃ", "ぅ", "ぇ", "ぉ", "ゃ", "ゅ", "ょ", "ゎ",
    "ァ", "ィ", "ゥ", "ェ", "ォ", "ャ", "ュ", "ョ", "ヮ",
}  # fmt: skip


def mora_split(text: str) -> list[str]:
    """Split a string of kana into its constituent morae."""
    current = ""
    morae = []

    for i, c in enumerate(text):
        if i == 0 or c in NON_MORAIC_KANA:
            current += c
        else:
            morae.append(current)
            current = c

    if current:
        morae.append(current)

    return morae


def mora_len(text: str) -> int:
    """Return the number of morae in `text`."""
    return len([c for i, c in enumerate(text) if i == 0 or c not in NON_MORAIC_KANA])


def mora_substr(text: str, start: int, end: int | None = None) -> str:
    """Extract a substring of `text` by morae rather than characters."""
    return "".join(mora_split(text)[start:end])


def kana_to_hiragana(text: str) -> str:
    """Convert all kana in `text` to hiragana."""
    result = ""
    for char in text:
        c = ord(char)
        if 0x30A1 <= c <= 0x30F6 or c == 0x30FD or c == 0x30FE:
            c -= 0x60
        result = result + chr(c)
    return result


if __name__ == "__main__":
    for s in ["しゃけ", "とうきょう", "いっぱい", "トウキョウ", "ねっちゅうしょう"]:
        print(f"mora_len({s}) = {mora_len(s)}")
    print()

    for s in ["しゃけ", "とうきょう", "いっぱい", "トウキョウ", "ねっちゅうしょう"]:
        print(f"mora_split({s}) = {mora_split(s)}")
    print()

    for s in ["ガーデン", "ヴヵヶ"]:
        print(f"kana_to_hiragana({s}) -> {kana_to_hiragana(s)!r}")
    print()

    for text, start, end in [
        ("しゃけ", 0, 1),
        ("しゃけ", -2, 1),
        ("しゃけ", 0, 2),
        ("しゃけ", 0, 3),
        ("しゃけ", 0, None),
        ("しゃけ", -2, None),
        ("しゃけ", 1, None),
        ("しゃけ", 1, 5),
        ("しゃけ", 1, 1),
        ("しゃけ", 0, 0),
        ("しゃけ", 2, None),
        ("しゃ", 1, None),
        ("しゃ", 0, 1),
    ]:
        print(f"mora_substr({text},{start},{end}) = {mora_substr(text,start,end)!r}")
