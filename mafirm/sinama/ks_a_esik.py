#!/usr/bin/env python3
"""KÖR SINAMA A — rekabet eşiği mantığı.

Bu dosyanın kuralı: her vaka `birimler/rekabet/yontem/tr-esikler.md` DÜZYAZISINDAN
türetilmiştir, esik.py'nin kodundan değil. esik.py'nin kendi _selftest'i altı
vaka içerir ve altısı da kodu yazan kişinin aklındaki vakalardır. Aşağıdakiler
o aklın dışında kalanlardır.

Ölçüt: şartname ne diyor. Kod ne yapıyor değil.
"""
import io
import os
import subprocess
import sys
import contextlib
# Kök dizin, betiğin KENDİ konumundan çözülür; sabit ~/mafirm değil.
# [Kör sınamanın kendi bulgusu] Betikler ~/mafirm'i sabitlediği sürece bir
# klon KENDİ ağacını değil, makinedeki kurulumu ölçer: klondaki kapi.py
# tamamen boşaltıldığında klonun denetimi hâlâ "DENETİM OK" diyordu. Bu, D
# takımının kitapta bulduğu kusurun aynısıdır — iddia ettiği şeye bakmayan
# bir kontrol. MAFIRM ortam değişkeniyle geçersiz kılınabilir.
_KOK_COZ = os.environ.get("MAFIRM") or os.path.dirname(
    os.path.dirname(os.path.abspath(__file__)))


sys.path.insert(0, os.path.join(_KOK_COZ, "birimler/rekabet/kod"))
import esik  # noqa: E402

ESIK_PY = os.path.join(_KOK_COZ, "birimler/rekabet/kod/esik.py")
sonuclar = []


def vaka(kod, baslik, beklenen, gercek, sartname):
    gecti = (beklenen == gercek)
    sonuclar.append((kod, baslik, gecti, beklenen, gercek, sartname))


# --- Sınır davranışı: şartname "aşması" diyor, "ulaşması" değil -------------
vaka("A-01", "A eşiği: toplam tam 3 milyar (aşmıyor) -> tabi değil",
     (False, "hiçbir eşik"),
     esik.bildirilmeli([2_000_000_000, 1_000_000_000], 0, []),
     "tr-esikler.md: 'toplamının 3.000.000.000 TL'yi aşması'")

vaka("A-02", "A eşiği: iki taraf tam 1 milyar (aşmıyor) -> A yok",
     False, esik.esik_a([1_000_000_000, 1_000_000_000, 1_500_000_000]),
     "tr-esikler.md: 'ayrı ayrı 1.000.000.000 TL'yi aşması'")

vaka("A-03", "A eşiği: üç taraf, ikisi tabanı aşıyor, toplam aşıyor -> A var",
     True, esik.esik_a([1_500_000_000, 1_200_000_000, 800_000_000]),
     "tr-esikler.md: 'en az ikisinin'")

vaka("A-04", "B eşiği: teknoloji hedefi tam 250 milyon (aşmıyor) -> B yok",
     False, esik.esik_b(250_000_000, [10_000_000_000], teknoloji=True),
     "tr-esikler.md: teknoloji istisnası 250.000.000 TL, koşul 'aşması'")

vaka("A-05", "B eşiği: diğer tarafın dünya cirosu tam 9 milyar -> B yok",
     False, esik.esik_b(1_200_000_000, [9_000_000_000]),
     "tr-esikler.md: 'dünya cirosunun 9.000.000.000 TL'yi aşması'")

# --- Teknoloji istisnası yalnızca B ayağındaki BİR rakamı değiştirir --------
vaka("A-06", "teknoloji bayrağı A eşiğini DEĞİŞTİRMEMELİ",
     esik.esik_a([2_000_000_000, 1_500_000_000]),
     esik.bildirilmeli([2_000_000_000, 1_500_000_000], 0, [],
                       teknoloji=True)[0],
     "tr-esikler.md: 'İstisna hedefin niteliğine bağlıdır' — yalnızca B ayağı")

# --- BURADAN İTİBARESİ: kitabın öz-sınamasının hiç bakmadığı yer ------------

# A-07: Kitabın KENDİ pilot vakası (§19). Alman alıcı, dünya cirosu 2,4 milyar
# AVRO. Eşik TL cinsindendir. Rakam çevrilmeden verilirse ne olur?
pilot_cevrilmemis = esik.bildirilmeli([], 1_400_000_000, [2_400_000_000])
vaka("A-07", "§19 pilotu: 2,4 milyar AVRO çevrilmeden verilirse",
     "bildirime tabi (B)", "bildirime tabi" if pilot_cevrilmemis[0]
     else "TABİ DEĞİL — sessiz yanlış cevap",
     "§19: 'avro rakamı TL'ye çevrilir'; kodda para birimi modeli yok")

# A-08: aynı pilot, çevrilmiş (1 EUR ~ 47 TL varsayımıyla)
pilot_cevrilmis = esik.bildirilmeli([], 1_400_000_000, [2_400_000_000 * 47])
vaka("A-08", "§19 pilotu: aynı olgular, TL'ye çevrilmiş",
     True, pilot_cevrilmis[0],
     "§19 'doğru cevap': B eşiği tespit edilir")

# A-09: Aynı işlemin verisi İKİ ayrı biçimde giriliyor ve hiçbir şey
# tutarlılığı kontrol etmiyor. Hedefin Türkiye cirosu tr_cirolar'a
# yazılmayı unutulursa A ayağı eksik hesaplanır.
# Gerçek: alıcı TR 2,5 milyar + hedef TR 1,4 milyar = 3,9 milyar -> A VAR.
dogru = esik.bildirilmeli([2_500_000_000, 1_400_000_000], 1_400_000_000, [])
unutulmus = esik.bildirilmeli([2_500_000_000], 1_400_000_000, [])
vaka("A-09", "hedef cirosu tr_cirolar'a yazılmazsa A ayağı kaybolur",
     dogru[0], unutulmus[0],
     "aynı işlem, iki bağlantısız girdi biçimi; tutarlılık kontrolü yok")

# A-10: Bilinmeyen ciro. Beceri §9 üç değerli cevap istiyor:
# evet / hayır / BELİRLENEMİYOR. Fonksiyon iki değerli.
bilinmeyen_sifir = esik.bildirilmeli([0, 0], 0, [])
vaka("A-10", "bilinmeyen ciro 0 olarak girilirse cevap ne olur",
     "belirlenemiyor", "hayır (%s)" % bilinmeyen_sifir[1],
     "skills/rekabet-esigi: 'evet / hayır / belirlenemiyor'")

# A-11: Bilinmeyeni None olarak vermek
try:
    esik.bildirilmeli([None], 0, [])
    n = "sessizce kabul"
except TypeError as e:
    n = "TypeError: %s" % str(e)[:40]
vaka("A-11", "bilinmeyen ciro None olarak verilirse",
     "belirlenemiyor sonucu ya da açık hata iletisi", n,
     "kanıt kuralı: bilinmeyen, sıfırdan farklıdır")

# A-12: Negatif ciro sessizce kabul ediliyor mu
try:
    _neg = "kabul edildi -> %s" % str(
        esik.bildirilmeli([-5_000_000_000, 9_000_000_000], 0, []))
except Exception as _e:
    _neg = "reddedilmeli"      # açık hata = doğru davranış
vaka("A-12", "negatif ciro reddediliyor mu",
     "reddedilmeli", _neg, "girdi doğrulaması")

# A-13: Devralan, kendi dünya cirosunu 'diğer taraflar' listesine koyarsa
# B ayağı kendi kendini karşılar. Şartname 'DİĞER işlem taraflarından'.
vaka("A-13", "hedef kendi dünya cirosuyla B ayağını karşılayabiliyor mu",
     "karşılayamamalı", "karşıladı" if esik.esik_b(
         1_200_000_000, [50_000_000_000]) else "karşılayamadı",
     "tr-esikler.md: 'DİĞER işlem taraflarından en az birinin' — koruma yok")

# A-14: Komut satırından gerçek bir işlem hesaplanabiliyor mu?
# §8 el kitabı, §9 becerisi ve §15.1 komutu 'gerçek ciro rakamlarıyla
# çalıştırılır' diyor.
p = subprocess.run([sys.executable, ESIK_PY,
                    "--tr", "2500000000", "--hedef", "1400000000"],
                   capture_output=True, text=True)
cli = p.stdout.strip().splitlines()[0][:60] if p.stdout.strip() else "(çıktı yok)"
vaka("A-14",
     "gerçek rakamlarla komut satırından hesap yapılabiliyor mu",
     "hesap çıktısı", cli,
     "§8: 'esik.py gerçek ciro rakamlarıyla çalıştırılır'")

# A-15: Birleşme (devralma değil) vakası. Şartname B ayağı için birleşmede
# 'taraflardan en az birinin' diyor; parametre adı 'hedef_tr'.
vaka("A-15", "birleşme vakası modelleniyor mu (devralma/birleşme ayrımı)",
     "ayrım var", "ayrım yok — tek 'hedef_tr' parametresi",
     "tr-esikler.md: 'birleşme işlemlerinde ise taraflardan en az birinin'")


# ===========================================================================
# İKİNCİ BÖLÜM — YAMALI API'YE KARŞI
# Yukarıdaki on beş vaka kitabın sistemini ölçer ve OLDUĞU GİBİ bırakılmıştır;
# hiçbiri yamaya uydurulmadı. Aşağıdakiler aynı kusurların kapanıp
# kapanmadığını yamalı API üzerinde ölçer.
# ===========================================================================

def y_vaka(kod, baslik, beklenen, gercek, sartname):
    vaka(kod, baslik, beklenen, gercek, sartname)


# A-07y: çevrilmemiş yabancı para SESSİZ bir cevap üretmemeli.
try:
    esik.tl(2_400_000_000, "EUR")
    _r = "sessizce kabul edildi"
except Exception as e:
    _r = "reddedildi: %s" % type(e).__name__
y_vaka("A-07y", "kursuz avro tutarı reddediliyor mu",
       "reddedildi: CiroHatasi", _r,
       "§19: 'avro rakamı TL'ye çevrilir ve hangi kurun kullanıldığı yazılır'")

# Kur verildi ama kaynağı verilmedi -> kanıt kuralı.
try:
    esik.tl(2_400_000_000, "EUR", kur=47)
    _r2 = "kaynaksız kur kabul edildi"
except Exception as e:
    _r2 = "reddedildi: %s" % type(e).__name__
y_vaka("A-07z", "kaynaksız kur reddediliyor mu",
       "reddedildi: CiroHatasi", _r2, "CLAUDE.md §1 kanıt kuralı")

# A-08y: §19 pilotu, tek modelden, doğru cevabı vermeli.
_p = esik.degerlendir([
    esik.Taraf("Alman alıcı",
               dunya_ciro=esik.tl(2_400_000_000, "EUR", 47, "TCMB 2026-08-27"),
               rol="devralan"),
    esik.Taraf("Türk hedef", tr_ciro=1_400_000_000, rol="hedef")])
y_vaka("A-08y", "§19 pilotu yamalı API'de", ("evet", "B eşiği (devre konu)"),
       (_p.sonuc, _p.ayak), "§19 'doğru cevap': B eşiği tespit edilir")

# A-09y: hedefin cirosu artık A ayağına ayrıca yazılmıyor — tek model.
_d = esik.degerlendir([
    esik.Taraf("Alıcı", tr_ciro=2_500_000_000, dunya_ciro=2_500_000_000,
               rol="devralan"),
    esik.Taraf("Hedef", tr_ciro=1_400_000_000, dunya_ciro=1_400_000_000,
               rol="hedef")])
y_vaka("A-09y", "A ayağı tek taraf listesinden türetiliyor mu",
       "evet", _d.sonuc,
       "aynı işlem tek bir modelden; unutulacak ikinci giriş biçimi yok")

# A-10y: bilinmeyen ciro 'hayır' değil 'belirlenemiyor'.
_b = esik.degerlendir([
    esik.Taraf("Alıcı", rol="devralan"), esik.Taraf("Hedef", rol="hedef")])
y_vaka("A-10y", "bilinmeyen ciro üç değerli cevap veriyor mu",
       "belirlenemiyor", _b.sonuc, "skills/rekabet-esigi: üç değerli cevap")

# A-11y / A-12y: None ve negatif artık açık hata.
try:
    esik.Taraf("X", tr_ciro=-1)
    _n = "negatif kabul edildi"
except Exception as e:
    _n = "reddedildi: %s" % type(e).__name__
y_vaka("A-12y", "negatif ciro reddediliyor mu", "reddedildi: CiroHatasi", _n,
       "girdi doğrulaması")

# A-13y: devre konu taraf kendi dünya cirosuyla B'yi karşılayamaz.
_k = esik.degerlendir([
    esik.Taraf("Alıcı", tr_ciro=1_000, dunya_ciro=1_000, rol="devralan"),
    esik.Taraf("Hedef", tr_ciro=1_200_000_000, dunya_ciro=50_000_000_000,
               rol="hedef")])
y_vaka("A-13y", "hedef kendi dünya cirosuyla B'yi karşılayamamalı",
       "hayır", _k.sonuc, "tr-esikler.md: 'DİĞER işlem taraflarından'")

# A-14y: komut satırından gerçek hesap.
_p2 = subprocess.run(
    [sys.executable, ESIK_PY,
     "--taraf", "Alman alıcı,dunya=2400000000EUR,rol=devralan",
     "--taraf", "Türk hedef,tr=1400000000,rol=hedef",
     "--kur", "EUR=47:TCMB 2026-08-27"],
    capture_output=True, text=True)
_ilk = _p2.stdout.strip().splitlines()[0] if _p2.stdout.strip() else "(çıktı yok)"
y_vaka("A-14y", "komut satırından gerçek işlem hesaplanıyor mu",
       "Bildirime tabi mi : EVET", _ilk,
       "§8: 'esik.py gerçek ciro rakamlarıyla çalıştırılır'")

# A-15y: birleşme ayrımı.
_m = esik.degerlendir([
    esik.Taraf("X", tr_ciro=1_200_000_000, dunya_ciro=1_200_000_000,
               rol="birlesen"),
    esik.Taraf("Y", tr_ciro=100_000_000, dunya_ciro=10_000_000_000,
               rol="birlesen")], islem_turu="birlesme")
y_vaka("A-15y", "birleşme işlemi modelleniyor mu", "evet", _m.sonuc,
       "tr-esikler.md: 'birleşme işlemlerinde ise taraflardan en az birinin'")



def rapor():
    print("=" * 78)
    print("KÖR SINAMA A — rekabet eşiği (şartnameden türetilmiş, koddan değil)")
    print("=" * 78)
    kaldi = 0
    for kod, baslik, gecti, bek, ger, sart in sonuclar:
        d = "GEÇTİ" if gecti else "KALDI"
        if not gecti:
            kaldi += 1
        print("%s  %-5s %s" % (d, kod, baslik))
        if not gecti:
            print("        beklenen : %s" % (bek,))
            print("        gerçek   : %s" % (ger,))
            print("        şartname : %s" % sart)
    print("-" * 78)
    print("%d vaka, %d geçti, %d KALDI" % (len(sonuclar),
                                           len(sonuclar) - kaldi, kaldi))
    return kaldi


if __name__ == "__main__":
    sys.exit(min(rapor(), 120))
