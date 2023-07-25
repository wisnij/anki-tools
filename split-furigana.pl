#!/usr/bin/perl -C
# Replace kanji/furigana like ABC[1,2,3] with A[1]B[2]C[3]

sub split_furigana {
    my ($kanji, $kana) = @_;
    return "${kanji}[${kana}]" if $kana !~ /,/;

    my @kanji = split //, $kanji;
    my @kana = split /,/, $kana;
    die "length mismatch: $kanji vs $kana\n"
        if @kanji != @kana;

    join '', map { "${kanji[$_]}[$kana[$_]]" } 0..$#kanji;
}

while (<>) {
    s/([\x{4E00}-\x{9FFF}]{2,})\[([^]]+)\]/split_furigana($1,$2)/eg;
    print;
}
