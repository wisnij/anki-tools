#!/usr/bin/env python3
"""Display any Kanji examples that don't have a corresponding Vocabulary entry."""

from collections import namedtuple
from datetime import datetime, timedelta
import os
import re
import sqlite3

from rich import box
from rich.console import Console
from rich.table import Table

DB_LOCATION = "~/.local/share/Anki2/Jim/collection.anki2"

Example = namedtuple("Example", ["note_id", "example_id", "jp", "en", "date"])


def dict_factory(cursor, row):
    fields = [column[0] for column in cursor.description]
    return {key: value for key, value in zip(fields, row)}


def notetype_id(cur, field_name):
    notetype = cur.execute(f"SELECT * FROM notetypes WHERE name = '{field_name}' COLLATE BINARY");
    return notetype.fetchone()["id"]


def note_fields(cur, notetype_id):
    fields = {}
    for field in cur.execute(f"SELECT * FROM fields WHERE ntid = {notetype_id}"):
        fields[field["ord"]] = field["name"]

    return fields


if __name__ == "__main__":
    db_file = os.path.expanduser(DB_LOCATION)

    db = sqlite3.connect(db_file)
    db.row_factory = dict_factory

    cur = db.cursor()

    kanji_id = notetype_id(cur, "Kanji")
    vocab_id = notetype_id(cur, "Japanese vocab")

    kanji_fields = note_fields(cur, kanji_id)
    vocab_fields = note_fields(cur, vocab_id)

    examples = []
    suffixes = ("]な", "]する")
    count = 0
    for note in cur.execute(f"SELECT * FROM notes WHERE mid = {kanji_id} ORDER BY id"):
        count += 1
        raw = note["flds"].split("\x1f")
        flds = {kanji_fields[n]: raw[n] for n in range(len(kanji_fields))}

        jp_examples = flds["Japanese examples"].split("<br>")
        en_examples = flds["English examples"].split("<br>")
        if len(jp_examples) != len(en_examples):
            print(f"ERROR: examples mismatch\n\t{jp_examples}\n\t{en_examples}")
            continue

        for n in range(len(jp_examples)):
            jp = jp_examples[n].strip()
            jp = jp.replace("*", "")
            jp = re.sub(r"\](な|する)$", "]", jp)
            examples.append(Example(
                jp=jp,
                en=en_examples[n].strip(),
                note_id=count,
                example_id=n + 1,
                date=datetime.fromtimestamp(note["id"]//1000),
            ))

    table = Table("date", "note", "ex#", "Japanese", "English", box=box.SIMPLE)
    for ex in sorted(examples):
        found = cur.execute(f"SELECT * FROM notes WHERE mid = {vocab_id} AND sfld = '{ex.jp}'")
        if not found.fetchone():
            table.add_row(
                str(ex.date), str(ex.note_id), str(ex.example_id), ex.jp, ex.en,
                style="yellow" if datetime.now() - ex.date < timedelta(days=1) else None,
            )

    Console().print(table)
