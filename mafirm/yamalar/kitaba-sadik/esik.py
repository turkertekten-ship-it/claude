#!/usr/bin/env python3
"""Türkiye'de birleşme denetimi bildirim eşiği testi.

Bu neden kod, neden hafıza değil. Testin iki ayağı var, her ayakta iki koşul
var ve teknoloji istisnası yalnızca bir ayaktaki bir rakamı değiştiriyor.
Bunu düzyazıda akıl yürüterek çözmek, hatanın yapıldığı yerdir; hata da iki
yönde de pahalıdır: gereksiz bildirim haftalara mal olur, gereken bildirimin
yapılmaması kapanışı geçersiz kılar.

Rakamlar: 2026/2 sayılı Tebliğ (RG 11.02.2026, sayı 33165), doğrulama
2026-08-27.
"""
import sys

# Tutarların hepsi TL. Adlandırıldı ki bir fark hangisinin oynadığını göstersin.
BIRLESIK_TR = 3_000_000_000       # A eşiği: Türkiye ciroları toplamı
IKI_TARAF_TR = 1_000_000_000      # A eşiği: en az iki tarafın her biri
HEDEF_TR = 1_000_000_000          # B eşiği: devre konu varlık / bir taraf
HEDEF_TR_TEKNOLOJI = 250_000_000  # B eşiği: teknoloji teşebbüsü hedef
DIGER_DUNYA = 9_000_000_000       # B eşiği: diğer taraflardan birinin dünya
DOGRULAMA = "2026-08-27"


def esik_a(tr_cirolar):
    """Toplam Türkiye cirosu ve en az iki tarafın tabanı aşması."""
    toplam = sum(tr_cirolar)
    tabani_asan = [c for c in tr_cirolar if c > IKI_TARAF_TR]
    return toplam > BIRLESIK_TR and len(tabani_asan) >= 2


def esik_b(hedef_tr, diger_dunya_cirolari, teknoloji=False):
    """Devre konu tarafın Türkiye cirosu, diğerinin dünya cirosuna karşı."""
    esik = HEDEF_TR_TEKNOLOJI if teknoloji else HEDEF_TR
    return (hedef_tr > esik
            and any(c > DIGER_DUNYA for c in diger_dunya_cirolari))


def bildirilmeli(tr_cirolar, hedef_tr, diger_dunya_cirolari, teknoloji=False):
    """(bildirime tabi mi, hangi ayak) döner; cevap gerekçesini taşısın."""
    a = esik_a(tr_cirolar)
    b = esik_b(hedef_tr, diger_dunya_cirolari, teknoloji)
    if a and b:
        return True, "her iki eşik"
    if a:
        return True, "A eşiği (yurt içi)"
    if b:
        return True, "B eşiği (devre konu)" + (" + teknoloji" if teknoloji else "")
    return False, "hiçbir eşik"


def _selftest():
    h = 0
    # A eşiği tam karşılanıyor: 2,0 + 1,5 = 3,5 milyar, ikisi de 1 milyar üstü.
    ok, sebep = bildirilmeli([2_000_000_000, 1_500_000_000], 0, [])
    if not ok or "A" not in sebep:
        print("  HATA A eşiği olumlu: %s %s" % (ok, sebep)); h += 1
    # Toplam aşıyor ama tabanı aşan TEK taraf var -> A eşiği karşılanmaz.
    ok, _ = bildirilmeli([2_900_000_000, 500_000_000], 0, [])
    if ok:
        print("  HATA A eşiği İKİ tarafın tabanı aşmasını ister"); h += 1
    # B eşiği: hedef 1,2 milyar TL Türkiye, alıcı 10 milyar TL dünya.
    ok, sebep = bildirilmeli([0], 1_200_000_000, [10_000_000_000])
    if not ok or "B" not in sebep:
        print("  HATA B eşiği olumlu"); h += 1
    # Aynı işlem, hedef 300 milyon: teknoloji teşebbüsü DEĞİLSE tabi değil.
    ok, _ = bildirilmeli([0], 300_000_000, [10_000_000_000])
    if ok:
        print("  HATA 300 milyonluk hedef olağan B eşiğini geçmemeli"); h += 1
    ok, sebep = bildirilmeli([0], 300_000_000, [10_000_000_000], teknoloji=True)
    if not ok or "teknoloji" not in sebep:
        print("  HATA teknoloji istisnası uygulanmadı"); h += 1
    # Sınır katıdır: rakamın tam üstünde olmak "aşmak" değildir.
    ok, _ = bildirilmeli([0], HEDEF_TR, [10_000_000_000])
    if ok:
        print("  HATA eşiğe tam eşit olmak aşmak sayılmamalı"); h += 1
    print("SELFTEST %s (rakamlar %s tarihinde doğrulandı)"
          % ("OK" if not h else "HATA %d" % h, DOGRULAMA))
    return h


if __name__ == "__main__":
    if "--self-test" in sys.argv:
        sys.exit(_selftest())
    print(__doc__.strip())
