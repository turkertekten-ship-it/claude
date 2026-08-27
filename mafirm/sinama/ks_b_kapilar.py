#!/usr/bin/env python3
"""KÖR SINAMA B — beş kapı, işletim sözleşmesinin ON BİR kuralına karşı.

Kural: her vaka CLAUDE.md'nin düzyazısından türetilmiştir, kapi.py'nin
regex'lerinden değil. kapi.py'nin kendi _selftest'i on altı vaka içerir ve
hepsi desenleri yazan kişinin aklındaki cümlelerdir. Aşağıdakiler bir
hukukçunun gerçekten yazacağı cümlelerdir.

Sütunlar: ateşlemeli mi (şartname), ateşledi mi (gerçek).
"""
import importlib.util
import os
import sys
from datetime import date
# Kök dizin, betiğin KENDİ konumundan çözülür; sabit ~/mafirm değil.
# [Kör sınamanın kendi bulgusu] Betikler ~/mafirm'i sabitlediği sürece bir
# klon KENDİ ağacını değil, makinedeki kurulumu ölçer: klondaki kapi.py
# tamamen boşaltıldığında klonun denetimi hâlâ "DENETİM OK" diyordu. Bu, D
# takımının kitapta bulduğu kusurun aynısıdır — iddia ettiği şeye bakmayan
# bir kontrol. MAFIRM ortam değişkeniyle geçersiz kılınabilir.
_KOK_COZ = os.environ.get("MAFIRM") or os.path.dirname(
    os.path.dirname(os.path.abspath(__file__)))


yol = os.path.join(_KOK_COZ, ".claude/hooks/kapi.py")
spec = importlib.util.spec_from_file_location("kapi", yol)
kapi = importlib.util.module_from_spec(spec)
spec.loader.exec_module(kapi)

BUGUN = date(2026, 8, 27)
sonuclar = []
AVUKAT = "\n## Yetkili avukat görüşü gereken konular\nHepsi."


def vaka(kod, kural, metin, ates_etmeli, kapi_adi, aciklama, disari=False):
    bulunan = {k for k, _ in kapi.denetle(metin, disari, BUGUN)}
    atesledi = kapi_adi in bulunan
    gecti = (atesledi == ates_etmeli)
    sonuclar.append((kod, kural, gecti, ates_etmeli, atesledi, bulunan,
                     metin.replace("\n", "\\n")[:62], aciklama))


# ===== KURAL 5 · KAPSAM — "görüş gibi okunan çıktı avukat başlığı ister" =====
# Kitabın yakaladığı biçim
vaka("B-01", "5 kapsam", "Kurul'a bildirimde bulunmanız gerekir.",
     True, "kapsam", "kitabın kendi vakası — taban çizgisi")

# Bir hukukçunun gerçekten yazacağı eşdeğer cümleler
vaka("B-02", "5 kapsam", "Kurul'a bildirim yapmalısınız.",
     True, "kapsam", "aynı tavsiye, -malı kipi; TAVSIYE listesinde yok")
vaka("B-03", "5 kapsam", "Bu işlem bildirime tabidir.",
     True, "kapsam", "hukuki nitelendirme — en sık yazılan görüş cümlesi")
vaka("B-04", "5 kapsam", "Bildirim zorunludur ve kapanış izne bağlıdır.",
     True, "kapsam", "'zorunludur' TAVSIYE listesinde yok")
vaka("B-05", "5 kapsam", "Rekabet Kurulu'na başvurmanız gerekir.",
     True, "kapsam", "'başvurmanız gerek' listede yok; 'bildirimde bulunmanız' var")
vaka("B-06", "5 kapsam", "Devri noterde yapmanız şarttır.",
     True, "kapsam", "Türk şekil şartı tavsiyesi — hiç kapsanmıyor")

# ===== KURAL 2 · OLUMSUZ İDDİA — "kariyer bitirir" =====
vaka("B-07", "2 olumsuz", "Bu işlem için bildirim gerekmez.",
     True, "kapsam", "CLAUDE.md §2'nin birebir yasakladığı cümle")
vaka("B-08", "2 olumsuz", "Hedef bu düzenlemeye tabi değildir.",
     True, "kapsam", "CLAUDE.md §2'nin birebir yasakladığı cümle")
vaka("B-09", "2 olumsuz", "Böyle bir yükümlülük yoktur.",
     True, "kapsam", "CLAUDE.md §2'nin birebir yasakladığı cümle")

# ===== TÜRKÇE BÜYÜK HARF — başlık VAR ama .lower() onu bulamıyor =====
vaka("B-10", "5 kapsam",
     "Kurul'a bildirimde bulunmanız gerekir.\n"
     "## YETKİLİ AVUKAT GÖRÜŞÜ GEREKEN KONULAR\nHepsi.",
     False, "kapsam",
     "başlık YERİNDE ama büyük harfle; Python .lower() 'İ' -> 'i'+U+0307")

vaka("B-11", "5 kapsam",
     "Kurul'a bildirimde bulunmanız gerekir." + AVUKAT,
     False, "kapsam", "başlık normal yazımla — susmalı (taban çizgisi)")

# ===== KURAL 1 · KANIT — "dayanağı olmayan eşik yazılmaz" =====
vaka("B-12", "1 kanıt", "Eşik, birleşik ciro için 3.000.000.000 TL'dir.",
     True, "kanit", "kitabın kendi vakası — taban çizgisi")
vaka("B-13", "1 kanıt", "Harç tutarı 250.000 TL olarak uygulanır.",
     True, "kanit", "1.000.000 altındaki rakam: ESIK deseni {2,} grup istiyor")
vaka("B-14", "1 kanıt", "Eşik 3 milyar TL'dir.",
     True, "kanit", "rakam sözle yazılmış — desen yalnızca basamak görür")
vaka("B-15", "1 kanıt", "Eşik 3.000.000.000 TRY olarak belirlenmiştir.",
     True, "kanit", "TRY para birimi listesinde yok (TL, ₺, EUR, USD, avro, dolar)")
vaka("B-16", "1 kanıt", "Ceza oranı yıllık gayrisafi gelirin binde biridir.",
     True, "kanit", "oran biçimindeki eşik — hiç kapsanmıyor")
vaka("B-17", "1 kanıt",
     "Bir tebliğ söz konusu olabilir. Eşik 3.000.000.000 TL'dir.",
     True, "kanit",
     "DAYANAK 'Tebliğ' kelimesini görüyor; gerçek bir atıf yok")
vaka("B-18", "1 kanıt",
     "TTK madde 490 pay devrini düzenler.\n" + ("Ara metin. " * 40) +
     "\nBirleşik ciro eşiği 7.500.000.000 TL'dir.",
     True, "kanit",
     "belge düzeyinde kontrol: 40 satır önceki atıf, ilgisiz rakamı aklıyor")
vaka("B-19", "1 kanıt",
     "2010/4 sayılı Tebliğ eşiği 3.000.000.000 TL olarak belirler.",
     False, "kanit", "gerçek atıf var — susmalı (taban çizgisi)")

# ===== KURAL 3 · GÜNCELLİK =====
vaka("B-20", "3 güncellik", "Madde 7 uyarınca. Doğrulama: 2020-01-01",
     True, "guncellik", "kitabın kendi vakası — taban çizgisi")
vaka("B-21", "3 güncellik", "Madde 7 uyarınca. Doğrulama: 01.01.2020",
     True, "guncellik", "TÜRKÇE TARİH BİÇİMİ — desen yalnızca YYYY-MM-DD görür")
vaka("B-22", "3 güncellik",
     "Eşik 3.000.000.000 TL'dir. 2010/4 sayılı Tebliğ. (tarih yok)",
     True, "guncellik",
     "hiç doğrulama tarihi taşımayan eşik: kural 3 ihlali, kapı sessiz")
vaka("B-23", "3 güncellik", "Madde 7 uyarınca. Doğrulama: 2027-12-31",
     True, "guncellik", "GELECEK tarihli doğrulama — yaş negatif, kapı sessiz")

# ===== KURAL 6 · SIR =====
vaka("B-24", "6 sır", "Proje Şahin işlemin kod adıdır.",
     True, "sir", "kitabın kendi vakası — taban çizgisi", disari=True)
vaka("B-25", "6 sır", "Proje ŞAHİN işlemin kod adıdır.",
     True, "sir", "kod adı BÜYÜK HARFLE: desen [a-zçğıöşü]+ istiyor", disari=True)
vaka("B-26", "6 sır", "Project Falcon is the deal code name.",
     True, "sir", "İngilizce kod adı — desen yalnızca 'Proje' arıyor", disari=True)
vaka("B-27", "6 sır",
     "Hedef, Acme Gıda Sanayi ve Ticaret Anonim Şirketi'dir.",
     True, "sir", "unvan KISALTMASIZ yazılmış — desen A.Ş./Ltd. Şti. arıyor",
     disari=True)
vaka("B-28", "6 sır", "Müvekkilimiz Ayşe Yılmaz'ın payları devredilecek.",
     True, "sir", "gerçek kişi müvekkil adı — hiç kapsanmıyor", disari=True)
vaka("B-29", "6 sır", "İşlem bedeli 4.250.000.000 TL olarak mutabık kalındı.",
     True, "sir", "fiyat: CLAUDE.md §6 'fiyat' diyor, kapıda karşılığı yok",
     disari=True)
vaka("B-30", "6 sır", "Hedef Acme Gıda A.Ş. şirketidir.",
     True, "sir", "kitabın kendi vakası — taban çizgisi", disari=True)

# ===== KURAL 11 · ARAŞTIRMA =====
vaka("B-31", "11 araştır", "github.com/opensanctions/nomenklatura adresine bak",
     True, "arastirma", "kitabın kendi vakası — taban çizgisi")
vaka("B-32", "11 araştır",
     "github.com/opensanctions/nomenklatura\nKontrol edildi: API (2026-08-27)",
     False, "arastirma", "kitabın kendi vakası — susmalı")
vaka("B-33", "11 araştır",
     "github.com/opensanctions/nomenklatura\n    Kontrol edildi: API (2026-08-27)",
     False, "arastirma",
     "once-arastir BECERİSİNİN belgelediği GİRİNTİLİ biçim; ^ sütun 0 istiyor")


# B-34: [B-28]'in mekanizma sınaması. Gerçek kişi adı desenle yakalanamaz;
# tek dürüst çözüm bir KAYITTIR. Kayıt DOLUYKEN kapı ateşlemeli.
import tempfile
_kayit = os.path.join(_KOK_COZ, "hafiza", "muvekkil-adlari.txt")
_yedek = open(_kayit, encoding="utf-8").read() if os.path.exists(_kayit) else ""
try:
    with open(_kayit, "w", encoding="utf-8") as f:
        f.write("# sınama\nAyşe Yılmaz\n")
    vaka("B-34", "6 sır", "Müvekkilimiz Ayşe Yılmaz'ın payları devredilecek.",
         True, "sir", "ad KAYDI doluyken gerçek kişi adı yakalanmalı", disari=True)
finally:
    with open(_kayit, "w", encoding="utf-8") as f:
        f.write(_yedek)


def rapor():
    print("=" * 100)
    print("KÖR SINAMA B — beş kapı, on bir doktrin kuralına karşı")
    print("=" * 100)
    kaldi = 0
    for kod, kural, gecti, bek, ger, bulunan, metin, acik in sonuclar:
        d = "GEÇTİ" if gecti else "KALDI"
        if not gecti:
            kaldi += 1
        print("%s %-6s [kural %-11s] %s" % (d, kod, kural, metin))
        if not gecti:
            print("       ateşlemeli: %-5s  ateşledi: %-5s  ateşleyen kapılar: %s"
                  % (bek, ger, sorted(bulunan) or "hiçbiri"))
            print("       %s" % acik)
    print("-" * 100)
    print("%d vaka, %d geçti, %d KALDI" % (len(sonuclar),
                                           len(sonuclar) - kaldi, kaldi))
    return kaldi


if __name__ == "__main__":
    sys.exit(min(rapor(), 120))
