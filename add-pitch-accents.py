#!/usr/bin/env python3
"""Inject pitch-accent information into vocabulary cards.
"""

import argparse
from dataclasses import dataclass
import json
import os
from pathlib import Path

from anki.collection import Collection
from rich.console import Console
from rich.syntax import Syntax

from util.furigana import furigana_to_kanji, furigana_to_kana
from util.mora import mora_len, mora_substr

DEFAULT_ACCENTS_FILE = Path(__file__).parent / "accents.json"
DEFAULT_DB_LOCATION = "~/.local/share/Anki2/Jim/collection.anki2"

console = Console(highlight=False)


@dataclass
class Stats:
    same: int = 0
    different: int = 0
    unknown: int = 0
    update: int = 0


def get_accent_pos(accent_data: dict, kanji: str, kana: str) -> int | None:
    if kanji != kana:
        # kanji with furigana; only look up readings specific to that kanji
        kanji_accents = accent_data.get(kanji)
        if kanji_accents:
            return kanji_accents.get(kana)
    else:
        # just kana
        return accent_data.get(kana)


def make_span(css_class: str, content: str) -> str:
    return f'<span class="{css_class}">{content}</span>'


def make_accent_span(accent_data: dict, furigana: str) -> str | None:
    kanji = furigana_to_kanji(furigana)
    kana = furigana_to_kana(furigana)
    if not kana:
        return None

    accent_pos = get_accent_pos(accent_data, kanji, kana)
    if accent_pos is None:
        return None

    num_morae = mora_len(kana)
    if accent_pos == 0:
        # heiban (LHHHHH)
        span = make_span("l-h" if num_morae > 1 else "h", mora_substr(kana, 0, 1))
        if num_morae > 1:
            span += make_span("h", mora_substr(kana, 1))
    elif accent_pos == 1:
        # atamadaka (HLLLLL)
        span = make_span("h-l", mora_substr(kana, 0, 1))
        if num_morae > 1:
            span += make_span("l", mora_substr(kana, 1))
    else:
        # nakadaka (LHHHHL) or odaka (LHHHH)
        span = make_span("l-h", mora_substr(kana, 0, 1))
        span += make_span("h-l", mora_substr(kana, 1, accent_pos))
        if accent_pos < num_morae:
            span += make_span("l", mora_substr(kana, accent_pos))

    return span


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--accents-file",
        default=DEFAULT_ACCENTS_FILE,
        help="pitch accents data file",
    )
    parser.add_argument(
        "--anki-collection",
        default=os.path.expanduser(DEFAULT_DB_LOCATION),
        help="Anki collection sqlite file",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="count",
        default=0,
        help="print more debugging output",
    )
    args = parser.parse_args()

    with open(args.accents_file) as accents_fh:
        accent_data = json.load(accents_fh)

    col = Collection(args.anki_collection)
    stats = Stats()
    updates = []
    for note_id in sorted(col.find_notes('"note:Japanese vocab"')):
        note = col.get_note(note_id)
        jp = note["Japanese"]
        new_accent = make_accent_span(accent_data, jp)
        if not new_accent:
            stats.unknown += 1
            if args.verbose:
                console.print(f"[yellow]unknown[/]: {jp!r}")
            continue

        current_accent = note["Pitch accent"]
        if not current_accent:
            stats.update += 1
            console.print(f"[green]new[/]: {jp} = [#ffffff]{new_accent}[/]")
            note["Pitch accent"] = new_accent
            updates.append(note)
        elif current_accent != new_accent:
            stats.different += 1
            console.print(
                f"[bold red]WARNING[/]: {jp}: accent difference\n"
                f"\tcurrent: [#ff0000]{current_accent!r}[/]\n"
                f"\tnew:     [#00ffff]{new_accent!r}[/]"
            )
        else:
            stats.same += 1
            if args.verbose >= 2:
                console.print(f"[dim white]same[/]: {current_accent!r}")

    print()
    print(f"same:      {stats.same}")
    print(f"unknown:   {stats.unknown}")
    print(f"different: {stats.different}")
    print(f"to update: {stats.update}")

    if updates:
        print()
        print(f"updating {len(updates)} notes")
        col.update_notes(updates)
        col.save()
