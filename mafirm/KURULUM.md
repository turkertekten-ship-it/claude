# Kurulum kaydı — ne kuruldu, ne doğrulandı, nerede kitaptan ayrıldı

Kurulum tarihi: 2026-08-27. Kaynak: *Uluslararası M&A Hukuku · Kurulum Kitabı*,
Arel Barzilay, Sürüm 1.0.

Kontrol edildi: kitabın tamamı §0–§19 (2026-08-27) · web araması ile 2026/2
sayılı Tebliğ (2026-08-27) · PyPI ve npm kayıtları (2026-08-27) · `git
ls-remote` ve sığ klon ile depo çözümlemesi (2026-08-27) · bu makinedeki gerçek
`import` ve çalıştırma denemeleri (2026-08-27) · bulunamayan: api.github.com,
resmigazete.gov.tr, mevzuat.gov.tr, rekabet.gov.tr, spk.gov.tr, huggingface.co,
openaipublic.blob.core.windows.net — hepsi ağ çıkışı politikasıyla engelli.

## §0 · Açılış talimatı

Kitabın §0'daki rol talimatı bu kurulumun sözleşmesidir ve olduğu gibi
uygulanmıştır: her bölüm ya bir dosya üretti ya bir dosyayı doğruladı,
doğrulaması başarısız olan bir bölümden ileri geçilmedi ve §16 denetimi sonda
çalıştırıldı.

## Nereye kuruldu

Kitap `~/mafirm` diyor. Sistem depo içinde `mafirm/` altında durur ve
`~/mafirm` oraya bir sembolik bağdır. Böylece kitaptaki her doğrulama komutu
birebir çalışır ve aynı zamanda her şey sürüm kontrolündedir.

`.claude/` neden depo kökünde değil: kökteki bir `settings.json`, bu depoda
çalışan her oturuma bloklayan bir kanca takardı. Kapılar pratiğin klasöründe
BLOCK, makine genelinde WARN kipindedir (`kur-genel.sh`).

## Kitaptan ayrıldığı yerler — hepsi bilerek ve gerekçeli

Kitabın kendi güncellik ve kanıt kuralları bu ayrımları emreder.

### 1. Teknoloji teşebbüsü istisnası üç noktada düzeltildi

Kitap §5.1 istisnayı eksik anlatıyor. 2026/2 sayılı Tebliğ üzerine yayımlanmış
uygulamacı çözümlemeleri şunu gösterdi:

| Konu | Kitap | Doğrulanan |
|---|---|---|
| Kapsam | "Türkiye'de faaliyet gösteren ya da AR-GE yürüten" | Türkiye'de **yerleşik** |
| Birleşme ayağı | yok | taraflardan **en az biri** yerleşik teknoloji teşebbüsü ise |
| Ciro tabanı | teşebbüsün cirosu | yalnızca **teknoloji alanı** cirosu |

Kitabın ölçütü fazla kapsayıcıdır: gereksiz bildirim üretir. Düzeltme
`birimler/rekabet/yontem/tr-esikler.md` ve `kod/esik.py` içinde işaretlidir.
`esik.py` kitabın altı sınama vakasını **olduğu gibi** korur ve doğrulamanın
eklediği beş vakayla on bire çıkar.

### 2. Yıldız sayıları yazılmadı

Kitap §13 her depo için yıldız veriyor. api.github.com bu oturumda kapalı;
yıldızlar kitaptan kopyalanabilirdi, kopyalanmadı. Yerine **çözümlenebilirlik**
ve **son commit tarihi** doğrulandı — ikisi de bakım sorusunu yıldızdan iyi
cevaplar. Ayrıntı: `birimler/_araclar/katalog.md`.

### 3. Üç depo tarihi kitapta yanlıştı

| Depo | Kitap | Gerçek |
|---|---|---|
| google/diff-match-patch | 2024-05-22 | **2019-07-25** |
| LexPredict/lexpredict-lexnlp | 2024-05-27 | **2023-03-06** |
| ICLRandD/Blackstone | 2024-07-16 | **2021-01-31** |

Üçü de gerçekte daha eski. Kitabın §13.4 kararları bundan zayıflamaz,
güçlenir: Blackstone "iki yıldır" değil beş buçuk yıldır bakımsızdır.

### 4. §14 kapısı, §12'nin iki sınama vakasını değiştirir

`kapi_arastirma` eklendiğinde, dayanağı olan ama "Kontrol edildi:" satırı
olmayan bir eşik cümlesi de ateşler. Kitabın §12'deki iki vakasının beklenen
sonucu bu yüzden güncellendi ve sebebi kodda yazılıdır: **dayanak** rakamın
NEREDEN geldiğini, **Kontrol edildi** NE ZAMAN bakıldığını kanıtlar. Güncellik
kuralı ikincisini de ister.

Kitap §14'te "yedi vaka — üçü ateşlemeli, dördü susmalı" diyor; saydığı yedi
vakanın ise biri ateşler, altısı susar. Sayım kitapta tutarsızdır. Uygulanan
küme on yedi vakadır: yedi ateşleyen, on susan, her kapı iki yönde sınanmış.

### 5. Sayımlar kitaptakinden yüksek

| Bileşen | Kitap | Kurulan | Neden |
|---|---|---|---|
| Beceri | 10 | 12 | §14 `once-arastir` + `token-verimliligi` |
| Yöntem dosyası | 6 | 10 | her birimin denetimden geçmesi için |
| Sınama vakası (eşik) | 6 | 11 | doğrulamanın eklediği vakalar |
| Sınama vakası (kapı) | 9→16 | 17 | bkz. yukarıda |

### 6. Kitapta olmayan iki katman eklendi

- **Token verimliliği** (`token-verimliligi` becerisi + `token-butce.py`).
  Uzun bir SPA'yı bağlama sokmanın maliyeti gerçektir ve ölçülmeden
  yönetilemez. Kırpmanın hukuki bir karar olduğu kuralı yazılıdır.
- **İş akışları** (`isakislari/`). Beceri, komut ve alt ajanları uçtan uca
  zincirler.

## Ortam kısıtları — dürüstçe

Bu makinede şunlar **doğrulanamadı** ve hiçbiri doğrulanmış gibi yazılmadı:

- Türk mevzuatının birincil metinleri (Resmî Gazete, mevzuat.gov.tr,
  rekabet.gov.tr, spk.gov.tr erişilemiyor). Madde numaraları ve oranlar
  ikincil kaynaklardan ve kitaptan alınmıştır; her yöntem dosyası bunu yazar.
- Kıdem tazminatı tavanı. `is-hukuku` dosyasına **hiçbir rakam yazılmamıştır**;
  "eşik doğrulanamadı" ibaresi yerindedir.
- GitHub yıldız sayıları.
- tiktoken sözlüğü — `token-butce.py` bu yüzden TAHMİN kipine düşer ve bunu
  çıktısının başına yazar.

## Depoya yükleme: çalıştırma biti

Bu oturumda `git push` için kimlik bilgisi yok; yükleme GitHub API'si üzerinden
yapıldı. API'nin dosya yükleme ucu **çalıştırma bitini taşımaz**: yereldeki
`100755` betikler depoda `100644` görünür. İçerik birebir aynıdır.

Bu sistemde hiçbir çağrı çalıştırma bitine bağlı değildir — her betik
`python3 <dosya>` ya da `bash <dosya>` olarak çağrılır ve öyle belgelenmiştir.
Depoyu klonlayıp `./denetim.sh` yazmak isteyen biri için:

    chmod +x ~/mafirm/denetim.sh ~/mafirm/kur-genel.sh \
             ~/mafirm/birimler/*/kod/*.py ~/mafirm/.claude/hooks/kapi.py

## Kapılarda bulunan iki kusur

Kurulumdan sonra bütün pratik kendi kapılarından geçirildi (her dosya bir
Write olayı olarak `kapi.py`'ye verildi). İki kusur çıktı; ikisi de kitabın
kendi uyarısının canlı örneğidir: doğru işi bloklayan bir kapı bir gün içinde
kapatılır ve ondan sonra hiçbir şey uygulanmaz.

1. **`arastirma` kapısı KARŞILANAMIYORDU.** `KONTROL` deseni `^` ile satır
   başına bakıyordu; oysa kanca `tool_input`un JSON hâlini görür ve orada
   gerçek yeni satır yoktur, `\n` kaçışlıdır. Dosyanın ortasındaki
   "Kontrol edildi:" satırı hiçbir zaman görülmüyordu — yani kapı, satırı
   taşıyan doğru dosyaları da bloklyordu. Desen artık her iki biçimi tanır.
2. **`guncellik` kapısı kendi kaynak dosyasını bloklyordu.** `kapi.py`'nin
   sınama vektöründeki 2020-01-01 tarihi, belgenin kendi tarihi sanılıyordu.
   Bir belgenin etkin doğrulama tarihi artık taşıdığı EN YENİ tarihtir.

Sınamaya, kancanın gerçekte gördüğü biçim (JSON'a gömülü içerik) eklendi.
Bu vakalar olmadan, hiçbir zaman karşılanamayan bir kapı sınamayı geçiyor
görünüyordu.

## Kitapta olmayan iki denetim eklendi

- **İç yönlendirme** (`_araclar/kod/yonlendirme.py`). Sistem sürekli
  yönlendirir; bir dosya yeniden adlandırıldığında bu yönlendirmeler sessizce
  kırılır ve baskı altındaki bir hukukçuyu çıkmaza gönderir. Betik her iç
  yolu, beceri adını, alt ajan adını ve slash komutunu gerçek dosya sistemine
  karşı çözer.
- **Eşik özellik sınaması** (`rekabet/kod/esik-ozellik.py`). `--self-test` on
  bir seçilmiş vakayı sınar; seçen kişi neyi düşünmediyse orada boşluk kalır.
  Özellik sınaması vakayı değil kuralı sınar: sınır katılığı, sıra
  bağımsızlığı, monotonluk ve en sessiz kusur — teknoloji istisnası kapsamı
  ASLA daraltmamalıdır, aksi hâlde gereken bir bildirim yapılmaz.

Her iki denetleyici de iki yönde sınandı: kasten kırık girdi verildiğinde
yakaladılar, geri alındığında sustular.

## Yükleme sırasında on bir sessiz bozulma

Depoya yükleme GitHub API'si üzerinden yapıldı ve içerik elle kopyalandı. Bu
yolda **on bir tek karakterlik bozulma** oluştu ve hepsi Türkçeye özgüydü:

    boşalttığı -> boşaltığı     (ikiz ünsüz düştü)
    liradır    -> liradir       (noktasız ı yerine noktalı i)
    SİLİNECEK  -> SİlenECEK
    araca      -> araça         (fazladan çengel)
    hatanın    -> haltanın
    daraltıldı -> daraldı
    koşuluna   -> koşuna

Bunların bir kısmı alt ajanlar tarafından, bir kısmı kurulumu yürüten
tarafından yapıldı — yani dikkat, bu kusuru sıfırlamıyor. Sonucu doğru kılan
şey dikkat değil, **byte-eş karşılaştırma ve yeniden deneme döngüsüdür**:
yerel dosya ile uzak dosya `git diff` ile karşılaştırıldı ve fark kalmayana
kadar tekrarlandı.

Bir `description:` satırındaki tek harf, bir becerinin ne zaman devreye
gireceğini değiştirir; bir mevzuat cümlesindeki tek harf daha kötüsünü yapar.
Bu yüzden bu iş gözle değil karşılaştırmayla bitirilir.

## Kurulum sırasında yakalanan üç gerçek kusur

1. **`pdfplumber` kuruluydu ama import edilemiyordu** — Debian'ın
   `cryptography` paketi `_cffi_backend` olmadan geliyordu. Kitabın §13'teki
   "kontrol pip list satırı değil bir import'tur" kuralının canlı kanıtı.
2. **`token.py` stdlib'deki `token` modülünü gölgeliyordu** ve `tokenize`
   üzerinden neredeyse her import'u kırıyordu. `token-butce.py` olarak
   yeniden adlandırıldı.
3. **PyPI'daki `repomix` gerçek repomix değil.** GitHub bağlantısı yok; gerçek
   olan npm paketidir (`yamadashy/repomix`). Kitabın §14'te uyardığı "kayıt adı
   depo adı olmayabilir" tuzağının bu kurulumdaki örneği.

## İkinci tur: web ve GitHub derinlemesine (2026-08-28)

İlk kurulumda "doğrulanamadı" diye bırakılan her kalem yeniden ele alındı.

**GitHub.** `api.github.com` hâlâ kapalı, ama GitHub **depo arama** uç noktası
çalışıyor. On beş deponun yıldızı, lisansı ve son güncellemesi canlı çekildi.
Sonuç: **kitabın yıldız sayıları esasen doğruydu**, sapma normal büyüme
kadar — yanlış olan tarihlerdi. İki yeni bulgu: `google/diff-match-patch`
**arşivlenmiş** bir depodur (kitap yalnızca "eski" diyor) ve
`great-expectations/great_expectations` adı artık hiç çözülmüyor, yalnızca
`fivetran/great_expectations` çözülüyor.

**Web.** Türk mevzuatı atıflarının tamamı çapraz doğrulandı ve **dört hata**
bulundu; en ağırı bekletici şartın yanlış maddeye bağlanmasıydı. Ayrıntı ve
tam liste `SINIRLAR.md` sınır 10'dadır.

**En sonuçlu düzeltme.** Bekletici şart 4054 m.11'de değil, **4054 m.10 ve
2010/4 sayılı Tebliğ m.10**'dadır; m.11 hiç bildirilmemiş işlemi düzenler.
Yanlış atıf dokuz dosyaya yayılmıştı ve on sekiz yerde düzeltildi. Bir kurum
yazışmasında yanlış madde numarası vermek, rakamı yanlış vermekle aynı
sınıftadır.

## Şimdi ne yapılmalı

`bash ~/mafirm/denetim.sh` yeşil dönmeli. Sonra §19'daki ilk dosya bir kez
çalıştırılır. Altı ay dolmadan `/esik-denetle` ile her eşik yeniden çekilir.

## Yetkili avukat görüşü gereken konular

Bu sistemdeki **her** Türk hukuku ifadesi — hiçbiri birincil kaynaktan teyit
edilemedi. Ayrıca: AGPL lisanslı bir bileşenin kurulup kurulmayacağı, kıdem
tazminatı tavanının güncel değeri ve teknoloji teşebbüsü istisnasının somut bir
işlemde uygulanıp uygulanmadığı.
