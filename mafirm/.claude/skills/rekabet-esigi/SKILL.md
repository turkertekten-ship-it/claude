---
name: rekabet-esigi
description: Bir işlemin Türkiye'de rekabet izni gerektirip gerektirmediği, eşiklerin aşılıp aşılmadığı, bildirim takviminin ne olduğu ya da tarafların kapanış yapıp yapamayacağı sorulduğunda kullan. 2010/4 sayılı Tebliğ'in 2026/2 ile değişik hâlini, teknoloji teşebbüsü istisnasını, bekletici etkiyi ve izinsiz kapanış cezasını kapsar. Türkiye dışındaki rekabet rejimleri için KULLANMA.
---

# Türkiye birleşme denetimi eşiği

## Bu soru asla hafızadan cevaplanmaz

Eşikler değişir. Kodu çalıştır:

    python3 birimler/rekabet/kod/esik.py --self-test

Sonra gerçek ciro rakamlarıyla işlemi hesapla. Hangi ayağın karşılandığını ve
hangi rakamları kullandığını yaz. Bir ciro rakamı tahminse bunu söyle ve cevabı
neyin değiştireceğini yaz.

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
