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
             d['stargazers_count'], d['pushed_at'][:10])"

   Dört alanı oku: çözülüyor mu, lisansı ne, kaç yıldız, en son ne zaman
   güncellenmiş. İki yıldır güncellenmemiş bir depo bir bağımlılık değil, bir
   okuma kaynağıdır.
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
