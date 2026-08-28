#!/usr/bin/env python3
"""KÖR SINAMA AL — takımların yan etkisi ve birbirinden bağımsızlığı.

Yönelim (otuzuncu tur). Yirmi dokuzuncu turun sonunda ölçülmemiş bir eksen
adlandırıldı: otuz dört takım artık aynı yardımcıyı, aynı beyan tabanını ve
aynı koşum betiğini paylaşıyor — her biri KENDİ başına mı düşüyor, yoksa
ortak bir nedenden hep birlikte mi kırmızıya dönüyor?

Ölçüm sonucu: takımlar ayrı süreçler olduğu için sıra bağımlılığının TEK
kanalı DOSYA SİSTEMİDİR. Ve o kanal açıktı:

  * B-34 fixture'ı CANLI `hafiza/muvekkil-adlari.txt`e yazıyor, aslını
    yalnızca bir DEĞİŞKENDE tutuyor, finally ile geri koyuyordu. finally
    SIGKILL'de koşmaz. Ölçüldü: süreç pencerede öldürüldüğünde canlı kayıt
    fixture'la kalıyor. Dosya .gitignore'da olduğu için sürüm denetiminden
    de dönülemiyor — tek kopya ölen sürecin belleğindeydi.
  * Dahası: denetim.sh o kalıntıyı "1 ad" sayıp
        UYARI müvekkil ad kaydı BOŞ — kural 6'nın gerçek kişi ayağı kapsanmıyor
    satırını
        ok    müvekkil ad kaydı    1 ad
    hâline getiriyordu. Koruma bozulurken ALARM DA KAPANIYORDU.
  * S-05 fixture'ı canlı `sinama/` dizinine bir .py bırakıyordu; kalıntı
    kalınca BİR SONRAKİ koşumda S-01 KALDI veriyor — sistemde hiçbir şey
    değişmemişken uydurma bir regresyon.

Doğru desen zaten takım ailesinde vardı: D (`${TMPDIR}/ks_d_kum`) ve Z
(`mkdtemp`) her şeyi kum havuzuna kopyalayıp orada bozuyor. Kusur disiplinin
YOKLUĞU değil, TEK TİP UYGULANMAMASIYDI — yirmi yedinci (AE) ve yirmi
sekizinci (AF) turlarda adlandırılan sınıfın aynısı: bir örneği düzeltmek
sınıfı kapatmaz.

Bu takım o sınıfı kalıcı bir sağlamaya çevirir.
"""
import hashlib
import os
import re
import shutil
import signal
import subprocess
import sys
import tempfile
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import beklenen  # noqa: E402

_KOK_COZ = os.environ.get("MAFIRM") or os.path.dirname(
    os.path.dirname(os.path.abspath(__file__)))
_SINAMA = os.path.join(_KOK_COZ, "sinama")
_BEN = os.path.basename(os.path.abspath(__file__))

# Özyineleme kilidi: AL, takımları koşturur. AL kendini koşturursa döngü
# doğar. Adla dışlamak yetmez (dosya adı değişebilir) — ortam değişkeni
# ikinci ve bağımsız bir kilittir. Kitabın D takımında bulunan "kendini
# denetleyen denetim" kusurunun bu takımdaki karşılığı.
if os.environ.get("KS_AL_ICINDE") == "1":
    print("AL kendi içinden çağrıldı — özyineleme kilidi devrede.")
    sys.exit(0)

sonuclar = []
ort = dict(os.environ, KS_AL_ICINDE="1")


def vaka(kod, baslik, gecti, kanit=""):
    sonuclar.append((kod, baslik, gecti, kanit))


# §8 ve kural 6 gereği CANLI ağaçta korunan yollar. Kaynağı denetim.sh'in
# kendi listesi (denetim.sh:196) ve Z takımının KORUNAN demeti.
KORUNAN = ("hafiza/muvekkil-adlari.txt", "hafiza/cikar-catismasi.md",
           "dosyalar/")


def _ozet(yol):
    try:
        with open(yol, "rb") as f:
            return hashlib.md5(f.read()).hexdigest()
    except OSError:
        return "(yok)"


def _agac(kok):
    """Ağacın dosya->md5 haritası. .git ve koşum kayıtları hariç."""
    h = {}
    for d, klasorler, dosyalar in os.walk(kok):
        klasorler[:] = [k for k in klasorler
                        if k not in (".git", "__pycache__")]
        for ad in dosyalar:
            tam = os.path.join(d, ad)
            rel = os.path.relpath(tam, kok)
            h[rel] = _ozet(tam)
    return h


# Koşumun BEYAN EDİLMİŞ kayıtları: bunların değişmesi yan etki değil,
# takımın görevidir. Başka her değişiklik yan etkidir.
BEYANLI_KAYIT = ("sinama/SAYIM.txt", "sinama/SONUC-once.txt",
                 "sinama/SONUC-sonra.txt")


def _takimlar():
    return sorted(a for a in os.listdir(_SINAMA)
                  if a.startswith("ks_") and a.endswith(".py") and a != _BEN)


# --- AL-01 · STATİK: hiçbir takım korunan CANLI yola yazmıyor ----------
# Ölçüt: dosyada hem korunan bir yol adı, hem de o yolu bir yazma kipiyle
# açan bir çağrı geçiyorsa ve yol bir kum havuzundan türemiyorsa kirlidir.
YAZMA = re.compile(r"""open\(\s*([A-Za-z_][A-Za-z0-9_]*)\s*,\s*["'][wa]""")
kirli = []
for t in _takimlar():
    metin = open(os.path.join(_SINAMA, t), encoding="utf-8").read()
    for ad_degisken in YAZMA.findall(metin):
        # o değişken nereden geliyor?
        atama = re.search(
            r"^\s*%s\s*=\s*(.+)$" % re.escape(ad_degisken), metin, re.M)
        if not atama:
            continue
        kaynak = atama.group(1)
        # [mutasyon dersi] İlk sürüm tam göreli yolu ("hafiza/muvekkil-
        # adlari.txt") arıyordu. Kod yolu os.path.join(_KOK_COZ, "hafiza",
        # "muvekkil-adlari.txt") diye BİLEŞEN BİLEŞEN kuruyor; o dizge hiç
        # geçmiyor. Mutasyon (B-34'ü canlı kayda geri döndür) KAÇTI.
        # Ölçüt dosya ADINA indirildi.
        korunan_mu = any(os.path.basename(k.rstrip("/")) in kaynak
                         for k in KORUNAN)
        kum_mu = ("mkdtemp" in kaynak or "_kum" in kaynak
                  or "TMPDIR" in kaynak or "gettempdir" in kaynak)
        if korunan_mu and not kum_mu:
            kirli.append("%s: %s = %s" % (t, ad_degisken, kaynak.strip()[:60]))
vaka("AL-01", "hiçbir takım korunan canlı yola yazmıyor",
     not kirli, "kirli: %s" % (kirli or "yok"))


# --- AL-02 + AL-03 · DİNAMİK: tek koşum, iki ölçüm -------------------
# AL-02'nin İLK TASARIMI kör zamanlıydı: takımı 0.05/0.12/0.25/0.40 s'de
# öldürüp korunan dosyaya bakıyordu. Pencere birkaç milisaniye olduğu için
# vuruş şansa kalıyordu — ve mutasyon sınamasında B-34 canlı kayda geri
# döndürüldüğünde AL-02 KIRMIZIYA DÖNMEDİ. Şansa bağlı bir vaka, vaka değildir.
#
# Yeni tasarım daha güçlü bir şey ölçer: korunan dosyalar koşum SIRASINDA
# hiçbir AN değişmiyor. Bir GÖZCÜ iş parçacığı yüksek frekansla örnekler.
# Dosya bir an bile değişiyorsa, o anda gelen bir SIGKILL onu kaybeder —
# yani AL-02 artık "öldürmeyi denedim, tutmadı" değil, "kaybedilecek bir
# an hiç yok" der. Ve vakuum değildir: kaç örnek alındığı kanıt olarak yazılır.
import threading

_gozcu_dur = threading.Event()
_gorulen = []
_ornek = [0]
_KORUNAN_TAM = [os.path.join(_KOK_COZ, k) for k in KORUNAN
                if not k.endswith("/")]
_TABAN = {y: _ozet(y) for y in _KORUNAN_TAM}


def _gozcu():
    while not _gozcu_dur.is_set():
        for y in _KORUNAN_TAM:
            _ornek[0] += 1
            if _ozet(y) != _TABAN[y]:
                _gorulen.append(os.path.basename(y))
        time.sleep(0.001)


once = _agac(_KOK_COZ)
_is = threading.Thread(target=_gozcu, daemon=True)
_is.start()
try:
    for t_ad in _takimlar():
        subprocess.run([sys.executable, os.path.join(_SINAMA, t_ad)],
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                       env=ort, timeout=300)
finally:
    _gozcu_dur.set()
    _is.join(timeout=5)
sonra = _agac(_KOK_COZ)

vaka("AL-02", "korunan dosyalar koşum SIRASINDA hiçbir an değişmiyor",
     not _gorulen,
     ("koşum sırasında değişen: %s" % sorted(set(_gorulen))) if _gorulen
     else "%d örnek alındı, hiçbirinde fark yok" % _ornek[0])

fark = []
for yol in sorted(set(once) | set(sonra)):
    if once.get(yol) == sonra.get(yol):
        continue
    if yol.replace(os.sep, "/") in BEYANLI_KAYIT:
        continue
    fark.append("%s (%s -> %s)" % (yol, once.get(yol, "yok")[:8],
                                   sonra.get(yol, "yok")[:8]))
vaka("AL-03", "takım koşumu ağacı değiştirmiyor",
     not fark, "değişen: %s" % (fark or "yok"))


# --- AL-04 · sinama/ dizininde kalıntı takım dosyası yok --------------
# S-05'in eski hâli buraya bir .py bırakıyordu; sinama/*.py sayan her şey
# onu 34. takım sanıyordu. AL-03'ün koşumundan SONRA bakılır.
kalinti = [a for a in os.listdir(_SINAMA)
           if a.endswith(".py") and (a.startswith("_") or "mutasyon" in a)]
vaka("AL-04", "sinama/ dizininde kalıntı .py yok",
     not kalinti, "kalıntı: %s" % (kalinti or "yok"))


# --- AL-05 · OLUMLU KONTROL: alarm yük taşıyor ------------------------
# AL-01/02'nin NEDEN önemli olduğunun kanıtı: ad kaydına bir sınama
# kalıntısı düşerse denetimin "kapsanmıyor" uyarısı SUSAR. Tamamen kum
# havuzunda ölçülür — canlı ağaca dokunulmaz.
kh = tempfile.mkdtemp(prefix="ks_al_alarm-")
try:
    hedef = os.path.join(kh, "mafirm")
    shutil.copytree(_KOK_COZ, hedef,
                    ignore=shutil.ignore_patterns(".git", "__pycache__"))
    kayit = os.path.join(hedef, "hafiza", "muvekkil-adlari.txt")

    def _denetim():
        r = subprocess.run([os.path.join(hedef, "denetim.sh"), "--yapisal"],
                           capture_output=True, text=True,
                           env=dict(os.environ, MAFIRM=hedef,
                                    KS_AL_ICINDE="1"), timeout=180)
        return (r.stdout or "") + (r.stderr or "")

    temiz_cikti = _denetim()
    with open(kayit, "w", encoding="utf-8") as f:
        f.write("# sınama\nAyşe Yılmaz\n")
    kirli_cikti = _denetim()

    uyariyordu = "kapsanmıyor" in temiz_cikti
    sustu = "kapsanmıyor" not in kirli_cikti
    vaka("AL-05", "alarm yük taşıyor: kalıntı uyarıyı susturur",
         uyariyordu and sustu,
         "temizken uyarıyor=%s · kalıntıyla susuyor=%s" % (uyariyordu, sustu))
finally:
    shutil.rmtree(kh, ignore_errors=True)


# --- AL-06 · STATİK: sıra bağımlılığının kanalı kapalı ----------------
# Takımlar ayrı SÜREÇLERDİR; aralarındaki tek paylaşılan durum dosya
# sistemidir. AL-03 o kanalın boş olduğunu dinamik olarak gösterdi. Burada
# aynı şey yapısal olarak gösterilir: hiçbir takım, BAŞKA bir takımın
# ürettiği koşum kaydını okumuyor. (denetim.sh'in SAYIM.txt'i okuması bir
# takım-takım bağı değildir; SAYIM.txt'i hepsi.sh yazar ve o KAYIT olmak
# üzere vardır — on altıncı turun katman dersi.)
# BU KOŞUMUN ürettiği dosyalar. SONUC-once.txt bunlardan DEĞİLDİR: o,
# kitaba sadık kurulumun yamalardan ÖNCEKİ ham çıktısıdır — donmuş bir
# arşiv. M-03'ün onu okuması meşrudur. Ama muafiyeti sınamadan tanımak,
# yirmi altıncı turda U-10'da düştüğüm tuzaktır: muafiyet AL-07 ile sınanır.
URETILEN = ("SONUC-sonra.txt", "SAYIM.txt")
okuyan = []
for t in _takimlar():
    metin = open(os.path.join(_SINAMA, t), encoding="utf-8").read()
    # yorum satırlarını at: ders anlatan yorumlar dosya adını anabilir
    kod = "\n".join(s for s in metin.splitlines()
                    if not s.lstrip().startswith("#"))
    for u in URETILEN:
        if u in kod:
            okuyan.append("%s -> %s" % (t, u))
vaka("AL-06", "hiçbir takım başka bir takımın koşum kaydını okumuyor",
     not okuyan, "okuyan: %s" % (okuyan or "yok"))


# --- AL-07 · MUAFİYETİN SINANMASI: SONUC-once.txt gerçekten arşiv mi ---
# AL-06, M-03'ün SONUC-once.txt okumasını muaf tutuyor. Muafiyetin dayanağı
# şu iddiadır: o dosyayı hiçbir koşucu YAZMAZ, donmuş bir arşivdir. Sınanmamış
# bir muafiyet, kapının deliğidir — bu yüzden iddia burada ölçülür.
yazan = []
for kosucu in ("hepsi.sh", "../denetim.sh"):
    yol = os.path.join(_SINAMA, kosucu)
    if not os.path.exists(yol):
        continue
    kod = "\n".join(s for s in open(yol, encoding="utf-8").read().splitlines()
                    if not s.lstrip().startswith("#"))
    if re.search(r">\s*\S*SONUC-once\.txt|SONUC-once\.txt[^\n]*[\"']w[\"']",
                 kod):
        yazan.append(kosucu)
# ayrıca takımların hiçbiri de yazmamalı
for tk in _takimlar():
    kod = open(os.path.join(_SINAMA, tk), encoding="utf-8").read()
    if re.search(r"SONUC-once[^\n]{0,40}[\"']w[\"']", kod):
        yazan.append(tk)
vaka("AL-07", "SONUC-once.txt donmuş arşiv: hiçbir koşucu onu yazmıyor",
     not yazan, "yazan: %s" % (yazan or "yok"))


# [AF-02] Kaybolan bir vaka, kırmızı bir vakadan kötüdür: kimse aramaz.
BEKLENEN_VAKA = 7


def rapor():
    if len(sonuclar) != BEKLENEN_VAKA:
        vaka("AL-00", "takım beyan ettiği vaka sayısını taşıyor", False,
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
