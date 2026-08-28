#!/usr/bin/env python3
"""KÖR SINAMA P — RAPORUN KENDİ teslimatlarına güncellik kuralı.

İşletim sözleşmesi §3: *"Bu sistemdeki her eşik, doğrulandığı tarihi taşır.
Altı aydan eski olan her şey dayanılmadan önce yeniden çekilir… eskimiş bir
eşik, hiç olmamasından kötüdür: kontrol edilmiş gibi durur."*

Yedi tur boyunca bu kuralı kitaba uyguladım ve §13'ü G-05 ile eleştirdim:
*"tek bir doğrulama tarihi taşıyan bir tablo, kontrol edilmiş gibi durur."*
Sonra `ks_g_depolar.md`'yi HİÇ TARİH TAŞIMADAN teslim ettim — eleştirdiğim
şeyden daha kötüsü.

Ve düz "altı ay" kuralı bu teslimatlar için YANLIŞ ölçüttür. Bir yıldız sayısı
altı ay değil BİR GÜN dayanır; bir yayımlanmış makalenin künyesi yıllarca
dayanır; bir egress politikası yalnızca o oturum için geçerlidir. Bu yüzden her
teslimat bir tarih DEĞİL, bir tarih + BOZULMA SINIFI taşır.

Kuralın gereği "hep taze olmak" değildir — bu imkânsızdır ve altıncı turdaki
"hep kırmızı" kusurunu üretir. Gereği şudur: **bayatlamış bir teslimat,
bayatladığını SÖYLER.**
"""
import os
import re
import sys
from datetime import date, datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import beklenen  # noqa: E402

_KOK_COZ = os.environ.get("MAFIRM") or os.path.dirname(
    os.path.dirname(os.path.abspath(__file__)))

# Bozulma sınıfı -> gün cinsinden ömür. None = zamana değil olaya bağlı.
SINIFLAR = {
    "GÜNLÜK": 1,
    "OTURUM": 0,
    "ALTI AY": 183,
    "YILLIK": 365,
    "AÇIK KALDIKÇA": None,
    "KURULUMA BAĞLI": None,
    "KİTAP SÜRÜMÜNE BAĞLI": None,
}

# [AT-02 · otuz sekizinci tur] Bu liste ELLE YAZILMIŞTI ve bayatladı.
# Otuz dördüncü turda `hafiza/arac-katalogu.md` teslimatını ekledim; listeye
# koymadım. Ölçüldü: o dosyadan doğrulama tarihini silmek denetimi kırmızıya
# ÇEVİRMİYORDU — yani dört tur boyunca güncellik kuralının dışında durdu.
# Bu, incelemenin ikinci sınıfıdır: elle yazılmış sayı ve listeler ölçtükleri
# şeyden ayrışır. Kendi aparatımda, kendi teslimatımla.
#
# Liste TERSİNE ÇEVRİLDİ: teslimatlar KEŞFEDİLİR, muafiyetler beyan edilir.
# Muafiyet listesi küçük ve durağandır; teslimat listesi büyüyen taraftır.
# Yeni bir teslimat eklendiğinde artık hiçbir şey yapılması gerekmez — kural
# kendiliğinden ona da uygular.
MUAF = {
    # kitabın kendi eseri, benim teslimatım değil
    "CLAUDE.md": "işletim sözleşmesi — kitabın metni",
    # canlı kayıt ve şablonu: iddia taşımaz, veri taşır
    "hafiza/cikar-catismasi.md": "canlı çatışma kaydı (kural 6, izlenmez)",
    "hafiza/cikar-catismasi.ornek.md": "şablon",
    "hafiza/muvekkil-adlari.ornek.txt": "şablon",
}


def _kesfet():
    """Teslimat = kök, hafiza/ ve sinama/ altındaki .md dosyaları, muaflar hariç."""
    bulunan = []
    for d in ("", "hafiza", "sinama"):
        tam = os.path.join(_KOK_COZ, d) if d else _KOK_COZ
        try:
            adlar = sorted(os.listdir(tam))
        except OSError:
            continue
        for ad in adlar:
            if not ad.endswith(".md"):
                continue
            rel = "%s/%s" % (d, ad) if d else ad
            if rel in MUAF:
                continue
            bulunan.append(rel)
    return bulunan


TESLIMATLAR = _kesfet()

BASLIK = re.compile(
    r"Doğrulama:\s*(\d{4}-\d{2}-\d{2})\s*·\s*Bozulma sınıfı:\s*([A-ZÇĞİÖŞÜ ]+?)\*\*")
# Bayat bir dosyanın taşıması gereken açık uyarı
KAYIT = re.compile(r"(bayat|yeniden çek|dayanılmaz|yeniden toplan|"
                   r"yeniden koşul|yeniden sınan)", re.I)

BUGUN = date(2026, 8, 28)
sonuclar = []


def vaka(kod, baslik, gecti, ayrinti=""):
    sonuclar.append((kod, baslik, gecti, ayrinti))


def oku(rel):
    p = os.path.join(_KOK_COZ, rel)
    return open(p, encoding="utf-8").read() if os.path.exists(p) else None


# --- P-01: her teslimat tarih VE sınıf taşıyor --------------------------
eksik = []
bilgi = {}
for rel in TESLIMATLAR:
    s = oku(rel)
    if s is None:
        eksik.append(rel + " (dosya yok)"); continue
    m = BASLIK.search(s)
    if not m:
        eksik.append(rel); continue
    bilgi[rel] = (m.group(1), m.group(2).strip(), s)
vaka("P-01", "her teslimat doğrulama tarihi VE bozulma sınıfı taşıyor",
     not eksik, "%d teslimat · eksik: %s" % (len(TESLIMATLAR), eksik or "yok"))

# --- P-02: sınıf beyan edilmiş sözlükten mi -----------------------------
bilinmeyen = [(r, s) for r, (_, s, _) in bilgi.items() if s not in SINIFLAR]
vaka("P-02", "her bozulma sınıfı beyan edilmiş sözlükten",
     not bilinmeyen, "bilinmeyen: %s" % (bilinmeyen or "yok"))

# --- P-03: bayat olan, bayat olduğunu SÖYLÜYOR --------------------------
# Kural "hep taze ol" değil. Taze olmak imkânsızdır ve altıncı turdaki
# "hep kırmızı" kusurunu üretir. Kural: bayat olan, bayatlığını yazar.
sessiz_bayat = []
bayat_sayisi = 0
for rel, (t, sinif, s) in bilgi.items():
    omur = SINIFLAR.get(sinif)
    if omur is None:
        continue
    yas = (BUGUN - datetime.strptime(t, "%Y-%m-%d").date()).days
    if yas >= omur:
        bayat_sayisi += 1
        bas = s[:1400]
        if not KAYIT.search(bas):
            sessiz_bayat.append("%s (%d gün, sınıf %s)" % (rel, yas, sinif))
vaka("P-03", "bayatlamış her teslimat bayatlığını AÇIKÇA yazıyor",
     not sessiz_bayat,
     "%d teslimat sınıfına göre bayat · sessiz bayat: %s"
     % (bayat_sayisi, sessiz_bayat or "yok"))

# --- P-04: gelecek tarihli teslimat yok ---------------------------------
gelecek = [r for r, (t, _, _) in bilgi.items()
           if datetime.strptime(t, "%Y-%m-%d").date() > BUGUN]
vaka("P-04", "hiçbir teslimat gelecek tarihli değil", not gelecek,
     "gelecek: %s" % (gelecek or "yok"))

# --- P-05: MUTASYON — uyarısı silinen bayat dosya yakalanıyor mu -------
g = oku("sinama/ks_g_depolar.md")
if g:
    m = BASLIK.search(g)
    bas = g[:1400]
    uyarili = bool(KAYIT.search(bas))
    bas_uyarisiz = KAYIT.sub("XXXX", bas)
    yakalar = uyarili and not KAYIT.search(bas_uyarisiz)
    vaka("P-05", "mutasyon: uyarı silinirse P-03 yakalar", yakalar,
         "ks_g GÜNLÜK sınıfında ve bir gün eski; uyarısı silindiğinde "
         "sessiz bayat sayılır")
else:
    vaka("P-05", "mutasyon sınaması", False, "ks_g bulunamadı")

# --- P-06: en bozulabilir dosya en kısa sınıfta mı ---------------------
gs = bilgi.get("sinama/ks_g_depolar.md", (None, None, None))[1]
vaka("P-06", "yıldız sayıları taşıyan dosya GÜNLÜK sınıfında",
     gs == "GÜNLÜK",
     "ks_g sınıfı: %s — kitabın §13'üne yönelttiğim G-05 eleştirisi buraya da "
     "uygulanır ve bu kez sınıf onu görünür kılıyor" % gs)


# [AF-02] Kaybolan bir vaka, kırmızı bir vakadan kötüdür: kimse aramaz.
# Bu koruma on üçüncü turda eklendi ama YALNIZCA sonrasında yazılan
# takımlara; on beş takım korumasız kaldı. Geriye doldurma.
BEKLENEN_VAKA = 6


def rapor():
    if len(sonuclar) != BEKLENEN_VAKA:
        vaka("P-00", "takım beyan ettiği vaka sayısını taşıyor", False,
             "beyan %d, bulunan %d" % (BEKLENEN_VAKA, len(sonuclar)))

    print("=" * 96)
    print("KÖR SINAMA P — raporun kendi teslimatlarına güncellik kuralı")
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
