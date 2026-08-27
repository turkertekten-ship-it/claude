# Kör sınama raporu · Uluslararası M&A Hukuku Kurulum Kitabı

Sürüm 1.0 · 2026-08-27 · OODA döngüsü: gözlem → yönelim → karar → eylem → döngü

## Yöntem

Kitap baştan sona, **kelimesi kelimesine** kuruldu: on dokuz bölüm, sekiz
uzmanlık birimi, on beş koltuk, on bir beceri, beş alt ajan, dokuz komut, dört
komut kütüphanesi dosyası, beş kapı, denetim betiği. Hiçbir bölüm "bağlam gibi
göründüğü için" atlanmadı; kitabın kendi kalite çubuğu uygulandı (§0
`<kalite_cubugu>`): her bileşen tam yazıldı, "örnek olarak" deyip kesilmedi.

Sonra **kör sınama** yapıldı. Kör olmasının tanımı şu: her vaka kitabın
DÜZYAZISINDAN türetildi, kodundan değil. Kitabın kendi öz-sınamaları
(esik.py'de altı vaka, kapi.py'de on altı) desenleri yazan kişinin aklındaki
vakalardır ve hepsi geçer. Kör sınama o aklın dışında kalanı arar: bir
hukukçunun gerçekten yazacağı cümleyi, kancanın gerçekten göreceği veriyi,
bozulduğunda denetimin gerçekten yakalayıp yakalamadığını.

Dokuz takım, 96 vaka:

| Takım | Neyi sınar | Kaynağı |
|---|---|---|
| A | Rekabet eşiği mantığı | `tr-esikler.md` düzyazısı |
| B | Beş kapı, on bir doktrin kuralına karşı | `CLAUDE.md` düzyazısı |
| C | **Üretim yolu** — gerçek kanca JSON'u, gerçek çıkış kodu | Kanca sözleşmesi |
| D | **Mutasyon sınaması** — sistemi bozup denetimin yakalayıp yakalamadığı | §16 |
| E | Kitabın doğrulama komutları vs kitabın beklenen değerleri | §3–§16 |
| F | Doktrin kapsama matrisi | §12'nin kendi iddiası |
| G | §13 deposu — 16 depo bağımsız yeniden çözüldü | GitHub API |
| H | §17 kaynakları — dört akademik çalışma | Yayıncı kayıtları |
| I | §5 mevzuatı — eşikler ve madde numaraları | Birincil kaynak (denendi) |

**Sonuç: 85 vaka koşuldu, 56'sı kaldı.** Yamadan sonra 96 vaka, 11 kaldı.

---

## Bir · Kurulum kendi denetimini geçemiyor

Kitaba sadık, eksiksiz kurulumda §16'nın denetimi kırmızı dönüyor.

Sebep zinciri tek bir yerde başlıyor. §12 dört kapı kuruyor ve dokuz vakalık
bir öz-sınama veriyor; geçiyor. §14 beşinci kapıyı (`kapi_arastirma`) ekliyor
ve "_selftest şu yedi vakayla genişletilir" diyor. Yedi vaka ekleniyor —
**ama var olan dokuzun beklenen değerleri hiç güncellenmiyor.** İkisinde eşik
rakamı var ve "Kontrol edildi:" satırı yok; yeni kapı ikisinde de ateşliyor:

```
  HATA "Eşik, birleşik ciro için 3.000.000.000 TL'di" -> {'arastirma', 'kanit'}, beklenen {'kanit'}
  HATA '2010/4 sayılı Tebliğ eşiği 3.000.000.000 TL ' -> {'arastirma'}, beklenen {}
SELFTEST HATA 2
```

Bundan sonrası mekanik: §14'ün doğrulaması kırmızı → §16'nın "dört kapı"
kontrolü kırmızı → `DENETİM BAŞARISIZ: 1` → §0'ın dördüncü yöntem kuralı
("Doğrulaması başarısız olan bir bölümden ileri geçme") kurulumu durduruyor →
§19'daki ilk dosya hiç çalışmıyor.

Kitap §16'da şunu yazıyor: *"Kurulumun işe yaradığının tek kanıtı yeşil bir
denetimdir; bunu çalıştırmadan 'bitti' diyen bir kurulum hiçbir şey
söylememiştir."* Kitabın kendi talimatları izlendiğinde o kanıt üretilemiyor.

---

## İki · Beşinci kapı üretimde asla geçilemiyor (C-10)

Bu, raporun en önemli bulgusu ve yalnızca üretim yolunu sınayarak görülüyor.

`kapi_arastirma`, çıktının `^Kontrol edildi:` satırı taşımasını istiyor.
Öz-sınama fonksiyona ham Python dizesi veriyor ve `re.M` ile `^` gerçek satır
başına oturuyor: geçiyor. Gerçek kanca ise stdin'den JSON okuyor ve kitabın
kodu metni şöyle düzleştiriyor:

```python
metin = json.dumps(olay.get("tool_input", {}), ensure_ascii=False)
```

`json.dumps` gerçek satır sonlarını **iki karakterlik `\n` dizisine** çevirir.
`re.M` ile `^` artık yalnızca dizenin en başına, yani `{` karakterine denk
gelir. **`Kontrol edildi:` satırı üretimde asla eşleşmez.**

Ölçüldü — aynı metin, iki yol:

```
GEÇTİ C-10  AYNI metin: öz-sınama yolu vs üretim yolu
       öz-sınama=temiz (temiz), üretim=çıkış 2          << yamadan ÖNCE
```

Sonuç: eşik rakamı ya da GitHub adresi içeren **her** yazma işlemi bloklanıyor.
Kitabın kendi §5.1 dosyası bloklanıyor. Kitabın istediği tam biçimdeki bir
çıktı — dayanağı, tarihi, iki zorunlu başlığı ve "Kontrol edildi" satırı olan —
bloklanıyor:

```
KALDI C-02  kitabın istediği TAM biçimde bir çıktıyı dosyaya yazmak
       kapı iletisi: BLOKLANDI [arastirma] rakam ya da depo anıldı, Kontrol edildi satırı yok
```

Kitap bu tehlikeyi §12'de kendisi yazıyor: *"Doğru işi bloklayan bir kapı bir
gün içinde kapatılır; sonra hiçbir şey uygulanmaz."* Beşinci kapı tam olarak o
kapıdır.

İkinci bir örnek aynı yönde: `once-arastir` becerisi çıktı biçimini **dört
boşluk girintili** bir kod bloğu olarak belgeliyor. `^Kontrol edildi:` sütun
sıfır istiyor. Becerinin belgelediği biçim, kapının reddettiği biçim (B-33).

---

## Üç · Bash: en geniş sızıntı kanalı hiç izlenmiyor

Sır kuralı (CLAUDE.md §6) müvekkili tanıtan bilginin makineden çıkmasını
yasaklıyor. Kapı `disari` bayrağını şöyle hesaplıyor:

```python
disari = arac in ("WebSearch", "WebFetch") or arac.startswith("mcp__")
```

Bash yok. Ve `settings.json` matcher'ı `"WebSearch|WebFetch|Write|Edit"` —
**kanca Bash'te hiç çalışmıyor.** Oysa kitabın kendisi §14'te `curl` ile GitHub
API'sine gitmeyi, §2'de `git`i, §13'te `pip install`i ve üç dış aracı Bash
üzerinden öneriyor.

Ölçüldü:

```
KALDI C-05  kod adını curl ile dışarı taşımak         beklenen 2, gerçek 0
KALDI C-06  hedef unvanını dış API'ye göndermek       beklenen 2, gerçek 0
KALDI C-07  müvekkil belgesini uzak depoya itmek      beklenen 2, gerçek 0
KALDI C-09  matcher Bash'i kapsıyor mu                WebSearch|WebFetch|Write|Edit
```

Aynı kod adı `WebSearch` içinde bloklanıyor, `curl` içinde geçiyor.

---

## Dört · Denetim, boş bir sistemi onaylıyor

Bir denetimin değeri geçtiği şeyde değil, **yakaladığı** şeydedir. Sistem on
beş kez bozuldu ve her seferinde denetimin kırmızıya dönüp dönmediğine bakıldı.

**Kitaba sadık denetim: 15 mutasyondan 4'ünü yakaladı, 11'ini kaçırdı.**

`DENETİM OK` diyor: sıfır beceri, sıfır alt ajan, sıfır komut, sıfır komut
kütüphanesi dosyası, işaretsiz koltuklar, tek kurallık bir CLAUDE.md, sıfır
yöntem dosyası, çıkar çatışması dosyası yok, `settings.json` içinde kanca yok,
on beş koltuğun on üçü silinmiş — ve **`esik.py` tamamen boş.**

Üç mekanizma:

1. `ls ... | wc -l` boru hattının çıkış kodu daima `wc`'nindir: **0**. Dört
   bileşen kontrolü hiçbir koşulda başarısız olamaz.
2. Boş bir Python dosyası `--self-test` ile **0** döner. Eşik hesaplayıcısını
   doğrulayan kontrol, hesaplayıcı hiç yokken geçiyor.
3. `test -z "$(grep -rL ...)"` hiç dosya yokken boş döner ve **geçer**. İki
   "doktrin gerçekten uygulanıyor mu" kontrolü boş bir dizinde boşuna geçiyor.

Doğrulandı:

```
boş esik.py --self-test çıkış kodu: 0
ls /yok/olmayan/*.md | wc -l  ->  çıktı: 0   çıkış kodu: 0
test -z "$(grep -rL Doğrulama: bosdizin/*.md)" çıkış: 0 (GEÇTİ — hiç dosya yokken)
```

---

## Beş · Doktrinin dörtte üçünün mekanizması yok

§12 şunu iddia ediyor: *"Yukarıdaki her şey doktrindir ve doktrin, sistemin
baskı altında olmadığı zaman uyduğu şeydir. Aşağıdaki dört otomatik kontrol,
baskı altında uyduğu şeydir."*

İşletim sözleşmesinin on bir kuralı, onları uygulayan bir mekanizma olup
olmadığına göre sınıflandırıldı:

| Kural | Durum | Kanıt |
|---|---|---|
| 1 · Kanıt | KISMİ | 1M altı rakam, sözle yazılmış rakam, TRY, oran biçimi görünmüyor; dayanak belge düzeyinde ve "Tebliğ" kelimesiyle tatmin oluyor |
| 2 · Olumsuz iddia | **YOK** | "kariyer bitirir" denen üç cümlenin üçü de hiçbir kapıyı ateşlemiyor |
| 3 · Güncellik | KISMİ | Türkçe tarih biçimi, tarihsiz eşik, gelecek tarih görünmüyor |
| 4 · Yön | **YOK** | hiçbir kapı çıktı sırasına bakmıyor |
| 5 · Kapsam | KISMİ | sekiz sabit ifade dışındaki her tavsiye kipi geçiyor; büyük harfli başlık YANLIŞ POZİTİF üretiyor |
| 6 · Sır | KISMİ | Bash kapsanmıyor; büyük harfli/İngilizce kod adı, kısaltmasız unvan, kişi adı, fiyat görünmüyor |
| 7 · İki hukuk | **YOK** | — |
| 8 · Çıkar çatışması | **YOK** | dosya hiç oluşturulmuyor; yokluğu denetimden geçiyor |
| 9 · İnsan onayı | **YOK** | — |
| 10 · Dil | **YOK** | — |
| 11 · Önce araştır | **BOZUK** | üretimde çalışmıyor (bkz. İki) |

**Tam mekanizmalı: 0. Kısmi: 4. Bozuk: 1. Hiç kapsanmayan: 6.**

Buna iki kalem daha eklenir. §7 koltukların "o hukukçunun gerçekten yazdığına"
dayanmasını istiyor — bu, sistemin en yüksek itibar riskidir ve hiçbir kapı bir
koltuk dosyasının uydurma olup olmadığını kontrol etmez. §18'in dokuz açık
sınırının hiçbiri makinece kontrol edilmez.

---

## Altı · Eşik hesaplayıcısı, önlemek için var olduğu hatayı yapıyor

`esik.py`'nin gerekçesi kendi belgesinde yazılı: *"Bunu düzyazıda akıl
yürüterek çözmek, hatanın yapıldığı yerdir."* Sekiz kör vaka kaldı; ikisi
belirleyici.

**A-14 · Gerçek bir işlemi hesaplayacak arayüz yok.** §8 el kitabı
"`esik.py` gerçek ciro rakamlarıyla çalıştırılır" diyor; §9 becerisi ve §15.1
komutu aynısını istiyor. Ama `__main__` yalnızca `--self-test` tanıyor; başka
her çağrıda docstring basıyor. Yani kod, hesabı yapmak için değil yalnızca
kendini sınamak için çağrılabiliyor — **hesap zorunlu olarak kafadan
yapılıyor.** Kodun varlık sebebi buydu.

**A-07 · Para birimi modeli yok, ve bu kitabın kendi pilotunu ters çeviriyor.**
§19'un ilk dosyası: dünya cirosu **2,4 milyar avro** olan bir Alman alıcı,
Türkiye cirosu 1,4 milyar TL olan bir hedefi alıyor. B eşiği "diğer taraflardan
birinin dünya cirosunun **9.000.000.000 TL**'yi aşması" diyor — eşik TL
cinsinden. Rakam çevrilmeden verilirse:

```
KALDI A-07  §19 pilotu: 2,4 milyar AVRO çevrilmeden verilirse
        beklenen : bildirime tabi (B)
        gerçek   : TABİ DEĞİL — sessiz yanlış cevap
```

2.400.000.000 sayısı 9.000.000.000'ın altındadır. Cevap sessizce tersine
döner ve bu, kitabın §19'da "doğru cevap" diye tarif ettiğinin tam tersidir.
Kitap çevirinin gerektiğini biliyor ("avro rakamı TL'ye çevrilir ve hangi kurun
kullanıldığı yazılır") ama kod bunu ne istiyor ne kontrol ediyor.

Kalanlar: bilinmeyen ciro `0` girilince "hayır" çıkıyor — oysa beceri üç
değerli cevap istiyor (**belirlenemiyor**) ve CLAUDE.md §2 olumsuz iddiayı
yasaklıyor (A-10); `None` verilince `TypeError` (A-11); negatif ciro sessizce
kabul (A-12); hedef kendi dünya cirosuyla B ayağını karşılayabiliyor (A-13);
aynı işlem iki bağlantısız biçimde giriliyor ve hedefin cirosunu A ayağına
yazmayı unutmak bildirimi sessizce yok ediyor (A-09); birleşme/devralma ayrımı
modellenmiyor (A-15).

---

## Yedi · Dış kaynaklar: kanal başarısız, içerik büyük ölçüde sağlam

### §13 · Depolar — 16/16 çözüldü
Hiçbir depo uydurma değil. Dört maddi bulgu:
- **courtlistener lisansı yanlış.** Kitap "açık (depoya bakın)"; gerçek
  **AGPL-3.0-or-later**. §13.7 tam da bu soruyu sorup PyMuPDF'i AGPL diye
  eliyor — aynı listede aynı lisanslı ikinci bir depo "açık" diye geçiyor.
- **diff-match-patch 2024-08-05'te arşivlendi**, kitap yazmıyor.
- **opensanctions verisi CC BY-NC 4.0** (kod MIT). NC = ticari kullanım dışı;
  bir hukuk bürosu ticari kuruluştur. §13.7'nin "asıl sahibin kararı"
  kategorisine giren bir lisans sorusu tabloda görünmüyor.
- **§14'ün önerdiği `curl https://api.github.com/...` komutu bu ortamda 403
  dönüyor.** Beceri, kendi belgelediği yöntemle çalıştırıldığında boş döner.

İki şüphem yanlış çıktı ve kitap haklı: `fivetran/great_expectations` ve
`Open-Source-Legal/OpenContracts` kanonik yollardır; benim hatırladığım yollar
onlara yönleniyor.

### §17 · Akademik kaynaklar — künye sağlam, aktarım hatalı
DOI, dergi, cilt, sayı, yıl, yazarlar, tasarım, örneklem, görev listesi, kol
yapısı: hepsi doğru. **Kitabın savını taşıyan dört olumsuz bulgunun dördü de
doğrulandı**, akıl yürütme modelinin insan kontrol kolundan daha fazla
uydurduğu (11'e 4) dâhil. Üç aktarım hatası:
- Süre düşüşü aralıkları (%20–28 / %20–34) hiçbir kaynakla uyuşmuyor; bulunan
  her kaynak %14–37 / %12–28 diyor ve geniş aralığı ters kola veriyor.
- **+0,26 puan bir karıştırma:** o rakam iki AI kolu ARASINDAKİ farktır,
  erişim destekli kolun kontrol grubuna karşı etkisi değil (o 0,25'tir).
- **"%19 daha düşük" → "19 YÜZDE PUANI daha düşük."** Mevcut ifade, kitabın
  kanıtlamak için alıntıladığı riski küçültüyor.

§17.2'nin çıkarımı da olgudan fazlasını söylüyor: 11'e 4 ham sayıdır, bu bir
ürün karşılaştırmasıdır (mekanizma değil), "en yetenekli" kol doğrulukta üstün
DEĞİLDİ ve yazarların kendi okuması erişim ile akıl yürütmeyi ödünleşim değil
tamamlayıcı sayıyor. Çalışma bir otomatik kapıyı hiç sınamadı.

### §5 · Mevzuat — üç bulgu, ikisi bildirime tabiliği değiştirir
**Bu ortamda hiçbir birincil kaynağa erişilemedi**: `mevzuat.gov.tr`,
`resmigazete.gov.tr`, `rekabet.gov.tr`, `spk.gov.tr` — hepsi reddedildi.
Aşağıdakiler desteklenmiş yeniden kurgudur, birincil doğrulama değildir. (Kanalın
güvenilmezliği ölçüldü: aynı SPK eşiği için dört sorguda %50, %90 ve %98 döndü.)

- **I-01 · Teknoloji istisnası yalnızca B ayağında olmayabilir.** Güncel
  m.7(2), indirimi (a) VE (b) bentlerine uyguluyor görünüyor. Doğruysa: A
  ayağında Türkiye'de yerleşik bir teknoloji hedefinin 250M–1Mr TL cirosu kendi
  ayağını karşılar; kitabın "tabi değil" saydığı işlem tabidir → **izinsiz
  kapanış maruziyeti.**
- **I-02 · Bağlantı ölçütü bayat.** Kitaptaki "faaliyet gösteren ya da Ar-Ge
  yapan" 2022/2'nin kalkmış ölçütü; güncel ölçüt "Türkiye'de yerleşik". Ters
  yönde hata: gerekmeyen bildirimler.
- **I-03 · Bekletici etkinin madde numarası yanlış.** Kitap dört yerde
  4054 m.11 diyor; m.11 "bildirilmemenin sonuçları"dır, bekletici kural
  m.10'dadır (+m.7/2). Esas doğru, atıf kuralın kendisini değil yaptırımını
  gösteriyor.

Ve şüphem yine yanlış çıktı: teknoloji istisnasının "aranmaz" biçiminde
işlediğini sanıyordum; o **2022/2'nin** kuralıydı ve 11 Şubat 2026'da aşıldı.
Kitabın çekirdek tarifi (indirim) doğru.

Bu üç bulgu **yamalanmadı.** Bir eşik değişikliği insan kararıdır (§11) ve kanıt
katmanı zayıftır. `hafiza/dogrulama-bulgulari.md` içinde açık bırakıldılar ve
`denetim.sh` her koşuda bildiriyor.

---

## Sekiz · Kitabın kendi beklenen değerleri bayatlıyor

| Bölüm | Beklenen | Gerçek | Sebep |
|---|---|---|---|
| §4 | 8 | **9** | §7 `_koltuklar/` ekliyor |
| §9 | 10 | **11** | §14 `once-arastir` becerisini ekliyor |
| §12/§14 | SELFTEST OK | **HATA 2** | §14 beşinci kapıyı ekliyor, dokuz beklenen kümeyi güncellemiyor |
| §16 | DENETİM OK | **BAŞARISIZ** | yukarıdakinin sonucu |

Ayrıca §3'ün "11" beklentisi §14'ün 11. kuralı yeniden yazdırmasına duyarlıdır:
metin eklenirse 12 olur ve **hiçbir kontrol buna bakmaz**.

---

## Dokuz · Kör sınamanın kendi hataları

Bir sınama takımı da sınanmalıdır. Üç hata yapıldı ve üçü de düzeltildi:

1. **Mutasyon sınaması ilk koşumda geçersizdi.** Taban çizgisi zaten kırmızıydı
   (§14 arızası), dolayısıyla her mutasyon sıfırdan farklı dönüyordu ve
   "15/15 yakalandı" ölçümü anlamsızdı. Kontrollü taban çizgisiyle yeniden
   koşuldu: gerçek sonuç 4/15.
2. **Kum havuzu yönlendirmesi sessizce koptu.** Yamalı `denetim.sh`
   `M="$HOME/mafirm"` kullanıyor; `sed` literal `~/mafirm` arıyordu. Mutasyonlar
   kum havuzuna uygulanırken denetim ASIL kurulumu ölçüyordu. Yönlendirmenin
   tuttuğunu doğrulayan bir kontrol eklendi.
3. **İki mevzuat/depo şüphem yanlıştı** (G-06, I-06). Kitap her ikisinde de
   haklıydı; benim hatırladığım bayattı. Kitabın kendi §14 kuralının kanıtı:
   *"bir ad, var olduğunun kanıtı değildir"* kadar *"hatırladığın ad, doğru ad
   değildir"* de geçerli.

---

## On · Yamadan sonra

Her yama, kapattığı vakanın kimliğiyle işaretli (`yamalar/DEGISIKLIKLER.md`).
Kitaba sadık sürümler `yamalar/kitaba-sadik/` altında duruyor.

| Takım | Önce | Sonra |
|---|---|---|
| A · eşik mantığı | 8 kaldı | 7 kaldı (**bilerek** — eski API'nin kaydı) + 9 yeni vaka geçti |
| B · beş kapı | 24 kaldı | **1 kaldı** (boş ad kaydı) |
| C · üretim yolu | 9 kaldı | **temiz** |
| D · mutasyon | 11 kaçtı | **temiz — 15/15 yakalandı** |
| E · beklenen değerler | 4 kaldı | 3 kaldı (kitabın kendi değerleri) |

Mühendislik katmanı yeşil: `denetim.sh --yapisal` → `DENETİM OK`.
Tam denetim kırmızı: `denetim.sh` → `DENETİM BAŞARISIZ: 3` — üç ENGELLEYİCİ
mevzuat bulgusu, birincil kaynak açılana kadar açık.

**Bu doğru davranıştır.** Bir eşiğin doğruluğu kod düzeltmesiyle kapatılamaz.

---

## Sonuç

Kitap iyi bir kitap. Doktrini sağlam, olumsuz kanıtı dürüstçe yazıyor (§17.1,
§18), Türk hukukçu ve vergi koltuklarını bilerek boş bırakıyor, kaynaklarını
gerçekten okumuş ve on altı deponun on altısı da gerçek.

Kusuru tek bir cümlede toplanıyor ve o cümleyi kitap kendisi yazmış:

> *"Her kapı iki yönde de sınanır: kusurlu vakada ateşlemeli, doğru vakada
> susmalı. Yalnızca geçen bir kapı, kapı değildir."*

Kitap bu ilkeyi biliyor ama **kendi öz-sınamalarını, kapıların gerçekte
çalıştığı yolda koşturmuyor.** Öz-sınama ham dize görüyor, üretim JSON görüyor;
öz-sınama sekiz sabit ifadeyi görüyor, hukukçu yüzlerce kip yazıyor; denetim
dosya sayıyor, `wc` çıkış kodunu yutuyor. Üç boşluğun üçü de aynı kökten: bir
sınamanın kendisi sınanmadan güvence sayılmış.

Aynı kitap §17.1'de bunun ölçülmüş karşılığını da veriyor: en yetenekli kol, en
çok uyduran koldu. Bir sistemin kendinden emin olması, doğru olmasıyla aynı şey
değildir — ve bu, kitabın kurduğu sistem için de geçerlidir.

---

### Nasıl yeniden koşulur
```
~/mafirm/sinama/hepsi.sh          # dokuz takım, 96 vaka
~/mafirm/denetim.sh --yapisal     # mühendislik katmanı
~/mafirm/denetim.sh               # mevzuat bulguları dâhil
```
Ham çıktılar: `sinama/SONUC-once.txt` (kitaba sadık) ve
`sinama/SONUC-sonra.txt` (yamalı). Dış doğrulamalar: `sinama/ks_g_depolar.md`,
`ks_h_kaynaklar.md`, `ks_i_mevzuat.md`.
