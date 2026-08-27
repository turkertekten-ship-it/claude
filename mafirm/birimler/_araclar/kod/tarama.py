#!/usr/bin/env python3
"""Karşı taraf adı eşleştirme (nomenklatura) — Türkçe harf çevirisine dayanıklı.

Neden kod. Türkçe adlar birden çok biçimde çevrilir: Şükrü / Sukru / Shukru,
Öztürk / Ozturk / Oztuerk. Elle tarama bu farkları kaçırır ve kaçırılan şey
cezai sorumluluk doğurabilir.

Bu betik YEREL çalışır. Ad hiçbir dış servise gitmez (işletim sözleşmesi §6).
Karşılaştırılacak liste `--liste` ile verilir; OpenSanctions veri kümesi ayrıca
indirilip yerelde kullanılır.

    python3 tarama.py "Acme Gıda A.Ş." --liste yaptirim.txt

Tarama karar değildir. Bir ad eşleşmesi bir ipucudur.

Doğrulama: 2026-08-27.
"""
import sys
import unicodedata


def normalize(s):
    """Harf çevirisi farklarını eritir: Şükrü -> sukru."""
    try:
        from normality import normalize as nz
        n = nz(s, latinize=True)
        if n:
            return n
    except Exception:
        pass
    s = unicodedata.normalize("NFKD", s.lower())
    return "".join(c for c in s if not unicodedata.combining(c)).strip()


def benzerlik(a, b):
    from difflib import SequenceMatcher
    return SequenceMatcher(None, normalize(a), normalize(b)).ratio()


def main(argv):
    if len(argv) < 2:
        print(__doc__.strip())
        return 2
    ad = argv[1]
    liste = []
    if "--liste" in argv:
        yol = argv[argv.index("--liste") + 1]
        liste = [s.strip() for s in open(yol, encoding="utf-8") if s.strip()]
    if not liste:
        print("liste verilmedi; yalnızca normalleştirme gösteriliyor.")
        print("  girdi      : %s" % ad)
        print("  normalize  : %s" % normalize(ad))
        return 0
    sonuc = sorted(((benzerlik(ad, x), x) for x in liste), reverse=True)
    print("Sorgu: %s   (normalize: %s)" % (ad, normalize(ad)))
    for oran, x in sonuc[:10]:
        isaret = "EŞLEŞME ADAYI" if oran >= 0.85 else ""
        print("  %.3f  %-40s %s" % (oran, x, isaret))
    print("\nTarama karar değildir. Her eşleşme adayı için kimlik doğrulaması")
    print("ve devam kararı yetkili avukat ister.")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
