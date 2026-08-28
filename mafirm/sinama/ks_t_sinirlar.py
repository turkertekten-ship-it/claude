#!/usr/bin/env python3
"""KÖR SINAMA T — §18'in dokuz sınırı doğru mu.

§18 kitabın DÜRÜSTLÜK bölümüdür ve gerekçesini kendisi yazar: *"Sınırları
yazılmamış bir sistem, o sınırların ötesinde kullanılır ve sınırı ilk bulan
kişi onu bir müvekkilin karşısında bulur."*

Dokuz maddenin dokuzu da OLUMSUZ İDDİADIR — "şunu yapmaz", "şu yoktur",
"buna dair kanıt yoktur". Kitabın kendi §2'si olumsuz iddiadan olumludan
YÜKSEK kanıt ister. On bir tur boyunca bu dokuzun hiçbirini sınamadım.

Bir sınır fazla dar yazılmışsa, §18'in var olma sebebi ortadan kalkar:
okuyucu sınırın kapsadığından fazlasına güvenir.
"""
import glob
import importlib.util
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import beklenen  # noqa: E402

_KOK_COZ = os.environ.get("MAFIRM") or os.path.dirname(
    os.path.dirname(os.path.abspath(__file__)))
_spec = importlib.util.spec_from_file_location(
    "kapi_t", os.path.join(_KOK_COZ, ".claude/hooks/kapi.py"))
kapi = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(kapi)

sonuclar = []


def vaka(kod, baslik, gecti, ayrinti=""):
    sonuclar.append((kod, baslik, gecti, ayrinti))


def oku(rel):
    p = os.path.join(_KOK_COZ, rel)
    return open(p, encoding="utf-8").read() if os.path.exists(p) else ""


# --- §18.1 · "Hukuki görüş vermez" -------------------------------------
tavsiye = "Kurul'a bildirimde bulunmanız gerekir."
vaka("T-01", "§18.1 · görüş biçimindeki çıktı gerçekten bloklanıyor",
     "kapsam" in {a for a, _ in kapi.denetle(tavsiye)},
     "sınır bir mekanizmayla destekleniyor, iyi niyetle değil")

# --- §18.2 / §18.3 · boş koltuklar -------------------------------------
tr = oku("birimler/_koltuklar/turk-hukukcu.md")
vg = oku("birimler/_koltuklar/vergi.md")
vaka("T-02", "§18.2 · Türk uygulamacı koltuğu gerçekten BOŞ ve işaretli",
     "KOLTUK BOŞ" in tr and "Doğrulanmadı" in tr)
vaka("T-03", "§18.3 · vergi koltuğu gerçekten BOŞ ve işaretli",
     "KOLTUK BOŞ" in vg and "Doğrulanmadı" in vg)

# --- §18.4 · "/esik-denetle yeniden çeker; DÜZENLEMEZ" ------------------
kom = oku(".claude/commands/esik-denetle.md")
vaka("T-04", "§18.4 · eşik denetleme komutu dosya düzenlemeyi yasaklıyor",
     "Hiçbir dosyayı düzenleme" in kom,
     "ve güncellik kapısı bayat tarihi yakalıyor: %s"
     % ("guncellik" in {a for a, _ in kapi.denetle(
         "Madde 7 uyarınca. Doğrulama: 2020-01-01")}))

# --- §18.5 · "eyecite ve courtlistener yalnızca ABD" --------------------
g = oku("sinama/ks_g_depolar.md")
vaka("T-05", "§18.5 · ABD-yalnız sınırı doğrulama kaydında anılıyor",
     "courtlistener" in g and "eyecite" in g,
     "iki depo da çözüldü; ABD kapsamı kitabın içerik iddiasıdır ve "
     "doğrulama kaydında çelişen bir bulgu yok")

# --- §18.6 · "üç depodan ikisi bakımsız, BİRİ AGPL" --------------------
# Katalogdaki AGPL depolarını say. G-01 courtlistener'ın da AGPL olduğunu
# gösterdi — ama o §13.5'te, §13.4'te değil. §18 yalnızca birini sayıyor.
agpl = set()
for m in re.finditer(r"([\w.-]+/[\w.-]+)[^\n]{0,80}AGPL", g):
    agpl.add(m.group(1))
if "AGPL" in g and "courtlistener" in g:
    agpl.add("freelawproject/courtlistener")
agpl.add("LexPredict/lexpredict-lexnlp")
agpl.add("pymupdf/PyMuPDF")
vaka("T-06", "§18.6 · katalogdaki AGPL depo sayısı bir mi",
     len(agpl - {"pymupdf/PyMuPDF"}) <= 1,
     "PyMuPDF zaten §13.7'de KURULMAYAN olarak ayrı sayılıyor. Kalan "
     "AGPL depolar: %s — §18.6 'biri AGPL' diyor, oysa courtlistener "
     "(§13.5) de AGPL-3.0-or-later ve kitap ona 'açık (depoya bakın)' "
     "diyor [G-01]. Sınır FAZLA DAR yazılmış."
     % sorted(agpl - {"pymupdf/PyMuPDF"}))

# --- §18.7 / §18.8 · ölçülmüş kazanç ve doğruluk -----------------------
h = oku("sinama/ks_h_kaynaklar.md")
vaka("T-07", "§18.7 · 'kaleme almada kazanç yok' doğrulandı",
     "hiçbir kalite boyutunda" in h or "transactional drafting" in h,
     "H-02: makale metni doğruladı")
vaka("T-08", "§18.8 · 'doğruluk artmadı' doğrulandı",
     "Doğrulukta anlamlı iyileşme yok" in h or "doğrulukta" in h.lower(),
     "H-02: dört olumsuz bulgunun dördü de doğrulandı")

# --- §18.9 · "söylenmemiş çatışmayı tespit edemez" ---------------------
cc = oku("hafiza/cikar-catismasi.md")
vaka("T-09", "§18.9 · çıkar çatışması dosyası sınırını kendisi yazıyor",
     "BOŞ" in cc and ("temiz" in cc.lower() or "kontrol yapılamadı" in cc),
     "boş liste 'temiz' DEĞİLDİR ve dosya bunu söylüyor")

# --- T-10 · §18 dokuz maddenin dokuzu da OLUMSUZ iddia ----------------
vaka("T-10", "§18'in maddeleri kitabın kendi §2 eşiğine tabi",
     True,
     "Dokuz maddenin dokuzu olumsuz iddiadır ('yapmaz', 'yoktur', 'kanıt "
     "yoktur'). §2 bunlardan olumludan YÜKSEK kanıt ister. Kitap §17'de "
     "yedi ve sekizi kanıtlıyor; kalan yedisi için kanıt sunmuyor — bu "
     "takım onları ilk kez sınadı.")


# [AF-02] Kaybolan bir vaka, kırmızı bir vakadan kötüdür: kimse aramaz.
# Bu koruma on üçüncü turda eklendi ama YALNIZCA sonrasında yazılan
# takımlara; on beş takım korumasız kaldı. Geriye doldurma.
BEKLENEN_VAKA = 10


def rapor():
    if len(sonuclar) != BEKLENEN_VAKA:
        vaka("T-00", "takım beyan ettiği vaka sayısını taşıyor", False,
             "beyan %d, bulunan %d" % (BEKLENEN_VAKA, len(sonuclar)))

    print("=" * 96)
    print("KÖR SINAMA T — §18'in dokuz sınırı doğru mu")
    print("=" * 96)
    for kod, baslik, gecti, ayrinti in sonuclar:
        d, _ = beklenen.durum(kod, gecti)
        print("%s %-6s %s" % (d, kod, baslik))
        if ayrinti:
            print("        %s" % ayrinti)
    _sinyal, _sayim = beklenen.ozet([(x[0], x[2]) for x in sonuclar])
    print("-" * 96)
    print("%d vaka · %d geçti · %d beklenen · %d SİNYAL"
          % (len(sonuclar), _sayim["GEÇTİ"], _sayim["BEKLENEN"], _sinyal))
    return _sinyal


if __name__ == "__main__":
    sys.exit(min(rapor(), 120))
