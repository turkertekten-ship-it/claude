---
name: spa-inceleme
description: Önüne bir SPA (pay alım satım sözleşmesi), pay devri sözleşmesi, varlık devri sözleşmesi ya da bunların bir taslağı veya tur değişikliği konduğunda kullan. Sözleşmeyi alıcı ya da satıcı açısından, pratiğin sabit sırasıyla inceler ve bulguları maliyetine göre sıralar. Sözleşme özeti istendiğinde DEĞİL, risk incelemesi istendiğinde kullan.
---

# SPA incelemesi

İşin, on sekiz ay sonra müvekkile zarar verecek olanı bulmaktır; belgeyi
özetlemek değil.

## Sıra sabittir — bir madde yoksa "yok" yaz

Olmayan bir madde bir bulgudur.

1. **Kapanış öncesi koşullar**: neler, her birini kim kontrol ediyor, saati ne.
2. **Ara dönem taahhütleri**: değer koruma mı fiilî kontrol mü? 4054 sayılı
   Kanun madde 11 bakımından izinsiz kapanış riski doğuranları işaretle.
3. **Beyanlar**: kapsam, sınırlayıcılar, bilgi ve önemlilik kayıtları.
4. **Açıklama**: veri odasının genel açıklama sayılması kabul edilmiş mi?
   Alıcıya maliyeti ne?
5. **Sınırlamalar**: tavan, alt sınır, asgari tutar, beyan sınıfı başına süre.
6. **Başvuru**: emanet, W&I ya da satıcı taahhüdü. Gerçekte kim ödeyebilir?
7. **Uygulanacak hukuk, tahkim yeri** ve satıcının gerçek mal varlığına karşı
   tenfiz edilebilirlik.
8. **SPA'nın bertaraf edemeyeceği Türk emredici kuralları**: devir şekil şartı,
   rekabet izni, işçi devri.

## Araç

Uzun bir belgede iki sürüm karşılaştırılacaksa göz değil kod:

    python3 ~/mafirm/birimler/_araclar/kod/karsilastir.py <eski> <yeni>

PDF ise önce madde yapısını çıkar:

    python3 ~/mafirm/birimler/_araclar/kod/belge.py <dosya> --yapi

## Çıktı

Tablo: madde numarası | ne diyor | maliyeti | düzeltme. En kötü önce, en çok
on beş satır; daha fazlası varsa kaçını hangi ölçütle bıraktığını söyle.
Sonra: müzakere sermayesini harcayacağım üç nokta ve neden o üçü.
Şununla bitir: Şimdi ne yapılmalı / Yetkili avukat görüşü gereken konular /
Kontrol edildi:
