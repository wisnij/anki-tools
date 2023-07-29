#!/usr/bin/env python3
"""Check Anki deck for common mistakes."""

import os
import re
import sqlite3
import sys

DB_LOCATION = "~/.local/share/Anki2/Jim/collection.anki2"

HIRAGANA_RE = re.compile(r"[\u3040-\u309F]")
KATAKANA_RE = re.compile(r"[\u30A0-\u30FF\u31F0-\u31FF]")
KANJI_RE = re.compile(r"[\u3400-\u4DBF\u4E00-\u9FFF\uF900-\uFAFF]")
SPACES = (" ", "&nbsp;")


def dict_factory(cursor, row):
    fields = [column[0] for column in cursor.description]
    return {key: value for key, value in zip(fields, row)}


def notetype_id(cur, field_name):
    notetype = cur.execute(
        f"SELECT * FROM notetypes WHERE name = '{field_name}' COLLATE BINARY"
    )
    return notetype.fetchone()["id"]


def note_fields(cur, notetype_id):
    fields = {}
    for field in cur.execute(f"SELECT * FROM fields WHERE ntid = {notetype_id}"):
        fields[field["ord"]] = field["name"]

    return fields


def fields_dict(note, field_names):
    raw_fields = note["flds"].split("\x1f")
    return {field_names[n]: raw_fields[n] for n in range(len(field_names))}


if __name__ == "__main__":
    db_file = os.path.expanduser(DB_LOCATION)
    db = sqlite3.connect(db_file)
    db.row_factory = dict_factory

    cur = db.cursor()

    # validate kanji
    kanji_id = notetype_id(cur, "Kanji")
    kanji_fields = note_fields(cur, kanji_id)
    kanji_count = 0
    kanji_errors = 0
    for note in cur.execute(f"SELECT * FROM notes WHERE mid = {kanji_id}"):
        kanji_count += 1
        fields = fields_dict(note, kanji_fields)
        kanji = fields["Kanji"]
        en = fields["Meaning"]
        display = f"{kanji} ({en})"

        error = False

        # missing required fields
        missing = list(
            f
            for f in {"Kanji", "Meaning", "Japanese examples", "English examples"}
            if not fields[f]
        )
        if missing:
            error = True
            for field in missing:
                print(f"{display}: '{field}' missing")

        # missing readings
        if not fields["Kun-yomi"] and not fields["On-yomi"]:
            error = True
            print(f"{display}: missing both Kun-yomi and On-yomi")

        # didn't switch on-yomi input to katakana
        on_yomi = fields["On-yomi"]
        if HIRAGANA_RE.search(on_yomi):
            error = True
            print(f"{display}: hiragana in On-yomi: {on_yomi!r}")

        # leading/trailing spaces
        if kanji.startswith(SPACES) or kanji.endswith(SPACES):
            error = True
            print(f"{display}: leading/trailing space: {kanji!r}")

        # Japanese examples with trailing spaces
        example_lines_ws = list(
            e for e in fields["Japanese examples"].split("<br>") if e.endswith(SPACES)
        )
        if example_lines_ws:
            error = True
            for line in example_lines_ws:
                print(f"{display}: trailing space in example: {line!r}")

        # kanji without furigana
        no_furigana = list(
            f
            for f in {"Japanese examples", "Notes"}
            if fields[f] and KANJI_RE.search(fields[f]) and "[" not in fields[f]
        )
        if no_furigana:
            error = True
            for field in no_furigana:
                print(f"{display}: no furigana in {field}: {fields[field]!r}")

        # parts without radical
        parts = fields["Parts"]
        if parts and "<b>" not in parts:
            error = True
            print(f"{display}: no radical indicated in {parts!r}")

        if error:
            kanji_errors += 1

    print(f"Kanji: {kanji_count} notes, {kanji_errors} error(s)\n")

    # validate vocabulary
    vocab_id = notetype_id(cur, "Japanese vocab")
    vocab_fields = note_fields(cur, vocab_id)

    vocab_count = 0
    vocab_errors = 0
    for note in cur.execute(f"SELECT * FROM notes WHERE mid = {vocab_id}"):
        vocab_count += 1
        fields = fields_dict(note, vocab_fields)
        jp = fields["Japanese"]
        en = fields["English"]
        display = f"{jp} ({en.replace('<br>', ' ')})"

        error = False

        # missing required fields
        missing = list(
            f for f in {"Japanese", "English", "Part of speech"} if not fields[f]
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
            if fields[f] and KANJI_RE.search(fields[f]) and "[" not in fields[f]
        )
        if no_furigana:
            error = True
            for field in no_furigana:
                print(f"{display}: no furigana in {field}: {fields[field]!r}")

        # Kana-only flag
        kana_only = fields["Kana only"]
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
