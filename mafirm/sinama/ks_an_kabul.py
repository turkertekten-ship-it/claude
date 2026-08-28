#!/usr/bin/env python3
"""KÖR SINAMA AN — otuz birinci turun YAMASININ kabul sınaması.

Yönelim (otuz ikinci tur). Otuz birinci tur `/esik-denetle`'ye bir canlı iş
katmanı ekledi ve iki işaret tanımladı: ETKİLENEN (dosya, artık değişmiş bir
eşiğe dayanıyor) ve SÜRÜMSÜZ (dosya hangi rakama dayandığını hiç yazmamış).
Bir yama, işe yaradığı GÖSTERİLENE kadar bir iddiadır.

Önce bir hipotez KURULDU ve ÇÜRÜTÜLDÜ — kaydı burada durur, çünkü çürüyen
hipotez de bir ölçümdür: "belki hiçbir çıktı hangi rakama dayandığını
yazmıyor, o hâlde SÜRÜMSÜZ her zaman doğru olurdu ve yama boş bir tespit
üretirdi." Kitabın kendi çıktı sözleşmesi (§15.1, `komutlar/15-1-esik-
sorusu.md`) bunu çürütüyor:

    <cikti>
    ... Sonra KULLANILAN RAKAMLAR ve her birinin NEREDEN GELDİĞİ.
    ... Şununla bitir: ... / Kontrol edildi:
    </cikti>

ve yönteminin dördüncü adımı: "Kullandığın eşiklerin doğrulama tarihini yaz."
Yani sözleşmeye uyan bir çıktı rakamı, kaynağı ve tarihi TAŞIR — geriye dönük
inceleme için yeterli. Yama boşluğa değil, kitabın kendi sözleşmesine dayanıyor.

Geriye asıl soru kalıyor: bu bilgiyle karar GERÇEKTEN verilebiliyor mu?
"""
import os
import re
import shutil
import subprocess
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import beklenen  # noqa: E402

_KOK_COZ = os.environ.get("MAFIRM") or os.path.dirname(
    os.path.dirname(os.path.abspath(__file__)))

sonuclar = []


def vaka(kod, baslik, gecti, kanit=""):
    sonuclar.append((kod, baslik, gecti, kanit))


def oku(*p):
    try:
        with open(os.path.join(_KOK_COZ, *p), encoding="utf-8") as f:
            return f.read()
    except OSError:
        return ""


SOZLESME = oku("komutlar", "15-1-esik-sorusu.md")
ESIK_KOD = oku("birimler", "rekabet", "kod", "esik.py")

# --- AN-01 · sözleşme geriye dönük incelemeye YETİYOR mu ---------------
# Üç bilgi gerekir: kullanılan RAKAM, rakamın KAYNAĞI, ve TARİH.
_rakam = re.search(r"kullanılan rakamlar", SOZLESME, re.I) is not None
_kaynak = re.search(r"nereden geldiği", SOZLESME, re.I) is not None
_tarih = (re.search(r"doğrulama tarihini yaz", SOZLESME, re.I) is not None
          or "Kontrol edildi:" in SOZLESME)
vaka("AN-01", "eşik çıktı sözleşmesi geriye dönük incelemeye yetiyor",
     _rakam and _kaynak and _tarih,
     "rakam=%s kaynak=%s tarih=%s" % (_rakam, _kaynak, _tarih))

# --- Sentetik dosya üretimi (KUM HAVUZU; canlı ağaca dokunulmaz) -------
# [AL-01/AL-03] Bu takım dosyalar/ altına HİÇBİR ŞEY yazmaz. Adlar açıkça
# kurgusaldır ve gerçek bir müvekkile karşılık gelmez.
# [Q · mevzuat iddiası DEĞİL] Aşağıdaki rakamlar UYDURMA ve öyle olmaları
# gerekiyor: sınanan şey karşılaştırmanın YAPILABİLİRLİĞİdir, belirli tarihsel
# eşiklerin doğruluğu değil. Gerçek bir tarihsel rakam yazmak §11'in mevzuat
# katmanına birincil kaynaksız bir iddia sokardı. İlk sürümde gerçekçi
# görünen rakamlar seçmiştim ve ikisi de HÂLÂ YÜRÜRLÜKTEKİ sabitlere denk
# geldi — vaka kendi fixture'ı yüzünden kırmızıya döndü, sistem yüzünden değil.
ESKI = """# ÖRNEK İŞ · eşik değerlendirmesi (SENTETİK — mevzuat iddiası değildir)
Cevap: bildirime tabi DEĞİL (B ayağı).
Kullanılan rakamlar:
  Hedefin Türkiye cirosu eşiği: 123.456.789 TL — kaynak: sentetik örnek
  Diğer tarafın dünya cirosu eşiği: 987.654.321 TL — kaynak: sentetik örnek
Kontrol edildi: sentetik (2024-03-11)
"""
SURUMSUZ = """# ÖRNEK İŞ İKİ · eşik değerlendirmesi
Cevap: bildirime tabi DEĞİL.
Hesap yapıldı, eşikler aşılmıyor.
Kontrol edildi: mevzuat (2024-03-11)
"""


def _rakamlar(metin):
    """Metindeki TL eşik rakamlarını normalize eder."""
    bulunan = set()
    for m in re.finditer(r"([0-9][0-9.\s]{6,})\s*TL", metin):
        s = re.sub(r"[.\s]", "", m.group(1))
        if s.isdigit():
            bulunan.add(int(s))
    return bulunan


GUNCEL = set()
for m in re.finditer(r"^[A-ZÇĞİÖŞÜ_]+\s*=\s*([0-9_]+)", ESIK_KOD, re.M):
    GUNCEL.add(int(m.group(1).replace("_", "")))

# --- AN-02 · ETKİLENEN kararı verilebiliyor mu ------------------------
# Sözleşmeye uyan eski bir çıktı, bugünkü rakamlarla karşılaştırılabilmeli.
_eski_rakam = _rakamlar(ESKI)
_farkli = _eski_rakam - GUNCEL
vaka("AN-02", "sözleşmeye uyan eski çıktı ETKİLENEN olarak ayırt edilebiliyor",
     bool(_eski_rakam) and bool(_farkli),
     "dosyadaki eşikler=%s · bugünküler=%s · artık geçerli olmayan=%s"
     % (sorted(_eski_rakam), sorted(GUNCEL), sorted(_farkli)))

# --- AN-03 · SÜRÜMSÜZ ayırt edilebiliyor mu ---------------------------
vaka("AN-03", "rakam taşımayan çıktı SÜRÜMSÜZ olarak ayırt edilebiliyor",
     not _rakamlar(SURUMSUZ),
     "rakamsız dosyada bulunan eşik: %s" % (sorted(_rakamlar(SURUMSUZ)) or "yok"))

# --- AN-04 · yamanın taradığı katman komutta GERÇEKTEN yazılı ---------
# AM-01 kapsamı ölçüyor; burada işaretlerin TANIMLI olduğu ölçülür. Bir
# işaret adı verip tanımını yazmamak, tespit edilemeyen bir işarettir.
KOMUT = re.sub(r"<!--.*?-->", " ", oku(".claude", "commands",
                                       "esik-denetle.md"), flags=re.S)
_isaretler = {"ETKİLENEN": False, "SÜRÜMSÜZ": False}
for ad in _isaretler:
    # işaret adı geçiyor VE aynı cümlede bir koşul anlatılıyor
    _isaretler[ad] = re.search(
        r"%s" % ad, KOMUT) is not None and re.search(
        r"[^.]*%s[^.]*\." % ad, KOMUT) is not None
vaka("AN-04", "yamanın tanıttığı iki işaret de komutta tanımlı",
     all(_isaretler.values()), "tanımlı: %s" % _isaretler)

# --- AN-05 · yamanın ÜRETTİĞİ tablo kural 6'yı çiğnetmiyor ------------
# Yama, satırları müvekkil dosya adlarını taşıyan bir tablo üretiyor. O
# tablo dışarı giden bir çağrıya konursa sır kapısı YAKALAMALIDIR. Yamanın
# güvenliği, yamanın kendi cümlesine değil kapıya sorulur.
kh = tempfile.mkdtemp(prefix="ks_an_")
try:
    kapi_yol = os.path.join(_KOK_COZ, ".claude/hooks/kapi.py")
    import importlib.util
    spec = importlib.util.spec_from_file_location("kapi_an", kapi_yol)
    kapi = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(kapi)
    tablo = ("Bayat eşiğe dayanan dosyalar:\n"
             "  dosyalar/Acme-Gida-devralma/  ETKİLENEN\n")
    bulunan = {k for k, _ in kapi.denetle(tablo, True, None)}
    vaka("AN-05", "yamanın ürettiği tablo dışarı çıkarken sır kapısına takılıyor",
         "sir" in bulunan,
         "dışarı giden çağrıda ateşleyen kapılar: %s" % (sorted(bulunan) or "yok"))
finally:
    shutil.rmtree(kh, ignore_errors=True)


# [AF-02] Kaybolan bir vaka, kırmızı bir vakadan kötüdür: kimse aramaz.
BEKLENEN_VAKA = 5


def rapor():
    if len(sonuclar) != BEKLENEN_VAKA:
        vaka("AN-00", "takım beyan ettiği vaka sayısını taşıyor", False,
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
