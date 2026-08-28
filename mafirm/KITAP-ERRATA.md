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

## §2 · Klasör ve depo

**[A] Gizlilik ile dayanıklılık §2'de AYNI mekanizmadır; birini seçmek
ötekini feda eder ve kitap bunu hiç söylemiyor.**
§2 tek adımda iki şey kuruyor: `git init` — kitabın TEK dayanıklılık aracı
(geri alma, kaza kurtarma, "dün ne yazmıştım") — ve `.gitignore` — kitabın
TEK gizlilik aracı. İkisi aynı mekanizmanın iki yönüdür. Kural 6 ("müvekkil
kimliği makineden çıkmaz") kimlik taşıyan her yolu `.gitignore`'a girmeye
zorlar; o yol depodan çıktığı anda **hiçbir kurtarma yolu kalmaz**. Oysa
`hafiza/` klasörünün §2'de yazılı varlık sebebi "oturumdan sağ çıkan
doğrulanmış tespitleri tutmak" — yani dayanıklılığın ta kendisi. Kimlik
taşıyan parçalar tam olarak var oluş sebeplerini kaybediyor. Kitap ikinci
bir dayanıklılık aracı önermiyor: ne yedek, ne kopya, ne "üzerine yazmadan
önce yedekle" cümlesi.

Bu, kâğıt üstünde bir itiraz değil; sonucu bu turda ÖLÇÜLDÜ. Sıradan bir
araç (kör sınama takımımın kendisi) korunan dosyalardan birini yerinde
yeniden yazıyor, aslını yalnızca bir DEĞİŞKENDE tutuyor ve `finally` ile
geri koyuyordu. `finally` SIGKILL'de koşmaz. Süreç o pencerede öldürüldü:
dosyanın 274 baytlık içeriği gitti, `.gitignore`'da olduğu için
`git checkout` ile dönülemedi, tek kopya ölen sürecin belleğindeydi.
Üstelik `denetim.sh` geriye kalan sınama artığını "1 ad" sayıp
`UYARI müvekkil ad kaydı BOŞ — kural 6'nın gerçek kişi ayağı kapsanmıyor`
satırını `ok müvekkil ad kaydı 1 ad` hâline getirdi: **koruma bozulurken
alarm da kapandı.** *(AL-01, AL-02, AL-05)*

→CEVAP: 6 — cevabın "sistem yamalı hâlde çalışıyor" cümlesi bu maddeyi
kapsamıyor, çünkü mesele bir kusur değil bir TASARIM BOŞLUĞU: kitabın
mimarisinde gizli olan hiçbir şey kurtarılabilir değildir. Pratiğe kurulum
yapan kişi bunu bilerek kurmalı ve `hafiza/`nın kimlik taşıyan dosyaları
için depodan bağımsız bir yedek yolu (şifreli disk kopyası, ayrı bir özel
depo) kendisi kurmalıdır. Kitabın §2'si bunu söylemediği sürece her
kurulum, sessiz ve geri alınamaz bir veri kaybına açıktır.

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
→CEVAP: YOK — mühendislik boşluğu; yamayla kapandı ve cevabın 'yamalı hâlde çalışıyor' cümlesi bunu kapsıyor. Cevap bir özet değil, en tehlikeli beşi.

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

## §6 · Sınır ötesi mimari

**[B] Kitap kendi içinde çelişiyor: kurucu bir işlem, önkoşul listesinde.**
§6 `mimari.md`'nin "Kapanış öncesi koşullar" listesinin **5. maddesi**,
işlemi *yetkilendiren* organ kararı ile Ltd. Şti.'de **TTK m.595/2 genel kurul
onayını** tek satırda topluyor. Kitabın kendi §5.3 `pay-devri.md`'si ikincisini
"devri tamamlayan **kurucu** işlem" sayar. Kurucu bir işlem kapanışın önkoşulu
olamaz: kapanış günü sırasının ilk adımı "koşulların karşılandığının teyidi"
olduğunda, o adım hiçbir zaman doğrulanamaz — koşul, kendisinden sonra gelecek
işleme bağlanmış olur.

Çelişkinin iki tarafı da kitabın içindedir; görmek için dış kaynak gerekmez.
Hangisinin doğru olduğu ise bir hukuki nitelendirmedir; §9 ve §11 uyarınca
kitabın düzyazısı **aynen bırakıldı** ve karar yetkili bir insana bırakıldı.
Önerilen tek satırlık düzeltme kum havuzunda uygulandı; U-01 ile U-02'yi
birlikte yeşile alıyor:

    5. Şirket organ kararları — işlemi yetkilendiren kararlar
       (Ltd. Şti.'de TTK m.595/2 genel kurul onayı bir koşul değil,
       kapanış günü devri tamamlayan kurucu işlemdir; bkz.
       `birimler/tr-sirketler/yontem/pay-devri.md`)

Bu kurulumda türetilmiş dosyalar (`kosul-takibi`, `kapanis-listesi`) ayrımı
zaten taşır, dolayısıyla becerileri kullanan kişi doğru sırayı görür. *(U-02)*

**[B] Birimler arası tutarlılık hiçbir yerde sınanmıyor.**
§4 birim yapısının gerekçesini "birimler aynı YAPIYI paylaşır" diye yazar ve
denetim yalnızca yapıyı sayar: INDEX var mı, `yontem/` dolu mu, üst bilgi
yerinde mi. İki birimin aynı hukuki işlemi farklı sıraya koyması ya da aynı
hükme farklı nitelik atfetmesi denetimi **yeşil bırakır**. Yapısal denetim,
içeriği hiç okumadığı için bu sınıfa kördür.
*(U-01, U-02, U-03, U-05, U-06, U-07, U-08, U-09, U-10, U-11)*

**[B] Raporun kendi kapsama matrisi, raporun kendi §2'sini çiğniyordu.**
Matris üç kuralda "YOK" (mekanizma yok) yazıyordu ve üçünün de mekanizması
vardı — kural 2 (N-01..N-08), kural 8 (denetim kontrolü, mutasyonla
doğrulandı), kural 7 (K-13). "YOK" bir **olumsuz iddiadır**; CLAUDE.md §2
olumsuz iddiadan olumludan yüksek kanıt ister ve matris o iddiayı üç kez
kanıtsız yazdı. El yazısı bir durum sütunu ölçtüğü sistemden bağımsız yaşar.
→ F-01 (matriste adı geçen her mekanizma gerçekten var) ve F-02 (her "YOK"
iddiası, aramanın boş dönmesiyle kanıtlı) eklendi; ikisi de mutasyonla
kırmızıya döndürüldü. *(F-01, F-02)*

**[A] Kitabın iki çıktı biçimi birbirini tanımıyor.** §3 ve §5.3 yöntem
dosyalarına `Doğrulama: <tarih>` yazdırıyor; §14 ise ÇIKTILARA
`Kontrol edildi: <kaynak> (<tarih>)` yazdırıyor. §12'nin güncellik kapısı
yalnızca birincisini tanıdığı için, §14'ü HARFİYEN izleyen bir çıktı kapıdan
"doğrulama tarihi yok" diye geri dönüyor. Kitap kendi emrettiği biçimi kendi
kapısında bloklıyor. → Kapı her iki biçimi de tanımalı. *(V-01)*
→CEVAP: YOK — dar bir biçim çelişkisi; müvekkile giden sonucu değiştirmiyor, kapı iki biçimi de tanıyor artık.

**[B] Genişletilmiş bir eşik deseni, doğru işi bloklar.** Kitabın kendi `ESIK`
deseni yalnızca basamak gruplu para tutarını görür ve B-13..B-18 bunun kaçırma
yüzeyini kanıtlar. Ama deseni "yüzde" içerecek biçimde genişletmek — bu
kurulumda yapıldı — Türkçede her SPA incelemesini ve her ortaklık yapısı notunu
üç kapıya birden takar: "yüzde" ticari metnin günlük kelimesidir (pay oranı,
tazminat tavanı, oy çoğunluğu). Kitabın kendi uyarısı buraya düşer: *"Doğru işi
bloklayan bir kapı bir gün içinde kapatılır."* → Bir yüzde ancak DÜZENLEYİCİ
bir ipucuyla aynı cümlede geçtiğinde eşik sayılmalı. *(V-03, V-08, V-24)*

**[B] Kitap bir madde bankası kuruyor, üç tüketici bağlıyor ve bankayı hiç
doldurmuyor.** §2 `emsal/` dizinini "onaylı madde bankası" olarak açar, §4 her
birim altında `birimler/<birim>/emsal/` açar, §10 `emsal-bulucu` alt ajanını
YALNIZCA orayı aramak üzere görevlendirir ve §14 `once-arastir`ın üçüncü
adımını oraya yönlendirir. Banka boş kurulur ve boşluğu hiçbir yerde
bildirilmez. Boş bankada arama yapan ajan "yeterince yakın emsal yok" der;
okuyucu bunu dünyaya dair bir tespit sanır. Kitabın kendi §14'ü tam bunu
yasaklar: *"Boş bir arama yokluğun kanıtı değildir."* → Denetim boş bankayı
sesli bildirmeli ve `emsal-bulucu` "banka boş" ile "yakın emsal yok"u
ayırmalı. *(W-02, W-03)*

**[A] Web yetkisi olan ajan, sır sınırını yazmıyor.** §10 `esik-denetcisi`'ye
`WebSearch` ve `WebFetch` veriyor — sistemdeki iki web yetkili ajandan biri.
Sorgu soyutlama kuralı ise §9'da `yaptirim-taramasi` BECERİSİNİN metninde
yazılı. Yani kural, onu uygulayacak yetkinin BULUNMADIĞI yerde duruyor:
internete gerçekten ulaşabilen ajanın metninde müvekkil adı/kod adı yasağı yok.
→ Riskli yetkisi olan her ajan sınırını kendi metninde taşımalı. *(X-06)*
→CEVAP: 4

**[C] Beyan edilmiş ama uygulanmayan bir "dışarı" kuralı.** §14'ün genişlettiği
sır kapısı `BashOutput`'u dışarı aracı sayıyor; §12'nin kanca matcher'ında ise
`BashOutput` yok. Beyan hiçbir zaman uygulanmıyor. Doğru düzeltme matcher'a
eklemek değil — `BashOutput`'un girdisi yalnızca bir `bash_id`'dir, dışarı yük
taşımaz; gerçek koruma komutun BAŞLATILDIĞI andadır. Beyan, uygulanabilir hâle
getirilmeli ya da kaldırılmalı. *(X-02, X-07)*

**[A] §2 bir depo kuruyor ve kural 6'nın yasakladığı şeyi mümkün kılıyor.**
Kurulumun ikinci adımı `git init` çalıştırır ve `.gitignore`'a yalnızca
`cikti/`, `dosyalar/*/veri/` ve `.DS_Store` yazar. Ama `git push` veriyi
makineden ÇIKARIR — kural 6'nın ("müvekkil kimliği makineden çıkmaz")
yasakladığı şey tam budur. Korunmayanlar: `dosyalar/<is>/` altındaki kapsam
notu, taslaklar ve yazışma (§2'ye göre CANLI İŞ; yalnızca `veri/` dışlanmış)
ve §8'in gerektirdiği çıkar çatışması listesi. §12'nin sır kapısı ön kapıyı
tutarken §2 yükleme rampasını açık bırakıyor.
→ `dosyalar/` tamamı ve kimlik taşıyan her `hafiza/` dosyası dışlanmalı;
izlenen sürüm olarak yalnızca ŞABLON bırakılmalı. Dikkat: bir yolu
`.gitignore`'a eklemek, o yol ZATEN izleniyorsa hiçbir şey yapmaz —
`git rm --cached` şarttır. *(Y-02, Y-03)*
→CEVAP: 4


**[A] Kurulum idempotent değil ve kitap bunu hiçbir yerde söylemiyor.**
§2'nin `printf ... > .gitignore` adımı ile §5, §12 ve §16'nın "yazılır"
talimatları ÜZERİNE YAZAR. Kitabı ikinci kez izleyen biri — yeni bir oturum,
ikinci bir hukukçu, ya da §0'ın dördüncü kuralının "denetim kırmızıysa dur ve
düzelt" talimatını izleyen kişi — uygulanmış HER YAMAYI geri alır. Kitapta ne
bir sürüm işareti, ne "bu dosya değiştirilmiş" kontrolü, ne de güvenli bir
yeniden kurulum yordamı var. → §2 bir "yeniden kurulum" bölümü taşımalı:
hangi dosyaların üzerine yazıldığı, önce neyin yedekleneceği, ve yeniden
kurulumdan sonra denetimin ZORUNLU koşulması. *(Z-02, Z-03)*
→CEVAP: 5


**[A] Denetim kendi bütünlüğünü doğrulayamaz.** §16'nın `denetim.sh`'i de
"yazılır" dosyalarından biridir. Kitaba sadık hâli geri konduğunda tüm ek
kontroller kaybolur ve betik "DENETİM OK" der — kural 6 koruması silinmiş olsa
bile. Yani denetçiyi ezmek, denetçinin yapacağı bütün kontrolleri devre dışı
bırakır ve uygulayıcı korumasız bir sisteme YEŞİL bir denetimle bakar.
Doğrulama, ezilen dosyanın DIŞINDA bir katmanda durmalıdır. *(Z-07, Z-08)*
→CEVAP: 5


**[A] Arıza politikası yalnızca ayrıştırmayı kapsıyor; gerisi AÇIK düşüyor.**
§12'nin C-08 gerekçesi doğrudur — ayrıştırılamayan bir olayda kanal bilinmez,
dolayısıyla dışarı yönde kapalı çözülür. Ama politika yalnızca `json.load`
çevresindedir. Ayrıştırmadan SONRAKİ her istisna işlenmez: Python geri izleme
basar, çıkış kodu 1 olur ve PreToolUse sözleşmesinde 1 "bloklamayan hata"dır —
araç çağrısı DEVAM EDER. Yani kancadaki her çökme kural 6'yı SESSİZCE devre
dışı bırakır. → İç arıza da politikaya tabi olmalı: kanal dışarıysa blokla,
yerelse uyar ve sürdür. Ayrıca geçerli JSON'un NESNE olduğu doğrulanmalı
(`[1,2,3]` ve `null` ayrıştırılır ama `.get()` çağrısında çöker).
*(AA-01g, AA-01k, AA-01l, AA-02)*
→CEVAP: 4

**[C] Kapsam kapısının deseni genişletilirse kanca donuyor — kitabın kusuru
değil, kitabı izleyenin düşeceği tuzak.** Kitabın kapsam kapısı sekiz sabit ifade arar. Türkçe kip
çeşitliliğini kapatmak için desen `\w+` ile genişletilirse (bu kurulumda
yapıldı), boşluksuz uzun bir dizgede felaket geri izleme oluşur: 20.000
karakter 6 saniye, 40.000 karakter 25 saniyeden fazla. base64 bir blok,
küçültülmüş bir dosya ya da boşluksuz çıkarılmış PDF metni pratiği DURDURUR —
bloklayan ya da açan bir kapıdan da kötüdür. → Nicelik belirteci sınırlanmalı;
Türkçe bir kelime otuz karakterden uzun değildir. Kitabın KENDİ deseni bu
kusuru taşımaz (AA-03 kitaba sadık kapıda GEÇİYOR); kusur, deseni bu kurulumda
genişletmemle doğdu ve buraya bir UYARI olarak yazıldı.
*(AA-03-20, AA-03-80, AA-03-200)*

**[C] Denetimin takım listesi deseni iki harfli adı görmüyor.** `ks_[a-z]_`
yalnızca tek harfli takım adlarını sayar; yirmi altıncı takımdan sonra eklenen
her takım sessizce kapsam dışı kalır ve "her takım raporda anılıyor" kontrolü
onları hiç istemez. Bir kapsama kontrolü, kapsamadığını söylemez. *(AA-01g, AA-03-20)*

**[B] Kapılar teşhis koyuyor, çare söylemiyor.** §12'nin beş kapısının hiçbir
iletisi uyulacak yolu göstermiyor: "dayanaksız eşik", "avukat başlığı yok",
"doğrulama tarihi yok" doğru teşhislerdir ama bloklanan kişi NE YAZACAĞINI
iletiden öğrenemez. §14 bir kapının nasıl öldüğünü kendisi yazar — "doğru işi
bloklayan bir kapı bir gün içinde kapatılır" — ve ekonomi DOĞRU bloklar için de
aynıdır: yolu söylemeyen bir kapı her seferinde zaman yakar, en ucuz çözüm onu
kapatmaktır. En kötüsü güncellik kapısıdır: kitap İKİ biçim kabul eder
(`Doğrulama: <tarih>` yöntem dosyalarında, `Kontrol edildi: <kaynak> (<tarih>)`
çıktılarda) ve ileti ikisini de saymaz; kullanıcı deneyerek bulmak zorunda
kalır. → Her blok iletisi bir EYLEM göstermeli ve birden çok kabul edilen
biçim varsa hepsini saymalı. *(AB-01, AB-02, AB-03b)*

**[B] Güncellik kapısı GELECEK tarihli bir doğrulamayı hiç görmüyor.** §12'nin
kapısı yalnızca BAYAT tarihi arar; ileri tarihli bir `Doğrulama:` satırı
sessizce geçer. Gelecek tarihli bir doğrulama, yapılmamış bir doğrulamanın en
olağan yazım biçimidir (kopyala-yapıştır, şablon, ileri tarihli taslak) ve
kapının varlık sebebi tam olarak budur. B-23 bunu kaçırma olarak kaydeder;
AC-04 aynı boşluğu kitaba sadık kapıda ikinci kez ölçer.

> **Ve bu kontrolü eklerken YENİ bir kusur doğdu.** Bir takvim tarihi saat
> dilimi taşımaz; makinenin "bugün"ü taşır. İkisini doğrudan karşılaştırmak,
> kıyasa olmayan bir saat dilimi sokar: dünya UTC-12 ile UTC+14 arasına, 26
> saate yayılır. İstanbul'da yazılan doğru bir doğrulama, Pasifik'teki bir
> masada "GELECEK tarihli" diye bloklanıyordu — ve kitap §6'da SINIR ÖTESİ bir
> pratik kuruyor, yani dosyalar tam olarak böyle dolaşıyor. Tolerans bir gündür
> ve orada biter (AC-04 beş gün ileri tarihin hâlâ bloklandığını, AC-05 bayat
> kontrolünün yaşadığını sabitler). *(B-23, AC-01, AC-02, AC-04)*

**[C] §15 komutları başka bileşenler hakkında SAYISAL iddialarda bulunuyor ve
hiçbiri korunmuyor.** `/spa-incele` "sekiz adımlı sıra", `/kurul-notu` "beş
bölümlü sıra", `/esik-denetle` "altı aydan eski" der. Üçü de BUGÜN doğrudur —
ve hiçbir kontrol onları bağlamaz. Kitabın kendi §9'u aynı sınıfta zaten
bayatladı ("10 beceri", §14 on birinciyi ekleyince). Beceri bir adım
kazandığında ya da `BAYAT_GUN` değiştiğinde komut sessizce yalan söylemeye
başlar. → Bir bileşenin başka bir bileşen hakkındaki her sayısal iddiası
kontrol edilen bir iddia olmalı. *(AD-01, AD-03)*

**[B] Türkçe metni ASCII sezgisiyle okumak, bu sistemde tekrar eden bir
sınıftır.** §12 `İ`.lower() tuzağını kendi kodunda çözer (B-10) ama çözümü bir
YERDE uygular; sistemin geri kalanında aynı hata dört ayrı biçimde geri gelir:
ek çekimi (defterine/Defterin/defteri eşleşmez), ünlü uyumu (adımLI ama
bölümLÜ), yarım karakter sınıfları, ve büyük harfli metinde çıplak `.lower()`.
Bir kurulum kitabı, dilin bu özelliğini TEK BİR YERDE değil, metin okuyan HER
bileşende ele almalı. → Türkçe metni desenle okuyan her bileşen için: küçültme
`tr_kucult` üzerinden, karakter sınıfları tam alfabe, ekler dört ünlü
varyantıyla. *(B-10, U-05, AD-01, AE-02, AE-03)*

**[C] Kitap, kendi dosyalarının özgün sürümünü saklamayı hiçbir yerde
söylemiyor.** §2 `git init` çalıştırır ama kurulumun ilerleyen bölümlerinde
§5, §12 ve §16'nın yazdığı dosyalar okuyucu tarafından yamalandığında "kitap ne
yazıyordu" sorusunu cevaplayacak bir referans kalmaz. Bu kurulumda taban elle
tutuldu ve yine de iki dosya (§2'nin `.gitignore`'u, §5'in `tr-esikler.md`'si)
gözden kaçtı; ikisi de kitabın metninden yeniden kuruldu. → Kitap, yamalanan
her dosyanın özgününü saklamayı ve bu tabanın eksiksizliğini denetlemeyi
söylemeli. *(AG-01, AG-02)*

## §7 · Ortak koltukları

**[B] Kitabın en yüksek itibar riskli kuralının hiçbir mekanizması yok.**
§7: "Bir koltuğun ağzına, o kişinin belgelenmiş görüşüyle çelişen bir söz asla
konmaz. Görüşü bilinmiyorsa koltuk bunu yazar." Bunu uygulayan kapı yok;
denetim de bakmıyor. §12'nin kendi uyarısı buraya düşüyor: belgedeki bir kurala
model sakinken uyulur.
→ Her koltuk dosyası zorunlu bir **`## Kaynak durumu`** bölümü taşımalı ve
altıncı bir kapı beyansız koltuğu bloklamalı. *(K-14, K-15)*

**[B] §7 koltuk provenansını en yüksek itibar riski sayıyor ama dayanağın
DOĞRULANMASINI istemiyor.** Kural "bir koltuğun ağzına belgelenmiş görüşüyle
çelişen söz konmaz" der; mekanizma (bu kurulumda eklenen altıncı kapı) beyanın
VARLIĞINI görür. Beyan ise adı geçen ESERLERE dayanır — ve o eserlerin gerçekten
var olup olmadığı, doğru kişiye ait olup olmadığı hiçbir yerde sorulmaz. On üç
koltuk gerçek ve çoğu yaşayan hukukçuların adını taşıdığı için bu, §1'in kanıt
kuralının en çok gerektiği yerde uygulanmaması demektir. Bu kurulumda altı eserin
altısı da doğrulandı ve kayda bağlandı; biri (ortak yazarlı bir kitap tek kişiye
atfediliyordu) düzeltildi. → Koltuk beyanındaki her eser, doğrulama kaydına
girmeli ve bir sonuç taşımalı. *(AI-02, AI-03, AI-04)*

## §9 · Beceriler — yaptırım taramasının zaman ekseni

**[A] Yaptırım taramasının son kontrol noktası İMZA; oysa en uzun maruziyet
aralığını kitabın kendi §5.1'i imza ile kapanış arasına koyuyor.**
`yaptirim-taramasi` becerisi zaman sorusunu kitapta en iyi soran yerdir —
üç kontrol noktası verir: *"gizlilik sözleşmesinden önce, münhasırlıktan
önce, imzadan önce."* Ama üçü de imzaya kadardır. §5.1 ise şunu yazıyor:
bildirime tabi bir işlem *"Kurul açıkça ya da inceleme süresinin dolmasıyla
zımnen karar vermeden hukuken geçerlilik kazanmaz. **İmza serbesttir;
kapanış değildir.**"*

Yani aralık kitabın **kendi tasarımından** doğuyor ve izin beklemesi ayları
bulabilir. Yaptırım listelerine atama ise haftalık yapılır. Kapanış kontrol
listesinde (`kapanis-listesi`) yeniden tarama adımı **yok**: liste izin
yazısını ve yetkilendirici organ kararlarını teyit ediyor, tarafların hâlâ
temiz olup olmadığını sormuyor.

Sonuç, bu incelemede bulunan **en ağır sonuçlu** boşluktur. Yanlış bir eşik
hesabı bir bildirim yükümlülüğünü etkiler; bu boşluk, işlemin
**tamamlanmasının hukuka uygun olup olmadığını** etkiler: imzada temiz olan
bir taraf izin beklenirken listeye girebilir ve işlem kapatılır.

Kitap burada iki şeyi de doğru yapıyor ve ikisi de olumlu kontrol olarak
tutuldu: *"eşleşmenin yokluğu temizlik kanıtı değildir"* ve *"tarama karar
değildir"* — gerçek bir adın taranması insan kararıdır ve makinenin dışında
yapılır (kural 6). *(AQ-01, AQ-02)*

→CEVAP: YOK — cevabın "yamalı hâlde sistem çalışıyor" cümlesi kapsıyor:
kontrol noktaları **dörde** çıkarıldı (kapanıştan hemen önce) ve
`kapanis-listesi`ne 0. adım olarak yaptırım yeniden taraması eklendi. Sorgu
soyutlama kuralı orada da mutlaktır ve tarama yine bir karar değildir —
eşleşme yetkili avukata gider.

## §9 · Beceriler

**[C] Beklenen değer bayat:** "10" yazıyor, §14 `once-arastir` ekleyince **11**
olur. *(E)*

**[C] Negatif sınır kuralı gösteriliyor ama söylenmiyor.** §9 haklı olarak
"yönlendirme yalnızca açıklama alanını okur" diyor ve tek işlenmiş örneğinde
("Türkiye dışındaki rekabet rejimleri için KULLANMA") negatif sınır kullanıyor
— ama bunu bir kural olarak yazmıyor. Kitabı izleyen biri kalan dokuz beceriyi
negatif sınırsız yazar ve yanlış yönlendirme kaçınılmaz olur. *(K-06)*

## §11 · Komutlar

**[A] `/esik-denetle` kendi vaadini tutamıyor: riski doğru adlandırıyor,
sonra yanlış dizini tarıyor.**
Komut gerekçesini kendi sözleriyle yazıyor — *"bir eşik değişikliği insan
kararıdır, çünkü **canlı bir dosyada verilmiş bir görüşü geçersiz
kılabilir**"* — ve kapanışı *"şu anda **hangi dosyalar** bayat bir rakama
dayanıyor"* diye bitiyor. Ama prosedürünün birinci adımı yalnızca
`birimler/*/yontem/` altını tarıyor. §2 kitabın kendi sözlüğünü kuruyor:
*"`dosyalar/` **canlı işleri** … tutar"*. Yani kapanış cümlesinin vaadi canlı
işler üzerinde; prosedür o dizini **hiç açmıyor**. Komut, doktrin
katmanındaki rakamın bayatladığını söyleyebilir; o rakama dayanarak
müvekkile ne söylendiğini söyleyemez.

İkinci yol da kapalı: `dosyalar/` kural 6 gereği `.gitignore`'dadır (Y-02),
yani sürüm geçmişinden de sorulamaz. *"Eşik değişti — hangi müvekkile artık
yanlış olan bir şey söyledik?"* sorusunun sistemde iki cevap yolu vardı ve
**ikisi de kapalıydı**. Bu, §2 maddesinin ikinci yüzüdür: gizlilik
mekanizması orada dayanıklılığı, burada geriye dönük erişimi feda ediyor.
*(AM-01, AM-03)*

→CEVAP: YOK — cevabın "yamalı hâlde sistem çalışıyor" cümlesi bunu kapsıyor:
tarama kapsamı komutun kendi vaadine eşitlendi (canlı iş katmanı eklendi,
ETKİLENEN ve SÜRÜMSÜZ işaretleri tanımlandı), "hiçbir dosyayı düzenleme"
kuralı aynen korundu ve tablonun makinede kalması kural 6 gereği açıkça
yazıldı. Kitaba sadık sürüm `yamalar/kitaba-sadik/esik-denetle.md`.

## §8 · Çıkar çatışması

**[A] Çatışma kontrolü tek yönlü ve yalnızca açılış anına bağlı.**
§8 tek cümledir: *"Bir dosya **açılmadan önce** `hafiza/cikar-catismasi.md`
**karşı taraflar için** kontrol edilir. Çatışma bir uyarı değil, durma
sebebidir."* `/dosya-ac` bunu birebir uyguluyor: *"verilen **karşı taraf**
adlarını ara."* İki bağ da sınanmamış:

**Yön.** Çatışma simetrik bir ilişkidir ve en ağır hâli tersidir: yeni
dosyanın **müvekkili**, açık bir dosyanın **karşı tarafı** olabilir — yani
şu anda aleyhine çalıştığımız kişi için çalışmaya başlarız. Kaydın kendi
biçimi (`<taraf adı> · <dosya> · <hangi tarafta> · <tarih>`) bu soruyu
cevaplayacak veriyi **zaten taşıyor**; prosedür hiç sormuyor.

**Zaman.** Kontrol açılış anına bağlı. Kayda sonradan bir ad girdiğinde
çatışma **o an doğar** ve hiçbir şey geriye bakmıyor. Otuz birinci turdaki
eşik sorusunun ("mevzuat değişti, verilmiş görüşe ne oluyor") çıkar
çatışması ayağındaki hâli — ve aynı kök: kitap kontrolleri **olaylara**
değil **anlara** bağlıyor.

Kitap iki şeyi doğru yapıyor ve bunlar olumlu kontrol olarak tutuldu: boş
kayıt "temiz" sayılmıyor, ve eşleşme uyarı değil durma sebebi. §18.9 de
sınırı dürüstçe beyan ediyor ("bu dosya yalnızca içine yazıldığı kadar
iyidir") — ama o sınır **açıklanmamış ilişkilere** dairdir; yön ve zaman
boşluğu açıklanmış ilişkilerde bile açıktır. *(AO-02, AO-03)*

→CEVAP: YOK — cevabın "yamalı hâlde sistem çalışıyor" cümlesi kapsıyor:
kontrol iki yönlü hâle getirildi ve kayda taraf işlendiğinde açık dosyaları
yeniden tarayan bir adım eklendi (bildirir, düzenlemez; tablo makinede
kalır). **Yama neyin çatışma SAYILDIĞINA karar vermez** — o bir meslek
kuralları meselesidir ve §9 uyarınca insana aittir; yalnızca mekanik
kontrolün iki yönü de kapsaması sağlandı.

## §12 · Kapılar — öz-sınamanın kapsama değişmezi yok

**[B] §12'nin öz-sınaması hiçbir yerde "her kapının bir vakası olmalı"
demiyor; §14 bu boşluğa düşüyor ve boşluk hâlâ açık.**
Raporun birinci bulgusu §14'ün beşinci kapıyı ekleyip §12'nin beklenen
kümelerini güncellememesidir. Ama o bir ÖRNEKTİR; **sınıf**, öz-sınamanın
kapsama değişmezinin hiç olmamasıdır. Bir kapı eklendiğinde hiçbir şey
"bunun vakası nerede?" diye sormuyor, ve öz-sınama eski vaka sayısıyla
"SELFTEST OK" demeye devam ediyor.

Bu maddenin kanıtı bu incelemenin kendisidir: otuz altıncı turda **yedinci
kapıyı ben ekledim ve öz-sınamaya tek bir vaka yazmadım.** Öz-sınama
"SELFTEST OK (20 vaka)" demeye devam etti — kapı eklenmeden önce de 20
diyordu. Kırk bir takımın hiçbiri görmedi, çünkü görecek bir ölçüt yoktu.
**Kitabın merkezî kusurunu, kitabı yamalarken tekrar ettim.** *(AS-01)*

→CEVAP: YOK — cevabın "yamalı hâlde sistem çalışıyor" cümlesi kapsıyor:
yedinci kapı için dört yönlü öz-sınama vakası eklendi (sessizlik ateşler,
onay kaydı susturur, taslak beyanı susturur, içeride hiç ateşlemez) ve
AS-01 artık `denetle()`'nin çağırdığı **her** kapının öz-sınamada beklenen
olarak geçtiğini her koşumda sorar. Örnek değil, sınıf kapatıldı.

## §12 · Kapılar — onay ihtiyacının beyanı, onayın kendisi değildir

**[A] §9 "adı belli bir insan onaylamadan kullanılmaz" diyor; hiçbir kapı
onay durumuna bakmıyor.**
§12'nin kapsam kapısı *"Yetkili avukat görüşü gereken konular"* başlığının
varlığını arıyor. Ama o başlık bir onay **kaydı** değil, onay
**ihtiyacının beyanıdır** — tam tersi. Ölçüldü: müvekkile giden, başlığı
usulünce taşıyan, hiçbir onay kaydı olmayan bir metin dışarı giden yolda
**hiçbir kapıya takılmıyor.**

Kitap onay verecek kişinin **adını** kaydediyor (`dosya-ac`'ın KAPSAM.md
şablonunda "İnsan onayı verecek kişi"). Yani sistem **kimin onaylayacağını**
biliyor; **onayladığını** hiçbir yerde kaydetmiyor. §9'un saydığı dört çıktı
türü — müvekkile ya da karşı tarafa gidecek her şey, her başvuru metni,
yönetim kuruluna sunulacak her rakam, süreye bağlı bir adımda dayanılacak
her Türk hukuku beyanı — bu boşluğun tam ortasında duruyor. *(AR-01, AR-02)*

→CEVAP: YOK — cevabın "yamalı hâlde sistem çalışıyor" cümlesi kapsıyor:
**yedinci kapı** eklendi. Kuralı dikkatle seçildi: kusur onayın *yokluğu*
değil, onay durumu hakkındaki **sessizliktir**. Bir taslak taslak olduğunu
söyleyebilir, bir inceleme onaylanmadığını yazabilir (bu raporun kendisi
öyle yapıyor); yasak olan, onaylanmış gibi görünen sessizliktir. Kapı ya bir
onay kaydı (`Onay: <ad soyad> · <YYYY-AA-GG>`) ya da açık bir durum beyanı
(`TASLAK` / `onaylanmamıştır`) ister.

## §12 · Kapılar — sır kapısının görmediği yol

**[A] Sır kapısı müvekkil ADINI arıyor ama müvekkil DOSYA YOLUNU görmüyor.**
§12'nin sır kapısı üç kalıba ve bir ad kaydına bakıyor: işlem kod adı,
şirket unvanı (`A.Ş.`, `Ltd. Şti.` ekleriyle) ve işlem bedeli. Ama §2
kurulumun ikinci adımında `dosyalar/` dizinini kuruyor ve §9'un `dosya-ac`
becerisi her iş için `dosyalar/<ad>/` klasörünü **müvekkilin/hedefin adıyla**
açıyor; çıktılar da `dosyalar/<ad>/cikti/` altına yazılıyor. Yani sıradan bir
oturum, doğal olarak şu biçimde metin üretir:

    dosyalar/Acme-Gida-devralma/cikti/esik-notu.md

Bu yol **tanımı gereği müvekkil kimliğidir** — §2 sözlüğünde `dosyalar/`
canlı işleri tutar — ama kapının hiçbir kalıbına uymaz: ASCII'ye katlanmış,
tirelenmiş, `A.Ş.` eki yok ve ad kaydında böyle yazılmıyor. Ölçüldü:
`disari=True` ile gönderilen böyle bir satırda **hiçbir kapı ateşlemiyordu.**

Bulgu, otuz birinci turun yamasının kabul sınamasında ortaya çıktı: yama
`/esik-denetle`ye satırları dosya adlarını taşıyan bir tablo ekliyor ve
"bu tablo makinede kalır" diyor. O cümlenin kapıya sorulması gerekiyordu —
soruldu, kapı görmüyordu. **Ama boşluk yamanın açtığı bir boşluk değil;
yamadan önce de oradaydı ve kitabın kendi klasör düzeninden doğuyor.**
*(AN-05)*

→CEVAP: YOK — cevabın "yamalı hâlde sistem çalışıyor" cümlesi kapsıyor:
kapıya somut canlı iş yolu kuralı eklendi. Yer tutucular (`dosyalar/`,
`dosyalar/*/`, `dosyalar/<is>/`) ateşlemez — belgeler ve kitabın kendi metni
onları kullanır; yalnızca somut bir ad ateşler. Otuz yedi takımın hiçbirinde
yanlış pozitif üretmedi.

## §12 · Kapılar

**[A] Öz-sınama üretim yolunu koşturmuyor.** Öz-sınama fonksiyona ham dize
veriyor; kanca `json.dumps(tool_input)` veriyor ve bu, satır sonlarını iki
karakterlik `\n` dizisine çevirir. Satır başı çapası olan her desen iki yolda
farklı davranır. **Bir kapının öz-sınaması, kapının gerçekte çalıştığı yolda
koşmalıdır.** *(C-10)*
→CEVAP: 1

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

## §13 · Depolar — katalog kurulumda hiç yok

**[A] §13'ün bütün araç kararları yalnızca KİTAPTA yaşıyor; kurulum hiçbir
katalog bırakmıyor.**
§13 altı depo için lisans, yıldız, son güncelleme ve bir **Karar** yazıyor
("Kullan", "Lisans kararı verilmeden kurulmaz", "Yöntemi için okunur") ve
"Hepsi 27 Ağustos 2026 tarihinde GitHub API'siyle doğrulandı" diyor. Ama §2
kurulumu yalnızca `birimler`, `emsal`, `hafiza`, `dosyalar`, `cikti`
klasörlerini açıyor ve hiçbiri araç kataloğu için değil. Kurulumu yapan
hukukçunun elinde:

* hangi aracın incelendiğine dair **yerel bir kayıt yok**,
* eskiyecek bir **doğrulama tarihi yok**,
* §16 denetiminin ya da herhangi bir komutun bakabileceği **bir şey yok**.

Karar yazılı, kararın dayandığı olgular bozuluyor ve ikisi arasındaki bağ
kurulumda hiç yok. Bu, otuz üçüncü turda adlandırılan kökün üçüncü örneğidir
— *kitap kontrolleri olaylara değil anlara bağlıyor* — bir farkla: burada
kontrol **kurulmuyor bile**. *(AP-01)*

→CEVAP: YOK — cevabın "yamalı hâlde sistem çalışıyor" cümlesi kapsıyor:
`hafiza/arac-katalogu.md` kuruldu. Her satır BİZİM doğrulama tarihimizi
taşır — kitabın beyan ettiği tarih bizim doğrulamamız sayılmaz — ve
doğrulanmamış bir satır "temiz" değil **kontrol edilmedi** demektir (§14'ün
ikinci tuzağı). Bir katalog satırını değiştirmek bir araç kararını
değiştirebileceği için dosya kendiliğinden düzenlenmez; §9 uyarınca insana
sorulur.

**[A] Tazeleme becerisi, kararı değiştiren iki alanı hiç okumuyor.**
§14'ün `once-arastir` becerisi GitHub API'sinden dört alan okuyor:
`full_name`, `license.spdx_id`, `stargazers_count`, `pushed_at`.

* **`archived` yok.** `pushed_at` bir vekildir, olgu değil. Salt okunur bir
  depo hata düzeltmesi de güvenlik yaması da almaz. Ölçüldü: §13.4'ün
  `google/diff-match-patch` için yazdığı *"eskime burada bozulma değildir"*
  gerekçesi, deponun **5 Ağustos 2024'te arşivlendiği bilinmeden**
  yazılmıştır. Kitabın kendi tazeleme aracı çalıştırılsaydı bile bunu
  göremezdi.
* **Veri lisansı yok.** API'nin `license` alanı yalnızca KOD lisansını
  döndürür. `opensanctions` kodu MIT iken **verisi CC BY-NC 4.0'dır ve
  ticari kullanıma kapalıdır** — kitap bu aracı ticari bir hukuk pratiği
  için öneriyor. Tek "Lisans" sütunu bu ayrımı yapısal olarak taşıyamaz.

*(AP-02, AP-03)*

→CEVAP: YOK — cevabın "yamalı hâlde sistem çalışıyor" cümlesi kapsıyor:
`once-arastir` beş alanı okuyacak ve veri lisansını kod lisansından ayrı
soracak biçimde genişletildi.

→CEVAP: YOK — cevabın "yamalı hâlde sistem çalışıyor" cümlesi kapsıyor:
`hafiza/arac-katalogu.md` kuruldu (her satır BİZİM doğrulama tarihimizi
taşır; kitabın beyanı bizim doğrulamamız sayılmaz ve doğrulanmamış satır
"temiz" değil "kontrol edilmedi" demektir), ve `once-arastir` beş alanı
okuyup veri lisansını ayrıca soracak biçimde genişletildi. Bir katalog
satırını değiştirmek bir araç kararını değiştirebileceği için dosya
kendiliğinden düzenlenmez; §9 uyarınca insana sorulur.

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

## §18 · Bilerek yapılmayanlar

**[B] §18.6 sınırı FAZLA DAR yazılmış: katalogda iki AGPL depo var, bir
değil.** Kitap "üç sözleşme çözümleme deposundan ikisi bakımsızdır, **biri**
AGPL-3.0'dır" diyor ve §13.4'teki `lexpredict-lexnlp`'yi kastediyor. Ama
§13.5'teki `freelawproject/courtlistener` de **AGPL-3.0-or-later**'dır ve kitap
ona "açık (depoya bakın)" diyor (G-01). Yani katalog iki AGPL bağımlılık
taşıyor ve §18 birini sayıyor.
Neden önemli: §18 kitabın DÜRÜSTLÜK bölümüdür ve gerekçesini kendisi yazar —
*"sınırı ilk bulan kişi onu bir müvekkilin karşısında bulur."* Fazla dar
yazılmış bir sınır, o bölümün var olma sebebini ortadan kaldırır: okuyucu
sınırın kapsadığından fazlasına güvenir.
→ §18.6 "katalogda iki AGPL bağımlılık vardır ve ikisi de asıl sahibin
kararını ister" biçiminde yazılmalı; §13.5'in lisans satırı düzeltilmeli.
*(T-06, G-01)*

**[C] §18'in dokuz maddesinin dokuzu da OLUMSUZ İDDİADIR** ("yapmaz",
"yoktur", "kanıt yoktur") ve kitabın kendi §2'si olumsuz iddiadan olumludan
YÜKSEK kanıt ister. Kitap yalnızca yedinci ve sekizinci maddeleri §17 ile
kanıtlıyor; kalan yedisi için kanıt sunmuyor.
→ §18'in her maddesi, onu doğrulayan mekanizmaya ya da kayda işaret etmeli.
*(T-01…T-10)*

## §14 · Önce araştır

**[A] `^Kontrol edildi:` çapası üretimde asla eşleşmez.** JSON'da gerçek satır
sonu yoktur. Kapı, eşik rakamı ya da GitHub adresi içeren her yazmayı
bloklar — kitabın kendi §5.1 dosyası dâhil. *(C-01…C-03, C-10)*
→CEVAP: 1


**[A] Yeni kapı eklenirken §12'nin dokuz beklenen kümesi güncellenmiyor.**
İkisi eşik rakamı içerdiği ve "Kontrol edildi" satırı taşımadığı için yeni kapı
onlarda ateşliyor: `SELFTEST HATA 2`. Zincir: §14 kırmızı → §16 kırmızı →
§0'ın dördüncü kuralı kurulumu durduruyor → §19 hiç çalışmıyor.
**Kitabın kendi talimatları izlendiğinde yeşil denetim üretilemiyor.** *(E)*
→CEVAP: 1

**[C] Belgelenen biçim, kapının reddettiği biçim.** `once-arastir` çıktı
satırını dört boşluk girintili gösteriyor; `^Kontrol edildi:` sütun sıfır
istiyor. *(B-33)*

**[C] `once-arastir` §0'ın çıktı sözleşmesini taşımıyor.** §0 "her esaslı
çıktı iki başlıkla biter" der; kitabın verdiği `once-arastir` gövdesi ikisini de
adlandırmaz. Kusur DEĞİL sayıldı — beceri bir araştırma notu üretir, müvekkile
giden bir teslim değil — ama bu bir kanaat olarak bırakılmadı: muafiyet
`beklenen.json` yerine sınamanın içinde BEYAN edildi ve U-11 muafiyeti
kapının kendisiyle sınıyor (belgelenen çıktı biçimi kapsam kapısına verilir;
kapı susarsa muafiyet doğrudur). *(U-10, U-11)*

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
→CEVAP: 3

**[C] Denetim kendi yol çözümlemesini denetlemiyor.** §16 betiği yolları
`~/mafirm` olarak sabitliyor. Sonuç: betik BAŞKA bir ağaca kopyalandığında
kendi ağacını değil, makinedeki kurulumu ölçer — ve bu, "iki kopya aynı sonucu
veriyor" karşılaştırmasıyla **yapısal olarak görülemez**, çünkü her iki ağaç da
diskteyken sonuçlar zaten aynı çıkar.
→ Kök, betiğin kendi konumundan çözülmeli (`BASH_SOURCE`, `__file__`) ve bir
ortam değişkeniyle geçersiz kılınabilmeli; gömülü Python parçacıkları da o
kökü kabuktan devralmalı. Denetim, kaynak ağaç YOKKEN de yeşil olmalı.
*(S-01, S-02)*

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
→CEVAP: 1


**[A] Ve asıl mesele:** §19 "bu iki cevabın arasındaki fark, kurulumun
tamamının sebebidir" diyor. Ölçüldü — kitaba sadık kapılarda **doğru cevap da
yanlış cevap da bloklanıyor**. Kapı sistemi, kurulumun sebebi olarak gösterilen
farkı ifade edemiyor. *(J-07s, J-08s)*

---
→CEVAP: 2

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
