#!/usr/bin/env python3
"""KÖR SINAMA AA — kapı ARIZALANDIĞINDA hangi yöne düşüyor.

Kanca her Write, Edit, Bash, WebSearch ve WebFetch çağrısının önünde durur.
Kitap §12'de çıkış kodunu yazar: 2 bloklar. PreToolUse sözleşmesinde 2 DIŞINDA
her sıfırdan farklı kod "bloklamayan hata"dır — yani araç çağrısı DEVAM EDER.

Bunun anlamı şudur: **kancadaki işlenmemiş her istisna, sessizce AÇIK yönde
çözülür.** Kural 6 uygulanmaz ve kimse bir şey görmez.

Bu teorik değil. Bu kurulumda iki kez oldu:
  · on dördüncü tur — `bugun` dizge geldiğinde TypeError
  · on yedinci tur  — _Bulgu nesnesinde group() yokluğunda AttributeError
İkisi de düzenleyici bağlamda yüzde geçen HER belgede kapıyı devre dışı
bıraktı. O turlarda "çöken kapı kötüdür" yazdım ama YÖNÜNÜ ölçmedim.

Üçüncü bir arıza biçimi daha var ve ikisinden de kötüdür: **hiç bitmemek.**
Bloklamayan da olsa bloklayan da olsa, dönmeyen bir kapı pratiği durdurur.
"""
import json
import os
import subprocess
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import beklenen  # noqa: E402

KOK = os.environ.get("MAFIRM") or os.path.dirname(
    os.path.dirname(os.path.abspath(__file__)))
KAPI = os.path.join(KOK, ".claude/hooks/kapi.py")
SURE_BUTCESI = 5.0            # saniye · bir kanca insanı bekletmemelidir
sonuclar = []


def vaka(kod, baslik, gecti, ayrinti=""):
    sonuclar.append((kod, baslik, gecti, ayrinti))


def kanca(ham, zaman=30):
    t = time.time()
    try:
        r = subprocess.run([sys.executable, KAPI], input=ham,
                           capture_output=True, text=True, timeout=zaman)
        return r.returncode, (r.stderr or "").strip(), time.time() - t
    except subprocess.TimeoutExpired:
        return None, "ZAMAN AŞIMI", time.time() - t


def olay(**kw):
    return json.dumps(kw)


# Düşmanca ve bozuk olay biçimleri. Hiçbiri bir POLİTİKA ihlali değil;
# hepsi İÇ ARIZA. Sorulan tek şey: kapı hangi yöne düşüyor.
BICIMLER = [
    ("AA-01a", "bozuk JSON", "{bozuk", True),
    ("AA-01b", "boş girdi", "", True),
    ("AA-01c", "tool_input yok", olay(tool_name="Write"), False),
    ("AA-01d", "tool_input dizge", olay(tool_name="Write", tool_input="x"), False),
    ("AA-01e", "tool_input liste", olay(tool_name="Write", tool_input=[1, 2]), False),
    ("AA-01f", "tool_name yok", olay(tool_input={"content": "x"}), False),
    ("AA-01g", "tool_name None", olay(tool_name=None, tool_input={"content": "x"}), False),
    ("AA-01h", "içerik None", olay(tool_name="Write", tool_input={"content": None}), False),
    ("AA-01i", "içerik sayı", olay(tool_name="Write", tool_input={"content": 42}), False),
    ("AA-01j", "derin iç içe", olay(tool_name="Write",
                                    tool_input={"a": {"b": {"c": ["x"]}}}), False),
    ("AA-01k", "JSON dizi (nesne değil)", "[1,2,3]", True),
    ("AA-01l", "JSON null", "null", True),
]
gecerli_kod, kotu = {0, 2}, []
for kod, ad, ham, _dis in BICIMLER:
    rc, err, sn = kanca(ham)
    ok = rc in gecerli_kod
    if not ok:
        kotu.append("%s -> %s" % (ad, "zaman aşımı" if rc is None else "çıkış %d" % rc))
    vaka(kod, "bozuk olay: %s" % ad, ok,
         "çıkış %s (%.0f ms)%s"
         % ("ZAMAN AŞIMI" if rc is None else rc, sn * 1000,
            "" if ok else " — 2 DIŞINDA sıfırdan farklı kod = BLOKLAMAYAN "
                          "hata; araç çağrısı DEVAM EDER, kural 6 uygulanmaz"))

# --- AA-02 · dışarı giden kanalda iç arıza KAPALI yönde çözülüyor mu --
# Kapıyı kasten bozamayız; ama arıza politikasının YAZILI olduğunu ve
# dışarı kanalını kapattığını doğrulayabiliriz.
kaynak = open(KAPI, encoding="utf-8").read()
politika = ("ic-ariza" in kaynak and "return 2" in kaynak
            and "disari = True" in kaynak)
vaka("AA-02", "ayrıştırma SONRASI arıza politikası yazılı ve dışarıda kapalı",
     politika,
     "kanca, ayrıştırma sonrası istisnayı yakalayıp dışarı kanalında 2 "
     "döndürüyor" if politika
     else "ayrıştırma sonrası istisna işlenmiyor — her çökme çıkış 1 = AÇIK")

# --- AA-03 · patolojik girdide SÜRE sınırlı ---------------------------
# Boşluksuz tek bir uzun belirteç: base64 blok, küçültülmüş dosya, boşluksuz
# çıkarılmış PDF metni. Gerçek hukuk pratiğinde hepsi olur.
for n in (20000, 80000, 200000):
    rc, err, sn = kanca(olay(tool_name="Write",
                             tool_input={"content": "x" * n}), zaman=30)
    vaka("AA-03-%d" % (n // 1000),
         "boşluksuz %d karakter bütçe içinde bitiyor" % n,
         rc in gecerli_kod and sn < SURE_BUTCESI,
         "%.0f ms (bütçe %.0f ms) çıkış %s"
         % (sn * 1000, SURE_BUTCESI * 1000,
            "ZAMAN AŞIMI" if rc is None else rc))

# --- AA-04 · gerçek belge boyutunda süre makul -----------------------
gercek = "Bu bir sözleşme maddesidir. " * 15000        # ~400 KB düzyazı
rc, err, sn = kanca(olay(tool_name="Write", tool_input={"content": gercek}),
                    zaman=30)
vaka("AA-04", "400 KB gerçek düzyazı bütçe içinde",
     rc in gecerli_kod and sn < SURE_BUTCESI,
     "%.0f ms çıkış %s" % (sn * 1000, "ZAMAN AŞIMI" if rc is None else rc))

# --- AA-05 · dayanıklılık DOĞRULUĞU bozmadı --------------------------
# Sınırlandırılmış desen hâlâ ateşlemeli; yoksa hız uğruna kapı satılmış olur.
DOGRULUK = [
    ("tavsiye kipi bloklanıyor",
     olay(tool_name="Write",
          tool_input={"content": "Kurul'a bildirimde bulunmanız gerekir."}), 2),
    ("kod adı dışarı çıkamıyor",
     olay(tool_name="WebSearch", tool_input={"query": "Proje Anadolu ciro"}), 2),
    ("meşru metin geçiyor",
     olay(tool_name="Write",
          tool_input={"content": "Toplantı 15.00'e alındı.\n"}), 0),
]
hatali = []
for ad, ham, bekleniyor in DOGRULUK:
    rc, _e, _s = kanca(ham)
    if rc != bekleniyor:
        hatali.append("%s (beklenen %d, gelen %s)" % (ad, bekleniyor, rc))
vaka("AA-05", "dayanıklılık yaması doğruluğu bozmadı",
     not hatali, "; ".join(hatali) if hatali
     else "üç davranış vakası da beklendiği gibi")


BEKLENEN_VAKA = len(BICIMLER) + 6


def rapor():
    if len(sonuclar) != BEKLENEN_VAKA:
        vaka("AA-00", "takım beyan ettiği vaka sayısını taşıyor", False,
             "beyan %d, bulunan %d" % (BEKLENEN_VAKA, len(sonuclar)))
    print("=" * 96)
    print("KÖR SINAMA AA — kapı arızalandığında hangi yöne düşüyor")
    print("=" * 96)
    for kod, baslik, gecti, ayrinti in sonuclar:
        d, _ = beklenen.durum(kod, gecti)
        print("%s %-9s %s" % (d, kod, baslik))
        if ayrinti:
            print("        %s" % ayrinti)
    _s, _c = beklenen.ozet([(x[0], x[2]) for x in sonuclar])
    print("-" * 96)
    print("%d vaka · %d geçti · %d beklenen · %d SİNYAL"
          % (len(sonuclar), _c["GEÇTİ"], _c["BEKLENEN"], _s))
    return _s


if __name__ == "__main__":
    sys.exit(min(rapor(), 120))
