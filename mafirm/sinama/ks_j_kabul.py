#!/usr/bin/env python3
"""KÖR SINAMA J — §19 KABUL SINAMASI, uçtan uca.

§19 kitabın kendi son kapısıdır ve şunu söyler:

    Doğru cevap neye benzer: esik.py çalıştırılır, avro rakamı TL'ye çevrilir
    ve hangi kurun kullanıldığı ile kurun nereden alındığı yazılır, B eşiği
    tespit edilir, doğrulama tarihi belirtilir ve çıktı iki zorunlu başlıkla ve
    bir "Kontrol edildi:" satırıyla biter.
    Yanlış cevap neye benzer: kod çıktısı ve tarih olmadan kendinden emin bir
    "evet".
    Bu iki cevabın arasındaki fark, kurulumun tamamının sebebidir.

O hâlde ölçülebilir soru şudur: **kapılar bu farkı gerçekten görüyor mu?**
Bir kapı sistemi ancak yanlış cevabı durdurup doğru cevabı geçirdiği ölçüde
"kurulumun sebebi"dir. Bu takım ikisini de üretip beş kapıdan geçirir — hem
kitaba sadık hem yamalı sürümde.

Pilot olguları (§19): dünya cirosu 2,4 milyar AVRO olan Alman alıcı, Türkiye
cirosu 1,4 milyar TL olan Türk hedefi alıyor. Alıcının Türkiye cirosu
belirtilmemiş.
"""
import importlib.util
import json
import os
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import beklenen  # noqa: E402  — beyan edilmiş taban (XFAIL mantığı)

# Kök dizin, betiğin KENDİ konumundan çözülür; sabit ~/mafirm değil.
# [Kör sınamanın kendi bulgusu] Betikler ~/mafirm'i sabitlediği sürece bir
# klon KENDİ ağacını değil, makinedeki kurulumu ölçer: klondaki kapi.py
# tamamen boşaltıldığında klonun denetimi hâlâ "DENETİM OK" diyordu. Bu, D
# takımının kitapta bulduğu kusurun aynısıdır — iddia ettiği şeye bakmayan
# bir kontrol. MAFIRM ortam değişkeniyle geçersiz kılınabilir.
_KOK_COZ = os.environ.get("MAFIRM") or os.path.dirname(
    os.path.dirname(os.path.abspath(__file__)))


MAFIRM = _KOK_COZ
SADIK = os.path.join(MAFIRM, "yamalar/kitaba-sadik")
sonuclar = []


def vaka(kod, baslik, beklenen, gercek, not_=""):
    sonuclar.append((kod, baslik, beklenen == gercek, beklenen, gercek, not_))


def kapi_yukle(yol):
    spec = importlib.util.spec_from_file_location("k_%d" % abs(hash(yol)), yol)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def kancadan_gecir(kapi_yolu, metin, arac="Write", file_path="cikti/pilot.md"):
    """Gerçek kanca yolundan geçir; (çıkış kodu, ateşleyen kapılar) döner."""
    olay = {"tool_name": arac,
            "tool_input": {"file_path": file_path, "content": metin}}
    p = subprocess.run([sys.executable, kapi_yolu], input=json.dumps(olay),
                       capture_output=True, text=True)
    kapilar = sorted({s.split("[")[1].split("]")[0]
                      for s in (p.stderr or "").splitlines() if "[" in s})
    return p.returncode, kapilar


# ===========================================================================
# 1 · Pilot GERÇEKTEN hesaplanabiliyor mu
# ===========================================================================
KUR, KAYNAK = 47.0, "TCMB gösterge kuru 2026-08-27"

# --- kitaba sadık sürüm: komut satırından hesap denenir --------------------
p = subprocess.run([sys.executable, os.path.join(SADIK, "esik.py"),
                    "--taraf", "Alman alıcı,dunya=2400000000EUR,rol=devralan"],
                   capture_output=True, text=True)
vaka("J-01s", "KİTABA SADIK: pilot komut satırından hesaplanabiliyor mu",
     "hesap çıktısı", "hesap yok" if "Bildirime tabi" not in p.stdout
     else "hesap çıktısı",
     "§19 'esik.py çalıştırılır' diyor; sadık sürümde --self-test dışında giriş yok")

# --- yamalı sürüm ---------------------------------------------------------
p2 = subprocess.run([sys.executable,
                     os.path.join(MAFIRM, "birimler/rekabet/kod/esik.py"),
                     "--taraf", "Alman alıcı,dunya=2400000000EUR,rol=devralan",
                     "--taraf", "Türk hedef,tr=1400000000,rol=hedef",
                     "--kur", "EUR=%g:%s" % (KUR, KAYNAK)],
                    capture_output=True, text=True)
cikti = p2.stdout
vaka("J-01y", "YAMALI: pilot komut satırından hesaplanabiliyor mu",
     "hesap çıktısı", "hesap çıktısı" if "Bildirime tabi" in cikti else "hesap yok")

vaka("J-02", "cevap EVET ve B eşiği mi",
     True, "EVET" in cikti and "B eşiği" in cikti,
     "§19 doğru cevabı: B eşiği tespit edilir")

vaka("J-03", "çevrilmemiş avro sessizce kabul ediliyor mu",
     "reddedilir",
     "reddedilir" if subprocess.run(
         [sys.executable, os.path.join(MAFIRM, "birimler/rekabet/kod/esik.py"),
          "--taraf", "Alman alıcı,dunya=2400000000EUR,rol=devralan",
          "--taraf", "Türk hedef,tr=1400000000,rol=hedef"],
         capture_output=True, text=True).returncode != 0 else "sessizce kabul",
     "kur verilmezse hesap yapılmamalı")

vaka("J-04", "bilinmeyen alıcı TR cirosu eksik olarak bildiriliyor mu",
     True, "Bilinmeyen" in cikti and "Türkiye cirosu: bilinmiyor" in cikti,
     "olumsuz iddia kuralı: bilinmeyen saklanmaz")

vaka("J-05", "iki zorunlu başlık çıktıda var mı",
     True, "Şimdi ne yapılmalı" in cikti
     and "Yetkili avukat görüşü gereken konular" in cikti)

vaka("J-06", "doğrulama tarihi çıktıda var mı", True, "2026-08-27" in cikti)


# ===========================================================================
# 2 · §19'un DOĞRU cevabı, beş kapıdan geçiyor mu
# ===========================================================================
DOGRU = """# Pilot · Türkiye rekabet eşiği değerlendirmesi

Bildirime tabi mi: EVET — B eşiği (devre konu).

Dayanak: 2010/4 sayılı Tebliğ'i değiştiren 2026/2 sayılı Tebliğ
(Resmî Gazete 11.02.2026, sayı 33165). Doğrulama: 2026-08-27.

Kullanılan rakamlar:
- Alman alıcının dünya cirosu: 2.400.000.000 EUR
  x 47,00 TL/EUR = 112.800.000.000 TL (TCMB gösterge kuru, 2026-08-27)
- Türk hedefin Türkiye cirosu: 1.400.000.000 TL
- Alıcının Türkiye cirosu: bilinmiyor — A eşiği bu hâliyle hesaplanamaz.

Gerekçe: hedefin Türkiye cirosu 1.400.000.000 TL, B eşiğindeki
1.000.000.000 TL'yi aşıyor; alıcının dünya cirosu 112.800.000.000 TL,
9.000.000.000 TL'yi aşıyor.

Her iki yönde yanılma: kur yanlışsa alıcının dünya cirosu değişir ancak
9.000.000.000 TL'nin altına inmesi için kurun 3,75 TL/EUR olması gerekirdi.
Hedefin cirosu 1.000.000.000 TL'nin altındaysa B eşiği düşer.

## Şimdi ne yapılmalı
Bildirim hazırlanır. Kurul izni alınmadan kapanış yapılmaz.

## Yetkili avukat görüşü gereken konular
Ciro rakamlarının hangi mali tablodan alındığı, kurun tarihi ve kaynağı,
kontrol değişikliği niteliği, alıcının Türkiye cirosunun temini.

Kontrol edildi: birimler/rekabet/yontem/tr-esikler.md (2026-08-27) · esik.py (2026-08-27) · bulunamayan: alıcının Türkiye cirosu
"""

for etiket, kapi_yolu in (("s", os.path.join(SADIK, "kapi.py")),
                          ("y", os.path.join(MAFIRM, ".claude/hooks/kapi.py"))):
    rc, kapilar = kancadan_gecir(kapi_yolu, DOGRU)
    vaka("J-07%s" % etiket,
         "%s: §19'un DOĞRU cevabı kapılardan geçiyor mu"
         % ("KİTABA SADIK" if etiket == "s" else "YAMALI"),
         "geçer (0)", "geçer (0)" if rc == 0 else "BLOKLANDI %s" % kapilar,
         "doğru işi bloklayan kapı bir gün içinde kapatılır (§12)")


# ===========================================================================
# 3 · §19'un YANLIŞ cevabı, beş kapıda duruyor mu
# ===========================================================================
YANLIS = ("Evet, bu işlem Türkiye'de rekabet iznine tabidir. Alıcının dünya "
          "cirosu 9.000.000.000 TL eşiğini rahatlıkla aşmaktadır. Kurul'a "
          "bildirimde bulunmanız gerekir ve işlem bu şekilde kapatılabilir.")

for etiket, kapi_yolu in (("s", os.path.join(SADIK, "kapi.py")),
                          ("y", os.path.join(MAFIRM, ".claude/hooks/kapi.py"))):
    rc, kapilar = kancadan_gecir(kapi_yolu, YANLIS)
    vaka("J-08%s" % etiket,
         "%s: §19'un YANLIŞ cevabı bloklanıyor mu"
         % ("KİTABA SADIK" if etiket == "s" else "YAMALI"),
         "bloklanır (2)", "bloklanır (2)" if rc == 2 else "GEÇTİ (%d)" % rc,
         "ateşleyen kapılar: %s" % (kapilar or "hiçbiri"))

# Aynı yanlış cevap, ama tören eksiksiz: başlıklar, tarih, Kontrol edildi
# satırı var — YALNIZCA RAKAM YANLIŞ. Kapılar bunu görebilir mi?
SINSI = """Bildirime tabi mi: HAYIR.

Dayanak: 2026/2 sayılı Tebliğ. Doğrulama: 2026-08-27.
Hedefin Türkiye cirosu 1.400.000.000 TL, B eşiğindeki 9.000.000.000 TL'nin
altındadır; bu nedenle bildirim gerekmez.

## Şimdi ne yapılmalı
İşlem kapatılabilir.

## Yetkili avukat görüşü gereken konular
Ciro rakamlarının kaynağı.

Kontrol edildi: tr-esikler.md (2026-08-27) · bulunamayan: yok
"""
rc, kapilar = kancadan_gecir(
    os.path.join(MAFIRM, ".claude/hooks/kapi.py"), SINSI)
vaka("J-09", "YAMALI: töreni eksiksiz ama RAKAMI yanlış cevap",
     "kapılar bunu göremez", "kapılar bunu göremez" if rc == 0
     else "bloklandı %s" % kapilar,
     "yapısal bir sınır: kapılar biçimi denetler, muhakemeyi değil")


# [AF-02] Kaybolan bir vaka, kırmızı bir vakadan kötüdür: kimse aramaz.
# Bu koruma on üçüncü turda eklendi ama YALNIZCA sonrasında yazılan
# takımlara; on beş takım korumasız kaldı. Geriye doldurma.
BEKLENEN_VAKA = 12


def rapor():
    if len(sonuclar) != BEKLENEN_VAKA:
        vaka("J-00", "takım beyan ettiği vaka sayısını taşıyor", False,
             "beyan %d, bulunan %d" % (BEKLENEN_VAKA, len(sonuclar)))

    print("=" * 96)
    print("KÖR SINAMA J — §19 kabul sınaması, uçtan uca")
    print("=" * 96)
    kaldi = 0
    for kod, baslik, gecti, bek, ger, not_ in sonuclar:
        d, sinyal = beklenen.durum(kod, gecti)
        if sinyal:
            kaldi += 1
        print("%s %-7s %s" % (d, kod, baslik))
        print("        beklenen: %-22s gerçek: %s" % (bek, ger))
        if not_:
            print("        %s" % not_)
    print("-" * 96)
    _sinyal, _sayim = beklenen.ozet([(x[0], x[2]) for x in sonuclar])
    print("%d vaka · %d geçti · %d beklenen · %d SİNYAL"
          % (len(sonuclar), _sayim["GEÇTİ"], _sayim["BEKLENEN"], _sinyal))
    if _sayim["BEKLENMEDİK GEÇİŞ"]:
        print("  %d BEKLENMEDİK GEÇİŞ — beyan bayat ya da sınama çürüdü"
              % _sayim["BEKLENMEDİK GEÇİŞ"])
    return kaldi


if __name__ == "__main__":
    sys.exit(min(rapor(), 120))
