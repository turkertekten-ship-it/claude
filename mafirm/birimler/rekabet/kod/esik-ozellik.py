#!/usr/bin/env python3
"""Eşik kodunun ÖZELLİK sınaması: tek tek vaka değil, kural sınaması.

Neden var. `esik.py --self-test` on bir somut vakayı sınar ve o vakalar
seçilmiştir; seçen kişi neyi düşünmediyse orada da bir boşluk vardır. Bu betik
vakayı değil KURALI sınar ve rastgele binlerce girdiyle bunu yapar:

  1. Sınır katıdır. "Aşmak" kesin eşitsizliktir; eşiğe tam eşit olmak aşmak
     değildir. Her eşikte ayrı ayrı sınanır.
  2. Sıra bağımsızlığı. Taraf cirolarının listedeki sırası sonucu
     değiştirmemelidir.
  3. Monotonluk. Ciro artarsa bir işlem bildirime tabi olmaktan ÇIKAMAZ.
  4. Teknoloji istisnası kapsamı ASLA daraltmaz. Yerleşik bir teknoloji
     hedefi, olağan eşiği zaten geçen bir işlemi tabi olmaktan çıkaramaz.
     Bu kusur sessiz olurdu: gereken bir bildirimi yapmamaya götürürdü.
  5. Yerleşiklik yoksa teknoloji bayrağı hiçbir şeyi değiştirmez (2026/2).
  6. `bildirilmeli`, `esik_a` ve `esik_b` ile tutarlıdır.

Doğrulama: 2026-08-27.

Kontrol edildi: birimler/rekabet/yontem/tr-esikler.md (2026-08-27) ·
bulunamayan: Resmî Gazete birincil metni — ağ çıkışı engelli.
"""
import importlib.util
import itertools
import os
import random
import sys

YOL = os.path.join(os.path.dirname(os.path.abspath(__file__)), "esik.py")
_spec = importlib.util.spec_from_file_location("esik", YOL)
e = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(e)

TUR = 300          # tur başına rastgele vaka
h = 0


def chk(kosul, ileti):
    global h
    if not kosul:
        print("  HATA: %s" % ileti)
        h += 1


def main():
    random.seed(20260827)          # yeniden üretilebilir olsun

    # 1. sınır katılığı
    chk(not e.esik_a([e.IKI_TARAF_TR, e.IKI_TARAF_TR, e.BIRLESIK_TR]),
        "A: taraf cirosu tam eşikte aşmak sayılmamalı")
    chk(e.esik_a([e.IKI_TARAF_TR + 1, e.BIRLESIK_TR + 1]),
        "A: eşik+1 aşmalı")
    chk(not e.esik_b(e.HEDEF_TR, [e.DIGER_DUNYA + 1]),
        "B: hedef tam eşikte geçmemeli")
    chk(not e.esik_b(e.HEDEF_TR + 1, [e.DIGER_DUNYA]),
        "B: dünya cirosu tam eşikte geçmemeli")
    chk(not e.esik_b(e.HEDEF_TR_TEKNOLOJI, [e.DIGER_DUNYA + 1], True),
        "teknoloji: tam eşikte geçmemeli")

    for _ in range(TUR):
        # 2. sıra bağımsızlığı
        c = [random.randint(0, 4_000_000_000)
             for _ in range(random.randint(2, 5))]
        r = e.esik_a(c)
        for p in itertools.islice(itertools.permutations(c), 6):
            chk(e.esik_a(list(p)) == r, "A sıraya duyarlı: %s" % (c,))

        # 3. monotonluk
        if e.esik_a(c):
            c2 = [x + random.randint(0, 10 ** 9) for x in c]
            chk(e.esik_a(c2), "A monoton değil: %s -> %s" % (c, c2))

        hedef = random.randint(0, 3_000_000_000)
        d = [random.randint(0, 2 * 10 ** 10)]
        if e.esik_b(hedef, d):
            chk(e.esik_b(hedef + random.randint(0, 10 ** 9),
                         [d[0] + random.randint(0, 10 ** 9)]),
                "B monoton değil")
            # 4. teknoloji istisnası kapsamı daraltmaz
            chk(e.esik_b(hedef, d, True),
                "teknoloji istisnası kapsamı DARALTTI: %s %s" % (hedef, d))

        # 5. yerleşiklik yoksa bayrak etkisiz
        chk(e.esik_b(hedef, d, True, yerlesik=False) == e.esik_b(hedef, d,
                                                                False),
            "yerleşik olmayan teknoloji bayrağı sonucu değiştirdi")

        # 6. bildirilmeli tutarlılığı
        tabi, _s = e.bildirilmeli(c, hedef, d)
        chk(tabi == (e.esik_a(c) or e.esik_b(hedef, d)),
            "bildirilmeli, esik_a/esik_b ile tutarsız")

    print("ÖZELLİK SINAMASI %s" % ("OK" if not h else "HATA %d" % h))
    return h


if __name__ == "__main__":
    sys.exit(main())
