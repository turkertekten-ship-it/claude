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
import glob
import os
import re
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
     "KISMİ*", "N-01..N-08",
     "B-07..B-09: CLAUDE.md'nin 'kariyer bitirir' dediği üç cümlenin üçü de "
     "hiçbir KAPIYI ateşlemiyor — pratiğin çıktısı bu kural bakımından "
     "korumasız. Mekanizma yalnızca BU RAPORUN olumsuz iddiaları için var: "
     "N takımı sekiz vakayla onları kanıta bağlıyor, denetim de her koşumda "
     "çalıştırıyor. Matris bunu önce 'YOK' diye yazıyordu; 9. ve 10. "
     "kurallarda aynı darlıktaki mekanizmalar KISMİ* sayıldığı hâlde. "
     "Dar bir mekanizmayı yok saymak, kapsamı olduğundan kötü gösterir; "
     "yok olanı var saymak ise daha kötüsünü yapar — ikisi de yazılıyor."),
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
     "KISMİ*", "K-13",
     "Hiçbir kapı bir İFADENİN hangi hukuk sisteminden geldiğini kontrol "
     "etmiyor — kuralın asıl ağırlığı burada ve orada mekanizma YOK. Ama "
     "kuralın koltuk ayağı sınanıyor: K-13 her dolu koltuğun 'konuşmadığı "
     "yer'i yazmasını istiyor, yani bir koltuk kendi hukuk sisteminin "
     "sınırını beyan etmek zorunda. Matris bunu 'YOK' diye yazıyordu; K-13 "
     "eklendikten sonra bayatlamıştı."),
    ("8",  "Çıkar çatışması kuralı",
     "KISMİ*", "denetim",
     "§2 hafiza/ klasörünü kuruyor ama cikar-catismasi.md dosyasını HİÇ "
     "oluşturmuyor. Bu kurulumda dosya kuruldu ve denetime bir kontrol "
     "eklendi; mutasyonla doğrulandı (dosya silinince DENETİM BAŞARISIZ). "
     "KAPI hâlâ yok ve kontrol dosyanın VARLIĞINI görür, dosya açılmadan "
     "önce çatışmanın gerçekten BAKILDIĞINI değil — mekanizma bu yüzden "
     "kısmi. Matris bunu 'YOK' diye yazmayı sürdürüyordu; not, kontrol "
     "eklendikten sonra bayatlamıştı."),
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
     "töreni eksiksiz ama RAKAMI yanlış bir cevap yedi kapıdan da geçiyor "
     "[J-09]. Kapılar biçimi denetler, muhakemeyi değil — ve §17.1'in kendi "
     "bulgusu tam olarak budur: kazanç açıklıkta, doğrulukta değil."),
]


# [AF-02] Kaybolan bir vaka, kırmızı bir vakadan kötüdür: kimse aramaz.
# Koruma on üçüncü turda eklendi ama yalnızca sonrasında yazılan takımlara.
BEKLENEN_VAKA = 2   # F-01 ve F-02; dogrula() içinde basılır
BEKLENEN_KURAL = 11   # işletim sözleşmesinin kural sayısı


def rapor():
    # F, diğer takımlar gibi bir `sonuclar` listesi TUTMAZ: matris KURALLAR
    # üzerinde yürür ve iki doğrulama vakasını dogrula() basar. Toplu geriye
    # doldurma bunu görmedi ve F'i çökertti — kör bir toplu düzenlemenin
    # bedeli. Koruma F'in KENDİ yapısına göre yazıldı.
    if len(KURALLAR) != BEKLENEN_KURAL:
        print("KALDI  F-00  matris beyan ettiği kural sayısını taşıyor")
        print("        beyan %d, bulunan %d" % (BEKLENEN_KURAL, len(KURALLAR)))

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
    return dogrula(sayim)


# --- Matrisin KENDİSİ sınanır -----------------------------------------
# Üç girdi arka arkaya BAYATLADI: 2, 8 ve 7 numaralı kurallar "YOK" yazıyordu
# ve üçünün de bir mekanizması vardı (sırasıyla N-01..N-08, denetim kontrolü,
# K-13). Sebep şu: "YOK" bir OLUMSUZ İDDİADIR ve CLAUDE.md §2 olumsuz iddiadan
# olumludan YÜKSEK kanıt ister. Matris bu iddiayı üç kez kanıtsız yazdı.
# El yazısı bir durum sütunu, ölçtüğü sistemden bağımsız yaşar. Artık
# yaşamıyor: her iddia burada makinece doğrulanıyor.
ANAHTAR = {
    "1": ("kanit",), "2": ("olumsuz",), "3": ("guncellik",),
    "4": ("yon", "başlık sırası"), "5": ("kapsam",), "6": ("sir", "gizli"),
    "7": ("iki hukuk", "konuşmadığı yer"), "8": ("catisma", "çatışma"),
    "9": ("onay",), "10": ("terim", "dil"), "11": ("arastirma", "Kontrol edildi"),
}


def _kaynaklar():
    parcalar = []
    for rel in [".claude/hooks/kapi.py", "denetim.sh"]:
        yol = os.path.join(_KOK_COZ, rel)
        if os.path.exists(yol):
            parcalar.append(open(yol, encoding="utf-8").read())
    for yol in glob.glob(os.path.join(_KOK_COZ, "sinama", "ks_*.py")) + \
            glob.glob(os.path.join(_KOK_COZ, "sinama", "ks_*.sh")):
        if os.path.basename(yol).startswith("ks_f_"):
            continue                      # matrisin kendi metni kanıt değildir
        parcalar.append(open(yol, encoding="utf-8").read())
    return "\n".join(parcalar)


def dogrula(sayim):
    kaynak = _kaynaklar()
    sinyal = 0

    # F-01 · mekanizma ADI GEÇEN her kural için o ad gerçekten çözülüyor mu
    cozulmeyen = []
    for no, ad, durum, kapi, _k in KURALLAR:
        if durum == "YOK" or kapi == "-":
            continue
        adlar = [x.strip() for x in re.split(r"[/,]| ve ", kapi) if x.strip()]
        for a in adlar:
            if a.startswith(("R-", "N-", "K-", "B-", "C-", "U-")):
                kok = a.split("..")[0]
                if kok not in kaynak:
                    cozulmeyen.append("%s -> %s" % (no, a))
            elif a == "denetim":
                if "kontrol " not in kaynak:
                    cozulmeyen.append("%s -> denetim" % no)
            elif ("kapi_" + a) not in kaynak:
                cozulmeyen.append("%s -> kapi_%s" % (no, a))
    if cozulmeyen:
        sinyal += 1
    print("%s %-5s matriste adı geçen her mekanizma gerçekten var"
          % ("KALDI" if cozulmeyen else "GEÇTİ", "F-01"))
    print("        %s" % ("çözülmeyen: " + ", ".join(cozulmeyen) if cozulmeyen
                          else "%d kuralın mekanizma atfı çözüldü"
                               % (11 - sayim["YOK"])))

    # F-02 · "YOK" bir olumsuz iddiadır (§2): kanıt, aramanın BOŞ dönmesidir
    yanlis_yok = []
    for no, ad, durum, _kapi, _k in KURALLAR:
        if durum != "YOK":
            continue
        bulunan = [a for a in ANAHTAR.get(no, ()) if a.lower() in kaynak.lower()]
        if bulunan:
            yanlis_yok.append("%s (%s bulundu)" % (no, ", ".join(bulunan)))
    if yanlis_yok:
        sinyal += 1
    print("%s %-5s 'YOK' diyen her kural gerçekten mekanizmasız (§2)"
          % ("KALDI" if yanlis_yok else "GEÇTİ", "F-02"))
    if yanlis_yok:
        print("        KANITSIZ OLUMSUZ İDDİA: %s" % "; ".join(yanlis_yok))
    elif sayim["YOK"] == 0:
        print("        'YOK' diyen kural kalmadı — iddia edilecek olumsuz "
              "yok. (Üç tur önce üç taneydi ve üçü de yanlıştı.)")
    else:
        print("        %d 'YOK' iddiasının hiçbiri için mekanizma bulunamadı"
              % sayim["YOK"])

    print("-" * 96)
    print("2 vaka · %d geçti · %d SİNYAL" % (2 - sinyal, sinyal))
    return sinyal


if __name__ == "__main__":
    sys.exit(min(rapor(), 120))
