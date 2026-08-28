#!/usr/bin/env python3
"""KÖR SINAMA Y — sır kapısı ön kapıyı tutuyor, ya yükleme rampası.

Kural 6 sistemin en sert kuralı: müvekkil kimliği makineden ÇIKMAZ. §12'nin
sır kapısı bunu WebSearch, WebFetch ve Bash çağrılarında uyguluyor ve X takımı
davranışla doğruladı.

Ama §2 kurulumun ikinci adımında şunu yapıyor:

    cd ~/mafirm && git init && git branch -M main
    printf '%s\\n' 'cikti/' 'dosyalar/*/veri/' '.DS_Store' > .gitignore

Yani kurulum bir SÜRÜM DEPOSUDUR ve `git push` veriyi makineden çıkarır —
kuralın yasakladığı şeyin ta kendisi. Korunan iki yol var: `cikti/` ve
`dosyalar/*/veri/`. Korunmayanlar:

  · `dosyalar/<is>/` — §2'ye göre CANLI İŞLER. `veri/` dışındaki her şey
    (kapsam notu, taslaklar, yazışma, notlar) izleniyor.
  · `hafiza/muvekkil-adlari.txt` — varlık sebebi GERÇEK AD tutmak.
  · `hafiza/cikar-catismasi.md` — §8'e göre karşı tarafları tutar.

Kapı ön kapıyı tutuyor; §2 yükleme rampasını açık bırakıyor. On altı tur
boyunca hiçbir takım "sistem NEYİ KALICI HÂLE GETİRİYOR" diye sormadı.
"""
import os
import re
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import beklenen  # noqa: E402

KOK = os.environ.get("MAFIRM") or os.path.dirname(
    os.path.dirname(os.path.abspath(__file__)))
sonuclar = []


def vaka(kod, baslik, gecti, ayrinti=""):
    sonuclar.append((kod, baslik, gecti, ayrinti))


def git(*a, cwd=None):
    r = subprocess.run(("git",) + a, cwd=cwd or KOK,
                       capture_output=True, text=True)
    return r.returncode, r.stdout.strip()


# Bir yolun HANGİ depoda izlendiğini bul: kurulum kökü ya da onu kapsayan
# herhangi bir üst depo (bu kurulumda ayna bir depo da var).
def _depo(yol):
    d = os.path.dirname(yol)
    while True:
        if os.path.isdir(os.path.join(d, ".git")):
            return d
        ust = os.path.dirname(d)
        if ust == d:
            return None
        d = ust


def izleniyor_mu(rel):
    """Herhangi bir depoda izleniyorsa True."""
    for kok in {KOK, _depo(os.path.join(KOK, rel))} - {None}:
        p = os.path.join(KOK, rel)
        if not os.path.exists(p):
            continue
        r = subprocess.run(["git", "ls-files", "--error-unmatch",
                            os.path.relpath(p, kok)],
                           cwd=kok, capture_output=True, text=True)
        if r.returncode == 0:
            return True
    return False


def yoksayiliyor_mu(rel):
    for kok in {KOK, _depo(os.path.join(KOK, rel))} - {None}:
        p = os.path.join(KOK, rel)
        r = subprocess.run(["git", "check-ignore", "-q",
                            os.path.relpath(p, kok)],
                           cwd=kok, capture_output=True, text=True)
        if r.returncode == 0:
            return True
    return False


# --- Y-01 · kimlik taşıyan depoları KENDİ METİNLERİNDEN bul -----------
# Kod okunmadı: her dosyanın kendi başlığı ne için var olduğunu söylüyor.
KIMLIK = re.compile(
    r"müvekkil|hedef şirket|karşı taraf|kod ad[ıi]|canlı iş|gerçek ad", re.I)
adaylar = {}
for rel in ("hafiza/muvekkil-adlari.txt", "hafiza/cikar-catismasi.md"):
    p = os.path.join(KOK, rel)
    if os.path.exists(p):
        m = open(p, encoding="utf-8", errors="replace").read()
        if KIMLIK.search(m):
            adaylar[rel] = "kendi metni kimlik verisi tuttuğunu söylüyor"
if os.path.isdir(os.path.join(KOK, "dosyalar")):
    adaylar["dosyalar/"] = "§2: canlı işleri tutar"

vaka("Y-01", "kimlik taşıyan kalıcı depolar tespit edildi", bool(adaylar),
     "; ".join("%s (%s)" % kv for kv in sorted(adaylar.items())))

# --- Y-02 · her biri sürüm denetiminden DIŞLANMIŞ mı -------------------
korumasiz = []
for rel in sorted(adaylar):
    if rel == "dosyalar/":
        # §2 yalnızca dosyalar/*/veri/ yoksayıyor; kardeş yollar açık.
        ornek = "dosyalar/ornek-is/kapsam-notu.md"
        if not yoksayiliyor_mu(ornek):
            korumasiz.append("dosyalar/<is>/ (yalnızca veri/ korunuyor)")
    elif not yoksayiliyor_mu(rel):
        korumasiz.append(rel)
vaka("Y-02", "kimlik taşıyan her depo .gitignore ile dışlanmış",
     not korumasiz,
     ("KORUMASIZ: %s — `git push` bunları makineden ÇIKARIR; kural 6'nın "
      "yasakladığı şey budur" % ", ".join(korumasiz))
     if korumasiz else "hepsi dışlanmış")

# --- Y-03 · şu an İZLENEN bir kimlik deposu var mı --------------------
izlenen = [r for r in sorted(adaylar) if r != "dosyalar/" and izleniyor_mu(r)]
vaka("Y-03", "hiçbir kimlik deposu sürüm denetimince izlenmiyor",
     not izlenen,
     ("İZLENİYOR: %s" % ", ".join(izlenen)) if izlenen else "hiçbiri izlenmiyor")

# --- Y-04 · GEÇMİŞTE hiç gerçek ad işlendi mi -------------------------
# Olumsuz iddia (§2): kanıt, geçmişin her sürümünün sayılmasıyla verilir.
# BOŞA GEÇMEZ. İlk sürüm SIFIR sürüm inceleyip "sızıntı yok" dedi: kurulum
# kökündeki depo commit taşımıyordu ve gerçek geçmiş bir AYNA depodaydı.
# "Hiç ad işlenmemiş" bir OLUMSUZ İDDİADIR; §2 onu kanıtsız yazmayı yasaklar
# ve sıfır incelenmiş sürüm kanıt değildir. Doğrulanamıyorsa vaka BAŞARISIZDIR.
def _kapsayan_depolar(rel):
    """Yolu KAPSAYAN her depo — izlenmese de. Bir yol izlemeden çıkarılmış
    olabilir; geçmişi yine de sorulabilir (`git log -- <yol>` silinmiş yolu
    da görür). İlk sürüm 'izleyen' depoları arıyordu ve düzeltmeden SONRA
    hiçbirini bulamıyordu."""
    tam = os.path.realpath(os.path.join(KOK, rel))
    bulunan, d = [], os.path.dirname(tam)
    while True:
        if os.path.isdir(os.path.join(d, ".git")):
            bulunan.append(d)
        ust = os.path.dirname(d)
        if ust == d:
            return bulunan
        d = ust


REL = "hafiza/muvekkil-adlari.txt"
sizinti, incelenen, bos_depo, depolar = [], 0, [], _kapsayan_depolar(REL)
for kok_depo in depolar:
    rel = os.path.relpath(os.path.realpath(os.path.join(KOK, REL)), kok_depo)
    _k, hepsi = git("rev-list", "--all", "--count", cwd=kok_depo)
    if hepsi.strip() in ("", "0"):
        # Depoda HİÇ commit yok: bu, sızıntı olmadığının OLUMLU kanıtıdır,
        # "bakamadım" değil. İki durumu ayırmak §2'nin istediği şeydir.
        bos_depo.append(os.path.basename(kok_depo) or kok_depo)
        continue
    _k, cikti = git("log", "--all", "--format=%h", "--", rel, cwd=kok_depo)
    for c in [x for x in cikti.split("\n") if x]:
        incelenen += 1
        _k2, icerik = git("show", "%s:%s" % (c, rel), cwd=kok_depo)
        gercek = [x for x in icerik.split("\n")
                  if x.strip() and not x.strip().startswith("#")]
        if gercek:
            sizinti.append("%s:%s (%d satır)"
                           % (os.path.basename(kok_depo), c, len(gercek)))
kanit = bool(incelenen) or bool(bos_depo)
vaka("Y-04", "geçmişte hiçbir sürümde gerçek ad işlenmemiş",
     kanit and not sizinti,
     ("SIZINTI: %s" % ", ".join(sizinti)) if sizinti
     else ("%d depo incelendi · %d sürüm tek tek açıldı · commit taşımayan "
           "depo: %s" % (len(depolar), incelenen, ", ".join(bos_depo) or "yok"))
     if kanit
     else "DOĞRULANAMADI: yolu kapsayan bir depo bulunamadı — sıfır "
          "incelenmiş sürüm, 'sızıntı yok' iddiasının kanıtı DEĞİLDİR")

# --- Y-05 · denetim "doldur" derken KORUMAYI da söylüyor mu ----------
d = subprocess.run(["bash", os.path.join(KOK, "denetim.sh"), "--yapisal"],
                   capture_output=True, text=True).stdout
# KAÇIŞ MADDESİ KALDIRILDI. İlk ölçüt "(denetim kaydı anmıyorsa geç)" idi:
# anmayı SİLMEK vakayı yeşile alıyordu. Koruduğu şeyi kaldırarak tatmin
# edilebilen bir kontrol, kontrol değildir — mutasyon bunu sağ kalarak
# gösterdi. Ölçüt artık koşulsuz: kayıt DOSYASI varsa, denetim korumayı
# söylemek ZORUNDADIR (dosya boş da olsa dolu da olsa).
kayit_var = os.path.exists(os.path.join(KOK, "hafiza/muvekkil-adlari.txt"))
soyluyor = bool(re.search(r"yoksay|gitignore|izlenmi|depoya girme", d, re.I))
vaka("Y-05", "denetim, kayıt dosyası varken korumasını her hâlde söylüyor",
     (not kayit_var) or soyluyor,
     ("kayıt dosyası var; denetim çıktısında koruma cümlesi %s"
      % ("var" if soyluyor else "YOK — kullanıcı gerçek adları §2'nin git "
         "init ettiği bir ağaca yazar ve ilk push kural 6'yı çiğner"))
     if kayit_var else "kayıt dosyası yok")

BEKLENEN_VAKA = 5


def rapor():
    if len(sonuclar) != BEKLENEN_VAKA:
        vaka("Y-00", "takım beyan ettiği vaka sayısını taşıyor", False,
             "beyan %d, bulunan %d" % (BEKLENEN_VAKA, len(sonuclar)))
    print("=" * 96)
    print("KÖR SINAMA Y — sistemin KALICI hâle getirdiği sır")
    print("=" * 96)
    for kod, baslik, gecti, ayrinti in sonuclar:
        dd, _ = beklenen.durum(kod, gecti)
        print("%s %-6s %s" % (dd, kod, baslik))
        if ayrinti:
            print("        %s" % ayrinti)
    _s, _c = beklenen.ozet([(x[0], x[2]) for x in sonuclar])
    print("-" * 96)
    print("%d vaka · %d geçti · %d beklenen · %d SİNYAL"
          % (len(sonuclar), _c["GEÇTİ"], _c["BEKLENEN"], _s))
    return _s


if __name__ == "__main__":
    sys.exit(min(rapor(), 120))
