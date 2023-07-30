#!/usr/bin/env python3
"""Check Anki deck for common mistakes."""

import os
import re
import sys

from anki.collection import Collection

DB_LOCATION = "~/.local/share/Anki2/Jim/collection.anki2"

HIRAGANA_RE = re.compile(r"[\u3040-\u309F]")
KATAKANA_RE = re.compile(r"[\u30A0-\u30FF\u31F0-\u31FF]")
KANJI_RE = re.compile(r"[\u3400-\u4DBF\u4E00-\u9FFF\uF900-\uFAFF]")
SPACES = (" ", "&nbsp;")


if __name__ == "__main__":
    db_file = os.path.expanduser(DB_LOCATION)
    col = Collection(db_file)

    # validate kanji
    kanji_count = 0
    kanji_errors = 0
    for note_id in sorted(col.find_notes("note:Kanji")):
        kanji_count += 1

        note = col.get_note(note_id)
        kanji = note["Kanji"]
        en = note["Meaning"]
        display = f"{kanji} ({en})"

        error = False

        # missing required fields
        missing = list(
            f
            for f in {"Kanji", "Meaning", "Japanese examples", "English examples"}
            if not note[f]
        )
        if missing:
            error = True
            for field in missing:
                print(f"{display}: '{field}' missing")

        # missing readings
        if not note["Kun-yomi"] and not note["On-yomi"]:
            error = True
            print(f"{display}: missing both Kun-yomi and On-yomi")

        # didn't switch on-yomi input to katakana
        on_yomi = note["On-yomi"]
        if HIRAGANA_RE.search(on_yomi):
            error = True
            print(f"{display}: hiragana in On-yomi: {on_yomi!r}")

        # leading/trailing spaces
        if kanji.startswith(SPACES) or kanji.endswith(SPACES):
            error = True
            print(f"{display}: leading/trailing space: {kanji!r}")

        # Japanese examples with trailing spaces
        example_lines_ws = list(
            e for e in note["Japanese examples"].split("<br>") if e.endswith(SPACES)
        )
        if example_lines_ws:
            error = True
            for line in example_lines_ws:
                print(f"{display}: trailing space in example: {line!r}")

        # kanji without furigana
        no_furigana = list(
            f
            for f in {"Japanese examples", "Notes"}
            if note[f] and KANJI_RE.search(note[f]) and "[" not in note[f]
        )
        if no_furigana:
            error = True
            for field in no_furigana:
                print(f"{display}: no furigana in {field}: {note[field]!r}")

        # parts without radical
        parts = note["Parts"]
        if parts and "<b>" not in parts:
            error = True
            print(f"{display}: no radical indicated in {parts!r}")

        if error:
            kanji_errors += 1

    print(f"Kanji: {kanji_count} notes, {kanji_errors} error(s)\n")

    # validate vocabulary
    vocab_count = 0
    vocab_errors = 0
    for note_id in sorted(col.find_notes('"note:Japanese vocab"')):
        vocab_count += 1

        note = col.get_note(note_id)
        jp = note["Japanese"]
        en = note["English"]
        display = f"{jp} ({en.replace('<br>', ' ')})"

        error = False

        # missing required fields
        missing = list(
            f for f in {"Japanese", "English", "Part of speech"} if not note[f]
        )
        if missing:
            error = True
            for field in missing:
                print(f"{display}: '{field}' missing")

        # leading/trailing spaces
        if jp.startswith(SPACES) or jp.endswith(SPACES):
            error = True
            print(f"{display}: leading/trailing space: {jp!r}")

        # kanji without furigana
        no_furigana = list(
            f
            for f in {"Japanese", "Japanese examples", "Notes"}
            if note[f] and KANJI_RE.search(note[f]) and "[" not in note[f]
        )
        if no_furigana:
            error = True
            for field in no_furigana:
                print(f"{display}: no furigana in {field}: {note[field]!r}")

        # Kana-only flag
        kana_only = note["Kana only"]
        if kana_only and "[" in jp:
            error = True
            print(f'{display}: marked "Kana only" but furigana in {jp!r}')
        if not kana_only and "[" not in jp:
            error = True
            print(f'{display}: not marked "Kana only" but no furigana in {jp!r}')

        if error:
            vocab_errors += 1

    print(f"Vocabulary: {vocab_count} notes, {vocab_errors} error(s)\n")

    sys.exit(1 if kanji_errors or vocab_errors else 0)
