---
description: Bir SPA'yı pratiğin sabit sırasına göre yapılandırılmış olarak inceler ve bulguları maliyetine göre sıralar.
---

`$ARGUMENTS` dosyasını alıcı açısından incele (satıcı istenirse bunu söyle).

PDF ya da DOCX ise önce madde yapısını çıkar:
`python3 ~/mafirm/birimler/_araclar/kod/belge.py $ARGUMENTS --yapi`

Sabit sırayla ilerle ve bir madde yoksa "yok" yaz — olmayan bir madde bir
bulgudur:

1. Kapanış öncesi koşullar: neler, kim kontrol ediyor, saati ne.
2. Ara dönem taahhütleri: değer koruma mı fiilî kontrol mü? 4054 sayılı Kanun
   madde 11 bakımından izinsiz kapanış riski doğuranları işaretle.
3. Beyanlar: kapsam, sınırlayıcılar, bilgi ve önemlilik kayıtları.
4. Açıklama: veri odası genel açıklama sayılıyor mu? Alıcıya maliyeti ne?
5. Sınırlamalar: tavan, alt sınır, asgari tutar, beyan sınıfı başına süre.
6. Başvuru: emanet, W&I ya da satıcı taahhüdü. Gerçekte kim ödeyebilir?
7. Uygulanacak hukuk, tahkim yeri ve satıcının gerçek mal varlığına karşı
   tenfiz edilebilirlik.
8. SPA'nın bertaraf edemeyeceği Türk emredici kuralları.

Çıktı: tablo (madde | ne diyor | maliyeti | düzeltme), en kötü önce, en çok on
beş satır. Sonra müzakere sermayesini harcayacağın üç nokta.
Şununla bitir: Şimdi ne yapılmalı / Yetkili avukat görüşü gereken konular /
Kontrol edildi:
