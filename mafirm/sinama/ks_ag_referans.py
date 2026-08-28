#!/usr/bin/env python3
"""KÖR SINAMA AG — kitaba sadık karşılaştırma tabanı eksiksiz mi.

`yamalar/DEGISIKLIKLER.md` bir SÖZ veriyor:

    "Kitaba sadık sürümler yamalar/kitaba-sadik/ altındadır. Karşılaştırma
     denetlenebilir olsun diye HİÇBİRİ SİLİNMEDİ."

Bu söz, raporun en önemli iddialarının dayanağıdır: J-01s ve J-07s kitabın
davranışını ÖLÇER, Z-05 kitaba sadık dosyayı geri koyup denetimin kırmızıya
döndüğünü gösterir, AA ve AB'nin atıfları "kusur kitabın" derken bu tabana
bakar. Taban eksikse, o cümlelerin hepsi eksik bir kıyasa dayanır.

Sözü hiçbir şey kontrol etmiyordu — ve söz DOĞRU DEĞİLDİ.

Kitaba ait dosya listesi, kitabın metninden (doc.txt) elle çıkarıldı ve
burada BEYAN edilir; kitap metni kuruluma dâhil olmadığı için koşum anında
yeniden türetilemez. Beyanın kendisi AG-04'te kitabın davranışıyla sınanır.
"""
import hashlib
import io
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import beklenen  # noqa: E402

KOK = os.environ.get("MAFIRM") or os.path.dirname(
    os.path.dirname(os.path.abspath(__file__)))
SADIK = os.path.join(KOK, "yamalar/kitaba-sadik")
sonuclar = []

# Kitabın METNİNDE gövdesi verilen dosyalar. Kaynak: doc.txt.
#   §2  satır 75      -> .gitignore
#   §5  satır 839+    -> birimler/rekabet/kod/esik.py
#   §5  satır ~200    -> birimler/rekabet/yontem/tr-esikler.md
#   §12 satır 839+    -> .claude/hooks/kapi.py
#   §12               -> .claude/settings.json
#   §16               -> denetim.sh
KITABIN = {
    ".gitignore": "cikti/",
    ".claude/hooks/kapi.py": "def denetle",
    ".claude/settings.json": "PreToolUse",
    "denetim.sh": "DENETİM",
    "birimler/rekabet/kod/esik.py": "def bildirilmeli",
    "birimler/rekabet/yontem/tr-esikler.md": "Bekletici etki",
}


def vaka(kod, baslik, gecti, ayrinti=""):
    sonuclar.append((kod, baslik, gecti, ayrinti))


# Özgün dosya adı eşlemesi: '.gitignore' özgünü, kendini yoksaymaması için
# 'gitignore' adıyla saklanır.
OZGUN_AD = {".gitignore": "gitignore"}


def ozgun_yolu(rel):
    return os.path.join(SADIK, OZGUN_AD.get(rel, os.path.basename(rel)))


def oku(p):
    return io.open(p, encoding="utf-8").read() if os.path.exists(p) else ""


def ozet(p):
    return hashlib.sha256(oku(p).encode("utf-8")).hexdigest()[:12]


# --- AG-01 · değiştirilen her KİTAP dosyasının özgünü korunmuş mu ----
korunmayan, korunan = [], []
for rel in sorted(KITABIN):
    canli = os.path.join(KOK, rel)
    ozgun = ozgun_yolu(rel)
    if not os.path.exists(canli):
        korunmayan.append("%s (canlı dosya yok)" % rel)
        continue
    if os.path.exists(ozgun):
        korunan.append(rel)
    else:
        korunmayan.append(rel)
vaka("AG-01", "kitaba ait her dosyanın özgün sürümü korunmuş",
     not korunmayan,
     ("ÖZGÜNÜ YOK: %s — bu dosyalar için 'kitap ne yapıyordu' sorusu artık "
      "cevaplanamaz" % ", ".join(korunmayan)) if korunmayan
     else "%d dosyanın özgünü yerinde" % len(korunan))

# --- AG-02 · DEGISIKLIKLER'in verdiği SÖZ doğru mu -------------------
soz = "hiçbiri silinmedi" in oku(os.path.join(KOK, "yamalar/DEGISIKLIKLER.md")).lower()
vaka("AG-02", "'hiçbiri silinmedi' sözü tutuluyor",
     (not soz) or not korunmayan,
     ("SÖZ TUTULMUYOR: belge 'hiçbiri silinmedi' diyor ama %d dosyanın "
      "özgünü yok (%s)" % (len(korunmayan), ", ".join(korunmayan)))
     if soz and korunmayan
     else "söz veriliyor ve tutuluyor" if soz else "belge böyle bir söz vermiyor")

# --- AG-03 · korunan özgün, canlı dosyadan GERÇEKTEN farklı mı -------
# Aynıysa ya yama hiç uygulanmadı ya da "özgün" diye yamalı sürüm kopyalandı;
# ikisi de kıyası anlamsız kılar ve sessizce olur.
ayni = []
for ad in sorted(os.listdir(SADIK)) if os.path.isdir(SADIK) else []:
    hedef = next((r for r in KITABIN
                  if OZGUN_AD.get(r, os.path.basename(r)) == ad), None)
    if not hedef:
        continue
    if ozet(os.path.join(SADIK, ad)) == ozet(os.path.join(KOK, hedef)):
        ayni.append(ad)
vaka("AG-03", "korunan her özgün, canlı dosyadan farklı",
     not ayni,
     ("ÖZDEŞ: %s — ya yama uygulanmadı ya da 'özgün' diye yamalı sürüm "
      "kopyalandı" % ", ".join(ayni)) if ayni
     else "korunan sürümlerin hepsi canlıdan farklı")

# --- AG-04 · korunan özgün GERÇEKTEN kitabın davranışını taşıyor mu --
# Beyan yeterli değil: kitaba sadık kapi.py, kitabın BİLİNEN kusurlarını
# göstermeli. Göstermiyorsa "kitaba sadık" etiketi yanlıştır.
ozgun_kapi = oku(os.path.join(SADIK, "kapi.py"))
kitabin_kusurlari = {
    "json.dumps üretim yolu (C-10)": "json.dumps" in ozgun_kapi,
    "Türkçe küçültme YOK (B-10)": "tr_kucult" not in ozgun_kapi,
    "olumsuz iddia kapısı YOK (B-07)": "OLUMSUZ" not in ozgun_kapi,
    "gelecek tarih kontrolü YOK (B-23)": "GELECEK" not in ozgun_kapi,
}
tasimayan = [k for k, v in kitabin_kusurlari.items() if not v]
vaka("AG-04", "korunan kapi.py kitabın bilinen kusurlarını taşıyor",
     not tasimayan and bool(ozgun_kapi),
     ("TAŞIMIYOR: %s — 'kitaba sadık' etiketi yanlış" % ", ".join(tasimayan))
     if tasimayan else
     "dört bilinen kusurun dördü de özgün dosyada mevcut" if ozgun_kapi
     else "özgün kapi.py okunamadı")

# --- AG-05 · derleme artığı depoya sızmıyor --------------------------
gi = oku(os.path.join(KOK, ".gitignore"))
artik = []
for kok, dizinler, _f in os.walk(KOK):
    if ".git" in kok:
        continue
    for d in dizinler:
        if d == "__pycache__" and "__pycache__" not in gi:
            artik.append(os.path.relpath(os.path.join(kok, d), KOK))
vaka("AG-05", "derleme artıkları .gitignore ile dışlanmış",
     not artik,
     ("__pycache__ dizini var ama .gitignore dışlamıyor: %s"
      % ", ".join(sorted(artik)[:3])) if artik
     else "derleme artığı yok ya da dışlanmış")


BEKLENEN_VAKA = 5


def rapor():
    if len(sonuclar) != BEKLENEN_VAKA:
        vaka("AG-00", "takım beyan ettiği vaka sayısını taşıyor", False,
             "beyan %d, bulunan %d" % (BEKLENEN_VAKA, len(sonuclar)))
    print("=" * 96)
    print("KÖR SINAMA AG — kitaba sadık karşılaştırma tabanı")
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
