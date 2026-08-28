#!/usr/bin/env python3
"""KÖR SINAMA AE — Türkçe metni ve kendi kimliklerini desenle okuyan her yer.

Bu takım bir SINIF taraması. Sebebi, aynı kusurun dört kez ayrı ayrı
bulunmuş olması ve her seferinde YALNIZCA rastladığım örneğin düzeltilmesi:

  · §12   — `İ`.lower() 'i' + U+0307 verir; "YETKİLİ" != "yetkili"   [B-10]
  · U-05  — Türkçe eklemeli: defterine / Defterin / defteri eşleşmez
  · AD-01 — ünlü uyumu: adımLI ama bölümLÜ; desen ikincisini atlıyordu
  · AA    — takım adı TEK HARF varsayımı üç ayrı bileşende gömülüydü

Dördü de aynı kökten: **Türkçe metni ASCII sezgisiyle okumak.** Ve dördü de
ancak o örneğe çarptığımda görüldü. Bir sınıfı örnek örnek düzeltmek, sınıfı
kapatmaz — bu takım sınıfın kendisini tarar.
"""
import importlib.util
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import beklenen  # noqa: E402

KOK = os.environ.get("MAFIRM") or os.path.dirname(
    os.path.dirname(os.path.abspath(__file__)))
sonuclar = []

TR_KUCUK = "çğıöşü"
TR_BUYUK = "ÇĞİÖŞÜ"


def vaka(kod, baslik, gecti, ayrinti=""):
    sonuclar.append((kod, baslik, gecti, ayrinti))


def kaynaklar():
    """Sistemin desen taşıyan her dosyası (sınama takımları dâhil)."""
    for rel in [".claude/hooks/kapi.py", "denetim.sh",
                "birimler/rekabet/kod/esik.py"]:
        p = os.path.join(KOK, rel)
        if os.path.exists(p):
            yield rel, open(p, encoding="utf-8").read()
    sd = os.path.join(KOK, "sinama")
    for ad in sorted(os.listdir(sd)) if os.path.isdir(sd) else []:
        if ad.endswith((".py", ".sh")) and ad != os.path.basename(__file__):
            yield "sinama/" + ad, open(os.path.join(sd, ad),
                                       encoding="utf-8").read()


KAYNAK = list(kaynaklar())

# --- AE-01 · vaka kimliği deseni İKİ HARFLİ öneki kabul ediyor mu -----
# Alfabe bittiğinde (AA, AB, AC, AD) tek harf varsayan her desen KÖR olur.
# Üç bileşende bulunmuştu; bu, dördüncüyü ve sonrakileri arar.
# Yalnızca KİMLİK biçimi: [A-Z] hemen ardından '-' ve rakam. İlk sürüm her
# [A-Z] sınıfını kimlik sanıyordu ve ks_l'deki ARAÇ ADI desenini
# (r"^[A-Z]\w*\(.*\)$" — Bash, WebFetch) yanlış yere işaretliyordu.
# Kimlik biçimi kaynak metinde ŞÖYLE görünür: [A-Z]-\d  ya da  [A-Z]-[0-9]
# Ölçüt basit tutuldu; ilk daraltma fazla kaçtı ve mutasyon (kimliği tek
# harfe geri döndürmek) SAĞ KALDI — dedektörü keskinleştirirken kör ettim.
TEK_HARF = re.compile(r"\[A-Z\](?!\{1,2\})-(?:\\d|\[0-9\])")
kor = []
for rel, m in KAYNAK:
    for satir_no, satir in enumerate(m.split("\n"), 1):
        if satir.lstrip().startswith("#"):
            continue
        if TEK_HARF.search(satir) and "{1,2}" not in satir:
            kor.append("%s:%d" % (rel, satir_no))
vaka("AE-01", "vaka kimliği desenleri iki harfli öneki de görüyor",
     not kor,
     ("TEK HARF VARSAYAN: %s — AA/AB/AC/AD kimlikleri bu desenlere "
      "GÖRÜNMEZ" % ", ".join(kor)) if kor
     else "%d dosya tarandı, tek harf varsayan desen yok" % len(KAYNAK))

# --- AE-02 · Türkçe harf sınıfları TAM mı, yarım mı -------------------
# Bir desen bazı Türkçe harfleri sayıp bazılarını atlarsa, o harfleri taşıyan
# kelimeler sessizce eşleşmez. Yarım alfabe, alfabesizlikten kötüdür: kapsıyor
# gibi görünür.
SINIF = re.compile(r"\[[^\]\n\s]{2,60}\]")   # boşluklu etiketler hariç
ALFABE_ESIGI = 3   # bu kadar Türkçe harf taşıyan bir sınıf ALFABE niyetlidir
yarim = []
for rel, m in KAYNAK:
    for s_ in SINIF.findall(m):
        kucuk = [c for c in TR_KUCUK if c in s_]
        buyuk = [c for c in TR_BUYUK if c in s_]
        if len(kucuk) >= ALFABE_ESIGI and len(kucuk) < len(TR_KUCUK):
            yarim.append("%s: %s (küçük eksik: %s)"
                         % (rel, s_[:44],
                            "".join(c for c in TR_KUCUK if c not in s_)))
        if len(buyuk) >= ALFABE_ESIGI and len(buyuk) < len(TR_BUYUK):
            yarim.append("%s: %s (büyük eksik: %s)"
                         % (rel, s_[:44],
                            "".join(c for c in TR_BUYUK if c not in s_)))
vaka("AE-02", "Türkçe harf içeren her karakter sınıfı TAM",
     not yarim, "; ".join(sorted(set(yarim))[:6]) if yarim
     else "yarım Türkçe alfabe taşıyan sınıf yok")

# --- AE-03 · Türkçe metinde çıplak .lower() kullanılıyor mu -----------
# §12'nin B-10 kusuru: 'İ'.lower() 'i' + U+0307 verir. Çözüm tr_kucult'tur;
# ama çözümü YAZMAK yetmez, her yerde KULLANILMASI gerekir.
# [kendi kusurum · otuz dokuzuncu tur] Ölçüt `#` ile başlayan satırları
# atlıyordu ama BELGE DİZGELERİNİ atlamıyordu. epilog.py'nin docstring'i bu
# kusuru ANLATIYOR ve içinde hem ".lower()" hem "metin" geçiyor — yani AE,
# kusurun kendisini değil kusurdan SÖZ EDEN düzyazıyı işaretledi. Yanlış
# pozitif üreten bir kapı, bir gün içinde kapatılır (V takımının dersi).
# AN'de yorum, AM'de açıklama cümlesi; burada belge dizgesi — aynı sınıf:
# metinden söz etmek metnin kendisi değildir.
def _belgesiz(kaynak):
    return re.sub(r'("""|\'\'\')(?:.|\n)*?\1',
                  lambda m: "\n" * m.group(0).count("\n"), kaynak)


ciplak = []
for rel, m in KAYNAK:
    if not rel.endswith(".py"):
        continue
    m = _belgesiz(m)
    for satir_no, satir in enumerate(m.split("\n"), 1):
        if satir.lstrip().startswith("#") or "tr_kucult" in satir:
            continue
        if re.search(r"\.lower\(\)", satir) and "ascii" not in satir.lower():
            # Kimlik/dosya adı gibi ASCII bağlamlar muaf; Türkçe metin değil.
            if re.search(r"metin|icerik|içerik|prose|duz|gövde|govde|satir",
                         satir, re.I):
                ciplak.append("%s:%d" % (rel, satir_no))
vaka("AE-03", "Türkçe metin üzerinde çıplak .lower() yok",
     not ciplak,
     ("ÇIPLAK: %s — 'İ' burada 'i'+U+0307 olur [B-10]" % ", ".join(ciplak))
     if ciplak else "Türkçe metin küçültmeleri tr_kucult üzerinden")

# --- AE-04 · DAVRANIŞ: Türkçe harfli metin kapıdan aynı geçiyor mu ---
# Sınıfın gerçek sonucu burada görülür: çğıöşü taşıyan bir cümle ile ASCII'ye
# indirgenmiş hâli AYNI kararı almalı — ikisi de aynı hukuki iddiayı taşıyor.
_sp = importlib.util.spec_from_file_location(
    "kapi_ae", os.path.join(KOK, ".claude/hooks/kapi.py"))
_k = importlib.util.module_from_spec(_sp)
_sp.loader.exec_module(_k)

CIFTLER = [
    ("Kurul'a bildirimde bulunmanız gerekir.",
     "Kurul'a bildirimde bulunmaniz gerekir."),
    ("İŞLEM BİLDİRİME TABİDİR.", "ISLEM BILDIRIME TABIDIR."),
    ("Şirketin payları devredilecektir.", "Sirketin paylari devredilecektir."),
]
ayrisan = []
for tr, ascii_ in CIFTLER:
    a = tuple(sorted(x for x, _ in _k.denetle(tr)))
    b = tuple(sorted(x for x, _ in _k.denetle(ascii_)))
    if a != b:
        ayrisan.append("%r -> %s ; ASCII -> %s" % (tr[:34], a, b))
vaka("AE-04", "Türkçe harfli metin ile ASCII hâli aynı kararı alıyor",
     not ayrisan, "; ".join(ayrisan) if ayrisan
     else "%d çift, kararlar örtüşüyor" % len(CIFTLER))

# --- AE-05 · tr_kucult gerçekten doğru mu (dört köşe) ----------------
KOSE = [("İ", "i"), ("I", "ı"), ("Ş", "ş"), ("YETKİLİ", "yetkili")]
bozuk = [("%s -> %r (beklenen %r)" % (g, _k.tr_kucult(g), b))
         for g, b in KOSE if _k.tr_kucult(g) != b]
vaka("AE-05", "Türkçe küçültme dört köşede de doğru",
     not bozuk, "; ".join(bozuk) if bozuk
     else "İ→i, I→ı, Ş→ş, YETKİLİ→yetkili")


BEKLENEN_VAKA = 5


def rapor():
    if len(sonuclar) != BEKLENEN_VAKA:
        vaka("AE-00", "takım beyan ettiği vaka sayısını taşıyor", False,
             "beyan %d, bulunan %d" % (BEKLENEN_VAKA, len(sonuclar)))
    print("=" * 96)
    print("KÖR SINAMA AE — Türkçeyi ve kendi kimliklerini desenle okumak")
    print("=" * 96)
    for kod, baslik, gecti, ayrinti in sonuclar:
        d, _ = beklenen.durum(kod, gecti)
        print("%s %-7s %s" % (d, kod, baslik))
        if ayrinti:
            print("        %s" % ayrinti)
    _s, _c = beklenen.ozet([(x[0], x[2]) for x in sonuclar])
    print("-" * 96)
    print("%d vaka · %d geçti · %d beklenen · %d SİNYAL"
          % (len(sonuclar), _c["GEÇTİ"], _c["BEKLENEN"], _s))
    return _s


if __name__ == "__main__":
    sys.exit(min(rapor(), 120))
