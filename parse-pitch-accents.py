#!/usr/bin/env python3
"""Parse the word data file from 10ten-ja-reader and extract just the
pitch-accent information to inject into my cards.  This part is semi-expensive
and the data isn't updated too often, so I can do it once and then cache the
results for later.
"""

import argparse
from collections import defaultdict
import json
import os
from pprint import pprint
import sys

DEFAULT_WORDS_FILE = "~/code/3rd-party/10ten-ja-reader/data/words.ljson"


def bitfield_to_idx(bitfield: int) -> list[int]:
    return list(n for n in range(0, 16) if bitfield & 2**n)


def parse_app(app: int | None) -> list[int] | bool:
    if app is None:
        # "If the field is absent, it means the reading applies to all of the kanji entries"
        return True
    elif app == 0:
        # "0 means it applies to none of them"
        return []
    else:
        return bitfield_to_idx(app)


def parse_words(words_file: str) -> list[dict, dict]:
    accents = defaultdict(dict)

    reading_conflicts = set()
    with open(words_file) as words_fh:
        for i, line_json in enumerate(words_fh):
            line_num = i + 1
            line = json.loads(line_json)
            # print(f"\n{line_num}: {line!r}")

            entry_kanji = line.get("k")
            entry_readings = line.get("r")
            entry_readings_meta = line.get("rm")
            if not (entry_readings and entry_readings_meta):
                continue

            apps = {}
            reading_accents = {}
            for i, reading in enumerate(entry_readings):
                if i >= len(entry_readings_meta):
                    break

                meta = entry_readings_meta[i]
                if not isinstance(meta, dict):
                    continue

                accent = meta.get("a")
                if isinstance(accent, int):
                    reading_accents[reading] = accent
                elif isinstance(accent, list):
                    reading_accents[reading] = accent[0]["i"]

                apps[reading] = parse_app(meta.get("app"))

            if not reading_accents:
                continue

            if entry_kanji:
                # print(f"kanji: {entry_kanji!r}\n  {reading_accents!r}\n  {apps!r}")
                for reading, accent in reading_accents.items():
                    app = apps[reading]
                    if app:
                        for i, kanji in enumerate(entry_kanji):
                            if app is True or i in app:
                                # print(f"kanji: {kanji!r} = {reading!r} = {accent}")
                                accents[kanji][reading] = accent
                    else:
                        # print(f"reading: {reading!r} = {accent}")
                        accents[reading] = accent
            else:
                # print(f"readings: {reading_accents!r}")
                for reading, accent in reading_accents.items():
                    if reading not in accents:
                        accents[reading] = accent
                    elif accents[reading] != accent:
                        print(
                            f"WARNING: accent conflict for {reading}: {accents[reading]} vs {accent}",
                            file=sys.stderr,
                        )
                        reading_conflicts.add(reading)

    for conflict in reading_conflicts:
        del accents[conflict]

    return accents


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    parser.add_argument(
        "--words-file", default=DEFAULT_WORDS_FILE, help="words data file to parse"
    )
    args = parser.parse_args()

    accents = parse_words(os.path.expanduser(args.words_file))
    print(json.dumps(accents, ensure_ascii=False, indent=4, sort_keys=True))
