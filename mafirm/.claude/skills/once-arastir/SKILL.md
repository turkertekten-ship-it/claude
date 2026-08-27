---
name: once-arastir
description: Bir eşik, harç, süre, düzenleyici gerekliliği, piyasa uygulaması ya da bir aracın var olup bakımının yapılıp yapılmadığı içeren HER soruya cevap vermeden ÖNCE kullan. Önce web, sonra GitHub, sonra yerel kaynaklar sırasıyla çalışır ve cevabı "Kontrol edildi" satırıyla döndürür. Bu tür soruları hafızadan cevaplama.
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

   **API kapalıysa** (bu makinede kapalı olabilir) yokluğa düşme, yolu değiştir:

       git ls-remote --heads https://github.com/<sahip>/<depo>   # çözülüyor mu
       git clone --depth 1 --filter=blob:none --no-checkout https://github.com/<sahip>/<depo> x
       git -C x log -1 --format=%cI                              # son commit
       curl -s https://pypi.org/pypi/<paket>/json                # sürüm, lisans
       curl -s https://registry.npmjs.org/<paket>                # sürüm, lisans

   Yıldız sayısı bu yolla çözülmez. O zaman yıldız **yazılmaz** — kitaptan ya da
   hafızadan kopyalanmaz.

3. **Yerel.** `birimler/*/yontem/`, `birimler/_araclar/katalog.md`, `emsal/`,
   `hafiza/`.

## Cevabın taşıması gereken

    Kontrol edildi: <kaynak> (<tarih>) · <kaynak> (<tarih>) · bulunamayan: <ne>

"Bulunamayan" zorunlu bir alandır. Boş dönen bir arama bir bulgudur.

## Arama başarısız olursa

Bunu cevabın içinde, o bilgiye ihtiyaç duyan cümlede söyle. Gövdede "eşik
doğrulanamadı" yazmak, arkasında hiçbir şey olmayan kendinden emin bir
rakamdan da, cümleyi sessizce silmekten de iyidir.

## İki tuzak

- **Kayıt adı depo adı olmayabilir. Çöz.** Bu kurulumda canlı bir örnek çıktı:
  PyPI'da `repomix` adında bir paket var ve GitHub bağlantısı yok; gerçek
  repomix npm paketidir (`yamadashy/repomix`).
- **Boş bir GitHub araması yokluğun kanıtı değildir.** Kayıtlara bak.
