#!/usr/bin/env python3
"""Display any Kanji examples that don't have a corresponding Vocabulary entry."""

from collections import namedtuple
from datetime import datetime, timedelta
import os
import re
import sys

from anki.collection import Collection
from rich import box
from rich.console import Console
from rich.table import Table

DB_LOCATION = "~/.local/share/Anki2/Jim/collection.anki2"

Example = namedtuple("Example", ["note_id", "example_id", "jp", "en", "date"])


if __name__ == "__main__":
    db_file = os.path.expanduser(DB_LOCATION)
    col = Collection(db_file)

    examples = []
    suffixes = ("]な", "]する")
    count = 0
    for note_id in sorted(col.find_notes("note:Kanji")):
        count += 1
        note = col.get_note(note_id)

        jp_examples = note["Japanese examples"].split("<br>")
        en_examples = note["English examples"].split("<br>")
        if len(jp_examples) != len(en_examples):
            print(
                f"ERROR: examples mismatch on {note['Kanji']} ({note['Meaning']}):\n"
                f"\t{jp_examples}\n"
                f"\t{en_examples}\n",
                file=sys.stderr,
            )
            continue

        for n in range(len(jp_examples)):
            jp = jp_examples[n].strip()
            jp = jp.replace("*", "")
            jp = re.sub(r"\](な|する)$", "]", jp)
            examples.append(
                Example(
                    jp=jp,
                    en=en_examples[n].strip(),
                    note_id=count,
                    example_id=n + 1,
                    date=datetime.fromtimestamp(note.id // 1000),
                )
            )

    last_date = max(ex.date for ex in examples)

    missing_examples = []
    for ex in examples:
        if not col.find_notes(f'note:"Japanese vocab" Japanese:"{ex.jp}"'):
            missing_examples.append(ex)

    table = Table("date", "note", "ex#", "Japanese", "English", box=box.SIMPLE)
    for ex in missing_examples:
        table.add_row(
            str(ex.date),
            str(ex.note_id),
            str(ex.example_id),
            ex.jp,
            ex.en,
            style="yellow" if last_date - ex.date < timedelta(days=1) else None,
        )

    Console().print(table)
