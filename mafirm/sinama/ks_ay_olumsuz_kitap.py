#!/usr/bin/env python3
"""KÖR SINAMA AY — kitap hakkındaki OLUMSUZ iddialar ve § atıflarının yeri.

Yönelim (kırk üçüncü tur). AW raporun ALINTILARINI, AX SAYILARINI sınadı.
Üçüncü kardeş en tehlikelisiydi ve sınanmamıştı: raporun kitabın NE
SÖYLEMEDİĞİNE dair iddiaları. Kitabın kendi 2. kuralı olumsuz iddiadan daha
yüksek bir kanıt eşiği ister; kırk birinci tur da kitap olgularını ters
yönde yanlış bilebildiğimi gösterdi.

İki bulgu çıktı.

BİR — çürütücü, iddianın KAPSAMINDA aranmalı. "§11'in eşik denetimi
`dosyalar/` dizinini taramıyor" iddiasını kitabın TAMAMINDA arayınca
`dosyalar/*/` bulundu ve iddia çürümüş göründü. Oysa o dize §2'nin
`.gitignore` satırında (`'dosyalar/*/veri/'`); §11'in komut metninde değil.
İddia ayakta — ama ölçüt yanlış yerde arıyordu. Olumsuz bir iddia ancak
KENDİ BÖLÜMÜNDE çürütülebilir.

İKİ — ve bu daha ağır: rapor §8'i "çıkar çatışması", §9'u "insan onayı"
diye anıyordu. Kitapta **§8 = İşlem el kitapları**, **§9 = Beceriler**.
Çatışma ve onay, işletim sözleşmesinin 8. ve 9. KURALLARIDIR ve sözleşme
kitabın §3'ünde durur. Yani rapor on iki yerde bir KURAL numarasını BÖLÜM
numarası gibi yazmıştı. AX-05 bunu göremezdi: §8 ve §9 kitapta gerçekten
VAR — sadece iddia edilen konuda değil. **Var olmak, o konuda olmak
değildir** — kırkıncı turun sınıfının atıf tarafındaki hâli.
"""
import html
import io
import os
import re
import sys
import zipfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import beklenen  # noqa: E402
import kitap as kitapmod  # noqa: E402
from kitap import metin as kitap_metni_ortak  # noqa: E402

_KOK_COZ = os.environ.get("MAFIRM") or os.path.dirname(
    os.path.dirname(os.path.abspath(__file__)))
_DOCX = ("/root/.claude/uploads/a0f718bf-fd01-52d5-a508-48d77db2834c/"
         "0ca2aeab-RePieArelMAAvukatClaudeKurulumKitabi.docx")

sonuclar = []


def vaka(kod, baslik, gecti, kanit=""):
    sonuclar.append((kod, baslik, gecti, kanit))


def tr(s):
    return s.replace("I", "ı").replace("İ", "i").lower()


def kitap():
    """[BE/AW, 51. tur] Ortak çıkarıcı. Eski yerel sürüm Word'ün
    yumuşak satır sonunu (<w:br/>) siliyordu ve iki yanındaki
    sözcükleri YAPIŞTIRIYORDU; kitaba yapılan birebir aramalar bir
    satır sonunu geçtiğinde sessizce başarısız oluyordu."""
    return kitap_metni_ortak()


K = kitap()
TESLIMAT = "\n".join(
    io.open(os.path.join(_KOK_COZ, d), encoding="utf-8").read()
    for d in ("RAPOR.md", "KITAP-ERRATA.md")
    if os.path.exists(os.path.join(_KOK_COZ, d)))



# [51. tur] Bölüm haritası artık metin deseninden değil, Word'ün Heading2
# biçeminden okunuyor: yumuşak satır sonları geri gelince numaralı liste
# maddeleri de satır başında "N." ile başladı ve desen onları başlık sandı.
BOLUM = kitapmod.govdeler() if K else {}

# Kitabın bölüm başlıkları — raporun anladığı hâliyle. Bir atıf bu haritayla
# uyuşmuyorsa ya rapor yanlış anmıştır ya da kitap değişmiştir; ikisi de
# sessiz kalmamalı.
BEKLENEN_BASLIK = {
    2: "kurulum", 3: "işletim sözleşmesi", 5: "türkiye", 7: "koltuk",
    9: "beceri", 11: "komut", 12: "durduran kontroller", 13: "depo",
    14: "önce araştır", 15: "komut kütüphanesi", 16: "denetim",
    18: "bilerek yapmadıkları", 19: "ilk dosya",
}

# OLUMSUZ İDDİALAR: her biri, KENDİ BÖLÜMÜNDE aranacak çürütücülerle.
# Çürütücü bölümde geçiyorsa iddia YANLIŞTIR ve vaka kırmızı olur.
OLUMSUZ = {
    "§2 ikinci bir dayanıklılık aracı önermiyor (yedek yok)":
        (2, ["yedek", "yedekle", "backup", "kopyasını al"]),
    "§13 araç kataloğu kurulumda dosya bırakmıyor":
        (13, ["arac-katalogu", "katalog.md", "> ~/mafirm/hafiza"]),
    "§16 kontrollerinin mutasyonla sınandığını hiçbir yer söylemiyor":
        (16, ["mutasyon", "bozarak sına"]),
    "§12 hiçbir kapı onay durumuna bakmıyor":
        (12, ["onay:", "onaylayan", "onaylandı"]),
    "§14 boş sonuç ilkesini yaptırım taramasına taşımıyor":
        (13, ["temizlik kanıtı", "eşleşmenin yokluğu"]),
}

if K is None:
    for k, b in (("AY-01", "olumsuz iddialar kendi bölümlerinde ayakta"),
                 ("AY-02", "kural numaraları bölüm numarası gibi anılmıyor"),
                 ("AY-03", "kitabın bölüm haritası raporun anladığı gibi"),
                 ("AY-04", "bölüm ayırıcı gerçekten çalışıyor")):
        vaka(k, b, False, "kitap kaynağı yok — DOĞRULANAMADI")
else:
    # --- AY-01 · olumsuz iddialar KENDİ bölümlerinde çürütülüyor mu ---
    _curuk = []
    for iddia, (n, teyit) in OLUMSUZ.items():
        govde = tr(BOLUM.get(n, ("", ""))[1])
        bulunan = [t for t in teyit if tr(t) in govde]
        if bulunan:
            _curuk.append("%s → §%d'de bulundu: %s" % (iddia[:40], n, bulunan))
    vaka("AY-01", "kitap hakkındaki olumsuz iddialar kendi bölümlerinde ayakta",
         not _curuk,
         "%d iddia sınandı · ÇÜRÜYEN: %s"
         % (len(OLUMSUZ), "; ".join(_curuk) if _curuk else "yok"))

    # --- AY-02 · KURAL numarası, BÖLÜM numarası gibi anılmıyor -------
    # İşletim sözleşmesinin kuralları §3'ün içindedir; onları "§N" diye
    # anmak kitabın N. bölümünü işaret eder ve o bölüm başka bir şeydir.
    KURAL_KONU = {1: "kanıt", 4: "başlık sırası", 8: "çatışma", 9: "onay"}
    # [Ellinci tur] Karakter sınıfı \n'i dışlıyordu: "§9\n(onay durumu)"
    # biçiminde SATIR KAYDIRMASI olan bir karışma ölçüte GÖRÜNMEZDİ ve
    # ölçüt sessizce yeşil kalıyordu. Aynı kaçış deliği AM-01 (39. tur) ve
    # BA (46. tur) takımlarında da çıkmıştı; bu üçüncüsü. Satır sonları
    # eşleştirmeden ÖNCE tek boşluğa indirilir — cümle sınırı (nokta) ve
    # tablo sınırı (|) hâlâ korunur.
    _TES = re.sub(r"[ \t]*\n[ \t]*", " ", TESLIMAT)
    _karisan = []
    for n, konu in KURAL_KONU.items():
        # Karakter sınıfı \n'i dışlamayı SÜRDÜRÜR; işi yapan şey yukarıdaki
        # normalleştirmedir. İki mekanizmayı birden kullanmak, mutasyonun
        # hangisini sınadığını belirsizleştirir: biri sökülünce öteki yakalar
        # ve ölçüt sağlam sanılır. Tek mekanizma, sınanabilir mekanizmadır.
        for m in re.finditer(r"§%d(?![0-9.])[^.\n|]{0,70}" % n, _TES):
            parca = m.group(0)
            if re.search(konu, parca, re.I) and "CLAUDE.md" not in parca:
                _karisan.append("§%d…%s" % (n, konu))
    vaka("AY-02", "işletim sözleşmesi kuralları bölüm numarası gibi anılmıyor",
         not _karisan,
         "kural/bölüm karışması: %s — kitapta §8=İşlem el kitapları, "
         "§9=Beceriler" % (sorted(set(_karisan)) or "yok"))

    # --- AY-03 · bölüm haritası raporun anladığı gibi mi -------------
    _sapan = []
    for n, anahtar in BEKLENEN_BASLIK.items():
        ad = tr(BOLUM.get(n, ("", ""))[0])
        if anahtar not in ad:
            _sapan.append("§%d: bekleniyor %r, kitapta %r" % (n, anahtar, ad))
    vaka("AY-03", "kitabın bölüm haritası raporun anladığı gibi",
         not _sapan, "sapan: %s" % (_sapan or "yok"))

    # --- AY-04 · OLUMLU KONTROL: ayırıcı vakum değil ----------------
    vaka("AY-04", "bölüm ayırıcı kitabın bölümlerini gerçekten buluyor",
         len(BOLUM) >= 19 and 0 in BOLUM and 19 in BOLUM,
         "%d bölüm bulundu (§0…§19)" % len(BOLUM))


# [AF-02] Kaybolan bir vaka, kırmızı bir vakadan kötüdür: kimse aramaz.
BEKLENEN_VAKA = 4


def rapor():
    if len(sonuclar) != BEKLENEN_VAKA:
        vaka("AY-00", "takım beyan ettiği vaka sayısını taşıyor", False,
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
