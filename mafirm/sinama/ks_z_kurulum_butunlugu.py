#!/usr/bin/env python3
"""KÖR SINAMA Z — kurulum İKİNCİ KEZ koşulduğunda ne oluyor.

Kitap bir KURULUM KİTABIDIR. Asıl kullanımı çalıştırılmaktır — ve on yedi tur
boyunca hiçbir takım onu İKİ KEZ çalıştırmadı.

§2'nin ikinci adımı yıkıcıdır:

    printf '%s\\n' 'cikti/' 'dosyalar/*/veri/' '.DS_Store' > .gitignore

`>` üzerine yazar. Aynı şey §12'nin `kapi.py`si, §5'in `esik.py`si ve §16'nın
`denetim.sh`i için de geçerli: hepsi "yazılır" der. Yani kitabı yeniden
izlemek — yeni bir oturum, ikinci bir hukukçu, ya da §0'ın dördüncü kuralının
"denetim kırmızıysa dur ve düzelt" talimatını izleyen biri — HER YAMAYI geri
alır. Kural 6 koruması dâhil.

Ölçülen: yıkım OLUYOR mu, ve OLDUĞUNDA denetim bunu söylüyor mu. İkincisi
daha önemlidir: sessiz bir geri alma, hiç yapılmamış bir düzeltmedir.
"""
import os
import re
import shutil
import subprocess
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import beklenen  # noqa: E402

KOK = os.environ.get("MAFIRM") or os.path.dirname(
    os.path.dirname(os.path.abspath(__file__)))
sonuclar = []


def vaka(kod, baslik, gecti, ayrinti=""):
    sonuclar.append((kod, baslik, gecti, ayrinti))


def _kum_havuzu():
    d = tempfile.mkdtemp(prefix="ks_z_")
    for ad in os.listdir(KOK):
        if ad in (".git", "__pycache__"):
            continue
        k, h = os.path.join(KOK, ad), os.path.join(d, ad)
        (shutil.copytree if os.path.isdir(k) else shutil.copy2)(k, h)
    return d


def _denetim(kok):
    r = subprocess.run(["bash", os.path.join(kok, "denetim.sh"), "--yapisal"],
                       capture_output=True, text=True,
                       env=dict(os.environ, MAFIRM=kok))
    return r.returncode, r.stdout


# --- Z-01 · .gitignore korumaları YERİNDE mi (denetim katmanı) --------
KORUNAN = ("dosyalar/", "hafiza/muvekkil-adlari.txt",
           "hafiza/cikar-catismasi.md")
gi = ""
if os.path.exists(os.path.join(KOK, ".gitignore")):
    gi = open(os.path.join(KOK, ".gitignore"), encoding="utf-8").read()
eksik = [k for k in KORUNAN if k not in gi]
vaka("Z-01", ".gitignore kimlik taşıyan yolları hâlâ dışlıyor",
     not eksik, "eksik: %s" % ", ".join(eksik) if eksik
     else "üç yolun üçü de yerinde")

# --- Z-02 · §2 YENİDEN koşulunca denetim KIRMIZIYA dönüyor mu --------
# Yıkımın olması kaçınılmaz (`>` üzerine yazar). Ölçülen şey yıkımın
# GÖRÜLÜP GÖRÜLMEDİĞİ: sessizce geri alınan bir koruma, hiç konmamıştır.
kh = _kum_havuzu()
try:
    onceki_kod, _ = _denetim(kh)
    # §2'nin komutları AYNEN:
    for alt in ("dosyalar", "birimler", "emsal", "hafiza", "cikti"):
        os.makedirs(os.path.join(kh, alt), exist_ok=True)
    for alt in ("skills", "agents", "hooks", "commands"):
        os.makedirs(os.path.join(kh, ".claude", alt), exist_ok=True)
    with open(os.path.join(kh, ".gitignore"), "w", encoding="utf-8") as f:
        f.write("cikti/\ndosyalar/*/veri/\n.DS_Store\n")
    sonraki_kod, sonraki_cikti = _denetim(kh)
    vaka("Z-02", "§2 yeniden koşulup koruma silinince denetim KIRMIZI",
         onceki_kod == 0 and sonraki_kod != 0,
         "yıkımdan önce çıkış %d, sonra %d%s"
         % (onceki_kod, sonraki_kod,
            "" if sonraki_kod else " — SESSİZ GERİ ALMA: denetim hâlâ OK"))

    # --- Z-03 · yıkım GERÇEKTEN oldu mu (mutasyon indi mi) ------------
    yeni_gi = open(os.path.join(kh, ".gitignore"), encoding="utf-8").read()
    vaka("Z-03", "§2'nin `>` yönlendirmesi korumayı gerçekten siliyor",
         all(k not in yeni_gi for k in KORUNAN[1:]),
         "yeniden koşumdan sonra .gitignore: %r — yıkım kanıtlandı, "
         "dolayısıyla Z-02 boşa geçmiyor" % yeni_gi.replace("\n", " | "))
finally:
    shutil.rmtree(kh, ignore_errors=True)

# --- Z-04 · yamalı dosyalar yama İZİNİ taşıyor ------------------------
# Bir yama, kendini tanıtmazsa geri alındığı fark edilmez.
# [AE-01] Tek harf varsayımının DÖRDÜNCÜ yeri. [AA-01], [AC-01], [AB-03b]
# bu desene GÖRÜNMÜYORDU; Z-04 yalnızca dosyalarda eski tek harfli işaretler
# de bulunduğu için geçiyordu — yani doğru sebeple değil.
YAMA = re.compile(r"\[[A-Z]{1,2}-\d{2}[a-z]?(?:, ?[A-Z]{1,2}-\d{2}[a-z]?)*\]")
izsiz = []
for rel in (".claude/hooks/kapi.py", "denetim.sh",
            "birimler/rekabet/kod/esik.py"):
    p = os.path.join(KOK, rel)
    if not os.path.exists(p):
        izsiz.append("%s (yok)" % rel)
    elif not YAMA.search(open(p, encoding="utf-8").read()):
        izsiz.append(rel)
vaka("Z-04", "yamalı her dosya kendini tanıtan bir yama izi taşıyor",
     not izsiz, "izsiz: %s" % ", ".join(izsiz) if izsiz
     else "üç yamalı dosyanın üçü de vaka kimliğiyle işaretli")

# --- Z-05 · kitaba sadık dosya geri konulursa denetim görüyor mu -----
sadik = os.path.join(KOK, "yamalar/kitaba-sadik/kapi.py")
if os.path.exists(sadik):
    kh2 = _kum_havuzu()
    try:
        oncek, _ = _denetim(kh2)
        shutil.copyfile(sadik, os.path.join(kh2, ".claude/hooks/kapi.py"))
        sonrak, _ = _denetim(kh2)
        vaka("Z-05", "kitaba sadık kapi.py geri konunca denetim KIRMIZI",
             oncek == 0 and sonrak != 0,
             "önce %d, sonra %d%s" % (oncek, sonrak,
                                      "" if sonrak else " — GERİ ALMA GÖRÜLMÜYOR"))
    finally:
        shutil.rmtree(kh2, ignore_errors=True)
else:
    vaka("Z-05", "kitaba sadık kapi.py geri konunca denetim KIRMIZI", False,
         "yamalar/kitaba-sadik/kapi.py yok — kıyas yapılamadı")

# --- Z-06 · `mkdir -p` gerçekten zararsız (olumlu kontrol) ------------
# Her şey bozuk değil: kurulumun bazı adımları idempotenttir ve bunu
# göstermek, Z-02'nin bir genelleme değil bir ÖLÇÜM olduğunu belli eder.
kh3 = _kum_havuzu()
try:
    a, _ = _denetim(kh3)
    for alt in ("dosyalar", "birimler", "emsal", "hafiza", "cikti"):
        os.makedirs(os.path.join(kh3, alt), exist_ok=True)
    b, _ = _denetim(kh3)
    vaka("Z-06", "`mkdir -p` adımlarının yeniden koşulması zararsız",
         a == b == 0, "önce %d, sonra %d" % (a, b))
finally:
    shutil.rmtree(kh3, ignore_errors=True)


# --- Z-07 · DENETİMİN KENDİSİ geri alınırsa kim görür ----------------
# En keskin hâli: kitabın kendi denetim.sh'ini geri koy -> DENETİM OK.
# Sonra kural 6 korumasını da sil -> hâlâ DENETİM OK. Yani denetçiyi
# ezmek, denetçinin yapacağı BÜTÜN kontrolleri devre dışı bırakır ve
# uygulayıcı yeşil bir denetimle korumasız bir sisteme bakar.
#
# Denetim kendi bütünlüğünü doğrulayamaz — doğrulayacak kod, ezilen
# dosyanın içindedir. Dış katman `sinama/`dır: kitap oraya hiçbir şey
# yazmaz, dolayısıyla yeniden kurulumdan SAĞ ÇIKAR. Kontrol buraya ait.
YAMA_IZI = ("[Z-02]", "[Y-05]", "[X]")
d_metin = ""
_dp = os.path.join(KOK, "denetim.sh")
if os.path.exists(_dp):
    d_metin = open(_dp, encoding="utf-8").read()
kayip = [i for i in YAMA_IZI if i not in d_metin]
vaka("Z-07", "denetçinin kendisi geri alınmamış (yama izleri yerinde)",
     not kayip,
     ("DENETÇİ GERİ ALINMIŞ — kayıp iz: %s. Kitabın denetim.sh'i bu "
      "kontrolleri taşımaz; yeşil bir denetim artık hiçbir şey kanıtlamaz."
      % ", ".join(kayip)) if kayip
     else "%d yama izinin hepsi denetim.sh içinde" % len(YAMA_IZI))

# --- Z-08 · denetimin kontrol sayısı sessizce düşmüş mü --------------
# Bir kontrolü silmek, onu kırmızıya döndürmekten sessizdir.
_asgari = 20
_adet = len(re.findall(r'^kontrol "', d_metin, re.M))
vaka("Z-08", "denetim beyan edilen asgari kontrol sayısını taşıyor",
     _adet >= _asgari,
     "%d kontrol (asgari %d)%s" % (_adet, _asgari,
                                   "" if _adet >= _asgari else " — DÜŞMÜŞ"))

BEKLENEN_VAKA = 8


def rapor():
    if len(sonuclar) != BEKLENEN_VAKA:
        vaka("Z-00", "takım beyan ettiği vaka sayısını taşıyor", False,
             "beyan %d, bulunan %d" % (BEKLENEN_VAKA, len(sonuclar)))
    print("=" * 96)
    print("KÖR SINAMA Z — kurulum ikinci kez koşulduğunda")
    print("=" * 96)
    for kod, baslik, gecti, ayrinti in sonuclar:
        d, _ = beklenen.durum(kod, gecti)
        print("%s %-6s %s" % (d, kod, baslik))
        if ayrinti:
            print("        %s" % ayrinti)
    _s, _c = beklenen.ozet([(x[0], x[2]) for x in sonuclar])
    print("-" * 96)
    print("%d vaka · %d geçti · %d beklenen · %d SİNYAL"
          % (len(sonuclar), _c["GEÇTİ"], _c["BEKLENEN"], _s))
    return _s


if __name__ == "__main__":
    sys.exit(min(rapor(), 120))
