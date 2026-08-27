#!/usr/bin/env python3
"""KÖR SINAMA L — çapraz referans bütünlüğü.

§4'ün gerekçesi: "birimler arasında geçen bir hukukçu her yerde aynı düzeni
bulur." Bu düzen, dosyaların birbirine yaptığı atıflarla ayakta duruyor ve
hiçbir kapı ile hiçbir denetim satırı o atıfların HEDEFİNİN VAR OLDUĞUNA
bakmıyor. Kırık bir atıf, sessiz bir yönlendirme hatasıdır: hukukçu boş bir
yere gönderilir ve oradan hafızayla devam eder — sistemin önlemek için var
olduğu şey.

Bu takımın kendi kusur kaydı (kör sınama de sınanır):
  1. sürüm çıplak dosya adlarını ("esik.py çalıştırılır") atıf saydı — oysa
     düzyazıdaki anıştırma bir bağlantı değildir. 32 sahte kırık üretti.
  2. sürüm GÖRECELİ atıfları köke göre çözdü: `birimler/rekabet/INDEX.md`
     içindeki `yontem/tr-esikler.md`, INDEX'in KENDİ dizinine göre çözülür.
     12 sahte kırık daha üretti.
  3. sürüm: önce içeren dosyanın dizinine, sonra köke göre çözer.
"""
import glob
import os
import re
import sys

_KOK_COZ = os.environ.get("MAFIRM") or os.path.dirname(
    os.path.dirname(os.path.abspath(__file__)))

# Yalnızca gerçek YOL atıfları: içinde / olanlar.
YOL = re.compile(r'`([~\w][\w./*-]*/[\w./*-]*\.(?:md|py|sh|json|txt))`')
sonuclar = []


def vaka(kod, baslik, gecti, ayrinti=""):
    sonuclar.append((kod, baslik, gecti, ayrinti))


def coz(yol, icindeki_dosya):
    """Önce içeren dosyanın dizinine, sonra köke göre."""
    yol = yol.replace("~/mafirm/", "")
    adaylar = [os.path.join(os.path.dirname(icindeki_dosya), yol),
               os.path.join(_KOK_COZ, yol)]
    for a in adaylar:
        if "*" in a:
            if glob.glob(a):
                return True
        elif os.path.exists(a):
            return True
    return False


# --- L-01: belge atıfları -------------------------------------------------
kirik, toplam = [], 0
for f in glob.glob(_KOK_COZ + "/**/*.md", recursive=True):
    rel = os.path.relpath(f, _KOK_COZ)
    if rel.startswith(("sinama/", "yamalar/")):
        continue
    for m in YOL.finditer(open(f, encoding="utf-8").read()):
        toplam += 1
        if not coz(m.group(1), f):
            kirik.append((rel, m.group(1)))
vaka("L-01", "belgelerdeki her yol atfının hedefi var", not kirik,
     "%d atıf incelendi, kırık: %s" % (toplam, kirik or "yok"))

# --- L-02: her INDEX kendi yöntem dosyalarını gösteriyor mu ---------------
eksik_index = []
for d in sorted(glob.glob(_KOK_COZ + "/birimler/*/")):
    if "_koltuklar" in d:
        continue
    idx = os.path.join(d, "INDEX.md")
    if not os.path.exists(idx):
        eksik_index.append(os.path.basename(d.rstrip("/")))
        continue
    icerik = open(idx, encoding="utf-8").read()
    for y in glob.glob(os.path.join(d, "yontem", "*.md")):
        if os.path.basename(y) not in icerik:
            eksik_index.append("%s -> %s" % (os.path.basename(d.rstrip("/")),
                                             os.path.basename(y)))
vaka("L-02", "her INDEX kendi yöntem dosyalarının hepsini anıyor",
     not eksik_index, "anılmayan: %s" % (eksik_index or "yok"))

# --- L-03: taşınabilirlik — belgelerde sabit ~/mafirm kalmış mı ----------
sabit = []
for kalip in ("/.claude/skills/*/SKILL.md", "/.claude/commands/*.md",
              "/.claude/agents/*.md", "/komutlar/*.md", "/birimler/**/*.md"):
    for f in glob.glob(_KOK_COZ + kalip, recursive=True):
        for i, satir in enumerate(open(f, encoding="utf-8"), 1):
            if "~/mafirm" in satir:
                sabit.append("%s:%d" % (os.path.relpath(f, _KOK_COZ), i))
vaka("L-03", "belgelerde sabit ~/mafirm yolu kalmamış", not sabit,
     "Bir klon KENDİ ağacını değil makinedeki kurulumu çalıştırmaya "
     "yönlendirilir. Kalan: %s" % (sabit or "yok"))

# --- L-04: beceri/komutların andığı kod dosyaları var mı -----------------
kod_ref = re.compile(r"python3\s+(\S+\.py)")
kayip = []
for f in (glob.glob(_KOK_COZ + "/.claude/skills/*/SKILL.md")
          + glob.glob(_KOK_COZ + "/.claude/commands/*.md")
          + glob.glob(_KOK_COZ + "/komutlar/*.md")):
    for m in kod_ref.finditer(open(f, encoding="utf-8").read()):
        if not coz(m.group(1), f):
            kayip.append((os.path.relpath(f, _KOK_COZ), m.group(1)))
vaka("L-04", "beceri ve komutların çalıştırdığı her betik var",
     not kayip, "kayıp: %s" % (kayip or "yok"))

# --- L-05: settings.json deny kalıpları biçimsel olarak geçerli mi -------
import json
ayar = json.load(open(os.path.join(_KOK_COZ, ".claude/settings.json"),
                      encoding="utf-8"))
deny = ayar.get("permissions", {}).get("deny", [])
bozuk = [d for d in deny if not re.match(r"^[A-Z]\w*\(.*\)$", d)]
vaka("L-05", "izin reddi kalıpları Araç(desen) biçiminde",
     bool(deny) and not bozuk,
     "%d kalıp, biçimsiz: %s" % (len(deny), bozuk or "yok"))

# --- L-06: hafiza/ dosyalarının hepsi yerinde ----------------------------
gerekli = ["hafiza/cikar-catismasi.md", "hafiza/muvekkil-adlari.txt",
           "hafiza/dogrulama-bulgulari.md"]
yok = [g for g in gerekli if not os.path.exists(os.path.join(_KOK_COZ, g))]
vaka("L-06", "hafiza/ dosyalarının hepsi var", not yok, "eksik: %s" % (yok or "yok"))


def rapor():
    print("=" * 96)
    print("KÖR SINAMA L — çapraz referans bütünlüğü")
    print("=" * 96)
    kaldi = 0
    for kod, baslik, gecti, ayrinti in sonuclar:
        d = "GEÇTİ" if gecti else "KALDI"
        if not gecti:
            kaldi += 1
        print("%s %-6s %s" % (d, kod, baslik))
        if ayrinti:
            print("        %s" % ayrinti)
    print("-" * 96)
    print("%d vaka, %d geçti, %d KALDI" % (len(sonuclar),
                                           len(sonuclar) - kaldi, kaldi))
    return kaldi


if __name__ == "__main__":
    sys.exit(min(rapor(), 120))
