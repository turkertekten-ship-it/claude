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
# Raporun kitap hakkındaki YOKLUK iddiaları: "kitap şunu söylemiyor".
# Her biri, o iddiayı ÇÜRÜTECEK metnin hangi bölümde aranacağını yazar.
#
# [Elli üçüncü tur] Bu tablo beş satırdı; teslimatlarda ise YİRMİ yoklukiddiası
# vardı. Kural 2 olumsuz iddiadan olumludan YÜKSEK kanıt ister — ve on beşi
# hiç sınanmamıştı. Üstelik elli birinci tura kadar kitap metni bozuk
# okunuyordu: satır sonunu geçen her birebir arama sessizce başarısız
# oluyordu, yani bir yokluk iddiası YANLIŞLIKLA doğrulanmış olabilirdi.
# AY-05 artık kapsamayı zorunlu kılıyor: beyan edilmemiş bir yokluk iddiası
# sınanmamış bir olumsuz iddiadır.
OLUMSUZ = {
    "§2 ikinci bir dayanıklılık aracı önermiyor (yedek yok)":
        (2, None, ["yedek", "yedekle", "backup", "kopyasını al"]),
    "§13 araç kataloğu kurulumda dosya bırakmıyor":
        (13, None, ["arac-katalogu", "katalog.md", "> ~/mafirm/hafiza"]),
    "§16 kontrollerinin mutasyonla sınandığını hiçbir yer söylemiyor":
        (16, None, ["mutasyon", "bozarak sına"]),
    "§12 hiçbir kapı onay durumuna bakmıyor":
        (12, None, ["onay:", "onaylayan", "onaylandı"]),
    "§14 boş sonuç ilkesini yaptırım taramasına taşımıyor":
        (13, None, ["temizlik kanıtı", "eşleşmenin yokluğu"]),
    # --- elli üçüncü turda eklenenler ---
    "§13 diff-match-patch'in arşivlendiğini yazmıyor":
        (13, "diff-match-patch", ["arşiv", "archived", "2024-08-05"]),
    "§9 negatif sınır kuralını gösteriyor ama söylemiyor":
        (9, None, ["negatif sınır", "sınır kuralı", "ne yapmayacağını yaz"]),
    "§13.3 eşleşme bulunmadığında ne anlama geldiğini söylemiyor":
        (13, None, ["eşleşme yoksa", "bulunamazsa", "eşleşme bulunmazsa"]),
    "§2 iki şeyi tek adımda kurmanın ödünleşimini söylemiyor":
        (2, None, ["ödünleş", "feda", "birini seçmek"]),
    "§16 birimler arası tutarlılığı sınamıyor":
        (16, None, ["birimler arası", "birimler arasında tutarlı"]),
    "§10 web yetkili ajana sır sınırını yazmıyor":
        (10, None, ["müvekkil adı", "sır sınırı", "gizlilik sınırı"]),
    "§2 kurulumun idempotent olmadığını söylemiyor":
        (2, None, ["idempotent", "yeniden çalıştır", "üzerine yaz"]),
    "§12 kapı iletilerinde çare göstermiyor":
        (12, None, ["nasıl düzeltilir", "şu biçimde ekleyin", "çare"]),
    "§2 özgün sürümü saklamayı söylemiyor":
        (2, None, ["özgün sürüm", "yedek kopya", "commit et"]),
    "§7 koltuk dayanağının doğrulanmasını istemiyor":
        (7, None, ["dayanağı doğrula", "kaynağı teyit", "doğrulanmış görüş"]),
    "§12 öz-sınamada her kapının bir vakası olmasını istemiyor":
        (12, None, ["her kapının", "kapı başına", "her kural için bir vaka"]),
    "§14 çıktı sözleşmesini once-arastir becerisine taşımıyor":
        (14, None, ["iki başlıkla biter", "Şimdi ne yapılmalı"]),
    "§12 metnin hangi KATMANDA olduğunu sormuyor (kural/yorum/örnek)":
        (12, None, ["yorum satırı", "örnek olarak", "katman", "yorumda geçen"]),
}

# AY-05'in beyanı: bugün teslimatlarda bu desene uyan YİRMİ İKİ cümlecik var.
# Bileşimi: on sekizi tabloda çürütücüsüyle beyanlı AYRI iddia; ikisi aynı
# iddianın ikinci kez yazılmış hâli; ikisi de İDDİA DEĞİL ANMA — AY takımını
# tarif eden tablo satırı ile §18'in kendi sözcüklerinin alıntısı.
#
# Sayı elli üçüncü turda 21'den 22'ye çıktı: o turun ANLATISI, takımın
# kapsamasını anlatırken kalıba uyan bir cümle daha ekledi. Bir kusuru
# arayan ölçüt, o kusuru belgeleyen düzyazıyı da sayar — bu incelemenin en
# sık sınıfı. Sayı ANMALARLA birlikte beyan edilir ve bileşimi burada
# yazılıdır; yeni bir yokluk İDDİASI yazmak sayıyı değiştirir ve iddia
# tabloya çürütücüsüyle girene kadar vakayı kırar. [kural 2]
BEYAN_YOKLUK = 22


if K is None:
    for k, b in (("AY-01", "olumsuz iddialar kendi bölümlerinde ayakta"),
                 ("AY-02", "kural numaraları bölüm numarası gibi anılmıyor"),
                 ("AY-03", "kitabın bölüm haritası raporun anladığı gibi"),
                 ("AY-04", "bölüm ayırıcı gerçekten çalışıyor")):
        vaka(k, b, False, "kitap kaynağı yok — DOĞRULANAMADI")
else:
    # --- AY-01 · olumsuz iddialar KENDİ bölümlerinde çürütülüyor mu ---
    def _cumlecikler(t):
        for p in re.split(r"(?<=[.:;!?])\s+|\n\n|\n(?=\|)|\s—\s", t):
            p = re.sub(r"\s+", " ", p).strip()
            if p:
                yield p

    _curuk = []
    for iddia, (n, konu, teyit) in OLUMSUZ.items():
        govde = BOLUM.get(n, ("", ""))[1]
        # [Elli üçüncü tur] Çürütücü, bölümün TAMAMINDA aranırsa BAŞKA BİR
        # KONU hakkındaki bir sözcük iddiayı çürütmüş görünür: §13'te
        # "bakımsız" geçiyor ama BAŞKA iki depo için. Konusu olan bir iddia,
        # çürütücüsünü KONUSUYLA AYNI CÜMLECİKTE aramalıdır.
        if konu:
            alan = " ".join(p for p in _cumlecikler(govde)
                            if tr(konu) in tr(p))
            if not alan.strip():
                # Çapa hiçbir cümleciği tutmuyorsa arama alanı BOŞTUR ve
                # hiçbir çürütücü bulunamaz: iddia boşlukta geçer. Çapa bir
                # daraltmadır, kaçış deliği değil.
                _curuk.append("%s → ÇAPA TUTMUYOR: %r §%d'de yok"
                              % (iddia[:40], konu, n))
                continue
        else:
            alan = govde
        bulunan = [t for t in teyit if tr(t) in tr(alan)]
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

    # --- AY-05 · her YOKLUK iddiası beyan edilmiş -------------------
    # Kural 2: olumsuz iddia olumludan YÜKSEK kanıt ister. Teslimatta geçen
    # ama tabloda karşılığı olmayan bir yokluk iddiası, SINANMAMIŞ bir
    # olumsuz iddiadır. Sayı beyanlıdır: yeni bir yokluk iddiası yazmak,
    # onu tabloya eklemeden bu vakayı kırar.
    _YOKLUK = re.compile(
        r"\b(demiyor|söylemiyor|yazmıyor|geçmiyor|önermiyor|taşımıyor|"
        r"bırakmıyor|bakmıyor|kapsamıyor|saymıyor|içermiyor|belirtmiyor|"
        r"anmıyor|tanımlamıyor|zorunlu kılmıyor|hiçbir yer\w*|"
        r"yer almıyor|bulunmuyor|sınanmıyor|istemiyor|yapmaz)\b", re.I)
    _KITAP = re.compile(r"§\s*\d|kitap|kitabın|kitabı\b|kitapta", re.I)
    _ANLATI = re.compile(r"\d+\. tur|turda|turunda|düzelt|yanlış okum", re.I)
    _bulunan = 0
    for _p in _cumlecikler(re.sub(r"```.*?```", " ", TESLIMAT, flags=re.S)):
        _p = re.sub(r"[*`_]", "", _p)
        if _YOKLUK.search(_p) and _KITAP.search(_p) and not _ANLATI.search(_p):
            _bulunan += 1
    vaka("AY-05", "kitap hakkındaki her yokluk iddiası tabloda beyanlı",
         _bulunan == BEYAN_YOKLUK and len(OLUMSUZ) >= 17,
         "teslimatta %d yokluk iddiası · beyan %d · tabloda %d çürütücü küme"
         % (_bulunan, BEYAN_YOKLUK, len(OLUMSUZ)))

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
BEKLENEN_VAKA = 5


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
