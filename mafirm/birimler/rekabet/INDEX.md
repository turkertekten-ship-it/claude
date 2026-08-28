# rekabet · Birleşme denetimi ve çok ülkeli bildirim stratejisi

## Buraya ne yönlenir
"Bu işlem Türkiye'de izin gerektirir mi", "ne zaman kapatabiliriz", "kaç
ülkede bildirim var" sorularının tamamı.

## Hangi yöntem dosyasına gider
| Soru | Dosya ya da kod |
|---|---|
| Eşik aşılıyor mu | `kod/esik.py` — hafızadan değil, çalıştırarak |
| Eşiklerin dayanağı ve doğrulama tarihi | `yontem/tr-esikler.md` |
| İzinden önce ne yapılamaz | `yontem/tr-esikler.md` § Bekletici etki |
| İzinsiz kapanışın cezası | `yontem/tr-esikler.md` § Yaptırım |

## Neden ayrı birim
Bekletici kapıdır. 4054 sayılı Kanun madde 10 ve 2010/4 sayılı Tebliğ madde 10 uyarınca bildirime tabi bir
işlem, Kurul kararı olmadan hukuken geçerlilik kazanmaz. Gönüllü bildirim
rejiminden gelen bir alıcının sezgisi burada yanlıştır ve yanlışlığın bedeli
işlemin kendisidir.

## Katı kural
Eşik sorusu asla hafızadan cevaplanmaz. Önce `kod/esik.py --self-test`, sonra
gerçek rakamlarla hesap, sonra kullanılan eşiklerin doğrulama tarihi.
