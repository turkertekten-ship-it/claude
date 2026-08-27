#!/usr/bin/env python3
"""Bir maddenin iki sürümünü gerçekten karşılaştırır (diff-match-patch).

Neden göz değil kod. Müzakere turları arasında değişen bir "ve"yi ya da bir
"makul çaba"nın "azami çaba" olmasını göz kaçırır; bu iki kelime tazminat
tavanından daha çok para taşıyabilir.

    python3 karsilastir.py <eski.txt> <yeni.txt>

Doğrulama: 2026-08-27.
"""
import sys

from diff_match_patch import diff_match_patch


def karsilastir(eski, yeni):
    dmp = diff_match_patch()
    d = dmp.diff_main(eski, yeni)
    dmp.diff_cleanupSemantic(d)
    return d


def yazdir(d):
    ekleme = silme = 0
    for op, metin in d:
        g = metin.replace("\n", "\\n")
        if op == 1:
            ekleme += len(metin); print("  + %s" % g)
        elif op == -1:
            silme += len(metin); print("  - %s" % g)
    print("\nözet: %d karakter eklendi, %d karakter silindi" % (ekleme, silme))
    if ekleme == silme == 0:
        print("iki sürüm aynı.")


def main(argv):
    if len(argv) < 3:
        print(__doc__.strip())
        return 2
    eski = open(argv[1], encoding="utf-8").read()
    yeni = open(argv[2], encoding="utf-8").read()
    yazdir(karsilastir(eski, yeni))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
