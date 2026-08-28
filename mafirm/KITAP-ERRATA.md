# Kitap için errata · Sürüm 1.0 → 1.1

> **Doğrulama: 2026-08-28 · Bozulma sınıfı: KİTAP SÜRÜMÜNE BAĞLI**
>
> Kitabın Sürüm 1.0 metnine karşı yazıldı. Yeni bir sürümde her madde
> yeniden sınanmalıdır; M takımı her maddenin bir vakaya bağlı kalmasını
> denetler.

Kör sınamanın bulduğu kusurların çoğu kurulumda değil, **kitabın metnindedir**.
Aşağıda bölüm bölüm ne yazdığı, ne yazması gerektiği ve hangi sınama vakasının
gösterdiği var. Kurulumu yapan yamalar `yamalar/DEGISIKLIKLER.md`; bu dosya
kitabın kendisi içindir.

Ağırlık: **[A]** kurulumu durdurur · **[B]** sonucu değiştirir ·
**[C]** doğruluk/tutarlılık.

---

## §3 · İşletim sözleşmesi

**[C] Kural 11 iki kez veriliyor ve hangisinin geçerli olduğu belirsiz.**
§3 kısa bir 11. kural yazıyor ("Ayrıntısı §14'te"), §14 ise uzun bir 11. kural
verip "işletim sözleşmesine 11. kural olarak yazılır" diyor. Harfiyen izleyen
biri EKLERSE `grep -c '^## '` 12 verir ve §3'ün beklenen değeri (11) bozulur;
hiçbir kontrol buna bakmaz.
→ §14 açıkça "§3'teki 11. kuralın YERİNE yazılır" demeli. *(E takımı)*

## §4 · Uzmanlık birimleri

**[C] Doğrulama beklenen değeri bayat.** `ls birimler/ | wc -l` için "8"
yazıyor; §7 `birimler/_koltuklar/` ekleyince gerçek değer **9** olur.
→ Ya beklenen 9 olmalı, ya komut `ls -d birimler/*/ | grep -vc _koltuklar`
olmalı. *(B-01, E)*

## §5.1 · Rekabet eşikleri — mevzuat

> Aşağıdaki üçü de **birincil kaynakla doğrulanamadı**: bu ortamda
> mevzuat.gov.tr, resmigazete.gov.tr, rekabet.gov.tr ve spk.gov.tr'ye
> erişilemedi. Desteklenmiş yeniden kurgudur ve kitabın kendi §11 kuralı
> gereği **insan teyidi ister**.

**[B] Teknoloji istisnası hangi bentlere uygulanıyor.** Kitap: "B eşiğindeki
devralınan taraf için aranan 1.000.000.000 TL yerine 250.000.000 TL". Güncel
m.7(2) indirimi birinci fıkranın **(a) ve (b) bentlerinin ikisine birden**
uyguluyor görünüyor.
→ Doğruysa: A ayağında Türkiye'de yerleşik bir teknoloji hedefinin 250M–1Mr TL
cirosu kendi ayağını karşılar. Kitabın "tabi değil" saydığı işlem tabidir —
**izinsiz kapanış maruziyeti**. *(I-01)*

**[B] Teknoloji bağlantı ölçütü yürürlükten kalkmış.** Kitap: "Türkiye'de
faaliyet gösteren ya da Türkiye'de araştırma geliştirme faaliyeti yürüten".
Bu **2022/2 sayılı Tebliğ'in** ölçütüdür; güncel ölçüt **"Türkiye'de
yerleşik"**tir. Ters yönde hata: gerekmeyen bildirimler.
Ayrıca 250 milyona yalnızca sayılan teknoloji faaliyetlerinden elde edilen
gelir sayılır ve rejim **birleşmeleri** de kapsar. *(I-02)*

**[B] Bekletici etkinin madde numarası yanlış.** Kitap dört yerde
"4054 sayılı Kanun, madde 11" diyor. M.11 **"Bildirilmemenin sonuçları"**dır;
bekletici kural **m.10**'dadır (m.7/2 ile birlikte), 2010/4 m.10'da
tekrarlanır. Esas doğru, atıf kuralın kendisini değil YAPTIRIMINI gösteriyor.
→ Düzeltilecek dört yer: `tr-esikler.md`, `esik.py`, `spa-inceleme` becerisi,
§15.2 komutu. *(I-03)*

> **Kanıt katmanı yükseltildi (2026-08-27).** Düzenleyicinin kendi alan adında
> iki bağımsız arama: m.10 ön inceleme + askıya alma + otuz günde zımni
> geçerlilik mekanizmasını taşıyor; m.11 bildirilmeme hâlini düzenliyor.
> Kanunun birebir metni egress ile engelli olduğu için statü hâlâ
> ENGELLEYİCİ. Atıf DEĞİŞTİRİLMEDİ; dört dosyada da yerinde `DOĞRULANAMADI`
> işareti duruyor (CLAUDE.md §1).

**[C] M.16 cezasının kanuni alt sınırı yazılmamış** (2026 için 302.484,86 TL).
"Küçük bir devralma için ölçeklenmez" savı doğru ama eksik. *(I-04)*

## §5.1 · esik.py — kod

**[B] Para birimi modeli yok.** Eşikler TL cinsinden; kod birim taşımıyor.
§19'un kendi pilotunda 2,4 milyar avro çevrilmeden verilirse
2.400.000.000 < 9.000.000.000 olur ve cevap **sessizce tersine döner**.
→ Tutarlar bir birim ve gerekiyorsa kur + kaynak taşımalı. *(A-07, J-03)*

**[A] Gerçek bir işlemi hesaplayacak arayüz yok.** §8, §9 ve §15.1 "gerçek ciro
rakamlarıyla çalıştırılır" diyor; `__main__` yalnızca `--self-test` tanıyor.
Kodun varlık sebebi hesabı kafadan yapmayı önlemekti.
→ Bir komut satırı arayüzü şart. *(A-14, J-01s)*

**[B] Cevap iki değerli.** §9 becerisi "evet / hayır / **belirlenemiyor**"
istiyor; `bildirilmeli()` yalnızca True/False dönüyor. Bilinmeyen bir ciro `0`
girilince cevap "hayır" olur — CLAUDE.md §2'nin yasakladığı olumsuz iddia.
*(A-10, A-11)*

**[C] Aynı işlem iki bağlantısız biçimde giriliyor.** `tr_cirolar` ile
`hedef_tr` arasında tutarlılık kontrolü yok; hedefin cirosunu A ayağına
yazmayı unutmak bildirimi sessizce yok eder. *(A-09)*

**[C] Girdi doğrulaması yok** (negatif ciro kabul ediliyor) · **devre konu
taraf kendi dünya cirosuyla B ayağını karşılayabiliyor** · **devralma/birleşme
ayrımı modellenmiyor** (şartname birleşme için ayrı ölçüt veriyor).
*(A-12, A-13, A-15)*

## §5.3 · TTK pay devri

**[C] İki incelik hatalı değil ama düz alıntılanırsa yanıltır.**
- **TTK 499** kaydı **açıklayıcıdır, kurucu değil**. Devir taraflar arasında
  ciro + zilyetliğin geçirilmesiyle tamamlanır (490/2). Kitabın "şirkete karşı
  hüküm ifade eder" ifadesi doğru; "kayda kadar geçersizdir"e kaymamalı.
- **TTK 595/1** tarafların **imzalarının** noterce onanmasını ister, noterin
  düzenlediği senet değil. *(I-05)*

## §7 · Ortak koltukları

**[B] Kitabın en yüksek itibar riskli kuralının hiçbir mekanizması yok.**
§7: "Bir koltuğun ağzına, o kişinin belgelenmiş görüşüyle çelişen bir söz asla
konmaz. Görüşü bilinmiyorsa koltuk bunu yazar." Bunu uygulayan kapı yok;
denetim de bakmıyor. §12'nin kendi uyarısı buraya düşüyor: belgedeki bir kurala
model sakinken uyulur.
→ Her koltuk dosyası zorunlu bir **`## Kaynak durumu`** bölümü taşımalı ve
altıncı bir kapı beyansız koltuğu bloklamalı. *(K-14, K-15)*

## §9 · Beceriler

**[C] Beklenen değer bayat:** "10" yazıyor, §14 `once-arastir` ekleyince **11**
olur. *(E)*

**[C] Negatif sınır kuralı gösteriliyor ama söylenmiyor.** §9 haklı olarak
"yönlendirme yalnızca açıklama alanını okur" diyor ve tek işlenmiş örneğinde
("Türkiye dışındaki rekabet rejimleri için KULLANMA") negatif sınır kullanıyor
— ama bunu bir kural olarak yazmıyor. Kitabı izleyen biri kalan dokuz beceriyi
negatif sınırsız yazar ve yanlış yönlendirme kaçınılmaz olur. *(K-06)*

## §12 · Kapılar

**[A] Öz-sınama üretim yolunu koşturmuyor.** Öz-sınama fonksiyona ham dize
veriyor; kanca `json.dumps(tool_input)` veriyor ve bu, satır sonlarını iki
karakterlik `\n` dizisine çevirir. Satır başı çapası olan her desen iki yolda
farklı davranır. **Bir kapının öz-sınaması, kapının gerçekte çalıştığı yolda
koşmalıdır.** *(C-10)*

**[B] Türkçe küçük harf.** `metin.lower()` ile aranan avukat başlığı, BÜYÜK
harfle yazıldığında bulunamaz: Python'da `"YETKİLİ".lower()` → `"yetki̇li̇"`
(`İ` → `i` + U+0307). Kapı doğru çıktıyı blokluyor.
→ Türkçeye duyarlı bir küçültme şart. Kitap §12'de tam da bu sınıftan bir
uyarıyı (binlik ayırıcı) yazmış ama ikincisini kaçırmış. *(B-10)*

**[B] Kural 2'nin (olumsuz iddia) hiçbir kapısı yok.** CLAUDE.md "kariyer
bitirir" diyor; "bildirim gerekmez", "tabi değildir", "yükümlülük yoktur"
cümlelerinin üçü de hiçbir kapıyı ateşlemiyor. *(B-07…B-09)*

**[B] Sır kapısı Bash'i görmüyor** ve `settings.json` matcher'ı Bash'i
çağırmıyor — oysa kitabın kendisi `curl`, `git`, `pip` ve üç dış aracı Bash
üzerinden öneriyor. Dışarı giden en geniş kanal izlenmiyor. *(C-05…C-09)*

**[B] Sır kapısının ÜÇÜNCÜ kusuru: Unicode kaçırma yüzeyi.** Kanal ve desen
kusurlarından ayrıdır ve ikisi düzeltilse bile kalır. Kapı düzyazının BİÇİMİNE
güveniyor; oysa üç yüzey desenleri atlatıyor ve üçü de **kaza olarak oluşur** —
PDF ya da Word'den kopyala yapıştır rutin olarak bunları üretir:
ayrışmış aksan (`A.Ş.` → `A.S` + U+0327), görünmez karakter (sıfır genişlikli
boşluk, yumuşak tire, yön işaretleyicileri) ve homoglif (Kiril `о`, Yunan `ο`).
Kitabın §12'si zaten aynı SINIFTAN bir kusur taşıyordu (Python'un `İ`.lower()
ayrışması) ama sınıfı genellemedi.
→ Sır kapısı eşleştirmeden önce metni normalleştirmeli: biçim karakterlerini
at, NFKC ile birleştir, dar bir homoglif tablosunu Latin'e katla. Yalnızca sır
kapısında; dışarı giden çağrıda fazla bloklamak, az bloklamaktan güvenlidir.
*(O-03…O-12)*

**[B] Sır kapısının İKİNCİ kusuru: desenler çok dar.** Yukarıdaki kanal
sorunundan ayrı bir kusurdur ve kanal düzeltilse bile kalır. İki desen var
("Proje Xxx" ve "Xxx A.Ş.") ve CLAUDE.md §6'nın saydığı şeylerin çoğunu
görmüyor: BÜYÜK harfle yazılmış kod adı (`Proje ŞAHİN`), İngilizce kod adı
(`Project Falcon`), kısaltmasız unvan (`... Anonim Şirketi`), gerçek kişi
müvekkil adı ve **fiyat** — oysa §6 fiyatı açıkça sayıyor. Ayrıca URL
kodlaması (`Proje+Şahin`) yalnızca boşluk arayan deseni atlatır.
→ Gerçek kişi adı desenle çözülemez; bir KAYIT ister (bkz. §7 önerisi).
*(B-25…B-29)*

**[C] TAVSIYE sekiz sabit ifade.** Bir hukukçunun yazdığı kiplerin çoğu
dışarıda: `-malısınız`, `zorunludur`, `şarttır`, `tabidir`, `başvurmanız
gerek`. *(B-02…B-06)*

**[C] ESIK deseni iki grup istiyor** (`{2,}`), yani 1.000.000 altındaki her
rakama kör. Örnek olarak 2026/2 sayılı Tebliğ'in kendi teknoloji eşiği
(250.000.000 TL) görünür ama bir noter harcı ya da damga vergisi ölçeğindeki
`250.000 TL` görünmez. Sözle yazılmış rakam (`3 milyar TL`),
`TRY` ve oran biçimleri (`binde bir`, `yüzde 98`) de görünmüyor. *(B-13…B-16)*

**[C] DAYANAK belge düzeyinde.** Metnin herhangi bir yerinde "Tebliğ" kelimesi
geçmesi bütün rakamları aklıyor; kırk satır önceki bir atıf ilgisiz bir rakamı
destekliyor sayılıyor. → İddia düzeyinde yakınlık, ya da açık bir `Dayanak:`
beyanı. *(B-17, B-18)*

**[C] Güncellik kapısı** Türkçe tarih biçimini (`01.01.2020`), **tarihi hiç
olmayan bir eşiği** ve gelecek tarihli doğrulamayı görmüyor. *(B-21…B-23)*

**[B] DAYANAK yalnızca Türk mevzuat atfını tanıyor.** Kanıt kuralı "her rakam
dayanağını yanında taşır" der — dayanağını, ille de bir KANUN MADDESİNİ değil.
Kitabın deseni yalnızca `madde N`, `NNNN/N sayılı`, `Resmî Gazete` gibi mevzuat
biçimlerini görüyor. Sonuç: doğru kaynaklanmış bir akademik etki büyüklüğü
("%19 daha düşük, *Organization Science* 2026") kanıt kapısını **asla geçemez**.
Kitabın kendi §17'si bu türden onlarca rakam taşır; §17 biçiminde yazılmış bir
çıktı kapı tarafından sonsuza kadar bloklanırdı.
→ Dayanağın TÜRÜ rakamın türüne bağlanmalı: para tutarı mevzuat atfı ister,
oran ve yüzde kaynak atfıyla yetinir. Gevşetme değil — kapı hâlâ bir dayanak
ister, doğru türdekini de tanır. *(Q-07)*

**[C] "bulunamayan:" alanı, atıf sanılıyor.** §14 her esaslı çıktının
`Kontrol edildi: … bulunamayan: <ne>` satırıyla bitmesini ZORUNLU kılıyor. Ama
o alan bulunAMAYAN kaynakları sayar; içindeki bir mevzuat adı bir atıf değil,
bir yokluk beyanıdır. Yakınlık penceresi ikisini ayırt etmediği için, §14'ün
zorunlu kıldığı satırın kendisi yanındaki her eşiği aklıyor.
→ Dayanak aranırken `bulunamayan:` alanı metinden düşülmeli. *(Q-06)*

**[C] Bozuk olayda kapı AÇIK başarısız oluyor** (`return 0`). Araç adı
okunamadığında kanalın dışarı gidip gitmediği bilinemez. *(C-08)*

## §12 · Kapılar — kapsanabilir ama kapsanmamış kurallar

**[C] §4, §9 ve §10 "kapı konusu değil" sayılmış; oysa üçü de kısmen makinece
kontrol edilebilir.** Kitap dört (sonra beş) kapı kuruyor ve kalan yedi kuralı
mekanizmasız bırakıyor. Ama:
- **§4 (önce cevap, en sonda yöntem)** bir BAŞLIK SIRASI kuralıdır ve doğrudan
  görülebilir. Bu raporun kendisi dokuz tur boyunca `## Yöntem` ile başladı ve
  cevabı 818. satırda tuttu; hiçbir şey uyarmadı.
- **§9 (insan onayı)** onayın kendisini izleyemez ama ONAY DURUMUNUN BEYANINI
  isteyebilir. Sessizlik onaylanmış gibi okunur.
- **§10 (ilk geçişte açıklama)** tanımlı bir terim listesi için kontrol
  edilebilir.
→ Üçü de kapı olmak zorunda değil; ama §16 denetiminde birer satır olabilirler.
Kitap onları "biçim kuralı" diye geçmekle, uygulanabilir olanı uygulanamaz
saymış oluyor. *(R-01, R-04, R-06)*

## §13 · Depolar

**[C] Tek bir doğrulama tarihi, farklı hızlarda bozulan verilere yetmiyor.**
§13 bütün katalog için tek bir tarih veriyor ("Hepsi 27 Ağustos 2026 tarihinde
doğrulandı"). Ama yıldız sayısı **bir gün**, lisans ve arşiv durumu **aylarca**,
proje kimliği **yıllarca** dayanır. Tek tarih, en hızlı bozulanı en yavaşıyla
aynı güvenilirlikte gösterir.
→ Her doğrulanmış tablo bir tarih VE bir **bozulma sınıfı** taşımalı; ve
bayatlayan bir tablo bayatladığını kendi başlığında söylemeli. Güncellik
kuralının gereği "hep taze olmak" değil — o imkânsızdır — bayatlığın görünür
olmasıdır. *(G-05, P-06)*

16 deponun 16'sı çözüldü; hiçbiri uydurma değil. Dört düzeltme:
- **[B] `freelawproject/courtlistener` lisansı "açık (depoya bakın)" değil,
  AGPL-3.0-or-later.** §13.7 tam da bu soruyu sorup PyMuPDF'i eliyor; aynı
  listede aynı lisanslı ikinci bir depo işaretsiz. *(G-01)*
- **[C] `google/diff-match-patch` 2024-08-05'te arşivlendi**, yazılmamış.
  §14'ün dört alanına "arşivlendi mi" eklenmeli. *(G-02)*
- **[B] `opensanctions` kodu MIT ama VERİSİ CC BY-NC 4.0.** Ticari bir
  pratikte bu, §13.7'nin AGPL'ye ayırdığı "asıl sahibin kararı" sorusudur.
  *(G-03)*
- **[C] Yıldız sayıları karışık**: dokuzu birime kadar tutuyor, yedisi
  tutmuyor. Hepsinin aynı gün doğrulandığı ifadesiyle uyuşmuyor. *(G-05)*

## §14 · Önce araştır

**[A] `^Kontrol edildi:` çapası üretimde asla eşleşmez.** JSON'da gerçek satır
sonu yoktur. Kapı, eşik rakamı ya da GitHub adresi içeren her yazmayı
bloklar — kitabın kendi §5.1 dosyası dâhil. *(C-01…C-03, C-10)*

**[A] Yeni kapı eklenirken §12'nin dokuz beklenen kümesi güncellenmiyor.**
İkisi eşik rakamı içerdiği ve "Kontrol edildi" satırı taşımadığı için yeni kapı
onlarda ateşliyor: `SELFTEST HATA 2`. Zincir: §14 kırmızı → §16 kırmızı →
§0'ın dördüncü kuralı kurulumu durduruyor → §19 hiç çalışmıyor.
**Kitabın kendi talimatları izlendiğinde yeşil denetim üretilemiyor.** *(E)*

**[C] Belgelenen biçim, kapının reddettiği biçim.** `once-arastir` çıktı
satırını dört boşluk girintili gösteriyor; `^Kontrol edildi:` sütun sıfır
istiyor. *(B-33)*

**[C] Önerilen doğrulama komutu her ortamda çalışmıyor.**
`curl https://api.github.com/...` ajan vekili arkasında 403 dönebilir; beceri
kendi belgelediği yöntemle boş döner ve §14'ün ikinci tuzağına ("boş arama
yokluğun kanıtı değildir") kendisi düşer. *(G-07)*

## §15 · Komut kütüphanesi

**[B] §15.2** izinsiz kapanış riskini "4054 sayılı Kanun madde 11"e
dayandırıyor — bkz. §5.1, m.10 olmalı. *(I-03)*

## §16 · Denetim

**[A] On bir kontrolün altısı hiçbir koşulda başarısız olamaz.** Mutasyon
sınaması: on beş bozmadan **on biri fark edilmiyor**. `DENETİM OK` diyor:
sıfır beceri, sıfır ajan, sıfır komut, kancasız `settings.json`, koltukların
on üçü silinmiş — ve **tamamen boş bir `esik.py`**.
Üç mekanizma:
1. `... | wc -l` boru hattının çıkış kodu daima `wc`'nindir: 0.
2. Boş bir Python dosyası `--self-test` ile 0 döner.
3. `test -z "$(grep -rL ...)"` hiç dosya yokken geçer.
→ Her kontrol bir **eşik** doğrulamalı, bir sayı yazdırmamalı. *(D takımı)*

**[C] Denetimin bakmadığı şeyler:** kancanın `settings.json`'da gerçekten
kayıtlı olup olmadığı, matcher'ın kapsamı, `hafiza/cikar-catismasi.md`'nin
varlığı (§2 klasörü kuruyor ama dosyayı hiç oluşturmuyor), koltuk sayısı ve
koltuk kaynak beyanları. *(C-09, K-14, D)*

## §17 · Ölçülmüş kanıt

Künye, tasarım, örneklem, görev listesi ve **dört olumsuz bulgunun dördü de**
doğrulandı — akıl yürütme modelinin insan kolundan fazla uydurduğu (11'e 4)
dâhil. Üç aktarım hatası:
- **[C] Süre düşüşü aralıkları** (%20–28 / %20–34) hiçbir kaynakla uyuşmuyor;
  bulunanlar %14–37 (erişim destekli) ve %12–28 (akıl yürütme) — ve kitap geniş
  aralığı ters kola veriyor. *(H-03)*
- **[C] +0,26 puan bir karıştırma:** o rakam iki AI kolu **arasındaki**
  farktır; erişim destekli kolun kontrole karşı etkisi 0,25'tir. *(H-04)*
- **[B] "%19 daha düşük" → "19 YÜZDE PUANI daha düşük."** Mevcut ifade,
  kitabın kanıtlamak için alıntıladığı riski küçültüyor. *(H-06)*
- **[C] §17.2'nin çıkarımı fazla geniş.** 11'e 4 ham sayıdır; bu bir ürün
  karşılaştırmasıdır, mekanizma değil; "en yetenekli" kol doğrulukta üstün
  değildi; ve çalışma bir otomatik kapıyı hiç sınamadı. *(H-10)*

## §19 · İlk dosya

**[A] Pilot, kitabın kendi kurulumunda çalıştırılamıyor.** Üç ayrı sebep:
`esik.py`'nin komut satırı arayüzü yok, avro çevirisi modellenmemiş, ve §14
sonrası öz-sınama kırmızı olduğu için §0 kurala göre buraya hiç gelinmiyor.
*(A-14, A-07, J-01s)*

**[A] Ve asıl mesele:** §19 "bu iki cevabın arasındaki fark, kurulumun
tamamının sebebidir" diyor. Ölçüldü — kitaba sadık kapılarda **doğru cevap da
yanlış cevap da bloklanıyor**. Kapı sistemi, kurulumun sebebi olarak gösterilen
farkı ifade edemiyor. *(J-07s, J-08s)*

---

## Kapıların yapısal sınırı — errata değil, yazılması gereken bir sınır

Töreni eksiksiz ama **rakamı yanlış** bir cevap bütün kapılardan geçiyor:
dayanağı var, tarihi var, iki başlığı var, "Kontrol edildi" satırı var — ve
eşiği yanlış okuyor. *(J-09)*

Kapılar **biçimi** denetler, **muhakemeyi** değil. Bu bir kusur değil bir
sınırdır ve §18'e onuncu madde olarak yazılmalıdır — çünkü §17.1'in kendi
bulgusu tam olarak budur: kazanç açıklıkta ve düzendedir, **doğrulukta
değildir.** Doğruluğu sağlayan şey kapılar değil, yetkili avukat onayıdır.

---

## Şimdi ne yapılmalı

1. **Üç ENGELLEYİCİ mevzuat bulgusunu birincil kaynaktan teyit ettirin.**
   Erişimi olan bir insan `resmigazete.gov.tr/eskiler/2026/02/20260211-5.htm`
   ve 4054 sayılı Kanun metnini açmalı. I-01 ve I-02 bildirime tabilik
   sonucunu **iki ayrı yönde** değiştirir; I-03 dört dosyaya yayılmış bir
   atıftır. Teyide kadar `birimler/rekabet/` çıktılarına canlı bir dosyada
   dayanılmaz.
2. **Kitabın §14 yamasını uygulamadan önce §12'nin dokuz beklenen kümesini
   güncelleyin.** Aksi hâlde kurulum kendi denetimini geçemez ve §19 hiç
   çalışmaz.
3. **Sır kapısını Bash'i kapsayacak biçimde kurun** ve müvekkil ad kaydını
   (`hafiza/muvekkil-adlari.txt`) doldurun; boş kayıt, kural 6'nın gerçek
   kişi ayağının kapsanmadığı anlamına gelir ve denetim bunu her koşumda
   söyler.
4. **`ks_g_depolar.md`'deki yıldız sayılarına dayanmadan önce yeniden çekin** —
   dosya GÜNLÜK bozulma sınıfındadır ve bu rapor yazıldığında zaten bir gün
   eskimişti.
5. **Bir sonraki kurulumda `sinama/hepsi.sh` koşun.** 0 SİNYAL, raporun hâlâ
   ölçtüğü sistemi anlattığının tek kanıtıdır.

## Yetkili avukat görüşü gereken konular

Bu rapor bir hukuk pratiğinin sistemini sınar; **hukuki görüş değildir** ve
kaleme alanı hiçbir ülkede baroya kayıtlı değildir. Aşağıdakiler dayanılmadan
önce yetkili avukat görüşü ister ve bu liste boş değildir:

- **Teknoloji teşebbüsü istisnasının kapsamı** (I-01): indirim 2026/2 m.7(2)
  uyarınca birinci fıkranın (a) ve (b) bentlerinin ikisine birden mi uygulanır?
  Cevap, bir işlemin bildirime tabi olup olmadığını değiştirir.
- **Teknoloji bağlantı ölçütü** (I-02): "Türkiye'de yerleşik" mi, yoksa
  kitaptaki "faaliyet gösteren ya da Ar-Ge yürüten" mi?
- **Bekletici etkinin dayanağı** (I-03): 4054 m.10 mu m.11 mi.
- **TTK 499 ve 595/1'in nitelendirilmesi** (I-05): pay defteri kaydının
  açıklayıcı mı kurucu mu olduğu, ve noter onayının kapsamı.
- **§5'teki her eşiğin bugünkü değeri.** Bu raporun mevzuat katmanı
  **birincil kaynakla doğrulanmadı**; kanıt katmanı arama motoru özetidir ve
  bunun gerekçesi `hafiza/egress-kaniti.md` içinde kanıtlıdır.
- **Bu raporun bulgularına dayanarak canlı bir dosyada atılacak her adım.**

Kontrol edildi: rekabet.gov.tr arama sonuçları (2026-08-27) · GitHub MCP depo
çözümlemesi (2026-08-27) · yayıncı kayıtları (2026-08-27) · vekil egress ret
kaydı (2026-08-28) · yerel kurulum ve sınama takımı (2026-08-28) ·
bulunamayan: 4054 sayılı Kanun ve 2026/2 sayılı Tebliğ'in birebir Resmî Gazete
metni (kuruluş egress politikası reddi)
