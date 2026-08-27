---
name: rekabet-esigi
description: Bir işlemin Türkiye'de rekabet izni gerektirip gerektirmediği, eşiklerin aşılıp aşılmadığı, bildirim takviminin ne olduğu ya da tarafların kapanış yapıp yapamayacağı sorulduğunda kullan. 2010/4 sayılı Tebliğ'in 2026/2 ile değişik hâlini, teknoloji teşebbüsü istisnasını, bekletici etkiyi ve izinsiz kapanış cezasını kapsar. Türkiye dışındaki rekabet rejimleri için KULLANMA.
---

# Türkiye birleşme denetimi eşiği

## Bu soru asla hafızadan cevaplanmaz

Eşikler değişir. Kodu çalıştır:

    python3 ~/mafirm/birimler/rekabet/kod/esik.py --self-test

Sonra gerçek ciro rakamlarıyla işlemi hesapla. Hangi ayağın karşılandığını ve
hangi rakamları kullandığını yaz. Bir ciro rakamı tahminse bunu söyle ve cevabı
neyin değiştireceğini yaz.

## Teknoloji istisnasında üç olgu önce tespit edilir

`yontem/tr-esikler.md` bu üçünü kitaptan ayrı olarak doğruladı:
1. Teşebbüs Türkiye'de **yerleşik** mi? Değilse istisna yoktur.
2. İşlem **devralma** mı **birleşme** mi? Devralmada devralınan taraf,
   birleşmede taraflardan herhangi biri yerleşik teknoloji teşebbüsü olmalıdır.
3. 250.000.000 TL testi teşebbüsün **teknoloji alanı cirosuyla** yapılır, toplam
   cirosuyla değil.

## Cevabın biçimi

1. Bildirime tabi mi: evet / hayır / belirlenemiyor ve hangi ayak.
2. Dayanılan rakamlar, her biri nereden geldiğiyle.
3. Kullanılan eşiklerin doğrulama tarihi.
4. Her iki yönde yanılırsan ne olur.
5. Şimdi ne yapılmalı / Yetkili avukat görüşü gereken konular.

## Tuzak

Bekletici. İmza serbest, izinden önce kapanış değil; ceza işlem değeri
üzerinden değil grup cirosu üzerinden hesaplanır. Kendi ülkesinde gönüllü rejim
olan bir alıcı, açıkça söylenmedikçe aksini varsayar.

Olumsuz cevap daha yüksek kanıt ister (işletim sözleşmesi §2): "bildirim
gerekmez" cümlesi, hangi hükmün aranıp bulunamadığını göstererek yazılır.

## Bu becerinin kendi araştırma kaydı

Kontrol edildi: `birimler/rekabet/yontem/tr-esikler.md` (2026-08-27) ·
2026/2 sayılı Tebliğ üzerine yayımlanmış uygulamacı çözümlemeleri (2026-08-27) ·
bulunamayan: Resmî Gazete ve rekabet.gov.tr birincil metni — ağ çıkışı engelli.
