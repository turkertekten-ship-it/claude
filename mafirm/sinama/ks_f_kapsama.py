#!/usr/bin/env python3
"""KÖR SINAMA F — DOKTRİN KAPSAMA MATRİSİ.

§12'nin kendi savı şu: "Yukarıdaki her şey doktrindir ve doktrin, sistemin
baskı altında OLMADIĞI zaman uyduğu şeydir. Aşağıdaki dört otomatik kontrol,
baskı altında uyduğu şeydir."

O hâlde ölçülebilir soru şu: işletim sözleşmesinin ON BİR kuralından kaçı
gerçekten baskı altında uygulanıyor? Bu takım her kuralı, onu uygulayan bir
mekanizma olup olmadığına göre sınıflandırır ve iddiayı sınar.

Sınıflar:
  MEKANİZMA  — 2 çıkış koduyla bloklayan çalışan bir kapı var
  KISMİ      — kapı var ama kör sınama B'de kanıtlanmış boşlukları var
  YOK        — hiçbir otomatik kontrol bu kuralı görmüyor
"""
import os
import sys
# Kök dizin, betiğin KENDİ konumundan çözülür; sabit ~/mafirm değil.
# [Kör sınamanın kendi bulgusu] Betikler ~/mafirm'i sabitlediği sürece bir
# klon KENDİ ağacını değil, makinedeki kurulumu ölçer: klondaki kapi.py
# tamamen boşaltıldığında klonun denetimi hâlâ "DENETİM OK" diyordu. Bu, D
# takımının kitapta bulduğu kusurun aynısıdır — iddia ettiği şeye bakmayan
# bir kontrol. MAFIRM ortam değişkeniyle geçersiz kılınabilir.
_KOK_COZ = os.environ.get("MAFIRM") or os.path.dirname(
    os.path.dirname(os.path.abspath(__file__)))


KURALLAR = [
    ("1",  "Kanıt kuralı",
     "KISMİ", "kanit",
     "B-13..B-18: 1M altı rakam, sözle yazılmış rakam, TRY, oran biçimi "
     "görünmüyor; DAYANAK belge düzeyinde ve 'Tebliğ' kelimesiyle tatmin oluyor"),
    ("2",  "Olumsuz iddia kuralı",
     "YOK", "-",
     "B-07..B-09: CLAUDE.md'nin 'kariyer bitirir' dediği üç cümlenin üçü de "
     "hiçbir kapıyı ateşlemiyor"),
    ("3",  "Güncellik kuralı",
     "KISMİ", "guncellik",
     "B-21..B-23: Türkçe tarih biçimi, tarihsiz eşik ve gelecek tarihli "
     "doğrulama görünmüyor"),
    ("4",  "Yön kuralı (önce cevap)",
     "MEKANİZMA*", "R-01/R-02",
     "KİTAPTA YOKTU: 'biçim kuralı, kapı konusu değil' diye geçilmişti. Oysa "
     "başlık sırası makinece görülebilir: R-01 ilk bölümün cevap olmasını, "
     "R-02 yöntemin bulgulardan sonra gelmesini denetliyor. Rapor dokuz tur "
     "boyunca bu kuralı çiğnedi ve hiçbir şey söylemedi."),
    ("5",  "Kapsam kuralı (avukat başlığı)",
     "KISMİ", "kapsam",
     "B-02..B-06: sekiz sabit ifade dışındaki her tavsiye kipi geçiyor; "
     "B-10: Türkçe büyük harf başlığı YANLIŞ POZİTİF üretiyor"),
    ("6",  "Sır saklama kuralı",
     "KISMİ", "sir",
     "C-05..C-07 + C-09: Bash ne kapının disari kümesinde ne de kancanın "
     "matcher'ında; B-25..B-29: büyük harf kod adı, İngilizce kod adı, "
     "kısaltmasız unvan, gerçek kişi adı, fiyat görünmüyor"),
    ("7",  "İki hukuk kuralı",
     "YOK", "-",
     "hiçbir kapı bir ifadenin hangi hukuk sisteminden geldiğini kontrol etmiyor"),
    ("8",  "Çıkar çatışması kuralı",
     "YOK", "-",
     "§2 hafiza/ klasörünü kuruyor ama cikar-catismasi.md dosyasını HİÇ "
     "oluşturmuyor; D mutasyonu: dosyanın yokluğu denetimden geçiyor"),
    ("9",  "İnsan onayı",
     "KISMİ*", "R-04/R-05",
     "Onayın kendisi izlenemez ama ONAY DURUMUNUN BEYANI izlenebilir: R-04 "
     "raporun onaysız olduğunu yazmasını, R-05 bunu ilk bölümde yazmasını "
     "istiyor. Sessizlik onaylanmış gibi okunur."),
    ("10", "Dil kuralı",
     "KISMİ*", "R-06",
     "'İlk geçtiklerinde açıklanır' şartı makinece kontrol edilebilir: R-06 "
     "tanımlı terim listesinde ilk geçişin yakınında bir açıklama arıyor."),
    ("11", "Önce araştır, sonra cevap ver",
     "BOZUK", "arastirma",
     "C-01..C-03, C-10: üretim yolunda json.dumps satır sonlarını kaçırdığı "
     "için ^Kontrol edildi: ASLA eşleşmiyor — kapı doğru işi bloklamaktan "
     "başka bir şey yapamıyor"),
]

EK = [
    ("§7 koltuk sağlaması",
     "MEKANİZMA*",
     "KİTAPTA YOKTU: 'bir koltuk o hukukçunun gerçekten yazdığına dayanır' "
     "kuralı sistemin en yüksek itibar riskiydi ve hiçbir kapı bakmıyordu "
     "[K-14]. Altıncı kapı eklendi: beyansız bir koltuk dosyası bloklanıyor, "
     "yöntem dosyaları etkilenmiyor [K-15]. Denetim de kontrol ediyor."),
    ("§18 kapsam sınırları",
     "YOK",
     "dokuz açık sınır sayılıyor; hiçbiri makinece kontrol edilmiyor"),
    ("kapıların yapısal sınırı",
     "SINIR",
     "töreni eksiksiz ama RAKAMI yanlış bir cevap altı kapıdan da geçiyor "
     "[J-09]. Kapılar biçimi denetler, muhakemeyi değil — ve §17.1'in kendi "
     "bulgusu tam olarak budur: kazanç açıklıkta, doğrulukta değil."),
]


def rapor():
    print("=" * 96)
    print("KÖR SINAMA F — doktrin kapsama matrisi")
    print("=" * 96)
    print("%-4s %-32s %-10s %s" % ("no", "kural", "durum", "kapı"))
    print("-" * 96)
    sayim = {"MEKANİZMA": 0, "MEKANİZMA*": 0, "KISMİ": 0,
             "KISMİ*": 0, "YOK": 0, "BOZUK": 0}
    for no, ad, durum, kapi, kanit in KURALLAR:
        sayim[durum] += 1
        print("%-4s %-32s %-10s %s" % (no, ad, durum, kapi))
        print("     %s" % kanit)
    print("-" * 96)
    for ad, durum, kanit in EK:
        print("  +  %-32s %-10s" % (ad, durum))
        print("     %s" % kanit)
    print("=" * 96)
    print("On bir kuraldan:")
    print("  tam mekanizmalı : %d  (%d'ü bu raporun eklediği)"
          % (sayim["MEKANİZMA"] + sayim["MEKANİZMA*"], sayim["MEKANİZMA*"]))
    print("  kısmi           : %d  (kanıtlanmış boşluklarla; %d'i bu raporun)"
          % (sayim["KISMİ"] + sayim["KISMİ*"], sayim["KISMİ*"]))
    print("  bozuk           : %d  (üretimde çalışmıyor)" % sayim["BOZUK"])
    print("  hiç kapsanmayan : %d" % sayim["YOK"])
    print()
    yoksun = sayim["YOK"] + sayim["BOZUK"]
    print("§12'nin iddiası: 'doktrin baskı altında uyulmayan şeydir; kapılar")
    print("uyulan şeydir.' Ölçüm: on bir kuralın %d tanesi baskı altında" % yoksun)
    print("çalışan bir mekanizmaya sahip DEĞİL; kalan %d tanesi kısmi."
          % sayim["KISMİ"])
    return sayim["YOK"] + sayim["BOZUK"]


if __name__ == "__main__":
    rapor()
    sys.exit(0)
