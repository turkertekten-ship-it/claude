#!/usr/bin/env python3
"""KÖR SINAMA W — sessizce boş arama kaynakları.

§14 kuralı kendisi yazıyor:

    "Boş bir arama yokluğun kanıtı değildir. Kayıtlara bak."

Kitap bunu GitHub araması için söylüyor. Ama aynı tuzağı KENDİ dosya
düzeninde kuruyor: §2 `emsal/` dizinini "onaylı madde bankası" olarak
açıyor, §10 `emsal-bulucu` alt ajanını yalnızca orayı aramak üzere
görevlendiriyor, §14 `once-arastir`ın üçüncü adımını oraya yönlendiriyor —
ve bankayı HİÇ DOLDURMUYOR.

Sonuç: banka boşken ajan "yeterince yakın emsal yok" der. Okuyucu bunu
DÜNYAYA dair bir tespit sanır; oysa BOŞ BİR DOLABA dair bir tespittir.
İkisi aynı cümleyle ifade edilirse §2 çiğnenmiş olur — olumsuz iddia,
kanıtsız.

Aynı kusurun bir örneği zaten kapatılmıştı: boş müvekkil ad kaydı denetimde
her koşumda sesli bildiriliyor. Bu takım kalan örnekleri arar.
"""
import os
import re
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import beklenen  # noqa: E402

KOK = os.environ.get("MAFIRM") or os.path.dirname(
    os.path.dirname(os.path.abspath(__file__)))
sonuclar = []


def vaka(kod, baslik, gecti, ayrinti=""):
    sonuclar.append((kod, baslik, gecti, ayrinti))


def oku(rel):
    p = os.path.join(KOK, rel)
    return open(p, encoding="utf-8").read() if os.path.exists(p) else ""


def dolu_mu(rel):
    p = os.path.join(KOK, rel)
    if not os.path.isdir(p):
        return None
    return any(not a.startswith(".") for _r, _d, fs in os.walk(p) for a in fs)


# --- W-01 · hangi dizinler ARAMA KAYNAĞI olarak adlandırılıyor ---------
# Kaynak: bileşenlerin KENDİ metni. Kod okunmadı; ajan ve beceri
# dosyalarının söylediği yer aranır.
ARANAN = {}
for kok, _d, fs in os.walk(os.path.join(KOK, ".claude")):
    for ad in fs:
        if not ad.endswith(".md"):
            continue
        yol = os.path.relpath(os.path.join(kok, ad), KOK)
        m = open(os.path.join(kok, ad), encoding="utf-8").read()
        for hedef in re.findall(r"`(emsal/|hafiza/|birimler/\*/emsal/)`", m):
            ARANAN.setdefault(hedef.rstrip("/"), set()).add(yol)

vaka("W-01", "arama kaynağı olarak adlandırılan dizinler tespit edildi",
     bool(ARANAN),
     "; ".join("%s <- %s" % (k, ", ".join(sorted(v)))
               for k, v in sorted(ARANAN.items())) or "hiçbiri bulunamadı")

# --- W-02 · adlandırılan her kaynak ya DOLU ya da SESLİ ----------------
denetim_ciktisi = subprocess.run(
    ["bash", os.path.join(KOK, "denetim.sh"), "--yapisal"],
    capture_output=True, text=True).stdout
# TERS MUTASYON DÜZELTMESİ: ilk sürüm `emsal/` ile `birimler/*/emsal/`yi AYRI
# kaynak sayıyor ve duyuruyu "emsal" alt dizgesiyle arıyordu. Denetim ikisini
# TEK BİR BANKA olarak sayar ve duyuruyu "madde bankası" diye etiketler.
# Bankayı doldurup duyuru sustuğunda takım hâlâ kırmızı kalıyordu — yani
# ölçtüğü şeyin tanımı, ölçenin tanımıyla aynı değildi.
def _banka_dosya_sayisi():
    yollar = [os.path.join(KOK, "emsal")] + [
        os.path.join(KOK, "birimler", b, "emsal")
        for b in sorted(os.listdir(os.path.join(KOK, "birimler")))
        if os.path.isdir(os.path.join(KOK, "birimler", b, "emsal"))]
    return sum(1 for y in yollar if os.path.isdir(y)
               for _r, _d, fs in os.walk(y)
               for a in fs if not a.startswith("."))


sessiz_bos = []
if any(h.startswith(("emsal", "birimler/")) for h in ARANAN):
    if _banka_dosya_sayisi() == 0 and "madde bankası" not in denetim_ciktisi:
        sessiz_bos.append("emsal + birimler/*/emsal (onaylı madde bankası)")
for hedef in sorted(ARANAN):
    if hedef.startswith(("emsal", "birimler/")):
        continue
    if dolu_mu(hedef) is False and hedef not in denetim_ciktisi:
        sessiz_bos.append(hedef)
vaka("W-02", "boş bir arama kaynağı denetimde SESLİ bildiriliyor",
     not sessiz_bos,
     ("SESSİZCE BOŞ: %s — arayan bileşen 'bulunamadı' der ve okuyucu bunu "
      "dünyaya dair bir tespit sanır" % ", ".join(sessiz_bos))
     if sessiz_bos else "boş kaynak yok ya da hepsi sesli")

# --- W-03 · arayan bileşen BOŞ KAYNAK ile BULUNAMADI'yı ayırıyor mu ----
# İlk sürüm ANAHTAR KELİME arıyordu ve once-arastir'ı GEÇİRDİ — ama onun
# "Boş bir GitHub araması yokluğun kanıtı değildir" cümlesi BAŞKA bir aramaya
# dairdir ve `emsal/` atfından uzaktadır. Doğru cevabı yanlış sebeple vermek,
# yanlış cevap vermekle aynı sınıftandır. Ayrım, ARADIĞI kaynağın YANINDA
# aranır; ayrıca §14'ün "bulunamayan:" alanı da geçerli bir mekanizmadır.
YAKIN = 700
BOSLUK = re.compile(r"boş|doldurul|bulunamayan\s*:", re.I)
ayirmayan = []
for yol in sorted({y for v in ARANAN.values() for y in v}):
    m = oku(yol)
    pencereler = [m[max(0, x.start() - YAKIN):x.end() + YAKIN]
                  for x in re.finditer(r"`?(?:emsal/|hafiza/)", m)]
    if not any(BOSLUK.search(p_) for p_ in pencereler):
        ayirmayan.append(yol)
vaka("W-03", "arayan bileşen BOŞ KAYNAK ile BULUNAMADI'yı ayırıyor",
     not ayirmayan,
     ("ayırmıyor: %s — §2 uyarınca 'emsal yok' bir olumsuz iddiadır ve "
      "boş bir dolap onun kanıtı değildir" % ", ".join(ayirmayan))
     if ayirmayan else "arayan bileşenlerin hepsi ayrımı yazıyor")

# --- W-04 · aynı kusurun kapatılmış örneği hâlâ kapalı mı -------------
vaka("W-04", "boş müvekkil ad kaydı hâlâ sesli bildiriliyor",
     "müvekkil ad kaydı" in denetim_ciktisi,
     "denetim bu kaydı her koşumda bildiriyor (regresyon koruması)")


BEKLENEN_VAKA = 4


def rapor():
    if len(sonuclar) != BEKLENEN_VAKA:
        vaka("W-00", "takım beyan ettiği vaka sayısını taşıyor", False,
             "beyan %d, bulunan %d" % (BEKLENEN_VAKA, len(sonuclar)))
    print("=" * 96)
    print("KÖR SINAMA W — sessizce boş arama kaynakları")
    print("=" * 96)
    for kod, baslik, gecti, ayrinti in sonuclar:
        d, _ = beklenen.durum(kod, gecti)
        print("%s %-6s %s" % (d, kod, baslik))
        if ayrinti:
            print("        %s" % ayrinti)
    _s, _c = beklenen.ozet([(x[0], x[2]) for x in sonuclar])
    print("-" * 96)
    print("%d vaka · %d geçti · %d beklenen · %d SİNYAL"
          % (len(sonuclar), _c["GEÇTİ"], _c["BEKLENEN"], _s))
    return _s


if __name__ == "__main__":
    sys.exit(min(rapor(), 120))
