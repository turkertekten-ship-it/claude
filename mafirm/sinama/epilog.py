#!/usr/bin/env python3
"""hepsi.sh'in EPİLOG kontrolleri — koşumun tamamını bilen katman.

Neden ayrı bir dosya (otuz dokuzuncu tur). Bu kontroller hepsi.sh'in içinde
gömülü bir heredoc'tu ve üç sonucu vardı:

  1. SINANAMIYORLARDI. Bir epilog kontrolünü mutasyonla sınamak, kırk üç
     takımın tamamını koşturmayı gerektiriyordu (~60 sn). Dört kontrol için
     dört tam koşum: dört dakika. AT'nin denetime uyguladığı ölçüt —
     "her kontrolün kanıtlanmış bir mutasyonu olmalı" — bu yüzden buraya
     hiç uygulanmamıştı.
  2. AE takımının desen taraması onları HİÇ GÖRMÜYORDU: AE `.py` dosyalarını
     tarıyor, bu kod ise bir `.sh` dosyasının içindeydi. Nitekim burada
     Türkçe metin üzerinde ÇIPLAK `.lower()` duruyordu — sınıfın yedinci
     sızması, dört tur boyunca taramanın kör noktasında.
  3. Kontrol mantığı ile koşum mekaniği aynı dosyada karışıyordu.

Ayrıştırma katman ihlali DEĞİLDİR: kontrol hâlâ tam günlüğü bilen tek yerden
çağrılıyor (hepsi.sh epilogu). Değişen tek şey, kontrolün (günlük, taban)
ikilisinin SAF BİR FONKSİYONU hâline gelmesi — yani sentetik bir günlükle,
tam koşum olmadan sınanabilmesi. Sınanan şey bir KOPYA değil, üretimde
koşan kodun kendisidir.
"""
import io
import json
import os
import re
import sys


def tr_kucult(s):
    """Türkçe-güvenli küçültme. Çıplak .lower() 'İ' harfini i+U+0307 yapar."""
    return s.replace("I", "ı").replace("İ", "i").lower()


def parmak(c):
    return {k[:6] for k in re.findall(r"[\wçğıöşüÇĞİÖŞÜ]{4,}", tr_kucult(c))}


def beyan_kontrolu(beyan, gunluk):
    """(yok, kaymis, belirtisiz) — beyan edilmiş taban ile koşum karşılaştırması."""
    yok, kaymis, belirtisiz = [], [], []
    for kod in sorted(beyan):
        m = re.search(r"^BEKLENEN\s+%s\s+[^\n]*\n(?:\s{4,}([^\n]*)\n)?"
                      % re.escape(kod), gunluk, re.M)
        if not m:
            yok.append(kod)
            continue
        belirti = beyan[kod].get("belirti")
        if not belirti:
            belirtisiz.append(kod)
            continue
        canli = (m.group(1) or "").strip()
        if not canli:
            continue
        a, b = parmak(belirti), parmak(canli)
        if a and len(a & b) / len(a) < 0.6:
            kaymis.append(kod)
    return yok, kaymis, belirtisiz


def sayim_kontrolu(rapor, toplam):
    """Raporun EL YAZISI vaka sayıları ile koşumun gerçek toplamı."""
    # [kendi kusurum · aynı turda yakalandı] Bash sürümünden PORT EDERKEN
    # çapayı düşürdüm: `\*\*[0-9]{3}$` (satır SONUNDA `**NNN`) yerine
    # `\*\*(\d{3})\b` yazdım ve ölçüt raporun ANLATISINDAKİ her kalın üç
    # haneli sayıyı yakaladı — 300, 302, 330, 690 gibi TARİHSEL rakamlar.
    # Yani port, çalışan bir ölçütü yanlış pozitif üretir hâle getirdi.
    # V takımının dersi: bir kapıyı genişletmek, onu kullanılmaz yapar.
    # Çapalar birebir geri konuldu; üçüncüsündeki sabit "15 mutasyon"
    # ifadesi de genelleştirildi (küme otuz sekizinci turda 27'ye çıktı).
    iddia = set()
    for kal in (r"\*\*(\d{3})$", r"^vaka, (\d{3}) mutasyon",
                r"(\d{3}) vaka \+ \d+ mutasyon"):
        iddia |= set(re.findall(kal, rapor, re.M))
    return sorted(i for i in iddia if int(i) != toplam)


def toplami_bul(gunluk):
    return sum(int(x) for x in re.findall(r"^(\d+) vaka", gunluk, re.M))


def _blok(baslik, alt):
    return ("\n  ------------------------------------------------------------\n"
            "  UYARI %s\n  %s" % (baslik, alt))


def calistir(gunluk_metni, beyan, rapor):
    """(çıktı satırları, uyarı sayısı). Saf fonksiyon: sınanabilir."""
    cikti, n = [], 0
    yok, kaymis, belirtisiz = beyan_kontrolu(beyan, gunluk_metni)
    alt = "Tam günlük üzerinden ölçüldü (epilog): beyan bayat ya da vaka kayboldu."
    for ad, kume in (
            ("beyanlı olup koşumda BEKLENEN görünmeyen vaka", yok),
            ("beyan edilen BELİRTİ artık canlı belirtiyle uyuşmuyor", kaymis),
            ("belirti KAYDI olmayan beyan", belirtisiz)):
        if kume:
            cikti.append(_blok("%s: %s" % (ad, " ".join(kume)), alt))
            n += 1
    toplam = toplami_bul(gunluk_metni)
    bayat = sayim_kontrolu(rapor, toplam)
    if bayat:
        cikti.append(_blok(
            "raporun vaka sayısı bayat: %s (gerçek: %d)"
            % (" ".join(bayat), toplam),
            "Bu satır yukarıdaki özetten SONRA hesaplanır: gerçek toplam ancak\n"
            "  bütün takımlar koştuktan sonra bilinir."))
        n += 1
    return cikti, n


def main(argv):
    gunluk_yolu, kok = argv[1], argv[2]
    gunluk = io.open(gunluk_yolu, encoding="utf-8", errors="replace").read()
    bj = os.path.join(kok, "sinama", "beklenen.json")
    beyan = json.load(io.open(bj, encoding="utf-8"))["vakalar"] \
        if os.path.exists(bj) else {}
    rj = os.path.join(kok, "RAPOR.md")
    rapor = io.open(rj, encoding="utf-8").read() if os.path.exists(rj) else ""
    cikti, n = calistir(gunluk, beyan, rapor)
    for blok in cikti:
        print(blok)
    return n


if __name__ == "__main__":
    sys.exit(main(sys.argv))
