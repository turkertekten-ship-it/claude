#!/usr/bin/env python3
"""KÖR SINAMA AC — kapının verdiği cevap MAKİNEYE göre değişiyor mu.

S takımı taşınabilirliği YOL düzeyinde ölçtü: klon ile kaynak ağaç aynı
sonucu veriyor mu. Ama bir kurulumun içinde bulunduğu ORTAM da değişkendir:
saat dilimi, yerel ayar, tarih. On yirmi tur boyunca hiçbir takım aynı
metnin farklı bir makinede aynı cevabı alıp almadığını sormadı.

Bu sistem için soru kozmetik değil. Kitap §6'da SINIR ÖTESİ bir pratik
kuruyor: aynı dosyalar İstanbul, Londra, New York ve Singapur arasında
dolaşır. Bir tarih damgası saat dilimi taşımaz — ama makinenin "bugün"ü
taşır. İkisini karşılaştırmak, olmayan bir saat dilimini kıyasa sokar.

Ölçülen: aynı metin, farklı ortam, aynı karar mı.
"""
import datetime
import json
import os
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import beklenen  # noqa: E402

KOK = os.environ.get("MAFIRM") or os.path.dirname(
    os.path.dirname(os.path.abspath(__file__)))
KAPI = os.path.join(KOK, ".claude/hooks/kapi.py")
sonuclar = []

# Dünyanın uçları: UTC-11'den UTC+14'e, 26 saatlik yayılım.
DILIMLER = ["Europe/Istanbul", "UTC", "Pacific/Midway", "Pacific/Kiritimati",
            "America/Los_Angeles", "Asia/Singapore", "America/New_York"]
YERELLER = ["C", "C.UTF-8", "tr_TR.UTF-8", "en_US.UTF-8", "de_DE.UTF-8"]


def vaka(kod, baslik, gecti, ayrinti=""):
    sonuclar.append((kod, baslik, gecti, ayrinti))


def kanca(icerik, tz=None, lang=None, arac="Write", alan="content"):
    env = dict(os.environ)
    if tz:
        env["TZ"] = tz
    if lang:
        env["LANG"] = env["LC_ALL"] = lang
    p = json.dumps({"tool_name": arac, "tool_input": {alan: icerik}})
    r = subprocess.run([sys.executable, KAPI], input=p,
                       capture_output=True, text=True, env=env)
    return r.returncode, (r.stderr or "").strip()


def kapilar(err):
    import re
    return tuple(sorted(set(re.findall(r"BLOKLANDI \[(\w+)\]", err))))


BUGUN = datetime.date.today().isoformat()
TAM = ("Eşik 1.000.000.000 TL (2010/4 sayılı Tebliğ m.7).\n"
       "Doğrulama: %s\n"
       "Kontrol edildi: rekabet.gov.tr (%s) · bulunamayan: yok\n" % (BUGUN, BUGUN))

# --- AC-01 · BUGÜN damgalı bir doğrulama hiçbir dilimde reddedilmiyor --
# Bir tarih damgası saat dilimi taşımaz. Dünyanın herhangi bir yerinde
# "bugün" olan bir tarih, başka bir makinede en çok bir gün ileride görünür.
reddeden = []
for tz in DILIMLER:
    _rc, err = kanca(TAM, tz=tz)
    if "guncellik" in kapilar(err):
        reddeden.append("%s (%s)" % (tz, err.split("\n")[0][:70]))
vaka("AC-01", "bugün damgalı doğrulama hiçbir saat diliminde reddedilmiyor",
     not reddeden,
     ("REDDEDEN DİLİM: %s — belge doğru, kapı yanlış; İstanbul'da yazılan "
      "bir doğrulama başka bir masada bloklanıyor" % "; ".join(reddeden))
     if reddeden else "%d dilimin hepsinde geçiyor" % len(DILIMLER))

# --- AC-02 · aynı metin bütün dilimlerde AYNI kapı kümesini veriyor ----
ORNEKLER = {
    "tam biçimli": TAM,
    "dayanaksız eşik": "Ciro eşiği 3.000.000.000 TL'dir.\n",
    "tavsiye kipi": "Kurul'a bildirimde bulunmanız gerekir.\n",
    "meşru kısa not": "Toplantı 15.00'e alındı.\n",
}
sapan = []
for ad, metin in ORNEKLER.items():
    kumeler = {tz: kapilar(kanca(metin, tz=tz)[1]) for tz in DILIMLER}
    if len(set(kumeler.values())) > 1:
        sapan.append("%s -> %s" % (ad, {t: k for t, k in kumeler.items()}))
vaka("AC-02", "aynı metin bütün saat dilimlerinde aynı kararı alıyor",
     not sapan, "; ".join(sapan)[:300] if sapan
     else "%d metin × %d dilim, sapma yok" % (len(ORNEKLER), len(DILIMLER)))

# --- AC-03 · yerel ayar kararı değiştirmiyor --------------------------
# Türkçe İ/ı tuzağı §12'de zaten bulunmuştu; burada sorulan, YEREL AYARIN
# kendisinin kararı kaydırıp kaydırmadığı.
TR_ORNEK = ("YETKİLİ AVUKAT GÖRÜŞÜ GEREKEN KONULAR\n\n"
            "Kurul'a bildirimde bulunmanız gerekir.\n")
yerel_sapan = []
for ad, metin in list(ORNEKLER.items()) + [("büyük harfli Türkçe", TR_ORNEK)]:
    kumeler = {}
    for lang in YERELLER:
        kumeler[lang] = kapilar(kanca(metin, lang=lang)[1])
    if len(set(kumeler.values())) > 1:
        yerel_sapan.append("%s -> %s" % (ad, kumeler))
vaka("AC-03", "aynı metin bütün yerel ayarlarda aynı kararı alıyor",
     not yerel_sapan, "; ".join(yerel_sapan)[:300] if yerel_sapan
     else "%d metin × %d yerel ayar, sapma yok"
          % (len(ORNEKLER) + 1, len(YERELLER)))

# --- AC-04 · gelecek tarih kontrolü HÂLÂ çalışıyor --------------------
# Yanlış pozitifi, kontrolü kapatarak çözmek en kolay ve en yanlış yoldur.
# Tolerans SINIRLI olmalı: gerçekten ileri bir tarih hâlâ bloklanmalı.
ileri = (datetime.date.today() + datetime.timedelta(days=5)).isoformat()
_rc, err = kanca("Eşik 1.000.000.000 TL (2010/4 sayılı Tebliğ m.7).\n"
                 "Doğrulama: %s\n"
                 "Kontrol edildi: x (%s) · bulunamayan: yok\n" % (ileri, ileri))
vaka("AC-04", "gerçekten gelecek tarihli doğrulama hâlâ bloklanıyor",
     "guncellik" in kapilar(err),
     "5 gün ileri tarih: %s"
     % ("bloklandı" if "guncellik" in kapilar(err)
        else "GEÇTİ — tolerans kontrolü öldürmüş"))

# --- AC-05 · bayat tarih kontrolü de HÂLÂ çalışıyor -------------------
bayat = (datetime.date.today() - datetime.timedelta(days=400)).isoformat()
_rc, err = kanca("Eşik 1.000.000.000 TL (2010/4 sayılı Tebliğ m.7).\n"
                 "Doğrulama: %s\n"
                 "Kontrol edildi: x (%s) · bulunamayan: yok\n" % (bayat, bayat))
vaka("AC-05", "bayat doğrulama hâlâ bloklanıyor",
     "guncellik" in kapilar(err),
     "400 günlük tarih: %s"
     % ("bloklandı" if "guncellik" in kapilar(err) else "GEÇTİ — kontrol ölü"))


BEKLENEN_VAKA = 5


def rapor():
    if len(sonuclar) != BEKLENEN_VAKA:
        vaka("AC-00", "takım beyan ettiği vaka sayısını taşıyor", False,
             "beyan %d, bulunan %d" % (BEKLENEN_VAKA, len(sonuclar)))
    print("=" * 96)
    print("KÖR SINAMA AC — kapının cevabı makineye göre değişiyor mu")
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
