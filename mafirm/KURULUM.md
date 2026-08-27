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

## Şimdi ne yapılmalı

`bash ~/mafirm/denetim.sh` yeşil dönmeli. Sonra §19'daki ilk dosya bir kez
çalıştırılır. Altı ay dolmadan `/esik-denetle` ile her eşik yeniden çekilir.

## Yetkili avukat görüşü gereken konular

Bu sistemdeki **her** Türk hukuku ifadesi — hiçbiri birincil kaynaktan teyit
edilemedi. Ayrıca: AGPL lisanslı bir bileşenin kurulup kurulmayacağı, kıdem
tazminatı tavanının güncel değeri ve teknoloji teşebbüsü istisnasının somut bir
işlemde uygulanıp uygulanmadığı.
