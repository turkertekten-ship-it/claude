#!/usr/bin/env python3
"""KÖR SINAMA AW — raporun kitaptan yaptığı alıntılar birebir mi.

Yönelim (kırk birinci tur). Kırk turdur kitabı kendi cümleleriyle
eleştiriyorum: §8'in tek cümlesi, §5.1'in "İmza serbesttir; kapanış
değildir"i, §9'un dört çıktı türü, §13'ün Karar sütunu, `/esik-denetle`'nin
kapanışı. **Bulguların çoğu bu alıntılara dayanıyor** — ve hiçbir şey
alıntıların doğru olduğunu sınamıyordu. Yanlış bir alıntı, üstüne kurulan
bulguyu da götürür.

Ölçüm bir hata buldu ve hata bana aitti. Otuz beşinci turda kitabı şu cümle
için övmüştüm: *"eşleşmenin yokluğu temizlik kanıtı değildir"* — yaptırım
taramasının boş sonuç tuzağını kapattığı gerekçesiyle. **O cümle kitapta
yok.** Kitabın §13.3'ü yalnızca "Tarama karar değildir" diyor. Cümleyi
`yaptirim-taramasi` becerisini yazarken ben eklemiştim ve altı tur sonra
kendi yamamı kitabın metni sanıp kitaba kredi verdim.

Otuz dördüncü turda AP-01 kendi teslimatımı kitabın eseri sanmıştı; orada
kitabı olduğundan iyi göstermişti. Aynı sınıf, ters yönde tekrar: **kendi
yamalarım ağaçta dururken kitabı ölçmek ikisini karıştırır.**

Üç alıntı daha düzeltildi: §1'in kanıt kuralı yanlış sözcüklerle, §14'ün boş
arama tuzağından "GitHub" düşmüş, ve §13.4'ün gerekçesinde sözcük sırası
ters ("eskime burada" → "burada eskime").
"""
import html
import io
import os
import re
import sys
import zipfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import beklenen  # noqa: E402
from kitap import metin as kitap_metni_ortak  # noqa: E402

_KOK_COZ = os.environ.get("MAFIRM") or os.path.dirname(
    os.path.dirname(os.path.abspath(__file__)))

# Kitabın kaynağı. Bulunamazsa vaka SESSİZ GEÇMEZ: açıkça kırmızı olur —
# doğrulanamayan bir alıntı, doğrulanmış sayılamaz (§14'ün ikinci tuzağı).
_DOCX = ("/root/.claude/uploads/a0f718bf-fd01-52d5-a508-48d77db2834c/"
         "0ca2aeab-RePieArelMAAvukatClaudeKurulumKitabi.docx")

sonuclar = []


def vaka(kod, baslik, gecti, kanit=""):
    sonuclar.append((kod, baslik, gecti, kanit))


def tr_kucult(s):
    return s.replace("I", "ı").replace("İ", "i").lower()


def norm(s):
    """Vurgu, tırnak biçimi, betik yorum öneki ve boşluk farkları silinir."""
    s = (s.replace("’", "'").replace("‘", "'")
          .replace("“", '"').replace("”", '"'))
    s = re.sub(r"\*\*|\*|`", "", s)
    s = re.sub(r"(?m)^\s*#\s?", "", s)
    s = re.sub(r"\s*#\s*", " ", s)
    s = re.sub(r"\s+", " ", s)
    return tr_kucult(s).strip()


def kitap_metni():
    """[BE/AW, 51. tur] Ortak çıkarıcı. Eski yerel sürüm Word'ün
    yumuşak satır sonunu (<w:br/>) siliyordu ve iki yanındaki
    sözcükleri YAPIŞTIRIYORDU; kitaba yapılan birebir aramalar bir
    satır sonunu geçtiğinde sessizce başarısız oluyordu."""
    return kitap_metni_ortak()


KITAP = kitap_metni()
K = norm(KITAP) if KITAP is not None else None

# Kitaba ATFEDİLMİŞ sayılan bağlam: yakınında § ya da "kitap" geçiyorsa.
ATIF = re.compile(r"§\s?\d|kitab[ıin]|kitap|becerisi|komutu", re.I)

# BEYAN EDİLMİŞ MUAFİYETLER — kitaptan DEĞİL, başka bir kaynaktan alıntılar.
# Her biri gerçek kaynağını yazar; liste küçük ve görünür kalır. Ölçüt
# "alıntı yok" demiyor, "alıntının kaynağı kitap değil" diyor.
MUAF = {
    "bu ortamda hiçbir birincil kaynağa erişilemedi.":
        "raporun KENDİ olumsuz iddiası (kural 2 ile kanıtlanıyor)",
    "sistem neyi kalıcı hâle getiriyor":
        "hiçbir takımın sormadığı soru — raporun kendi ifadesi",
    "§14, §12'nin öz-sınamasını bozuyor":
        "raporun kendi bulgu başlığı",
    "mekanizmanın erişimi eksik":
        "raporun kendi ayrımı (AM-02 olumlu kontrolü)",
    "bildirilmemenin sonuçları":
        "4054 sayılı Kanun m.11'in MADDE BAŞLIĞI, kitabın metni değil",
    "eşleşmenin yokluğu temizlik kanıtı değildir":
        "BENİM yamam (yaptirim-taramasi); kitapta yok — bkz. errata §13.3",
    "spa-inceleme becerisindeki sekiz adımlı sırayı uygula":
        "raporun kurmaca örneği (bir komutun ne diyebileceği)",
    "kurul-notu becerisindeki beş bölümlü sırayı uygula":
        "raporun kurmaca örneği",
    # I-01..I-03 tablosunun sağ sütunu "Kaynakların yazdığı" başlığını
    # taşır: bunlar MEVZUAT ve ikincil kaynak alıntılarıdır, kitabın metni
    # değil. Kitapta bulunmamaları BEKLENEN durumdur — zaten bulgunun
    # tamamı kitabın yazdığı ile kaynakların yazdığının FARKIDIR.
    "…birleşme işlemleri ile bu nitelikteki teşebbüslerin devralınmasında…":
        "2010/4 sayılı Tebliğ metni (I-01 karşılaştırması)",
    "istisnanın uygulaması 'türkiye'de yerleşik' teşebbüslerle sınırlanmış":
        "ikincil kaynak özeti (I-02 karşılaştırması)",
    "birleşme ve devralmaların kurula bildirilmesi":
        "4054 sayılı Kanun m.10 MADDE BAŞLIĞI (I-03 karşılaştırması)",
    # Raporun DÜZELTME tablosu, yanlış hâli doğru hâlin yanında GÖSTERİR.
    # Sol sütun kitaba yapılmış bir atıf değil, düzeltilmiş bir hatanın
    # sergilenmesidir. Bir yanlış alıntıdan SÖZ ETMEK, o yanlış alıntıyı
    # YAPMAK değildir — bu takımın avladığı sınıfın, takımın kendi
    # üstünde beliren hâli (altıncı kılık).
    "dayanağı olmayan bir iddia yazılmaz":
        "düzeltme tablosunda gösterilen YANLIŞ hâl (§1)",
    "boş bir arama yokluğun kanıtı değildir":
        "düzeltme tablosunda gösterilen YANLIŞ hâl (§14)",
    "eskime burada bozulma değildir":
        "düzeltme tablosunda gösterilen YANLIŞ hâl (§13.4)",
}


def alintilar():
    """(dosya, satır, ham) — kitaba atfedilmiş görünen alıntılar."""
    for dosya in ("RAPOR.md", "KITAP-ERRATA.md"):
        yol = os.path.join(_KOK_COZ, dosya)
        if not os.path.exists(yol):
            continue
        sat = io.open(yol, encoding="utf-8").read().splitlines()
        for i, s_ in enumerate(sat):
            # "→" ile başlayan satır ÖNERİLEN DÜZELTMEDİR: kitabın ne
            # dediğini değil, ne demesi gerektiğini söyler. Onu alıntı
            # saymak, düzeltmeyi kitapta aramak demektir — ve düzeltme
            # tanımı gereği kitapta YOKTUR. [anmak ≠ atfetmek]
            if s_.lstrip().startswith("→"):
                continue
            if not ATIF.search(" ".join(sat[max(0, i - 2):i + 1])):
                continue
            for m in re.findall(r'\*"([^"]{25,200})"\*', s_):
                yield dosya, i + 1, m


# --- AW-01 · kitaba atfedilen her alıntı kitapta birebir var ---------
if K is None:
    vaka("AW-01", "kitaba atfedilen her alıntı kitapta birebir var", False,
         "kitap kaynağı (%s) bulunamadı — DOĞRULANAMADI, doğrulanmış "
         "sayılamaz" % os.path.basename(_DOCX))
    vaka("AW-02", "muafiyetler gerçekten kitapta yok", False, "kaynak yok")
    vaka("AW-03", "her muafiyet gerçek kaynağını beyan ediyor", False, "kaynak yok")
    vaka("AW-04", "alıntı bulunuyor (ölçüt vakum değil)", False, "kaynak yok")
else:
    _eksik, _ok = [], 0
    for dosya, no, ham in alintilar():
        q = norm(ham)
        if q in MUAF:
            continue
        # elips ile kısaltılmış alıntı: parçaları ayrı ayrı aranır
        parcalar = [p for p in re.split(r"…|\.\.\.", ham) if len(p.strip()) >= 18]
        if parcalar and all(norm(p) in K for p in parcalar):
            _ok += 1
        else:
            _eksik.append("%s:%d %r" % (dosya, no, q[:56]))
    vaka("AW-01", "kitaba atfedilen her alıntı kitapta birebir var",
         not _eksik,
         "%d alıntı doğrulandı · BULUNAMAYAN: %s"
         % (_ok, "; ".join(_eksik[:4]) if _eksik else "yok"))

    # --- AW-02 · muafiyetler GERÇEKTEN kitapta yok -------------------
    # Muafiyet listesi bir kaçış deliği olmamalı: listede olup da kitapta
    # GEÇEN bir cümle, gereksiz yere muaf tutulmuş demektir.
    _gereksiz = [q for q in MUAF if q in K]
    vaka("AW-02", "muaf tutulan hiçbir alıntı aslında kitapta değil",
         not _gereksiz, "kitapta olduğu hâlde muaf: %s" % (_gereksiz or "yok"))

    # --- AW-03 · her muafiyet gerçek kaynağını beyan ediyor ----------
    _bos = [q for q, k in MUAF.items() if len(k.strip()) < 12]
    vaka("AW-03", "her muafiyet gerçek kaynağını yazıyor",
         not _bos, "gerekçesiz muafiyet: %s" % (_bos or "yok"))

    # --- AW-04 · ölçüt VAKUM DEĞİL: gerçekten alıntı buluyor ---------
    _sayi = sum(1 for _ in alintilar())
    vaka("AW-04", "ölçüt gerçekten alıntı topluyor (vakum değil)",
         _sayi >= 15, "%d atıflı alıntı tarandı" % _sayi)


# [AF-02] Kaybolan bir vaka, kırmızı bir vakadan kötüdür: kimse aramaz.
BEKLENEN_VAKA = 4


def rapor():
    if len(sonuclar) != BEKLENEN_VAKA:
        vaka("AW-00", "takım beyan ettiği vaka sayısını taşıyor", False,
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
