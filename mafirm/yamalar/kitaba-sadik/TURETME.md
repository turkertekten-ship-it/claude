# Kitaba sadık kopyaların türetme kaydı

> **Doğrulama: 2026-08-28 · Bozulma sınıfı: KİTAP SÜRÜMÜNE BAĞLI**

Bu klasördeki dosyalar "kitaba sadık" diye anılıyor ve raporun bütün
**önce/sonra** karşılaştırması onlara dayanıyor. Kırk dördüncü tura kadar
hiçbir şey onların gerçekten kitaba sadık olduğunu sınamıyordu: AG-01..05
dosyaların *var olduğunu*, canlı sürümden *farklı* olduğunu ve kitabın
bilinen kusurlarını *taşıdığını* ölçüyor — ama hiçbiri **kitabın metniyle**
karşılaştırmıyordu.

Karşılaştırıldı: **262 esaslı satırın 258'i** kitapta birebir bulundu.
Kalan dördü aşağıda beyan edilmiştir.

## Neden dört satır kitapta birebir yok

§12 `denetle()` fonksiyonunu **dört** kapıyla basıyor. §14 beşinci kapıyı
(`kapi_arastirma`) veriyor ve şöyle diyor:

> *"denetle() içine diğer dördün yanına eklenir ve _selftest şu yedi
> vakayla genişletilir — üçü ateşlemeli, dördü susmalı"*

Yani kitap **sonucu basmıyor, talimatı veriyor.** Beş kapılı `denetle()`
metnini kitaptan kopyalamak mümkün değildir; talimatı uygulayarak yazmak
gerekir. Aşağıdaki dört satır bu yüzden **kitabın talimatıyla türetilmiştir**
— uydurma değil, ama kitabın harfi de değil. Ayrımı yazmak zorundayız:
kırk birinci turda kendi yamamı kitabın metni sanıp kitaba kredi vermiştim.

## Beyan

| dosya | satır | metin | dayanak |
|---|---|---|---|
| `kapi.py` | 9 | `arastirma   araştırılmadan anılan bir eşik rakamı ya da depo` | §14'ün beşinci kapıyı belge başlığına eklemesi |
| `kapi.py` | 112 | `"""Beş kapının hepsi. (kapı, ileti) listesi döner."""` | §14: "diğer dördün yanına eklenir" — dört → beş |
| `kapi.py` | 114 | `kapi_sir(metin, disari), kapi_guncellik(metin, bugun),` | aynı çağrı listesinin §14 sonrası hâli |
| `kapi.py` | 115 | `kapi_arastirma(metin))` | §14'ün eklenmesini istediği çağrı |

Başka hiçbir satır türetilmemiştir. Bir satır bu listede yoksa kitapta
birebir bulunmak zorundadır; AZ-01 bunu her koşumda sınar. Liste bir kaçış
deliği de olamaz: beyan edilen bir satır kitapta **geçiyorsa** gereksiz
beyan sayılır ve AZ-03 kırmızı verir.
