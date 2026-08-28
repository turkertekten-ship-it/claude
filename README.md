# Kör sınama · Uluslararası M&A Hukuku Kurulum Kitabı

Bu depo, "RePie Arel M&A Avukat Claude Kurulum Kitabı" (Sürüm 1.0,
27 Ağustos 2026) adlı kurulum kitabının **kelimesi kelimesine kurulmuş** hâlini
ve o kuruluma karşı yapılmış **kör sınamayı** içerir.

## Kör sınama nedir
Her sınama vakası kitabın **düzyazısından** türetildi, kodundan değil. Kitabın
kendi öz-sınamaları (esik.py'de 6 vaka, kapi.py'de 16) desenleri yazan kişinin
aklındaki vakalardır ve hepsi geçer. Kör sınama o aklın dışında kalanı arar.

## Sonuç
- Kitaba sadık, eksiksiz kurulum: **85 vaka, 56 başarısız.**
- Kitabın kendi **§19 kabul sınamasında** doğru cevap DA yanlış cevap DA
  bloklanıyor: kapı sistemi, §19'un "kurulumun tamamının sebebi" dediği farkı
  ifade edemiyor.
- Kitabın kendi §16 denetimi, kitap harfiyen izlendiğinde **yeşile dönmüyor.**
- Denetim, on beş bozmadan **on birini fark etmiyor** — sıfır beceri, kancasız
  ayarlar ve **tamamen boş bir `esik.py`** taşıyan bir sistemde "DENETİM OK".
- İşletim sözleşmesinin on bir kuralından **yedisinin** çalışan bir mekanizması
  yok; hiçbirinin tam mekanizması yok.
- Yamadan sonra: **132 vaka, 13 başarısız** — on üçü de ya kitabın davranışının
  bilerek bırakılmış kaydı ya da belgelenmiş bir öntanımlı boşluk. Mutasyon
  yakalama 4/15 → **15/15**.
- Kitapta hiç bulunmayan **altıncı kapı** eklendi: §7'nin koltuk sağlaması
  kuralı (sistemin en yüksek itibar riski) artık mekanizmayla uygulanıyor.

## Okuma sırası
1. `mafirm/RAPOR.md` — bulguların tamamı, kanıtlarıyla
2. `mafirm/KITAP-ERRATA.md` — **kitabın metni için** bölüm bölüm düzeltme
   listesi, 41 madde, ağırlık işaretli; **her maddesi çalışan bir sınama
   vakasına bağlı** ve bu bağ denetimde zorunlu tutuluyor
3. `mafirm/yamalar/DEGISIKLIKLER.md` — her yama, kapattığı vaka kimliğiyle
4. `mafirm/sinama/` — sınama takımları ve ham çıktılar
5. `mafirm/yamalar/kitaba-sadik/` — kitaba sadık özgün sürümler

## Koşum
```
cd mafirm && ./sinama/hepsi.sh   # on üç takım, 132 vaka
cd mafirm && ./denetim.sh --yapisal   # mühendislik katmanı  -> DENETİM OK
cd mafirm && ./denetim.sh            # mevzuat bulguları dâhil -> BAŞARISIZ: 3
```

Betikler kökü kendi konumundan çözer: klon kendi ağacını ölçer.

## Açık kalanlar
Üç mevzuat bulgusu (`mafirm/hafiza/dogrulama-bulgulari.md`) **bilerek
yamalanmadı**: bir eşik değişikliği insan kararıdır ve bu ortamda hiçbir
birincil kaynağa (mevzuat.gov.tr, resmigazete.gov.tr, rekabet.gov.tr,
spk.gov.tr) erişilemedi. İkisi bildirime tabilik sonucunu değiştirir.
