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
| 22 | **`/esik-denetle`** | Komut kapanışta "hangi dosyalar bayat bir rakama dayanıyor" diye bitiyor ama yalnızca `birimler/*/yontem/` tarıyordu; §2'de canlı işleri tutan `dosyalar/` hiç açılmıyordu. Canlı iş katmanı (B) eklendi, ETKİLENEN ve SÜRÜMSÜZ işaretleri tanımlandı. "Hiçbir dosyayı düzenleme" korundu; tablonun makinede kalması kural 6 gereği yazıldı. |
| 23 | **`.claude/hooks/kapi.py` · sır kapısı** | Kapı müvekkil adını arıyor ama `dosyalar/<ad>/` biçimindeki müvekkil DOSYA YOLUNU görmüyordu; §9'un `dosya-ac` becerisi bu klasörleri müvekkil adıyla açtığı için sıradan bir oturum doğal olarak böyle metin üretir. Somut canlı iş yolu kuralı eklendi; yer tutucular ateşlemez. |
| 24 | **`/dosya-ac` komutu ve becerisi** | §8'in kontrolü tek yönlüydü ("verilen karşı taraf adlarını ara") ve yalnızca açılış anına bağlıydı. Çatışma simetriktir: yeni dosyanın müvekkili açık bir dosyanın karşı tarafı olabilir. Kontrol iki yönlü yapıldı; kayda taraf işlendiğinde açık dosyaları yeniden tarayan adım eklendi. Neyin çatışma sayıldığına karar verilmedi — §9 uyarınca insan kararı. |
| 25 | **`hafiza/arac-katalogu.md` (yeni) ve `once-arastir`** | §13'ün araç kararları kurulumda hiçbir dosya bırakmıyordu — karar kitapta, kararın dayandığı olgular bozulmakta. Katalog kuruldu; her satır bizim doğrulama tarihimizi taşır ve doğrulanmamış satır 'temiz' sayılmaz. `once-arastir` `archived` alanını ve kod/veri lisansı ayrımını okuyacak biçimde genişletildi. |
| 26 | **`yaptirim-taramasi` ve `kapanis-listesi`** | Taramanın üç kontrol noktası da imzaya kadardı; §5.1 ise imza ile kapanış arasına izin beklemesi koyuyor ve listelere atama haftalık. Dördüncü nokta (kapanıştan hemen önce) ve kapanış listesine 0. adım yeniden tarama eklendi. Tarama yine karar değildir; sorgu soyutlama kuralı mutlak. |
| 27 | **`.claude/hooks/kapi.py` · yedinci kapı** | §9 "adı belli bir insan onaylamadan kullanılmaz" diyor ama hiçbir kapı onay durumuna bakmıyordu; kapsam kapısının aradığı başlık onay İHTİYACININ beyanı, onayın kaydı değil. `kapi_onay` eklendi: §9 sınıfı bir çıktı ya onay kaydı ya da açık durum beyanı taşımalı. Kusur onayın yokluğu değil, onay durumu hakkındaki sessizlik. |\n
| 28 | **`.claude/hooks/kapi.py` · öz-sınama** | Yedinci kapı eklenmiş ama öz-sınamaya tek vaka yazılmamıştı; öz-sınama eski sayıyla "SELFTEST OK" demeye devam ediyordu — §14'ün kusurunun aynısı, bu kez benim elimde. Dört yönlü vaka eklendi (sessizlik/onay kaydı/taslak/içeride) ve AS-01 kapsamayı her koşumda sağlıyor. |\n## Eklenen dosyalar
| 29 | **`sinama/ks_d_denetim.sh`** | 26 kontrolün 9'u hiçbir mutasyonla sınanmıyordu; mutasyon yalnızca denetimin çıkış koduna bakıyor, hangi kontrolün kırmızıya döndüğüne bakmıyordu. 12 mutasyon eklendi (15 → 27) ve her mutasyon hedef kontrolünü beyan edip doğruluyor. |
| 30 | **`sinama/ks_d_denetim.sh` · ortam sızıntısı** | Dışarıdan MAFIRM verildiğinde kum havuzundaki denetim onu miras alıp CANLI ağacı denetliyordu; üç kontrol Python takımlarına devrettiği için mutasyon görünmüyordu. Çıplak koşumda 27/27, MAFIRM'li koşumda 24/27 — takımın cevabı çağıranın ortamına bağlıydı. Kum havuzu kökü sabitlendi. |
| 31 | **`sinama/ks_p_guncellik.py`** | Teslimat listesi ELLE yazılmıştı; 34. turda eklenen `hafiza/arac-katalogu.md` listeye konmamıştı ve dört tur boyunca güncellik kuralının dışında kaldı. Liste tersine çevrildi: teslimatlar keşfedilir, muafiyetler beyan edilir. |
| 32 | **`sinama/epilog.py` (yeni) ve `hepsi.sh`** | Epilogun dört kontrolü gömülü heredoc'tu ve mutasyonla sınanamıyordu (her biri için tam koşum, ~60 sn). Saf fonksiyona çevrildi; katman korundu, sınama 32 ms'ye indi. Gömülü kodda duran çıplak .lower() de düzeltildi — AE `.sh` taramıyordu. |
| 33 | **`sinama/ks_m_izlenebilirlik.py`** | Atıf ölçütü üç kez fazla dar/fazla genişti: önek listesi "ABCE" diye sabitlenmişti; sonra 'anmak tanımlamak sayıldı' (uydurma kimlik D'nin fixture'ında, AU'nun beyanında ve M'nin kendi yorumunda geçiyordu); son olarak J'nin çalışma anında kurduğu kimlikler görünmüyordu. Ölçüt: her takım yalnızca KENDİ önekini tanımlar, taban ekleri tanınır. |
| 34 | **`sinama/ks_ae_desen.py`** | AE-03 belge dizgelerini atlamıyordu ve epilog.py'nin kusuru ANLATAN docstring'ini kusur sandı. Belge dizgeleri ölçüm dışına alındı. |
| 35 | **`sinama/ks_af_aparat.py`** | AF-04 `"belirti" in _hepsi` diyordu; mantık epilog.py'ye taşındıktan sonra dizge yalnızca hepsi.sh'in YORUMUNDA kalmıştı ve ölçüt geçmeye devam ediyordu. Yorumlar ve belge dizgeleri ölçüm dışına alındı. |
| 36 | **`sinama/ks_ap_katalog.py`** | AP-02 URL'den sonraki 700 karaktere bakıyordu; `archived` curl komutundan silinse bile açıklama düzyazısında durduğu için geçiyordu. Ölçüt komutun kendisine bağlandı. |
| 37 | **`sinama/ks_k_yonlendirme.py`** | K-12'nin 120 karakterlik penceresi MEŞRUDUR (atıf gerçekten bir yakınlık olgusudur) ama gerekçesi yazılı değildi; AV-02 MUAF beyanı eklendi. |
| 38 | **`sinama/ks_d_denetim.sh`** | Kum havuzu yolu sabitti (`${TMPDIR}/ks_d_kum`); eşzamanlı iki koşum birbirini eziyor ve taban çizgisi sistemde hiçbir şey bozuk olmadığı hâlde kırmızı veriyordu. Her koşum kendi havuzunu alır; AL-08 sınıfı tarar. |
| 39 | **RAPOR.md ve KITAP-ERRATA.md · atıf biçimi** | İşletim sözleşmesinin kuralları on iki yerde "§N" diye anılıyordu; oysa kitapta §8 = İşlem el kitapları, §9 = Beceriler. Kurallar §3'ün içindedir. Atıflar "kural N" biçimine çevrildi; AY-02 karışmayı her koşumda sınıyor. |
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
