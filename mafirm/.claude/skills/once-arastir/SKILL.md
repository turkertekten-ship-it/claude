---
name: once-arastir
description: Bir eşik, harç, süre, düzenleyici gerekliliği, piyasa uygulaması ya da bir aracın var olup bakımının yapılıp yapılmadığı içeren HER soruya cevap vermeden ÖNCE kullan. Önce web, sonra GitHub, sonra yerel kaynaklar sırasıyla çalışır ve cevabı "Kontrol edildi" satırıyla döndürür. Bu tür soruları hafızadan cevaplama. Yalnızca yerel dosyalardan cevaplanabilecek sorular için KULLANMA.
---

# Önce araştır, sonra cevap ver

## Sıra

1. **Web.** Özetini değil birincil kaynağı. Türk eşikleri için Resmî Gazete
   metni ya da düzenleyicinin kendi sayfası. Çekilen tarihi kaydet.
2. **GitHub, API üzerinden.** Asla hafızadan:

       curl -s "https://api.github.com/repos/<sahip>/<depo>" | python3 -c "
       import json,sys; d=json.load(sys.stdin)
       print(d['full_name'], (d.get('license') or {}).get('spdx_id'),
             d['stargazers_count'], d['pushed_at'][:10], d['archived'])"

   **Beş** alanı oku: çözülüyor mu, kod lisansı ne, kaç yıldız, en son ne
   zaman güncellenmiş, ve **arşivlenmiş mi**. İki yıldır güncellenmemiş bir
   depo bir bağımlılık değil, bir okuma kaynağıdır.

   `archived` alanı ayrıca okunur çünkü `pushed_at` bir VEKİLDİR, olgu
   değil: salt okunur bir depo hata düzeltmesi de güvenlik yaması da almaz
   ve bu, "kullan" kararını doğrudan değiştirir. (§13.4'ün `diff-match-patch`
   için yazdığı "eskime burada bozulma değildir" gerekçesi, deponun
   5 Ağustos 2024'te arşivlendiği bilinmeden yazılmıştır.)

2b. **Veri lisansı, kod lisansından ayrı sorulur.** API'nin `license` alanı
   yalnızca deponun beyan ettiği KOD lisansını döndürür. Veri yayımlayan bir
   depoda README ve `LICENSE` dosyaları ayrıca okunur: `opensanctions`
   kodu MIT iken **verisi CC BY-NC 4.0'dır ve ticari kullanıma kapalıdır.**
   Ticari bir pratikte bu bir soru değil, bir sınırdır.
3. **Yerel.** `birimler/*/yontem/`, `emsal/`, `hafiza/`.

## Cevabın taşıması gereken

    Kontrol edildi: <kaynak> (<tarih>) · <kaynak> (<tarih>) · bulunamayan: <ne>

## Arama başarısız olursa

Bunu cevabın içinde, o bilgiye ihtiyaç duyan cümlede söyle. Gövdede "eşik
doğrulanamadı" yazmak, arkasında hiçbir şey olmayan kendinden emin bir
rakamdan da, cümleyi sessizce silmekten de iyidir.

## İki tuzak

- Kayıt adı depo adı olmayabilir. Çöz.
- Boş bir GitHub araması yokluğun kanıtı değildir. Kayıtlara bak.
