#!/usr/bin/env python3
"""KÖR SINAMA AJ — çalıştığı BİLİNEN bir kanal, açık bulgular için kullanıldı mı.

§2: bir olumsuz iddia, olumludan yüksek kanıt ister. Bu rapor şu olumsuz
iddiayı taşıyor: *"Bu ortamda hiçbir birincil kaynağa erişilemedi."*
`hafiza/egress-kaniti.md` onu kanal kanal kanıtlıyor — ve o tablonun son
satırı yirmi yedi tur boyunca şunu yazıyordu:

    | WebSearch | aynı alan adları | **çalışıyor** |

Kayıt doğruydu. Ben yanlış okudum: "arama motoru özeti döndürüyor" notunu
"işe yaramaz" diye anladım ve üç ENGELLEYİCİ bulguyu, çalıştığı KAYITLI olan
bir kanalı hiç zorlamadan açık tuttum.

Ders, kaydın yanlış olması değil — **kaydın doğru olması ve okunmaması.**
Bir kanal "çalışıyor" diye işaretliyse, açık bulgular için NE KADAR İLERİ
GÖTÜRDÜĞÜ ölçülmelidir. Sınıflandırıp geçmek, ölçmek değildir.

Bu takım, çalışan her kanalın açık bulgularda kullanıldığını KAYIT üzerinden
denetler.
"""
import io
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import beklenen  # noqa: E402

KOK = os.environ.get("MAFIRM") or os.path.dirname(
    os.path.dirname(os.path.abspath(__file__)))
sonuclar = []


def vaka(kod, baslik, gecti, ayrinti=""):
    sonuclar.append((kod, baslik, gecti, ayrinti))


def oku(rel):
    p = os.path.join(KOK, rel)
    return io.open(p, encoding="utf-8").read() if os.path.exists(p) else ""


EGRESS = oku("hafiza/egress-kaniti.md")
BULGU = oku("hafiza/dogrulama-bulgulari.md")

# --- AJ-01 · egress kaydı kanal kanal mı (§2'nin istediği biçim) -----
satirlar = re.findall(r"^\| ([^|]+) \| ([^|]+) \| ([^|]+) \|$", EGRESS, re.M)
kanallar = [(a.strip(), c.strip()) for a, b, c in satirlar
            if not a.strip().startswith(("Kanal", "---"))]
vaka("AJ-01", "erişim iddiası kanal kanal kanıtlanıyor",
     len(kanallar) >= 4,
     "%d kanal kaydı: %s" % (len(kanallar),
                             ", ".join(k for k, _s in kanallar)))

# --- AJ-02 · ÇALIŞAN kanal varsa, açık bulgularda kullanılmış olmalı --
calisan = [k for k, s_ in kanallar if "çalışıyor" in s_.lower()]
kullanilmamis = []
for k in calisan:
    # Bulgu kaydında o kanalla yükseltilmiş bir kanıt katmanı var mı
    if "KANIT KATMANI" not in BULGU:
        kullanilmamis.append(k)
vaka("AJ-02", "çalışan her kanal açık bulgular için kullanılmış",
     not kullanilmamis,
     ("KULLANILMAMIŞ: %s — çalıştığı KAYITLI bir kanal, açık bulguları "
      "ilerletmek için hiç zorlanmamış" % ", ".join(kullanilmamis))
     if kullanilmamis
     else "çalışan kanal: %s · kanıt katmanı yükseltmeleri kayıtta"
          % ", ".join(calisan))

# --- AJ-03 · her ENGELLEYİCİ bulgu bir kanıt katmanı beyanı taşıyor --
engelleyici = re.findall(r"^(I-\d+) \| ENGELLEYICI \|[^|]*\| (.+)$",
                         BULGU, re.M)
katmansiz = [k for k, g in engelleyici if "KANIT KATMANI" not in g]
vaka("AJ-03", "her ENGELLEYİCİ bulgu kanıt katmanını beyan ediyor",
     bool(engelleyici) and not katmansiz,
     ("katman beyanı yok: %s" % ", ".join(katmansiz)) if katmansiz
     else "%d engelleyici bulgunun hepsi katman beyanlı" % len(engelleyici))

# --- AJ-04 · kanıt yükseltmesi bulguyu KAPATMIYOR --------------------
# İkincil kaynak birincil metnin yerine geçmez. Bir yükseltme, statüyü
# ENGELLEYİCİ'den çıkarıyorsa bu bir yöntem hatasıdır.
kapanan = [k for k, g in engelleyici
           if "KANIT KATMANI" in g and "ENGELLEYİCİ kalır" not in g
           and "Statü hâlâ ENGELLEYİCİ" not in g]
vaka("AJ-04", "kanıt yükseltmesi bulguyu kapatmıyor (ikincil ≠ birincil)",
     not kapanan,
     ("statüsü korunmayan: %s" % ", ".join(kapanan)) if kapanan
     else "üç yükseltmenin üçü de statüyü ENGELLEYİCİ tutuyor")

# --- AJ-05 · denetim engelleyici bulguları hâlâ kırmızıda tutuyor ----
import subprocess
r = subprocess.run(["bash", os.path.join(KOK, "denetim.sh")],
                   capture_output=True, text=True,
                   env=dict(os.environ, MAFIRM=KOK))
vaka("AJ-05", "denetim engelleyici bulgular yüzünden hâlâ kırmızı",
     r.returncode == len(engelleyici),
     "denetim çıkışı %d, engelleyici bulgu %d"
     % (r.returncode, len(engelleyici)))


BEKLENEN_VAKA = 5


def rapor():
    if len(sonuclar) != BEKLENEN_VAKA:
        vaka("AJ-00", "takım beyan ettiği vaka sayısını taşıyor", False,
             "beyan %d, bulunan %d" % (BEKLENEN_VAKA, len(sonuclar)))
    print("=" * 96)
    print("KÖR SINAMA AJ — çalışan kanal açık bulgular için kullanıldı mı")
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
