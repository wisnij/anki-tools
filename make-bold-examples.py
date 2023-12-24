#!/usr/bin/env python3
"""Make vocabulary words in examples bold."""

import argparse
from dataclasses import dataclass
import os
import re

from anki.collection import Collection
from rich.console import Console
from rich.highlighter import RegexHighlighter
from rich.theme import Theme
import rich.markup

from util.furigana import furigana_to_kana

DEFAULT_DB_LOCATION = "~/.local/share/Anki2/Jim/collection.anki2"


class BoldHighlighter(RegexHighlighter):
    highlights = [r"(?P<bold><b>.*?</b>)"]


theme = Theme({"bold": "yellow"})
console = Console(highlighter=BoldHighlighter(), theme=theme)


@dataclass
class Stats:
    count: int = 0
    no_examples: int = 0
    already_bold: int = 0
    not_in_examples: int = 0
    update: int = 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--anki-collection",
        default=os.path.expanduser(DEFAULT_DB_LOCATION),
        help="Anki collection sqlite file",
    )
    parser.add_argument(
        "-n",
        "--dry-run",
        action="store_true",
        help="show what would be done without committing changes",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="count",
        default=0,
        help="print more debugging output",
    )
    args = parser.parse_args()

    col = Collection(args.anki_collection)
    stats = Stats()
    updates = []
    for note_id in sorted(col.find_notes('"note:Japanese vocab"')):
        stats.count += 1

        note = col.get_note(note_id)
        orig_jp = note["Japanese"]
        jp = re.sub("^〜 ?", "", orig_jp)

        examples = note["Japanese examples"]
        if not examples:
            stats.no_examples += 1
            if args.verbose:
                console.print(f"[dim white]no examples[/dim white]: {orig_jp}")
            continue

        if "<b>" in examples:
            stats.already_bold += 1
            if args.verbose:
                console.print(f"[yellow]already bold[/yellow]: {orig_jp}")
            continue

        bolded = None
        if jp in examples:
            # strip off any preceding or trailing spaces which might be there to
            # delimit kanji-furigana blocks, as the HTML tag boundry will also
            # do that
            examples = re.sub(f" *({re.escape(jp)}) *", r"<b>\1</b>", examples)
            bolded = "kana" if note["Kana only"] else "kanji"
        else:
            jp_kana = furigana_to_kana(jp)
            if jp_kana in examples:
                examples = re.sub(f" *({re.escape(jp_kana)}) *", r"<b>\1</b>", examples)
                bolded = "furigana"

        if bolded:
            stats.update += 1
            note["Japanese examples"] = examples
            updates.append(note)
            console.print(f"[green]bolded {bolded}[/green]: {orig_jp}")
            if args.verbose >= 2:
                for line in examples.split("<br>"):
                    console.print(f"    {line}")
        else:
            stats.not_in_examples += 1
            console.print(f"[red]not in examples[/red]: {orig_jp}")

    print()
    print(f"count:           {stats.count}")
    print(f"no examples:     {stats.no_examples}")
    print(f"not in examples: {stats.not_in_examples}")
    print(f"already bold:    {stats.already_bold}")
    print(f"to update:       {stats.update}")

    if updates and not args.dry_run:
        print()
        print(f"updating {len(updates)} notes")
        col.update_notes(updates)
        col.save()
