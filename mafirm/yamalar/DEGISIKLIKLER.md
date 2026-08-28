# Yamalar — her değişiklik, kapattığı kör sınama vakasıyla

Kitaba sadık sürümler `yamalar/kitaba-sadik/` altındadır. Karşılaştırma
denetlenebilir olsun diye hiçbiri silinmedi.

> **Bu söz bir süre DOĞRU DEĞİLDİ.** Yirmi beşinci turda AG takımı iki
> eksik buldu: `.gitignore` (§2, on yedinci turda kural 6 için değiştirildi)
> ve `birimler/rekabet/yontem/tr-esikler.md` (§5, DOĞRULANAMADI işaretleri
> konuldu). İkisinin de özgünü **kitabın kendi metninden yeniden kuruldu** ve
> `kitaba-sadik/` altına konuldu. `.gitignore` özgünü, kendini yoksaymaması
> için `gitignore` adıyla saklanıyor. Söz artık AG-01 ve AG-02 ile her
> koşumda kontrol ediliyor — çünkü kontrol edilmeyen bir söz, verilmemiş bir
> sözdür.

Kural: **mevzuat rakamlarına ve madde numaralarına DOKUNULMADI.** Bir eşik
değişikliği insan kararıdır (§11, `/esik-denetle`) ve mevzuat bulguları yalnızca
ikincil kaynakla desteklendi. Onlar `hafiza/dogrulama-bulgulari.md` içinde açık
bırakıldı; `denetim.sh` her koşuda sesli olarak bildirir ve ENGELLEYİCİ olanlar
denetimi kırmızıda tutar.

## kapi.py — beş kapı

| # | Kapatılan | Değişiklik |
|---|---|---|
| 1 | **C-01, C-02, C-03, C-10** | Üretim yolu. `json.dumps(tool_input)` gerçek satır sonlarını iki karakterlik `\n` dizisine çeviriyordu; `re.M` ile `^Kontrol edildi:` üretimde ASLA eşleşmiyordu. Artık `tool_input` içindeki dize değerleri toplanıp GERÇEK satır sonuyla birleştiriliyor. Öz-sınama yolu ile üretim yolu aynı metni görüyor. |
| 2 | **B-10** | Türkçe küçük harf. `"YETKİLİ".lower()` Python'da `"yetki̇li̇"` verir (`İ` → `i`+U+0307) ve avukat başlığı büyük harfle yazıldığında kapı onu göremiyordu — yani DOĞRU çıktıyı blokluyordu. `tr_kucult()` eklendi. |
| 3 | **B-02..B-06** | Tavsiye kalıpları. Sekiz sabit ifade, kip ve ek tabanlı desenlerle değiştirildi: `-manız gerek`, `-malısınız`, `tabidir`, `zorunludur`, `şarttır`, `gereklidir`. |
| 4 | **B-07..B-09** | **Olumsuz iddia kapısı — kitapta hiç yoktu.** CLAUDE.md §2'nin "kariyer bitirir" dediği cümleler (`gerekmez`, `tabi değil`, `yükümlülük yoktur`, `muaftır`) artık avukat başlığı olmadan geçemiyor. |
| 5 | **B-17, B-18, C-01** | Kanıt kapısı belge düzeyinden İDDİA düzeyine indi: dayanak rakamın ±300 karakterinde olmalı. Ama hukuk metni paragraf paragraf atıf vermez — bir `Dayanak:` beyanı kendinden sonrasını yönetir; o yüzden ikinci yol olarak açık `Dayanak:` beyanı kabul ediliyor. İkisi birden olmadan yalnızca "Tebliğ" kelimesinin geçmesi artık yetmiyor. |
| 6 | **B-13..B-16** | Eşik deseni: `{2,}` → `{1,}` (250.000 TL gibi bir milyon altı rakamlar), sözle yazılmış rakam (`3 milyar TL`), `TRY` ve `lira`, oran biçimleri (`binde bir`, `yüzde 98`, `%5`). |
| 7 | **B-21, B-22, B-23** | Güncellik: Türkçe tarih biçimi (`01.01.2020`), **tarihi hiç olmayan eşik** ve gelecek tarihli doğrulama artık yakalanıyor. |
| 8 | **B-25..B-27, B-29, C-05, C-06** | Sır kalıpları: büyük harfli kod adı, İngilizce `Project`, kısaltmasız unvan (`... Anonim Şirketi`), işlem bedeli. Ayırıcı sınıfı `+`, `%20`, `_`, `-` içeriyor — URL kodlaması desenleri atlatıyordu. |
| 9 | **B-28 / B-34** | Gerçek kişi adı desenle yakalanamaz. `hafiza/muvekkil-adlari.txt` KAYDI eklendi. Kayıt boşken bu ayak KAPSANMIYOR ve `denetim.sh` bunu her koşuda söylüyor — saklamıyor. |
| 10 | **C-05, C-06, C-07, C-09** | **Bash.** Dışarı giden en geniş kanaldı ve ne kapının `disari` kümesinde ne de `settings.json` matcher'ındaydı: `curl`, `git push`, `gh`, `pip install` hiç görülmüyordu. Kapı artık Bash komutunu inceliyor, matcher Bash'i (ve MultiEdit, NotebookEdit) kapsıyor. |
| 11 | **C-08** | Ayrıştırılamayan olay artık KAPALI yönde başarısız oluyor. Araç adı okunamadığında çağrının dışarı gidip gitmediği bilinemez; sır kuralı bilinmeyen bir kanalda veri göndermeyi kabul edemez. |

## esik.py — rekabet eşiği

| # | Kapatılan | Değişiklik |
|---|---|---|
| 12 | **A-07** | **Para birimi modeli.** `tl(tutar, birim, kur, kaynak)`. Çevrilmemiş avro reddediliyor; kur verilip kaynağı verilmezse de reddediliyor (kanıt kuralı). Kitabın §19 pilotu bu kusur yüzünden SESSİZCE "bildirime tabi değil" veriyordu. |
| 13 | **A-09** | `Taraf` sınıfı ve tek taraf listesi. A ve B ayakları AYNI veriden türüyor; unutulacak ikinci giriş biçimi yok. Türkiye cirosu dünya cirosunu aşarsa hata. |
| 14 | **A-10, A-11** | Üç değerli cevap: evet / hayır / **belirlenemiyor**. Bilinmeyen `None`'dır, `0` değildir. Bilinen rakamlar bir ayağı karşılıyorsa cevap "evet"tir; karşılamıyor ama bilinmeyen varsa "belirlenemiyor"dur — CLAUDE.md §2 gereği "hayır" YAZILMAZ. |
| 15 | **A-12** | Negatif ciro, bool, dize reddediliyor. |
| 16 | **A-13** | B ayağında "diğer taraflar" devre konu tarafın kendisini dışlıyor. |
| 17 | **A-14** | **Komut satırı.** `--taraf`, `--kur`, `--birlesme`. §8, §9 ve §15.1 "gerçek ciro rakamlarıyla çalıştırılır" diyordu; kitabın sürümünde bunu yapacak arayüz YOKTU ve hesap zorunlu olarak kafadan yapılıyordu. |
| 18 | **A-15** | Devralma / birleşme ayrımı ve `rol` alanı. |

Geriye dönük uyum: `esik_a`, `esik_b`, `bildirilmeli` duruyor. İkisi de
belgelenmiş biçimde eksik (tek biçimli giriş, iki değerli cevap) ve yeni işler
için `degerlendir()` öneriliyor. Kör sınamanın A-07..A-15 vakaları BİLEREK bu
eski yola karşı bırakıldı: kusurun kaydı olarak dururlar.

## denetim.sh — denetim

| # | Kapatılan | Değişiklik |
|---|---|---|
| 19 | **D-01..D-15** | Mutasyon sınaması kitaba sadık sürümde 15 bozmadan 11'inin fark edilmediğini gösterdi. Üç mekanizma: (a) `... \| wc -l` boru hattının çıkış kodu daima `wc`'nindir, yani 0; (b) BOŞ bir Python dosyası `--self-test` ile 0 döner; (c) `test -z "$(grep -rL ...)"` hiç dosya yokken geçer. Her kontrol artık bir EŞİK doğruluyor: `enaz()` ve `oz_sinama()` yardımcıları. |
| 20 | yeni | Eklenen kontroller: her birimin INDEX.md'si, koltuk sayısı, kancanın settings.json'da GERÇEKTEN kayıtlı olması, matcher'ın Bash'i kapsaması, çıkar çatışması dosyasının varlığı, müvekkil ad kaydının doluluğu. |
| 21 | yeni | `--yapisal` bayrağı: mühendislik katmanını mevzuat bulgularından ayırır. Bayraksız koşumda ENGELLEYİCİ mevzuat bulguları denetimi kırmızıda tutar. |

## Eklenen dosyalar
- `hafiza/cikar-catismasi.md` — §2 `hafiza/` klasörünü kuruyordu ama bu dosyayı
  hiç oluşturmuyordu; oysa CLAUDE.md §8 ve §8 el kitabı Aşama 0 onu bir kapı
  sayıyor. Boş bir listenin "temiz" DEĞİL "kontrol yapılamadı" demek olduğu
  dosyanın kendisine yazıldı.
- `hafiza/muvekkil-adlari.txt` — sır kapısının ad kaydı.
- `hafiza/dogrulama-bulgulari.md` — açık mevzuat ve kaynak bulguları.

## Sayılar
Kitaba sadık kurulum: 85 vaka, **56 başarısız**.
Yamalı kurulum: 96 vaka, **11 başarısız** — 7'si bilerek bırakılan eski API
vakası, 1'i boş ad kaydı, 3'ü kitabın kendi bayat beklenen değerleri.
Mutasyon sınaması: 4/15 → **15/15**.
