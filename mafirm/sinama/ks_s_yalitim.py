#!/usr/bin/env python3
"""KÖR SINAMA S — yalıtım: klon GERÇEKTEN yalnız mı.

Dokuz tur boyunca "kaynak ≡ klon" diye doğruladım. O karşılaştırma bir şeyi
YAPISAL OLARAK göremez: her iki ağaç da diskte dururken, klondan bir dosya
kaynağa uzansa bile iki koşum aynı sonucu verir. Ölçüm, ölçtüğü kusuru
gizliyordu.

Kaynak ağacı geçici olarak kaldırıp klonu tek başına koşturunca çıktı:
`denetim.sh` içindeki İKİ gömülü Python parçacığı kökü kendi başına
`expanduser('~/mafirm')` ile çözüyordu. Kaynak ağaç yokken denetim
"DENETİM BAŞARISIZ: 1" veriyordu — var olmayan bir ağaca uzandığı için.
Ve takım hâlâ "0 SİNYAL" diyordu, çünkü hiçbir vaka denetimin kendi yol
çözümlemesine bakmıyordu.

Bu, bu oturumda aynı sınıfın ÜÇÜNCÜ tekrarı (kapi.py ad kaydı, ks_b ad kaydı,
denetim.sh gömülü parçacıkları): **iddia ettiği şeyin dışına uzanan bir
kontrol.** Kitabın D takımıyla bulduğum kusurun tam karşılığı.
"""
import os
import re
import subprocess
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import beklenen  # noqa: E402

_KOK_COZ = os.environ.get("MAFIRM") or os.path.dirname(
    os.path.dirname(os.path.abspath(__file__)))

sonuclar = []


def vaka(kod, baslik, gecti, ayrinti=""):
    sonuclar.append((kod, baslik, gecti, ayrinti))


# --- S-01: hiçbir çalıştırılabilir dosya kökü sabitlemesin -------------
# Muaf: kitaba sadık kopyalar (tarihsel kayıt) ve L'nin kendi dedektör dizeleri
# (o dize, aranan DESENİN kendisidir, bir yol değil).
SABIT = re.compile(r"(expanduser\(\s*[\"']~/mafirm|\$HOME/mafirm|\"\$HOME\"/mafirm)")
MUAF_DOSYA = ("yamalar/kitaba-sadik/", "sinama/ks_l_referans.py",
              "sinama/ks_s_yalitim.py")
kirli = []
for kok, _, dosyalar in os.walk(_KOK_COZ):
    if "/.git" in kok or "__pycache__" in kok:
        continue
    for d in dosyalar:
        if not d.endswith((".py", ".sh")):
            continue
        rel = os.path.relpath(os.path.join(kok, d), _KOK_COZ)
        if rel.startswith(MUAF_DOSYA):
            continue
        icerik = open(os.path.join(kok, d), encoding="utf-8",
                      errors="replace").read()
        for i, satir in enumerate(icerik.splitlines(), 1):
            if SABIT.search(satir):
                kirli.append("%s:%d" % (rel, i))
vaka("S-01", "hiçbir çalıştırılabilir dosya kökü sabitlemiyor",
     not kirli, "sabitleyen: %s" % (kirli or "yok"))

# --- S-02: DİNAMİK — denetim sahte bir HOME ile çalışıyor mu ----------
sahte = tempfile.mkdtemp(prefix="yalitim-home-")
ortam = dict(os.environ, HOME=sahte)
ortam.pop("MAFIRM", None)
ortam.pop("MAFIRM_KOK", None)
r = subprocess.run([os.path.join(_KOK_COZ, "denetim.sh"), "--yapisal"],
                   capture_output=True, text=True, env=ortam, timeout=120)
vaka("S-02", "denetim sahte bir HOME ile yapısal olarak yeşil",
     r.returncode == 0,
     "çıkış %d · son satır: %s"
     % (r.returncode, (r.stdout or r.stderr).strip().splitlines()[-1:]))

# --- S-03: DİNAMİK — kapı sahte HOME ile ad kaydını doğru yerden okuyor
kapi_yol = os.path.join(_KOK_COZ, ".claude/hooks/kapi.py")
r2 = subprocess.run([sys.executable, kapi_yol, "--self-test"],
                    capture_output=True, text=True, env=ortam, timeout=60)
vaka("S-03", "kapı öz-sınaması sahte HOME ile geçiyor",
     r2.returncode == 0 and "SELFTEST OK" in r2.stdout,
     r2.stdout.strip().splitlines()[-1:] or r2.stderr[:80])

# --- S-04: köke giden yol yalnızca __file__ ya da MAFIRM'den türesin --
coz = []
for f in sorted(os.listdir(os.path.join(_KOK_COZ, "sinama"))):
    if not f.endswith(".py") or f in ("beklenen.py",):
        continue
    icerik = open(os.path.join(_KOK_COZ, "sinama", f), encoding="utf-8").read()
    if "_KOK_COZ" in icerik and "abspath(__file__)" not in icerik:
        coz.append(f)
vaka("S-04", "her takım kökü kendi konumundan çözüyor",
     not coz, "çözmeyen: %s" % (coz or "yok"))

# --- S-05: MUTASYON — sabit yol eklenirse S-01 yakalar ---------------
gecici = os.path.join(_KOK_COZ, "sinama", "_yalitim_mutasyon.py")
try:
    with open(gecici, "w", encoding="utf-8") as f:
        f.write("import os\nyol = os.path.expanduser('~/mafirm/x')\n")
    bulundu = any(
        SABIT.search(l)
        for l in open(gecici, encoding="utf-8").read().splitlines())
    vaka("S-05", "mutasyon: sabit yol eklenirse desen yakalar", bulundu)
finally:
    if os.path.exists(gecici):
        os.remove(gecici)


# [AF-02] Kaybolan bir vaka, kırmızı bir vakadan kötüdür: kimse aramaz.
# Bu koruma on üçüncü turda eklendi ama YALNIZCA sonrasında yazılan
# takımlara; on beş takım korumasız kaldı. Geriye doldurma.
BEKLENEN_VAKA = 5


def rapor():
    if len(sonuclar) != BEKLENEN_VAKA:
        vaka("S-00", "takım beyan ettiği vaka sayısını taşıyor", False,
             "beyan %d, bulunan %d" % (BEKLENEN_VAKA, len(sonuclar)))

    print("=" * 96)
    print("KÖR SINAMA S — yalıtım: klon gerçekten yalnız mı")
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
