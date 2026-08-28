#!/usr/bin/env python3
"""KÖR SINAMA AI — koltukların dayandığı ESERLER gerçekten var mı.

§7, koltuk provenansını sistemin **en yüksek itibar riski** sayar:

    "Bir koltuğun ağzına, o kişinin belgelenmiş görüşüyle çelişen bir söz asla
     konmaz. Görüşü bilinmiyorsa koltuk bunu yazar."

K-14 kuralın hiçbir mekanizması olmadığını buldu; K-15 altıncı kapıyı ekledi ve
her koltuk artık bir `## Kaynak durumu` beyanı taşımak ZORUNDA. Kapı beyanın
VARLIĞINI görür.

Beyanın KENDİSİ ise adı geçen eserlere dayanır — "Anatomy of a Merger (1975)",
"A Manual of Style for Contract Drafting", "Tools and Weapons". Yirmi altı tur
boyunca hiç kimse o eserlerin var olup olmadığını, doğru kişiye ait olup
olmadığını sormadı. Yani §1'in kanıt kuralı, §7'nin en çok önemsediği
iddialara uygulanmamıştı: gerçek ve yaşayan hukukçuların ağzına konan bir
mercek, doğrulanmamış bir bibliyografyaya dayanıyordu.

Bu takım eserleri KAYIT ile bağlar. Doğrulamanın kendisi ks_h_kaynaklar.md
içindedir (H-20..H-25, 2026-08-28); burada kontrol edilen şey, her koltuk
iddiasının o kayda düşmüş olmasıdır.
"""
import io
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import beklenen  # noqa: E402

KOK = os.environ.get("MAFIRM") or os.path.dirname(
    os.path.dirname(os.path.abspath(__file__)))
KOLTUK = os.path.join(KOK, "birimler/_koltuklar")
sonuclar = []


def vaka(kod, baslik, gecti, ayrinti=""):
    sonuclar.append((kod, baslik, gecti, ayrinti))


def oku(p):
    return io.open(p, encoding="utf-8").read() if os.path.exists(p) else ""


KAYIT = oku(os.path.join(KOK, "sinama/ks_h_kaynaklar.md"))
DOSYALAR = sorted(a for a in os.listdir(KOLTUK)) if os.path.isdir(KOLTUK) else []


def kaynak_durumu(m):
    b = re.search(r"## Kaynak durumu\n(.*?)(?=\n## |\Z)", m, re.S)
    # Satır sarması: markdown'da bir eser adı iki satıra bölünür
    # ("The Future of\nPrivacy") ve tırnak içi eşleşme kaçar. Aynı sınıf,
    # U-05'te ve AD-01'de de çıkmıştı: Türkçe/sarılmış metni desenle okumak.
    return re.sub(r"\s+", " ", b.group(1)).strip() if b else ""


# --- AI-01 · her koltuk bir Kaynak durumu beyanı taşıyor -------------
# K-15 kapısı bunu zorluyor; burada REGRESYON koruması olarak tekrar ölçülür.
beyansiz = [a for a in DOSYALAR
            if not kaynak_durumu(oku(os.path.join(KOLTUK, a)))
            and "KOLTUK BOŞ" not in oku(os.path.join(KOLTUK, a))]
vaka("AI-01", "her dolu koltuk bir Kaynak durumu beyanı taşıyor",
     not beyansiz, "; ".join(beyansiz) if beyansiz
     else "%d koltuk dosyası tarandı" % len(DOSYALAR))

# --- AI-02 · beyanda adı geçen her ESER doğrulama kaydında var mı ----
ESER = re.compile(r'"([A-ZÇĞİÖŞÜ][^"]{8,70})"')
kayitsiz, bulunan = [], set()
for a in DOSYALAR:
    m = oku(os.path.join(KOLTUK, a))
    kd = kaynak_durumu(m)
    for eser in ESER.findall(kd):
        if eser.lower().startswith(("doğrulan", "kesin", "makul", "türk")):
            continue                      # sistem ifadeleri, eser değil
        bulunan.add(eser)
        if eser not in re.sub(r"\s+", " ", KAYIT):
            kayitsiz.append("%s -> %r" % (a[:-3], eser[:44]))
vaka("AI-02", "koltuk beyanındaki her eser doğrulama kaydında",
     not kayitsiz,
     ("KAYITSIZ: %s — gerçek bir hukukçunun ağzına konan mercek, "
      "doğrulanmamış bir bibliyografyaya dayanıyor" % "; ".join(kayitsiz))
     if kayitsiz else "%d eser adlandırılmış, hepsi kayıtta" % len(bulunan))

# --- AI-03 · kayıttaki her eser bir DOĞRULAMA SONUCU taşıyor ---------
# Kayda yazılmak yetmez: "Doğrulandı" ya da açık bir olumsuz sonuç gerekir.
kayit_satirlari = re.findall(r"^\| (H-2\d) \| ([^|]+) \|[^|]*\| ([^|]+) \|",
                             KAYIT, re.M)
sonucsuz = [f"{k} {e.strip()[:34]}" for k, e, s_ in kayit_satirlari
            if "doğrulandı" not in s_.lower() and "bulunamadı" not in s_.lower()]
vaka("AI-03", "kayıttaki her koltuk dayanağı bir sonuç taşıyor",
     bool(kayit_satirlari) and not sonucsuz,
     ("sonuçsuz: %s" % "; ".join(sonucsuz)) if sonucsuz
     else "%d dayanak kaydı, hepsi sonuçlu" % len(kayit_satirlari)
     if kayit_satirlari else "koltuk dayanak kaydı bulunamadı")

# --- AI-04 · ORTAK YAZARLI eser, tek kişiye atfedilirken söyleniyor --
# Bir koltuk, ortak yazarlı bir kitabı tek kişinin görüşü gibi sunarsa,
# §7'nin "belgelenmiş görüşü" ölçütü sessizce genişlemiş olur.
ORTAK = {"Tools and Weapons": "Carol Ann Browne"}
eksik_ortak = []
for a in DOSYALAR:
    kd = kaynak_durumu(oku(os.path.join(KOLTUK, a)))
    for eser, ortak in ORTAK.items():
        if eser in kd and ortak not in kd:
            eksik_ortak.append("%s -> %s (ortak yazar %s anılmıyor)"
                               % (a[:-3], eser, ortak))
vaka("AI-04", "ortak yazarlı eser, koltuk beyanında ortak yazarıyla anılıyor",
     not eksik_ortak, "; ".join(eksik_ortak) if eksik_ortak
     else "ortak yazarlı eserler ortak yazarıyla anılıyor")

# --- AI-05 · BOŞ koltuk hiçbir görüş üretmiyor ----------------------
# §7'nin en tehlikeli hâli: boş bırakılması gereken bir koltuğun akla yatkın
# metinle doldurulması. turk-hukukcu ve vergi bilerek boştur.
dolduruIan = []
for a in DOSYALAR:
    m = oku(os.path.join(KOLTUK, a))
    if "KOLTUK BOŞ" not in m:
        continue
    # Boş bir koltuk "ne der" ya da "mercek" bölümü taşımamalı
    if re.search(r"## Getirdiği mercek|## .* ne der", m):
        dolduruIan.append(a[:-3])
vaka("AI-05", "boş bırakılan koltuk hiçbir görüş üretmiyor",
     not dolduruIan, "; ".join(dolduruIan) if dolduruIan
     else "%d boş koltuk, hiçbiri görüş üretmiyor"
          % sum(1 for a in DOSYALAR if "KOLTUK BOŞ" in oku(os.path.join(KOLTUK, a))))


BEKLENEN_VAKA = 5


def rapor():
    if len(sonuclar) != BEKLENEN_VAKA:
        vaka("AI-00", "takım beyan ettiği vaka sayısını taşıyor", False,
             "beyan %d, bulunan %d" % (BEKLENEN_VAKA, len(sonuclar)))
    print("=" * 96)
    print("KÖR SINAMA AI — koltukların dayandığı eserler")
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
