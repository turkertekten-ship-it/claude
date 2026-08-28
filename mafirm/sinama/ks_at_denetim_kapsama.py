#!/usr/bin/env python3
"""KÖR SINAMA AT — denetimin kontrollerinin mutasyon kapsaması.

Yönelim (otuz sekizinci tur). Otuz yedinci tur bir sınıf kapattı: her KAPI
öz-sınamada beklenen olarak geçmeli. Aynı soru bir katman aşağıda hiç
sorulmamıştı: denetimin 26 KONTROLÜNDEN kaçı mutasyonla sınanıyor?

Ölçüldü — çıkarım yapılmadı. D takımının on beş mutasyonu tek tek koşuldu ve
her birinin HANGİ kontrolü HATA'ya düşürdüğü kaydedildi. Sonuç: 26 kontrolün
17'si sınanıyordu, **dokuzu hiçbir mutasyonla sınanmamıştı**:

    uzmanlık birimleri · her birimin INDEX.md'si · koltuk kapısı gerçekten
    bloklıyor · errata izlenebilir · olumsuz iddia kanıtlı · raporun beyan
    sayısı · her takım tabloda · teslimatlar tarih taşıyor · kimlik yolları
    .gitignore'da

Bu, raporun ÜÇÜNCÜ bulgusunun ölçüm tarafındaki hâlidir — kitabın on bir
kontrolünden altısının hiçbir koşulda başarısız olamaması. Kitabı o ölçütle
eleştirirken kendi denetimimin dokuz kontrolünü aynı ölçüte tabi tutmamıştım.
Doğru ifade "dokuz kontrol bozuk" DEĞİL, "dokuz kontrol SINANMAMIŞ"tır:
üçünün çalıştığını bu oturumda kendi gözümle gördüm, ama görmek sağlama
değildir.

İkinci bulgu: mutasyonun kendisi de gevşekti. D yalnızca denetimin çıkış
koduna bakıyordu, hangi kontrolün kırmızıya döndüğüne değil — ve ölçüldü ki
"bütün becerileri sil" mutasyonu ALAKASIZ bir kontrolü de kırmızıya
çeviriyor. Yani hedef kontrol hiç çalışmasa bile mutasyon "yakalandı"
sayılabilirdi: iddia ettiği şeye bakmayan bir kontrol.
"""
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import beklenen  # noqa: E402

_KOK_COZ = os.environ.get("MAFIRM") or os.path.dirname(
    os.path.dirname(os.path.abspath(__file__)))

DENETIM = open(os.path.join(_KOK_COZ, "denetim.sh"),
               encoding="utf-8").read()
D = open(os.path.join(_KOK_COZ, "sinama", "ks_d_denetim.sh"),
         encoding="utf-8").read()
P = open(os.path.join(_KOK_COZ, "sinama", "ks_p_guncellik.py"),
         encoding="utf-8").read()

sonuclar = []


def vaka(kod, baslik, gecti, kanit=""):
    sonuclar.append((kod, baslik, gecti, kanit))


# Her iki liste de KAYNAKTAN türetilir. Elle yazılmış bir liste, ölçtüğü
# şeyden ayrışır — bu takımın bulduğu kusurun ta kendisi (AT-02).
KONTROLLER = re.findall(r'^kontrol "([^"]+)"', DENETIM, re.M)
HEDEFLER = re.findall(r'^\s*"([^"]+)"\s*$|^mutasyon "[^"]+"[^\n]*"([^"]+)"\s*$',
                      D, re.M)
HEDEF_KUME = {a or b for a, b in HEDEFLER if (a or b)}
# Çok satıra yayılmış mutasyon çağrılarının son argümanı da toplanır
HEDEF_KUME |= set(re.findall(r'^\s+"([^"]+)"\s*$', D, re.M))

# --- AT-01 · her kontrol en az bir mutasyonun HEDEFİ mi -------------
_sinanmamis = [k for k in KONTROLLER if k not in HEDEF_KUME]
vaka("AT-01", "denetimin her kontrolü bir mutasyonun beyan edilmiş hedefi",
     not _sinanmamis,
     "%d kontrolden mutasyonsuz: %s — sınanmamış bir kontrolün hiçbir "
     "koşulda başarısız olup olamayacağı BİLİNMEZ"
     % (len(KONTROLLER), _sinanmamis or "yok"))

# --- AT-02 · P'nin teslimat listesi keşifle kuruluyor mu ------------
# Elle yazılmış liste bayatlar: otuz dördüncü turda eklenen teslimat dört tur
# boyunca güncellik kuralının dışında kaldı.
_kesif = "_kesfet()" in P and "MUAF" in P
_elle = re.search(r"TESLIMATLAR = \[\s*\"", P) is not None
vaka("AT-02", "teslimat listesi elle yazılmıyor, keşfediliyor",
     _kesif and not _elle,
     "keşif=%s · elle yazılmış liste=%s" % (_kesif, _elle))

# --- AT-03 · her mutasyon bir hedef beyan ediyor mu -----------------
_cagri = re.findall(r'^mutasyon\s+("(?:[^"\\]|\\.)*"|\\\s*\n\s*"[^"]*")',
                    D, re.M)
_mut_sayisi = len(re.findall(r'^mutasyon ', D, re.M))
# Beyansız çağrı: satır sonu \ ile devam etmeyen ve iki argümanla biten
_beyansiz = len(re.findall(
    r'^mutasyon "[^"]+"\s+"[^"]*"\s*$', D, re.M))
vaka("AT-03", "her mutasyon hedef kontrolünü beyan ediyor",
     _beyansiz == 0,
     "%d mutasyondan hedefsiz: %d" % (_mut_sayisi, _beyansiz))

# --- AT-04 · D hedefi GERÇEKTEN doğruluyor mu ----------------------
# Beyan etmek yetmez; beyanın sağlanması gerekir (AF'nin dersi).
_dogruluyor = ('grep -qF "HATA  $hedef"' in D
               or "grep -qF \"HATA  $hedef\"" in D)
vaka("AT-04", "D, mutasyonun hedef kontrolü kırmızıya çevirdiğini doğruluyor",
     _dogruluyor,
     "mutasyon fonksiyonu yalnızca çıkış koduna bakıyorsa, hedef kontrol hiç "
     "çalışmasa da mutasyon 'yakalandı' sayılır")

# --- AT-05 · OLUMLU KONTROL: kırmızı tabana karşı mutasyon okunmuyor
_taban = ("TABAN ÇİZGİSİ YEŞİL DEĞİL" in D and "exit 99" in D)
vaka("AT-05", "taban çizgisi yeşil değilse mutasyon sınaması geçersiz sayılıyor",
     _taban,
     "kırmızı tabana karşı okunan bir mutasyon hiçbir şey kanıtlamaz")


# [AF-02] Kaybolan bir vaka, kırmızı bir vakadan kötüdür: kimse aramaz.
BEKLENEN_VAKA = 5


def rapor():
    if len(sonuclar) != BEKLENEN_VAKA:
        vaka("AT-00", "takım beyan ettiği vaka sayısını taşıyor", False,
             "beyan %d, bulunan %d" % (BEKLENEN_VAKA, len(sonuclar)))
    genislik = max(len(b) for _, b, _, _ in sonuclar) + 2
    for kod, baslik, gecti, kanit in sonuclar:
        etiket, _ = beklenen.durum(kod, gecti)
        print("%-14s %-6s %-*s %s"
              % (etiket, kod, genislik, baslik, kanit if not gecti else ""))
    sinyal, sayim = beklenen.ozet([(k, g) for k, _, g, _ in sonuclar])
    print("-" * 100)
    print("%d vaka · %d geçti · %d beklenen · %d SİNYAL"
          % (len(sonuclar), sayim["GEÇTİ"], sayim["BEKLENEN"], sinyal))
    return sinyal


if __name__ == "__main__":
    sys.exit(rapor())
