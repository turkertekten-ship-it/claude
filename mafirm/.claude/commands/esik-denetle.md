---
description: Sistemdeki her mevzuat eşiğini birincil kaynağından yeniden çeker; hangilerinin değiştiğini, hangilerinin bayatladığını ve hangi CANLI DOSYALARIN bayat bir rakama dayandığını bildirir.
---

<!-- [AM-01/AM-03 · otuzuncu birinci tur] Kitaba sadık sürüm
     yamalar/kitaba-sadik/esik-denetle.md dosyasındadır. Kitabın sürümü
     kapanışta "şu anda hangi dosyalar bayat bir rakama dayanıyor" diye
     bitiyor ve gerekçesinde riski kendi sözleriyle adlandırıyor: bir eşik
     değişikliği "canlı bir dosyada verilmiş bir görüşü geçersiz kılabilir".
     Ama prosedürünün birinci adımı yalnızca `birimler/*/yontem/` tarıyordu;
     §2'nin sözlüğünde canlı işleri tutan dizin `dosyalar/` ise hiç
     açılmıyordu. Vaadin kapsamı prosedürün kapsamından genişti.
     İkinci yol da kapalıydı: `dosyalar/` kural 6 gereği .gitignore'dadır
     (Y-02), yani sürüm geçmişinden de sorulamaz. "Eşik değişti, hangi
     müvekkile artık yanlış olan bir şey söyledik?" sorusunun iki cevap
     yolu vardı ve ikisi de kapalıydı. Tarama kapsamı genişletildi;
     "hiçbir dosyayı düzenleme" kuralı aynen korundu. -->

İki kapsamı da tara.

**A. Doktrin katmanı — `birimler/*/yontem/`**
"Doğrulama:" satırı taşıyan her dosya için:

1. Eşiği ve yazılı doğrulama tarihini oku.
2. Tarih altı aydan eskiyse BAYAT olarak işaretle.
3. Dosyada adı geçen birincil kaynağı çek.
4. Karşılaştır. Bildir: değişmemiş / değişmiş (iki rakamla) / doğrulanamadı.

**B. Canlı iş katmanı — `dosyalar/*/`**
Bir eşiğe, tebliğ sürümüne ya da doğrulama tarihine atıf yapan her çıktı için:

5. Dosyanın hangi eşiğe ve hangi tebliğ sürümüne dayandığını oku.
6. A'da o eşik DEĞİŞMİŞ çıktıysa, dosyayı **ETKİLENEN** olarak işaretle —
   verilmiş görüş artık başka bir rakama dayanıyor olabilir.
7. Dosya bir eşiğe dayandığı hâlde hangi sürüme dayandığını YAZMIYORSA,
   **SÜRÜMSÜZ** olarak işaretle. Sürümsüz bir görüş, değişiklikten
   etkilenip etkilenmediği söylenemeyen bir görüştür; bu da bir bulgudur.

Bir tablo yazdır. Hiçbir dosyayı düzenleme — bir eşik değişikliği insan
kararıdır, çünkü canlı bir dosyada verilmiş bir görüşü geçersiz kılabilir.

**Bu tablo makinede kalır.** Satırları müvekkil dosyalarının adlarını taşır;
işletim sözleşmesi kural 6 uyarınca dışarı giden hiçbir çağrıya konmaz.

Şununla bitir: kaç eşik kontrol edildi, kaçı bayat, kaç canlı dosya
ETKİLENEN, kaç canlı dosya SÜRÜMSÜZ — ve şu anda hangi dosyalar bayat bir
rakama dayanıyor.
