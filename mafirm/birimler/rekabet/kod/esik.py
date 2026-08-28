#!/usr/bin/env python3
"""Türkiye'de birleşme denetimi bildirim eşiği testi.

Bu neden kod, neden hafıza değil. Testin iki ayağı var, her ayakta iki koşul
var ve teknoloji istisnası yalnızca bir ayaktaki bir rakamı değiştiriyor.
Bunu düzyazıda akıl yürüterek çözmek, hatanın yapıldığı yerdir; hata da iki
yönde de pahalıdır: gereksiz bildirim haftalara mal olur, gereken bildirimin
yapılmaması kapanışı geçersiz kılar.

Rakamlar: 2026/2 sayılı Tebliğ (RG 11.02.2026, sayı 33165), doğrulama
2026-08-27.

Teknoloji istisnasında bu dosya kurulum kitabı §5.1'den ÜÇ noktada ayrılır ve
ayrım bilerek yapılmıştır (bkz. yontem/tr-esikler.md):

  1. İstisna Türkiye'de YERLEŞİK teknoloji teşebbüslerine bağlıdır. Kitaptaki
     "Türkiye'de faaliyet gösteren ya da AR-GE yürüten" ölçütü önceki rejimin
     daha geniş tanımıdır; olduğu gibi bırakmak gereksiz bildirim üretir.
  2. Devralmada devralınan taraf, BİRLEŞMEDE ise taraflardan herhangi biri
     Türkiye'de yerleşik teknoloji teşebbüsü ise istisna uygulanır. Kitap
     birleşme ayağını atlıyor.
  3. 250.000.000 TL eşiği teşebbüsün TOPLAM cirosuyla değil, yalnızca sayılan
     teknoloji alanlarındaki cirosuyla ölçülür. Kitapta bu darlık yok.

Teknoloji alanları: dijital platformlar, yazılım ve oyun yazılımı, finansal
teknolojiler, biyoteknoloji, farmakoloji, tarım kimyasalları, sağlık
teknolojileri.

Kontrol edildi: 2026/2 sayılı Tebliğ üzerine yayımlanmış uygulamacı
çözümlemeleri, web araması (2026-08-27) · yontem/tr-esikler.md (2026-08-27) ·
bulunamayan: Resmî Gazete birincil metni — ağ çıkışı engelli.
"""
import sys

# Tutarların hepsi TL. Adlandırıldı ki bir fark hangisinin oynadığını göstersin.
BIRLESIK_TR = 3_000_000_000       # A eşiği: Türkiye ciroları toplamı
IKI_TARAF_TR = 1_000_000_000      # A eşiği: en az iki tarafın her biri
HEDEF_TR = 1_000_000_000          # B eşiği: devre konu varlık / bir taraf
HEDEF_TR_TEKNOLOJI = 250_000_000  # B eşiği: teknoloji teşebbüsü hedef
DIGER_DUNYA = 9_000_000_000       # B eşiği: diğer taraflardan birinin dünya
DOGRULAMA = "2026-08-27"

TEKNOLOJI_ALANLARI = (
    "dijital platformlar", "yazılım ve oyun yazılımı", "finansal teknolojiler",
    "biyoteknoloji", "farmakoloji", "tarım kimyasalları",
    "sağlık teknolojileri",
)


def esik_a(tr_cirolar):
    """Toplam Türkiye cirosu ve en az iki tarafın tabanı aşması."""
    toplam = sum(tr_cirolar)
    tabani_asan = [c for c in tr_cirolar if c > IKI_TARAF_TR]
    return toplam > BIRLESIK_TR and len(tabani_asan) >= 2


def teknoloji_esigi_uygulanir(teknoloji, islem_turu="devralma",
                              yerlesik=True):
    """2026/2'nin daralttığı kapı: istisna gerçekten uygulanır mı.

    Devralmada devralınan taraf, birleşmede taraflardan en az biri Türkiye'de
    YERLEŞİK bir teknoloji teşebbüsü olmalıdır. Yerleşiklik olgusu yoksa
    istisna yoktur ve olağan 1.000.000.000 TL eşiği geri gelir.
    """
    if not teknoloji:
        return False
    if not yerlesik:
        return False
    return islem_turu in ("devralma", "birlesme")


def esik_b(hedef_tr, diger_dunya_cirolari, teknoloji=False,
           islem_turu="devralma", yerlesik=True, teknoloji_alan_cirosu=None):
    """Devre konu tarafın Türkiye cirosu, diğerinin dünya cirosuna karşı.

    teknoloji_alan_cirosu verilmişse 250.000.000 TL testi ONUNLA yapılır;
    teşebbüsün toplam cirosuyla değil. Verilmemişse hedef_tr kullanılır ve
    bu, eşiği olduğundan kolay geçirebilir — çağıran bunu bilmelidir.
    """
    uygulanir = teknoloji_esigi_uygulanir(teknoloji, islem_turu, yerlesik)
    esik = HEDEF_TR_TEKNOLOJI if uygulanir else HEDEF_TR
    olculen = hedef_tr
    if uygulanir and teknoloji_alan_cirosu is not None:
        olculen = teknoloji_alan_cirosu
    return (olculen > esik
            and any(c > DIGER_DUNYA for c in diger_dunya_cirolari))


def bildirilmeli(tr_cirolar, hedef_tr, diger_dunya_cirolari, teknoloji=False,
                 islem_turu="devralma", yerlesik=True,
                 teknoloji_alan_cirosu=None):
    """(bildirime tabi mi, hangi ayak) döner; cevap gerekçesini taşısın."""
    a = esik_a(tr_cirolar)
    b = esik_b(hedef_tr, diger_dunya_cirolari, teknoloji, islem_turu,
               yerlesik, teknoloji_alan_cirosu)
    tek = teknoloji_esigi_uygulanir(teknoloji, islem_turu, yerlesik)
    if a and b:
        return True, "her iki eşik"
    if a:
        return True, "A eşiği (yurt içi)"
    if b:
        return True, "B eşiği (devre konu)" + (" + teknoloji" if tek else "")
    if teknoloji and not tek:
        return False, ("hiçbir eşik (teknoloji istisnası UYGULANMADI: "
                       "Türkiye'de yerleşiklik yok)")
    return False, "hiçbir eşik"


def _selftest():
    h = 0
    # --- kurulum kitabı §5.1'deki altı vaka, olduğu gibi ---
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

    # --- 2026/2 doğrulamasının eklediği vakalar ---
    # Yerleşiklik yoksa istisna da yok: 300 milyon olağan eşiği geçmez.
    ok, sebep = bildirilmeli([0], 300_000_000, [10_000_000_000],
                             teknoloji=True, yerlesik=False)
    if ok or "yerleşiklik" not in sebep:
        print("  HATA yerleşik olmayan teknoloji teşebbüsüne istisna "
              "uygulanmamalı: %s %s" % (ok, sebep)); h += 1
    # Birleşme ayağı: taraflardan biri yerleşik teknoloji teşebbüsü.
    ok, sebep = bildirilmeli([0], 300_000_000, [10_000_000_000],
                             teknoloji=True, islem_turu="birlesme")
    if not ok or "teknoloji" not in sebep:
        print("  HATA birleşmede teknoloji istisnası uygulanmalı"); h += 1
    # Ciro darlığı: toplam ciro 300 milyon ama teknoloji alanı cirosu 200
    # milyon -> 250 milyonluk eşik KARŞILANMAZ.
    ok, _ = bildirilmeli([0], 300_000_000, [10_000_000_000], teknoloji=True,
                         teknoloji_alan_cirosu=200_000_000)
    if ok:
        print("  HATA 250 milyon testi teknoloji ALANI cirosuyla yapılmalı")
        h += 1
    # Aynı işlem, teknoloji alanı cirosu 260 milyon -> karşılanır.
    ok, sebep = bildirilmeli([0], 300_000_000, [10_000_000_000],
                             teknoloji=True, teknoloji_alan_cirosu=260_000_000)
    if not ok or "teknoloji" not in sebep:
        print("  HATA teknoloji alanı cirosu eşiği aşıyorsa tabi olmalı"); h += 1
    # Teknoloji istisnası B ayağının İKİNCİ koşulunu kaldırmaz: dünya cirosu
    # 9 milyarı aşmıyorsa bildirim yok.
    ok, _ = bildirilmeli([0], 300_000_000, [8_000_000_000], teknoloji=True)
    if ok:
        print("  HATA teknoloji istisnası dünya cirosu koşulunu kaldırmaz")
        h += 1

    print("SELFTEST %s (rakamlar %s tarihinde doğrulandı)"
          % ("OK" if not h else "HATA %d" % h, DOGRULAMA))
    return h


def _sayi(x):
    """'1.200.000.000', '1_200_000_000' ve '1200000000' aynı sayıdır."""
    t = str(x).strip().replace("_", "").replace(" ", "")
    # Türkçe biçim: nokta binlik ayırıcıdır.
    t = t.replace(".", "").replace(",", "")
    return int(t)


def _hesapla(argv):
    """Gerçek rakamlarla işlemi hesaplar. Cevap gerekçesini yanında taşır."""
    import argparse
    a = argparse.ArgumentParser(
        prog="esik.py", add_help=True,
        description="Türkiye birleşme denetimi bildirim eşiği hesabı.")
    a.add_argument("--tr-cirolar", required=True,
                   help="Tarafların Türkiye ciroları, virgülle: 2.000.000.000,1.500.000.000")
    a.add_argument("--hedef-tr", required=True,
                   help="Devre konu tarafın Türkiye cirosu")
    a.add_argument("--diger-dunya", default="",
                   help="Diğer tarafların dünya ciroları, virgülle")
    a.add_argument("--teknoloji", action="store_true",
                   help="Devre konu taraf teknoloji teşebbüsü mü")
    a.add_argument("--islem-turu", choices=["devralma", "birlesme"],
                   default="devralma")
    a.add_argument("--yerlesik", choices=["evet", "hayir"], default="evet",
                   help="Teknoloji teşebbüsü Türkiye'de YERLEŞİK mi (2026/2)")
    a.add_argument("--teknoloji-alan-cirosu", default=None,
                   help="Yalnızca sayılan teknoloji alanlarındaki ciro")
    n = a.parse_args(argv)

    tr = [_sayi(x) for x in n.tr_cirolar.split(",") if x.strip()]
    hedef = _sayi(n.hedef_tr)
    dunya = [_sayi(x) for x in n.diger_dunya.split(",") if x.strip()]
    alan = _sayi(n.teknoloji_alan_cirosu) if n.teknoloji_alan_cirosu else None
    yerlesik = n.yerlesik == "evet"

    tabi, sebep = bildirilmeli(tr, hedef, dunya, n.teknoloji, n.islem_turu,
                               yerlesik, alan)
    uygulandi = teknoloji_esigi_uygulanir(n.teknoloji, n.islem_turu, yerlesik)
    b_esigi = HEDEF_TR_TEKNOLOJI if uygulandi else HEDEF_TR
    olculen = alan if (uygulandi and alan is not None) else hedef

    print("CEVAP: %s" % ("BİLDİRİME TABİ" if tabi else "bildirime tabi DEĞİL"))
    print("  gerekçe: %s" % sebep)
    print()
    print("A eşiği (yurt içi)")
    print("  toplam TR cirosu        : %15d  (eşik %d)" % (sum(tr), BIRLESIK_TR))
    print("  tabanı aşan taraf sayısı: %15d  (en az 2, taban %d)"
          % (len([c for c in tr if c > IKI_TARAF_TR]), IKI_TARAF_TR))
    print("  sonuç                   : %s" % ("karşılandı" if esik_a(tr) else "karşılanmadı"))
    print()
    print("B eşiği (devre konu)")
    print("  ölçülen TR cirosu       : %15d  (eşik %d)" % (olculen, b_esigi))
    if uygulandi:
        print("    -> teknoloji istisnası UYGULANDI (%s, Türkiye'de yerleşik)"
              % n.islem_turu)
        if alan is None:
            print("    -> UYARI: --teknoloji-alan-cirosu verilmedi. 250 milyon")
            print("       testi teşebbüsün TOPLAM cirosuyla değil, yalnızca")
            print("       sayılan teknoloji alanlarındaki cirosuyla yapılır.")
    elif n.teknoloji:
        print("    -> teknoloji istisnası UYGULANMADI (Türkiye'de yerleşik değil)")
    print("  en yüksek dünya cirosu  : %15d  (eşik %d)"
          % (max(dunya) if dunya else 0, DIGER_DUNYA))
    print("  sonuç                   : %s"
          % ("karşılandı" if esik_b(hedef, dunya, n.teknoloji, n.islem_turu,
                                    yerlesik, alan) else "karşılanmadı"))
    print()
    print("Kullanılan eşiklerin doğrulama tarihi: %s" % DOGRULAMA)
    print("Dayanak: 2026/2 sayılı Tebliğ (RG 11.02.2026, sayı 33165)")
    print()
    print("## Şimdi ne yapılmalı")
    if tabi:
        print("Kapanış Kurul iznine bağlanır ve bu koşuldan feragat edilemez.")
        print("İzinden önce bütünleşme, ortak fiyatlandırma ve ortak müşteri")
        print("görüşmesi yapılmaz (4054 sayılı Kanun m.10, 2010/4 sayılı Tebliğ m.10).")
    else:
        print("Olumsuz sonuç, olumludan daha yüksek kanıt ister. Ciro")
        print("rakamlarının kaynağı ve hesap yöntemi yazıya geçirilmelidir.")
    print()
    print("## Yetkili avukat görüşü gereken konular")
    print("Ciro hesabının yöntemi, kontrol değişikliği tespiti, teknoloji")
    print("teşebbüsü ve yerleşiklik niteliği ve bu sonuca dayanılıp")
    print("dayanılamayacağı.")
    return 0


if __name__ == "__main__":
    if "--self-test" in sys.argv:
        sys.exit(_selftest())
    if len(sys.argv) > 1:
        sys.exit(_hesapla(sys.argv[1:]))
    print(__doc__.strip())
    print()
    print("Hesap için: esik.py --tr-cirolar ... --hedef-tr ... --diger-dunya ...")
    print("Sınama için: esik.py --self-test")
