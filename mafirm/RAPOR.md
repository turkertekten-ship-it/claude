# Kör sınama raporu · Uluslararası M&A Hukuku Kurulum Kitabı

> **Doğrulama: 2026-08-28 · Bozulma sınıfı: KURULUMA BAĞLI**
>
> Bulgular, sınandıkları kurulum için geçerlidir. Kitabın metni ya da
> kurulum değişirse `sinama/hepsi.sh` yeniden koşulmalıdır: 0 SİNYAL,
> raporun hâlâ ölçtüğü sistemi anlattığının kanıtıdır.

Sürüm 1.0 · 2026-08-27 · OODA (gözlem → yönelim → karar → eylem → döngü) döngüsü

## Cevap

**Kitap iyi bir kitap ve harfiyen izlendiğinde çalışmıyor.** Kitaba sadık,
eksiksiz kurulumda 85 kör sınama vakasının 56'sı başarısız oldu ve kitabın
kendi §16 denetimi yeşile dönmedi.

Altı cümlede sebebi:

1. **§14, §12'nin öz-sınamasını bozuyor** ve düzeltilmiyor; zincir §16'yı
   kırmızıya, §0'ın dördüncü kuralını da kurulumu durdurmaya götürüyor. §19'daki
   ilk dosya hiç çalışmıyor.
2. **Kapılar biçimi denetliyor, muhakemeyi değil** — ve kitaba sadık hâlleriyle
   §19'un DOĞRU cevabını da YANLIŞ cevabını da bloklıyorlar, yani §19'un
   "kurulumun tamamının sebebi" dediği farkı ifade edemiyorlar.
3. **Denetim on beş bozmadan on birini görmüyor**; sıfır beceri, kancasız
   ayarlar ve tamamen boş bir `esik.py` taşıyan bir sistemde "DENETİM OK" diyor.
4. **Sır kuralı, kapının bakmadığı yerlerden sızıyor.** §12'nin sır kapısı
   metni denetler; ama §2 kurulumu bir **sürüm deposu** yapar ve canlı iş
   dosyalarını dışlamaz (`git push` veriyi makineden çıkarır — kural 6'nın
   yasakladığı şey), kancadaki her **çökme** kapıyı sessizce AÇIK bırakır
   (2 dışında her çıkış kodu "bloklamayan hata"dır), ve web yetkisi olan
   ajanın metninde sorgu sınırı yoktur. Üçü de §12'nin dışında kalır.
5. **Kitabı ikinci kez izlemek her yamayı geri alır** — denetim betiği dâhil.
   Denetçiyi ezmek, denetçinin yapacağı bütün kontrolleri devre dışı bırakır
   ve uygulayıcı korumasız bir sisteme **yeşil** bir denetimle bakar.
6. **Gizlilik ile dayanıklılık §2'de aynı mekanizmadır**, dolayısıyla biri
   seçilince öteki feda edilir — ve kitap bunu söylemez. §2 tek adımda hem
   `git init` (kitabın tek geri alma aracı) hem `.gitignore` (tek gizlilik
   aracı) kurar. Kural 6, müvekkil kimliği taşıyan her yolu `.gitignore`'a
   girmeye zorlar; o yol o anda **kurtarılamaz** hâle gelir. Oysa `hafiza/`
   klasörünün §2'de yazılı varlık sebebi "oturumdan sağ çıkan tespitleri
   tutmak", yani dayanıklılığın kendisidir. Ölçüldü: bu dosyalardan birini
   yerinde yeniden yazan sıradan bir araç öldürüldüğünde içerik gitti,
   `git checkout` ile dönülemedi — ve `denetim.sh` geriye kalan artığı
   "1 ad" sayıp *"kural 6'nın gerçek kişi ayağı kapsanmıyor"* uyarısını
   sustur du: koruma bozulurken alarm da kapandı.

**Yamalı hâlde sistem çalışıyor:** elli iki çalıştırılabilir takım — **387
vaka, 27 mutasyon, 12 bağımlılık doğrulaması, 0 sinyal**;
denetimin mutasyon yakalaması 4/15 → 15/15 → **27/27** (mutasyon kümesi otuz
sekizinci turda on beşten yirmi yediye çıkarıldı: 26 kontrolün dokuzu hiç
sınanmıyordu), birimler arası tutarlılık takımının
kendi mutasyon yakalaması 10/10. Ama **üç mevzuat bulgusu ile kitabın kendi içindeki bir çelişki açık kalır**
ve bunlar kod düzeltmesiyle kapanmaz: ikisi bir işlemin bildirime tabi olup olmadığını değiştirir ve
birincil kaynak erişimi olan bir insan gerektirir; dördüncüsü (§6'nın koşul
listesi ile §5.3'ün pay devri anlatısı arasındaki çelişki) bir hukuki
nitelendirmedir ve §9 uyarınca kitabın düzyazısı aynen bırakılmıştır —
önerilen düzeltme kum havuzunda gösterildi.

**Bu rapor hukuki görüş değildir ve adı belli bir insan tarafından
onaylanmamıştır** (işletim sözleşmesi §9). Mevzuat katmanı birincil kaynakla
doğrulanamadı; gerekçesi `hafiza/egress-kaniti.md` içinde kanıtlıdır.
Ayrıntı için aşağı inin; yöntem en sonda.


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
başına oturuyor: geçiyor. Gerçek kanca ise stdin'den JSON (programlar arasında veri taşıyan
metin biçimi) okuyor ve kitabın
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
API'sine (bir programın başka programlara açtığı erişim arayüzü) gitmeyi, §2'de `git`i, §13'te `pip install`i ve üç dış aracı Bash
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

> Bu tablo **kitaba sadık** kurulumun ölçümüdür — kitabın verdiği hâl.
> Yamalı sistemin güncel ölçümü aşağıda, "Yamadan sonra" bölümünde ve her
> koşumda `sinama/ks_f_kapsama.py` çıktısında.

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
Türkiye cirosu 1,4 milyar TL olan bir hedefi alıyor. 2010/4 sayılı Tebliğ'i
değiştiren 2026/2 sayılı Tebliğ'in B eşiği (kitapta yazıldığı hâliyle; bkz.
I-01/I-02 çekinceleri) "diğer taraflardan birinin dünya cirosunun
**9.000.000.000 TL**'yi aşması" diyor — eşik TL cinsinden. Rakam çevrilmeden verilirse:

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
  **AGPL** (ağ üzerinden hizmet verse bile kullanıcıya kendi kaynak kodunu
açmayı zorunlu kılan bulaşıcı açık kaynak lisansı) **3.0 veya sonrası**. §13.7 tam da bu soruyu sorup PyMuPDF'i AGPL diye
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
DOI (bir akademik yayının kalıcı kimlik numarası), dergi, cilt, sayı, yıl, yazarlar, tasarım, örneklem, görev listesi, kol
yapısı: hepsi doğru. **Kitabın savını taşıyan dört olumsuz bulgunun dördü de
doğrulandı**, akıl yürütme modelinin insan kontrol kolundan daha fazla
uydurduğu (11'e 4) dâhil. Üç aktarım hatası:
- Süre düşüşü aralıkları (%20–28 / %20–34) hiçbir kaynakla uyuşmuyor; bulunan
  her kaynak %14–37 / %12–28 diyor ve geniş aralığı ters kola veriyor
  (H-03; ayrıntı `sinama/ks_h_kaynaklar.md`).
- **+0,26 puan bir karıştırma:** o rakam iki AI kolu ARASINDAKİ farktır,
  erişim destekli kolun kontrol grubuna karşı etkisi değil (o 0,25'tir).
- **"%19 daha düşük" → "19 YÜZDE PUANI daha düşük."** Mevcut ifade, kitabın
  kanıtlamak için alıntıladığı riski küçültüyor.

§17.2'nin çıkarımı da olgudan fazlasını söylüyor: 11'e 4 ham sayıdır, bu bir
ürün karşılaştırmasıdır (mekanizma değil), "en yetenekli" kol doğrulukta üstün
DEĞİLDİ ve yazarların kendi okuması erişim ile akıl yürütmeyi ödünleşim değil
tamamlayıcı sayıyor. Çalışma bir otomatik kapıyı hiç sınamadı.

### §5 · Mevzuat — üç bulgu, ikisi bildirime tabiliği değiştirir
**Bu oturumda dört Türk birincil kaynağı alan adına HTTPS (şifreli web bağlantısı
protokolü), kuruluş
egress politikasıyla CONNECT (bir vekil üzerinden şifreli bağlantı açma isteği; ret,
bağlantı kurulmadan önce orada verildi) aşamasında 403 ile reddedildi** (kanıt: `hafiza/egress-kaniti.md`): `mevzuat.gov.tr`,
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

## Yedi buçuk · §19: kitabın kendi kabul sınaması

§19, kitabın son kapısıdır ve şunu söyler: *"Doğru cevap neye benzer: esik.py
çalıştırılır, avro rakamı TL'ye çevrilir… Yanlış cevap neye benzer: kod çıktısı
ve tarih olmadan kendinden emin bir 'evet'. **Bu iki cevabın arasındaki fark,
kurulumun tamamının sebebidir.**"*

Bu ölçülebilir bir iddiadır. İki cevap da üretilip beş kapıdan geçirildi.

| | Doğru cevap | Yanlış cevap |
|---|---|---|
| **Kitaba sadık kapılar** | **BLOKLANDI** `[arastirma]` | BLOKLANDI `[arastirma, kanit, kapsam]` |
| **Yamalı kapılar** | geçer (0) | BLOKLANDI `[arastirma, guncellik, kanit, kapsam]` |

Kitaba sadık sistemde **her ikisi de bloklanıyor.** Kapı sistemi, §19'un
"kurulumun tamamının sebebi" dediği farkı ifade edemiyor: eşik rakamı içeren
her şeyi durduruyor. Kaynak: J-07s ve J-08s vakalarının
çıkış kodları — duyarlılık %100, isabet %0.

Pilot ayrıca **hiç hesaplanamıyor**: `esik.py`'nin komut satırı arayüzü yok,
avro çevirisi modellenmemiş, ve §14 sonrası öz-sınama kırmızı olduğu için §0'ın
kuralına göre buraya zaten hiç gelinmiyor.

### Ve kapıların göremediği şey

Töreni eksiksiz ama **rakamı yanlış** bir cevap — dayanağı, tarihi, iki başlığı
ve "Kontrol edildi" satırı olan, ama eşiği ters okuyan — **altı kapıdan da
geçiyor** (J-09).

Bu bir kusur değil bir sınırdır ve yazılması gerekir: kapılar **biçimi**
denetler, **muhakemeyi** değil. Kitabın kendi §17.1 bulgusu tam olarak budur —
kazanç açıklıkta, düzende ve profesyonellikte; **doğrulukta değil.** Doğruluğu
sağlayan şey kapılar değil, yetkili avukat onayıdır.

---

## Yedi çeyrek · Yönlendirme ve koltuk sağlaması

Hiçbir kapının bakmadığı katman. On beş vaka; ikisi kitabın metnine ait:

- **§9 negatif sınır kuralını gösteriyor ama söylemiyor.** Tek işlenmiş
  örneğinde ("Türkiye dışındaki rekabet rejimleri için KULLANMA") kullanıyor,
  kural olarak yazmıyor. Kitabı izleyen biri kalan on beceriyi negatif sınırsız
  yazar — ve §9'un kendi uyarısına göre yönlendirme yalnızca o alanı okur.
- **§7'nin koltuk kuralının hiçbir mekanizması yok.** *"Bir koltuğun ağzına, o
  kişinin belgelenmiş görüşüyle çelişen bir söz asla konmaz."* Bu, sistemin en
  yüksek itibar riskidir — yaşayan, adı belli bir hukukçu söz konusudur — ve
  onu uygulayan tek şey iyi niyetti. §12'nin kendi uyarısı buraya düşüyor.

Kapatıldı: **altıncı kapı** eklendi. Beyansız bir koltuk dosyası bloklanıyor
(K-14), yöntem dosyaları etkilenmiyor (K-15), denetim de kontrol ediyor.

---

## Yedi buçuk artı · Referans bütünlüğü ve iki canlı kusur

Üçüncü tur, kapatıldı sanılan iki şeyin canlı kaldığını gösterdi.

**Taşınabilirlik düzeltmem bir regresyon bıraktı.** İki belge — `rekabet-esigi`
becerisi ve `denetim` komutu — hâlâ `~/mafirm` yolunu sabitliyordu. Yani bir
klonun becerisi, modele KENDİ ağacını değil makinedeki kurulumu çalıştırmasını
söylüyordu. Betikleri taşınabilir yapmak yetmiyor; onlara işaret eden belgeler
de taşınabilir olmalı.

**Eski API'nin sessizliği belgelenmişti ama kapatılmamıştı.** `bildirilmeli()`
hâlâ çağrılabiliyordu ve §19 pilotunda hiçbir uyarı olmadan
`(False, 'hiçbir eşik')` döndürüyordu. Bir kusuru belgelemek, onu kaldırmaz:
kod canlı kaldığı sürece biri onu çağırır. Artık iki uyarı veriyor — biri
kullanımdan kaldırma, biri de **olası birim hatası**: devre konu taraf eşiği
aşarken "diğer dünya cirosu" eşiğin hemen altında kalıyorsa, bu tipik olarak
çevrilmemiş bir yabancı para tutarıdır. Uyarı iki yönde sınandı: §19 pilotunda
ateşliyor, meşru bir TL işleminde susuyor.

---

## Yedi buçuk artı iki · I-03'ün kanıt katmanı yükseldi

Alt ajan birincil kaynağa ulaşamamıştı. Kendim iki bağımsız arama yaptım ve
düzenleyicinin kendi alan adında şunu doğruladım: **madde 10** ön inceleme, on
beş günlük süre, işlemin askıya alınması ve bildirimden otuz gün sonra zımni
geçerlilik mekanizmasını taşıyor; **madde 11** ise bildirilmeme hâlini
düzenliyor. Kitabın atfı yanlış.

Yine de statü **ENGELLEYİCİ kalıyor**: kanunun birebir metni
(`mevzuat.gov.tr/MevzuatMetin/1.5.4054.pdf`) egress ile engelli ve madde
başlığı okunamadı. Karar, kitabın kendi §11 kuralına uygun: **atıf
değiştirilmedi**, ama CLAUDE.md §1'in emrettiği gibi **yerinde işaretlendi** —
dört dosyanın dördünde de `DOĞRULANAMADI` ibaresi, ne olduğunu ve nereye
bakılacağını söyleyerek duruyor.

Aynı işlem I-01 ve I-02 için de yapıldı ve **denetime yeni bir kontrol
eklendi**: her ENGELLEYİCİ bulgunun adı geçen dosyalarda, **bulguyu adıyla
anan** bir işaret bulunmak zorunda. Böylece bulgu kaydı bir not olmaktan çıkıp
uygulanan bir mekanizma oldu. İki yönde sınandı.

---

## Yedi buçuk artı üç · Raporun kendisi kanıt kuralına tabi

Bu rapor kitaba kırk bir düzeltme öneriyor. Bir düzeltme önerisi, arkasında onu
gösteren çalışan bir sınama yoksa **bir kanaattir, bir bulgu değildir** — ve
kitabın kendi kanıt kuralı (CLAUDE.md §1) tam olarak bunu yasaklıyor:
*"Dayanağı olmayan bir eşik yazılmaz."* Aynı ölçüt rapora uygulandı.

M takımı dört soru soruyor: her madde bir vakaya atıf yapıyor mu; atıf yapılan
her kimlik gerçekten TANIMLI mı (uydurma dayanak var mı); ağır maddelerin
atıfları kitaba sadık sistemde gerçekten başarısız oldu mu; ve ters yönde —
sadık sistemde kalan her vaka açıklanmış mı.

İlk koşumda dördün üçü kaldı. **Üç başarısızlığın ikisi M'nin kendi
kusuruydu**: ayrıştırıcı aralık biçimindeki atıfları (`B-07…B-09`) görmüyordu
ve dinamik kurulan kimlikleri (`"J-07%s" % etiket`) tanıyamıyordu; bu yüzden
yedi maddeyi "atıfsız" ve yedi kimliği "uydurma" sanıyordu.

Ama arkalarında **üç gerçek kusur** vardı:

1. **Sır kapısının ikinci kusuru errata'da hiç yoktu.** Kanal sorununu (Bash)
   yazmıştım; **desen darlığını** yazmamıştım. İkisi ayrı kusurdur ve kanal
   düzeltilse bile desen kusuru kalır: büyük harfli kod adı, İngilizce kod adı,
   kısaltmasız unvan, gerçek kişi adı ve **fiyat** görünmüyor — oysa CLAUDE.md
   §6 fiyatı açıkça sayıyor. Beş başarısız vaka (B-25…B-29) hiçbir errata
   maddesine bağlı değildi. Eklendi.
2. **İki errata maddesi hiçbir vakaya atıf yapmıyordu** (§16'nın "denetimin
   bakmadığı şeyler" listesi ve §19'un pilot maddesi). Bağlandı.
3. **`ks_a_esik.py` içinde ölü bir kod yapısı vardı**: `vaka("A-15" if False
   else "A-14", ...)`. Çalışıyordu ama A-14 kimliğini statik olarak
   bulunamaz kılıyordu. Temizlendi. Ayrıca errata'nın `J-01` atfı belirsizdi;
   gerçek kimlik `J-01s`.

Şimdi dördü de geçiyor: kırk bir maddenin kırk biri gerçek bir vakaya bağlı,
uydurma dayanak yok, ağır maddelerin hepsi sadık sistemde gerçekten kaldı ve
kalan kırk bir vakanın hepsi açıklanmış. Denetime kalıcı bir kontrol eklendi —
bir errata maddesinin atfı silinirse denetim kırmızıya dönüyor.

---

## Yedi buçuk artı dört · Raporun kendi olumsuz iddiası kanıtsızdı

İşletim sözleşmesi §2 bu sistemdeki en sert kuraldır: *"Olumsuz bir iddia,
olumludan daha yüksek bir kanıt eşiği ister… ancak o yükümlülüğü getirecek olan
hükmü göstererek ve nereye bakıldığını söyleyerek yazılır."*

Kural kitabın çıktısı için yazıldı. Ama **bu rapor da bir çıktıdır** ve şu
olumsuz iddiayı taşıyordu: *"Bu ortamda hiçbir birincil kaynağa erişilemedi."*
Dört tur boyunca o iddia yalnızca **iki araç hatasına** dayanıyordu. Yani rapor,
kitapta bulduğu kusurun aynısını yapıyordu.

Eksik olan üç şey vardı ve üçü de yapılabilirdi:

1. **Ortamın kendi belgesini hiç okumamıştım.** `/root/.ccr/README.md`, 403'ün
   ne anlama geldiğini tanımlıyor: *"The destination host is not allowed by your
   organization's egress policy… Do not retry or route around it — report the
   blocked host."* Yani red geçici bir arıza değil, bir politika kararı — ve
   doğru davranış onu aşmak değil, bildirmek.
2. **Bash + curl kanalını hiç denememiştim.** WebFetch'i hukuk kaynaklarına,
   curl'ü GitHub'a denemiştim; curl'ü hukuk kaynaklarına hiç denemedim. Dördü
   de `CONNECT tunnel failed, response 403` (CONNECT: vekil üzerinden şifreli bağlantı açma isteği; 403 orada reddedildi) verdi.
3. **Vekilin kendi kaydını hiç sormamıştım.** `__agentproxy/status` uç noktası
   dört reddi zaman damgasıyla ve host adıyla kaydediyor.

Şimdi iddia kesin biçimde yazılı ve `hafiza/egress-kaniti.md` içinde
kanıtlanıyor:

```
connect_rejected  www.mevzuat.gov.tr:443     gateway answered 403 to CONNECT
connect_rejected  www.rekabet.gov.tr:443     gateway answered 403 to CONNECT
connect_rejected  www.resmigazete.gov.tr:443 gateway answered 403 to CONNECT
connect_rejected  www.spk.gov.tr:443         gateway answered 403 to CONNECT
```

N takımı sekiz vakayla bunu denetliyor — ve iki kaçamağı özellikle kapatıyor:
**çalışan kanal da yazılmalı** (WebSearch çalışıyor; döndürdüğü şey sayfa metni
değil arama motoru özeti) ve **iddia fazla geniş yazılmamalı** ("hiçbir şeye
erişilemedi" yanlış olurdu; GitHub MCP (modele dış araç bağlamayı
standartlaştıran protokol) ile on altı depo çözüldü).

Bu kanıt üç mevzuat bulgusunu **çözmüyor**. Yalnızca neden çözülemediğini
doğrulanabilir kılıyor — ve N-08 raporun bunu çözdüğünü iddia etmediğini
denetliyor.

---

## Yedi buçuk artı beş · Takımın kendi sinyali bozuktu

Beş tur boyunca her koşum "13 kaldı" dedi ve ben her seferinde "on üçünün
tamamı hesaplı" diye kapattım. Bu, **kitabın D takımında bulunan kusurun
aynadaki hâliydi.**

Kitabın denetimi HEP YEŞİLDİ — on beş bozmadan on birini fark etmiyordu, yani
yeşil hiçbir şey söylemiyordu. Benim takımım HEP 13-KIRMIZIYDI — ve sabit bir
kırmızı da hiçbir şey söylemez. Yedi vaka her koşumda kırmızı olduğu için
okuyucu kırmızıyı görmezden gelmeyi öğrenir. İkisi de aynı kusurdur: **bilgi
taşımayan bir sinyal.**

Ölçüldü. Daha önce yamalanmış bir kusuru (B-10, Türkçe küçük harf) yeniden
enjekte ettim:

```
  toplam başarısız vaka               14        << 13'tü, 14 oldu
```

Hepsi bu. Hangi vakanın yeni olduğunu takım söylemiyor; bir insan bunu fark
etmek için önceki koşumu hatırlamak ya da diff almak zorunda.

### Beyan edilmiş taban

`sinama/beklenen.json` bilinen ve gerekçeli her sapmayı **beyan eder** — her
biri sınıfı ve nedeniyle. Üç durum ayrılır:

| | anlamı | sinyal mi |
|---|---|---|
| **BEKLENEN** | beyan edilmiş, hâlâ başarısız | hayır |
| **KALDI** | beyan EDİLMEMİŞ başarısızlık — regresyon | **evet** |
| **BEKLENMEDİK GEÇİŞ** | beyan edilmiş ama artık geçiyor — beyan bayat ya da sınama çürüdü | **evet** |

Aynı regresyon yeniden enjekte edildiğinde artık şöyle görünüyor:

```
  B · beş kapı / on bir kural         1 SİNYAL
  TOPLAM SİNYAL                         1
  SİNYAL VAR: ya beyan edilmemiş bir başarısızlık (regresyon), ya da
  beyanlı olup artık GEÇEN bir vaka (beyan bayat / sınama çürüdü).
```

İki yön de sınandı: bir regresyon sinyal üretiyor, ve geçen bir vakayı
"başarısız" diye beyan etmek de sinyal üretiyor (C-10 ile denendi).
Taban eşleşmesinde takım **0 SİNYAL** ile yeşil.

### Ve bunu denetime bağlamak özyineleme üretti

Denetime "takım tabanla eşleşiyor mu" kontrolü eklemeyi denedim: denetim →
`hepsi.sh` → D takımı (denetimin mutasyon sınaması) → denetim → … Koşum yüz
yirmi saniyede bitmedi. **Denetimi denetleyen takımı denetimin kendisi
çağıramaz** — bir katman ihlali. Kontrol kaldırıldı ve yerine gerekçesi
yazıldı; taban eşleşmesi `hepsi.sh`'in kendi çıkış kodudur ve orada kalır.

---

## Yedi buçuk artı altı · Kapı, düzyazının biçimine güveniyordu

B takımındaki her vaka bir hukukçunun gerçekten **yazacağı** cümleydi. Ama sır
kapısı (§6) bir **güvenlik denetimidir** ve güvenlik denetimi yalnızca iyi
niyetli girdiyle sınanmaz. Bunu altı tur boyunca hiç sınamamıştım.

Ve bu kuramsal bir tehdit modeli değil: üç yüzeyin üçü de **kaza olarak
oluşur.** PDF (taşınabilir belge biçimi) ya da Word'den
kopyala yapıştır rutin olarak yumuşak tire,
sıfır genişlikli karakter ve ayrışmış aksan üretir. Bir müvekkil kod adı veri
odası belgesinden kopyalanıp bir web aramasına yapıştırıldığında kapının onu
görmesi gerekir. Görmüyordu:

| Yüzey | Örnek | Kapı |
|---|---|---|
| NFD ayrışması | `A.Ş.` → `A.S` + U+0327 | **kaçırdı** |
| Sıfır genişlikli boşluk | `Proje⁠<U+200B>Şahin` | **kaçırdı** |
| Homoglif | Kiril `о` ile `Prоje` | **kaçırdı** |

Kitabın §12'si zaten **aynı sınıftan** bir kusur taşıyordu ve ikinci turda
bulunmuştu: Python'un `İ`.lower() ayrışması. Kitap o kusuru düzeltmemişti;
ben düzelttim ama **sınıfı genellemedim** — tek bir örneği yamalayıp yüzeyin
tamamını sınamadım. Altı tur sonra döndüm.

Düzeltme yalnızca sır kapısında: biçim karakterlerini at, NFKC (Unicode'un uyumluluk normalleştirmesi: ayrışmış aksanları tek
karaktere indirger) ile birleştir,
dar bir homoglif tablosunu — Latin harfe görsel olarak eşdeğer Kiril/Yunan harfleri — Latin'e katla. Diğer kapılarda uygulanmadı — aşırı
normalleştirme yanlış pozitif üretir; ama **dışarı giden bir çağrıda fazla
bloklamak, az bloklamaktan güvenlidir.**

O takımı on yedi vaka: on iki kaçırma yüzeyi kapandı, **dört negatif kontrol**
kapının masum metinde, mevzuat metninde ve Türkçe aksanlı olağan cümlede
sustuğunu doğruluyor, ve bir vaka kapının kendi öz-sınamasının bozulmadığını
denetliyor.

---

## Yedi buçuk artı yedi · Eleştirdiğim şeyi ben daha kötü yapmışım

§13'ü G-05 ile eleştirdim: *"tek bir doğrulama tarihi taşıyan bir tablo,
kontrol edilmiş gibi durur."* Sonra `ks_g_depolar.md`'yi — içeriği baştan sona
yıldız sayısı ve lisans durumu olan bir tabloyu — **hiç tarih taşımadan**
teslim ettim. Eleştirdiğim şeyden kötüsü.

Ve yalnızca o değil: yedi teslimatın **yedisi de** tarihsizdi. RAPOR.md,
KITAP-ERRATA.md, üç dış doğrulama dosyası, egress kanıtı ve bulgu kaydı.
İşletim sözleşmesi §3 açık: *"Bu sistemdeki HER eşik, doğrulandığı tarihi
taşır."*

### Ama düz "altı ay" kuralı bu teslimatlar için yanlış ölçüt

Bir yıldız sayısı altı ay değil **bir gün** dayanır. Bir yayımlanmış makalenin
künyesi **yıllarca** dayanır. Bir egress politikası **yalnızca o oturum** için
geçerlidir. Tek bir eşiğe sıkıştırmak, en hızlı bozulanı en yavaşıyla aynı
güvenilirlikte gösterir — kitabın §13'te yaptığı hatanın ta kendisi.

Her teslimat artık bir tarih **ve bir bozulma sınıfı** taşıyor:

| Sınıf | Ömür | Örnek |
|---|---|---|
| GÜNLÜK | 1 gün | yıldız sayıları (`ks_g_depolar.md`) |
| OTURUM | o oturum | egress kanıtı |
| ALTI AY | 183 gün | mevzuat doğrulaması |
| YILLIK | 365 gün | akademik künye |
| KURULUMA / KİTAP SÜRÜMÜNE BAĞLI | olaya bağlı | rapor, errata |

### Ve kuralın gereği "hep taze olmak" değil

Taze kalmak imkânsızdır ve altıncı turdaki "hep kırmızı" kusurunu üretir.
Gereği şudur: **bayatlamış bir teslimat, bayatladığını söyler.** P-03 tam olarak
bunu denetliyor — şu anda iki teslimat sınıfına göre bayat ve ikisi de bunu
kendi başlığında yazıyor. Uyarısı silinirse P-05 yakalıyor.

---

## Yedi buçuk artı sekiz · Sistem kendi raporunu reddediyordu

Sekiz tur boyunca kitabın kapılarını sertleştirdim. Dokuzuncu turda o kapıları
kendi raporuma tuttum:

```
RAPOR.md  [kapsam] görüş gibi okunuyor, avukat başlığı yok
```

Kapı haklıydı. Bu rapor Türk hukuku ifadeleri taşıyor — *"izinsiz kapanış
maruziyeti"*, *"bildirime tabidir"* — ve `## Sonuç` ile bitiyordu; işletim
sözleşmesi §5'in istediği iki zorunlu başlıkla değil.

**Daha kötüsü: bu çıktıyı sekizinci turda ekranda gördüm ve üzerinden geçtim.**
§12'nin öngördüğü kusurun ta kendisi: *"belgedeki bir kurala model sakinken
uyulur, görev uzayınca atlanır."* Sekiz tur, tam da "görev uzayınca"dır.

Rapor artık iki zorunlu başlıkla bitiyor ve avukat başlığı **boş değil**: beş
mevzuat kalemi ve bu raporun mevzuat katmanının birincil kaynakla
doğrulanmadığı, adlarıyla yazılı.

### Ve kapıyı raporun üzerinde koşturmak, kapıda üç kusur daha buldu

1. **DAYANAK yalnızca mevzuat atfını tanıyor.** Kanıt kuralı "her rakam
   dayanağını taşır" der — dayanağını, ille de bir *kanun maddesini* değil.
   Doğru kaynaklanmış bir akademik etki büyüklüğü ("%19 daha düşük,
   *Organization Science* 2026") kapıyı **asla geçemezdi**. Kitabın kendi §17'si
   bu türden onlarca rakam taşır: §17 biçiminde yazılmış bir çıktı sonsuza
   kadar bloklanırdı. Dayanağın türü artık rakamın türüne bağlı — para tutarı
   mevzuat atfı ister, oran kaynak atfıyla yetinir.
2. **Cycle 3'te eklediğim `Dayanak:` kuralı belge düzeyi gevşekliğini geri
   getirmişti.** C-01'i çözmek için koyduğum kural, uzun bir raporun başındaki
   tek bir beyanla sonundaki dayanaksız her eşiği aklıyordu — B-17/B-18'de
   teşhis ettiğim kusurun aynısı, bir `Dayanak:` satırının arkasına saklanmış.
   Kapsam artık ikili: başvuru malzemesinde dosyanın tamamı, başka her yerde
   bir sonraki `##` başlığa kadar. İkisi de gerekliydi — yalnızca birincisi
   §19'un doğru cevabını bloklardı, yalnızca ikincisi kitabın tr-esikler.md'sini.
3. **§14'ün zorunlu kıldığı satırın kendisi kapıyı kandırıyordu.**
   `bulunamayan: 4054 sayılı Kanun metni` ibaresi — bir kaynağın BULUNAMADIĞINI
   söyleyen alan — yakınlık penceresinde bir mevzuat atfı olarak okunuyor ve
   yanındaki her eşiği aklıyordu. Alan artık dayanak aranırken metinden
   düşülüyor.

---

## Yedi buçuk artı dokuz · Rapor, yöntemle başlıyordu

§4: *"Her çıktı cevapla başlar. Sonra gerekçe, en sonda yöntem. Yöntemi merak
eden okuyucu aşağı iner; cevabı merak eden ilk paragrafta bulur."*

Bu rapor dokuz tur boyunca **`## Yöntem` ile başlıyordu** ve cevabı 818.
satırda tutuyordu — kuralın önlemek için var olduğu şeyin ta kendisi. Artık
`## Cevap` ile başlıyor, yöntem bulguların sonrasına indi, ve iki zorunlu
başlık en sonda kaldı.

Aynı turda kural 9 ve §10 da uygulandı: raporun **onaysız olduğu ilk bölümde**
yazılı (sessizlik onaylanmış gibi okunur), ve NFKC, CONNECT, homoglif gibi
terimler ilk geçtiklerinde açıklandı.

### Ve bu, kitapta bir kusur daha gösterdi

F matrisinde §4, §9 ve §10 "hiç kapsanmayan" diye duruyordu — kitap onları
"biçim kuralı, kapı konusu değil" diye geçmişti. Oysa üçü de kısmen makinece
kontrol edilebilir: kural 4 bir başlık sırası kuralıdır, kural 9 onayın kendisini değil
ama **beyanını** isteyebilir, §10 tanımlı bir terim listesi için denetlenebilir.
Kitap, uygulanabilir olanı uygulanamaz saymış. Matris güncellendi: kapsanmayan
kural sayısı **altıdan üçe** indi.

### Ve koşum betiğimde `| wc -l` kusurunun kendisini buldum

F takımı çöktü ve takım hâlâ **0 SİNYAL** dedi. Sebebi tek satırdı:

```
python3 "$S/ks_f_kapsama.py" | tail -8; topla "F · doktrin kapsama matrisi" 0
```

Çıkış kodu **elle 0 yazılmış**, üstelik boru hattının kodu zaten `tail`'inki.
Kitabın denetiminde D takımıyla bulduğum kusurun kendi koşum betiğimdeki hâli.
Düzeltildi ve mutasyonla doğrulandı — ama **ilk mutasyon denemem yine
tutmadı** (`sys.exit(0)` satırından sonra eklediğim satır hiç çalışmadı) ve
kuralımı üçüncü kez hatırlamak zorunda kaldım: *bir mutasyon sınaması,
mutasyonun olduğunu kanıtlamadan geçerli değildir.*

---

## Yedi buçuk artı on · Ölçüm, ölçtüğü kusuru gizliyordu

Dokuz tur boyunca "kaynak ≡ klon" diye doğruladım. O karşılaştırma bir şeyi
**yapısal olarak göremez**: her iki ağaç da diskte dururken, klondan bir dosya
kaynağa uzansa bile iki koşum aynı sonucu verir. Ölçüm, ölçtüğü kusuru
gizliyordu.

Kaynak ağacı geçici olarak kaldırıp klonu **tek başına** koşturunca çıktı:

```
DENETİM BAŞARISIZ: 1
```

`denetim.sh` içindeki iki gömülü Python parçacığı kökü kendi başına
`expanduser('~/mafirm')` ile çözüyordu. Kaynak ağaç yokken denetim var olmayan
bir ağaca uzanıyor ve yanlış yere kırmızı veriyordu. **Ve takım hâlâ 0 SİNYAL
diyordu**, çünkü hiçbir vaka denetimin kendi yol çözümlemesine bakmıyordu.

Bu, bu oturumda aynı sınıfın **üçüncü** tekrarı — `kapi.py`'nin ad kaydı,
`ks_b`'nin ad kaydı, şimdi `denetim.sh`'in gömülü parçacıkları: *iddia ettiği
şeyin dışına uzanan bir kontrol.* Kitabın D takımıyla bulduğum kusurun tam
karşılığı, üç ayrı yerde, benim elimden.

S takımı bunu kalıcı kılıyor: statik olarak hiçbir çalıştırılabilir dosyanın
kökü sabitlemediğini, dinamik olarak da denetimin ve kapının **sahte bir HOME
altında** yeşil kaldığını doğruluyor.

---

## Yedi buçuk artı on bir · Dürüstlük bölümünde fazla dar bir sınır

Kullanıcının isteği "hepsine kör test" idi. On bir tur sonra kapsamı saydım:
dört bölüm hiç sınanmamıştı — §6, §8, §15 ve **§18**.

§18 kitabın **dürüstlük bölümüdür** ve gerekçesini kendisi yazar: *"Sınırları
yazılmamış bir sistem, o sınırların ötesinde kullanılır ve sınırı ilk bulan
kişi onu bir müvekkilin karşısında bulur."* Dokuz maddesinin **dokuzu da
olumsuz iddiadır** — "yapmaz", "yoktur", "kanıt yoktur" — ve kitabın kendi §2'si
olumsuz iddiadan olumludan yüksek kanıt ister. On bir tur boyunca hiçbirini
sınamamıştım.

Sekizi doğru çıktı. Biri değil.

**§18.6 fazla dar yazılmış.** Kitap *"üç sözleşme çözümleme deposundan ikisi
bakımsızdır, **biri** AGPL-3.0'dır"* diyor ve §13.4'teki `lexpredict-lexnlp`'yi
kastediyor. Ama §13.5'teki `freelawproject/courtlistener` **de AGPL-3.0-or-later**
— G-01'de doğrulandı — ve kitap ona "açık (depoya bakın)" diyor. Katalog **iki**
AGPL bağımlılık taşıyor; §18 birini sayıyor.

Bu, bir rakam hatasından fazlasıdır. §18 fazla dar yazılmış bir sınırla, kendi
var olma sebebini ortadan kaldırır: okuyucu sınırın kapsadığından fazlasına
güvenir. Ve kitabın §13.7'si tam da bu soruyu ciddiye alıyor — *"copyleft
lisanslı bir bağımlılığı ticari bir pratiğin yığınına sokan cümle"* — yani
kitap riski biliyor, yalnızca ikinci örneğini kaçırıyor.

T-06, kitabın davranışının kaydı olarak **beyan edilmiş tabana** eklendi;
düzeltmesi errata'da.

---

## Yedi buçuk artı on iki · Birimler birbiriyle çelişiyordu

Kapsamı yeniden saydım. Geriye tek bir sınıf kalmıştı: **birimler arası
tutarlılık**. §4 birim yapısının gerekçesini kendisi yazar — birimler aynı
**yapıyı** paylaşır — ve kitabın denetimi tam olarak o yapıyı sayar: INDEX var
mı, `yontem/` dolu mu, üst bilgi yerinde mi. Hiçbir yerde bir birimin
**söylediği** ile başka bir birimin söylediği karşılaştırılmaz. On iki tur
boyunca ben de bunu yapmamıştım: §6 ve §8 içeriği yalnızca referans bütünlüğü
için okunmuştu.

On vakalık U takımı yazıldı. Üç gerçek çelişki çıktı, üçü de **benim
yazdığım** dosyalarda.

**Bir · `hukuki-cevirmen` TTK m.499'a kurucu nitelik atfediyordu.** Ajan,
yabancı hukukçuya "pay defteri … TTK m.499 bakımından **kurucu** bir işlevi
vardır" diyordu. Kitabın kendi `pay-devri.md`'si tersini söyler: devir taraflar
arasında ciro ve zilyetliğin devriyle tamamlanır (m.490/2); pay defteri kaydı
devrin **şirkete karşı** hüküm ifade etmesini sağlar, onu **kurmaz**. Bir
çevirmen ajanının bunu ters söylemesi, `pay-devri.md`'nin açılış paragrafının
uyardığı hatanın ta kendisidir: *"yabancı bir hukukçunun en yaygın hatası."*

Bunun kaydı **zaten errata'mda vardı** (I-05, §5.3: "TTK 499 açıklayıcıdır,
kurucu değil"). Uyarı yazılıydı; metin yine kaydı. Çünkü hiçbir şey bakıyordu.

**İki · Kapanış günü sırası TTK m.595'i ters çeviriyordu.** `kapanis-listesi`
"2. Organ kararları → 3. Noter işlemleri" diyordu. `pay-devri.md` ise
m.595/1'de noter onaylı devir sözleşmesini, m.595/2'de onu **tamamlayan**
genel kurul onayını sıralar. Listeyi izleyen bir uygulamacı, henüz noter
onaylı hâli bulunmayan bir devri onaylamak için genel kurul toplardı.

**Üç · Bir koşul, aynı anda kapanış günü adımıydı.** Kapanış günü sırasının
1. adımı "kapanış öncesi koşulların karşılandığının teyidi"dir. "Organ
kararları" hem o koşul listesinde hem de 2. adımdaydı: 1. adım hiçbir zaman
doğrulanamazdı.

Üçü de düzeltildi. Dördüncü bulgu düzeltilmedi ve sebebi önemli.

### Kitabın kendi içindeki çelişki — ve neden dokunulmadı

U-02 düzeltmeden sonra da kırmızı kaldı, çünkü kalan taraf **kitaba sadık
metindedir**: §6 `mimari.md`'nin koşul listesindeki 5. madde, işlemi
*yetkilendiren* organ kararı ile Ltd. Şti.'de **TTK m.595/2 genel kurul
onayını** tek satırda topluyor — ve kitabın kendi §5.3'ü ikincisini "devri
tamamlayan **kurucu** işlem" sayar. Kurucu bir işlem kapanışın önkoşulu olamaz.

Çelişkinin iki tarafı da kitabın içinde; görmek için dış kaynak gerekmiyor.
Ama **hangisinin doğru olduğu bir hukuki nitelendirmedir** ve §9 ile §11 onu
yetkili bir insana bırakır. Kitabın düzyazısı bu yüzden **aynen bırakıldı**.
Bunun yerine:

- Önerilen tek satırlık düzeltme bir **kum havuzunda uygulandı** ve U-01 ile
  U-02'yi birlikte yeşile aldığı gösterildi — öneri iddia değil, gösterim.
- Türetilmiş dosyalar (`kosul-takibi`, `kapanis-listesi`) ayrımı açıkça taşır,
  dolayısıyla becerileri kullanan kişi doğru sırayı görür.
- U-02, gerekçesiyle **beyan edilmiş tabana** yazıldı; errata'da §6 kaydı var.

### Takımın kendi iki kusuru — ikisi de kitapta bulduğum sınıflardan

U takımı yazılırken **iki kör nokta** üretildi; mutasyon sınaması ikisini de
yakaladı ve ikisi de bu raporun kitapta işaret ettiği sınıflardandır:

- **U-09 sabit `True` yazılmıştı.** Tarama bir ihlal bulsa bile vaka yeşil
  kalıyordu — §16'da bulduğum `topla "F" 0` kusurunun birebir aynısı, kendi
  elimle.
- **`bas()` Türkçe kısaltmada kırpıyordu.** İşlem adı ilk noktada kesiliyordu
  ("Şirket organ kararları ve **Ltd**"), dolayısıyla "genel kurul onayı"
  hiçbir başlıkta görünmüyor ve **kitabın gerçek çelişkisi gizleniyordu**.
  §12'nin İ/nokta tuzaklarıyla aynı aile.

Ayrıca U-03 bir kez **boşa geçti**: aradığı adım listede bulunmayınca "çakışma
yok" deyip yeşile döndü. Yeniden yazıldı; adımı bulamamak artık başarısızlıktır.

Ve iki kez bir vaka **sessizce kayboldu** (yama, hedefini zaten silmiş bir
ikinci `replace` yüzünden). İlkinden sonra takıma **beyan edilmiş vaka sayısı**
kondu; ikincisini o yakaladı. Kaybolan bir vaka, kırmızı bir vakadan kötüdür:
kimse aramaz.

Mutasyon sonucu: **10 mutasyonun 10'u yakalandı.**

---

## Yedi buçuk artı on üç · Kapıyı genişletmiştim; doğru işi bloklamaya başlamıştı

On üç tur boyunca kapıların **KAÇIRMA** yüzeyini ölçtüm: B takımı neyin
sızdığını, O takımı sır kapısının nasıl atlatıldığını sayıyor. Aynasını hiç
ölçmedim. Oysa kitap o aynayı **kendisi adlandırıyor** ve ölümcül sayıyor:

> *"Doğru işi bloklayan bir kapı bir gün içinde kapatılır; sonra hiçbir şey
> uygulanmaz."*

V takımı bir Türk M&A avukatının **gerçekten üreteceği** on yedi metin yazdı —
eşik değerlendirmesi, kapanış listesi, madde incelemesi, kurul notu, ortaklık
yapısı, dava envanteri, emsal metni, yaptırım taraması — ve altı kapıyı
hepsine koşturdu. Metinler kapı koduna göre değil, kitabın §0 çıktı
sözleşmesine göre yazıldı.

**Dört metinde kapı ateşledi. Üçü gerçek kusurdu ve üçü de benimdi.**

### Bir · "yüzde", Türkçe ticari metnin günlük kelimesidir

Kitabın kendi `ESIK` deseni yalnızca basamak gruplu para tutarıdır:

    ESIK = re.compile(r"\d{1,3}(?:[.,]\d{3}){2,}\s?(?:TL|₺|EUR|USD|avro|dolar)", re.I)

Ben bunu **genişlettim** — `binde \w+|yüzde \w+|%\s?\d+` — çünkü B-13..B-18
kaçırma vakalarını kapatıyordum. Sonucu ölçmedim.

Türkçede "yüzde" pay oranıdır, tazminat tavanıdır, sepettir, oy çoğunluğudur,
earn-out payıdır. Genişletilmiş desen bunların **hepsini bir mevzuat eşiği**
sayıyordu. Yani **her SPA (Share Purchase Agreement: pay alım satım
sözleşmesi) incelemesi ve her ortaklık yapısı notu** üç kapıyı
birden ateşliyordu: `kanit` dayanak istiyordu, `guncellik` doğrulama tarihi,
`arastirma` "Kontrol edildi" satırı — doğrulanacak hiçbir mevzuat olmadığı
hâlde.

Bu, kitabın uyardığı kapatılma sebebinin tam kendisidir. Ve ben yaptım:
kaçırma yüzeyini kapatırken yanlış pozitif yüzeyini açtım, sonra on üç tur
boyunca yalnızca kaçırmayı ölçtüm.

**Düzeltme geri alma değil.** Ayrım biçimde değil bağlamdadır. Bir yüzde,
bu işleme dair bir **olguyu** anlatabilir (payların dağılımı, tazminat tavanı)
ya da bir **kuralı** anlatabilir (bir tebliğin aradığı oran). Yalnızca ikincisi
dayanak ve tarih ister.

> Bu paragrafın ilk hâli kuralı bir **örnekle** anlatıyordu ve örnek, kaynaksız
> bir oran cümlesiydi. Kapı onu yakaladı — **haklı olarak**: bir raporda
> kaynaksız duran bir oran, okuyucu için örnek değil beyandır. Kapıyı
> gevşetmek yerine cümle değiştirildi. Bir yüzde artık ancak
düzenleyici bir ipucuyla (eşik, sınır, ceza, Tebliğ, Kanun, madde, Kurul,
zorunlu, tabi…) **aynı cümlede** geçtiğinde eşik sayılıyor. V-24 daraltmanın
delik açmadığını kanıtlıyor: dayanaksız bir *düzenleyici* yüzde hâlâ üç
kapıdan da geçemiyor.

### İki · Kitabın iki çıktı biçimi birbirini tanımıyordu

`guncellik` kapısı yalnızca `Doğrulama: <tarih>` biçimini tanıyordu. Ama
kitabın §14'ü **çıktılar** için başka bir biçim emrediyor:
`Kontrol edildi: <kaynak> (<tarih>)`. Yani §14'ü **harfiyen izleyen** bir
hukukçunun çıktısı, kapıdan "doğrulama tarihi yok" diye geri dönüyordu. Aynı
olgu için iki sözleşme, ve kapı yalnızca birini biliyor. Kapı artık ikisini de
tanıyor.

### Üç · Bir kapı çöküyordu

Düzeltmeyi yazarken `re.Match` yerine geçen asgari bir nesne kullandım ve
`group()` metodunu koymadım. Düzenleyici bağlamda yüzde geçen **her belgede**
kanca `AttributeError` ile düşüyordu. **Çöken bir kapı, yanlış ateşleyen
kapıdan kötüdür**: üretimde her yazmayı düşürür.

Ve V takımı bunu **görmedi** — çünkü korpusta düzenleyici bağlamlı *meşru* bir
yüzde yoktu. Sınama, sınadığı yüzeyin bir köşesini hiç ziyaret etmemişti;
kusuru gerçek raporu kapıdan geçiren Q takımı buldu. Köşe V-17 olarak eklendi;
kapı ayrıca dizge tarihe karşı dayanıklı hâle getirildi.

### Takımın kendi kusuru

V-17 ilk yazıldığında **yanlış listeye** düştü: ihlalli metinler listesine.
Beklentisi boş olduğu için `set() & X == set()` her zaman doğru çıkıyor ve
kapıların canlılığını ölçen V-30'un sayısını **sahte biçimde** 4/4'ten 5/5'e
çıkarıyordu. Bir yerleşim kontrolü eklendi: sıfır beklentili bir kayıt artık
ihlalli listesinde duramıyor.

Mutasyon: `yüzde`yi yeniden koşulsuz eşik saymak V-03/V-08/V-31'i, `Kontrol
edildi` tanımasını geri almak V-01/V-17/V-31'i kırmızıya döndürdü.

---

## Yedi buçuk artı on dört · Boş bir dolap, yokluğun kanıtı değildir

§14 kuralı kendisi yazıyor:

> *"Boş bir GitHub araması yokluğun kanıtı değildir. Kayıtlara bak."*

Kitap bunu dış arama için söylüyor. Aynı tuzağı **kendi dosya düzeninde**
kuruyor:

- §2 `emsal/` dizinini açıyor ve ona bir ad veriyor: **onaylı madde bankası**.
- §4 her birim altında `birimler/<birim>/emsal/` açıyor.
- §10 `emsal-bulucu` alt ajanını **yalnızca orayı aramak** üzere
  görevlendiriyor.
- §14 `once-arastir`ın üçüncü adımını oraya yönlendiriyor.
- **Ve bankayı hiç doldurmuyor.**

Sonuç: banka boşken ajan *"yeterince yakın emsal yok"* der. Okuyucu bunu
**dünyaya** dair bir tespit sanır; oysa **boş bir dolaba** dair bir tespittir.
İkisi aynı cümleyle ifade edildiğinde §2 çiğnenmiş olur — olumsuz iddia,
kanıtsız. Ve bu, bir ajanın tek işini sessizce yapılamaz kılar.

Kusurun bir örneği daha önce kapatılmıştı: boş müvekkil ad kaydı denetimde
**her koşumda sesli** bildiriliyor. İkinci örneği on dört tur boyunca
görmedim çünkü hiçbir takım "bir bileşenin aradığı yer dolu mu" diye
sormamıştı. W takımı sordu.

İki düzeltme:

1. **Denetim artık boş madde bankasını sesli bildiriyor** — müvekkil ad
   kaydıyla birebir aynı desende.
2. **`emsal-bulucu` iki cevabı ayırmak zorunda:** *"banka boş"* (dolapta hiç
   madde yok — emsal yokluğunun kanıtı DEĞİL) ile *"yeterince yakın emsal
   yok"* (banka dolu, tarandı, yakın biçim çıkmadı). Her ikisinde de kaç
   dosyanın tarandığı yazılır.

`cikti/` ve `dosyalar/` de boş, ama onlar `.gitignore`'lu çalışma
dizinleridir; aranan bir bilgi kaynağı değiller. Ayrım takımın içinde yazılı.

### Takımın kendi kusuru — ters mutasyon buldu

W-02'nin ilk hâli `emsal/` ile `birimler/*/emsal/`yi **ayrı** kaynak sayıyor
ve denetimin duyurusunu "emsal" alt dizgesiyle arıyordu. Denetim ise ikisini
**tek bir banka** olarak sayar ve duyuruyu "madde bankası" diye etiketler.
Bankayı doldurup duyuru sustuğunda takım hâlâ kırmızı kalıyordu: **ölçtüğüm
şeyin tanımı, ölçenin tanımıyla aynı değildi.** Bunu düz mutasyon değil,
**ters** mutasyon buldu — kusuru geri getirmek değil, düzeltmeyi uygulamak.

Ayrıca W-03'ün ilk hâli `once-arastir`ı **doğru sebeple değil** geçiriyordu:
anahtar kelime araması, becerinin GitHub'a dair uyarısını yakalıyordu. Ölçüt
yakınlığa bağlandı; beceri şimdi §14'ün `bulunamayan:` alanı sayesinde ve
onun sayesinde geçiyor.

Mutasyon: duyuruyu kaldırmak W-02'yi, ajandan ayrımı kaldırmak W-03'ü
kırmızıya döndürdü; bankayı doldurmak ikisini de doğru biçimde susturdu.

---

## Yedi buçuk artı on beş · Yetki bir açıklama değil, bir imkândır

§10 beş alt ajan kuruyor ve her birine bir `tools:` satırı yazıyor. O satır bir
**açıklama değil, bir yetkidir**: ajanın gerçekten yapabildiği şey. Kural 6
(sır saklama) sistemin en yüksek sonuçlu kuralıdır ve §12'nin sır kapısıyla
uygulanıyor — ama kapı **metin** denetler, **yetki** denetlemez. On beş tur
boyunca hiçbir takım şunu sormadı: *her ajanın elindeki her araç, kancanın
gerçekten izlediği bir araç mı?*

İki bulgu çıktı.

**Bir · Beyan edilmiş ama uygulanmayan bir "dışarı" kuralı.** Kapı
`BashOutput`'u dışarı aracı sayıyordu; kancanın matcher'ında ise **yoktu**.
Yani beyan hiçbir zaman uygulanmıyordu. Beyan edilmiş ama uygulanmayan bir
kural, kuralın hiç olmamasından **kötüdür**: okuyucu korunduğunu sanır.

Düzeltme matcher'a eklemek **değil**: `BashOutput`'un girdisi yalnızca bir
`bash_id`'dir, dışarı giden bir yük taşımaz. Gerçek koruma komutun
**başlatıldığı** andadır — arka planda başlatılan bir `curl` de Bash olarak
denetlenir. Bunu davranışla doğruladım ve X-07 olarak sabitledim: bir gerekçe,
yorum satırında kaldığı sürece bir iddiadır.

**İki · Web yetkisi olan ajan, sır sınırını yazmıyordu.** `esik-denetcisi`
sistemdeki iki web yetkili ajandan biri. `yaptirim-taramasi` **becerisi**
"sorgu soyutlama kuralı burada zorunludur" diyor — ama internete gerçekten
ulaşabilen **ajanın** metninde böyle bir satır yoktu. Kural, onu uygulayacak
yetkinin bulunmadığı yerde yazılıydı. Ajanın metnine sorgu sınırı eklendi:
aranan mevzuattır, işlem değil; sorgu soyutlanır; emin değilsen sorma.

Davranış da sınandı, iddia değil: kod adı taşıyan bir WebSearch, WebFetch ve
Bash çağrısının üçü de bloklanıyor (çıkış 2); meşru bir
`rekabet.gov.tr` çağrısı bloklanmıyor (çıkış 0). Yani kapı hem canlı hem de
doğru işi geçiriyor — on dördüncü turun ölçtüğü denge burada da tutuyor.

---

## Yedi buçuk artı on beş buçuk · Aynı katman ihlali, bu kez veri yolundan

Vaka sayısını kendi kendine denetlesin diye denetime bir kontrol koydum:
*"raporun vaka sayısı, son koşumun kaydıyla uyuşuyor mu."* Kayıt olarak
`SONUC-sonra.txt` seçildi.

Sonuç: `hepsi.sh` **kırmızıya döndü** — üstelik tek başına koşulduğunda yeşil
olan D takımından. Sebep, betiğin kendisini çağırmak değildi; **yazdığı
dosyaydı**:

    hepsi.sh > SONUC-sonra.txt    (yönlendirme dosyayı BAŞTA keser)
      └─ D takımı → denetim.sh → yarım kalmış kaydı okur → kırmızı
           └─ D'nin taban çizgisi bozulur → 99 sinyal

Denetime "takım koşuyor mu" kontrolünü koymanın özyineleme ürettiğini onuncu
turda bulmuş ve gerekçesiyle yazmıştım. **Aynı ihlali, çağrı yolundan değil
veri yolundan yeniden kurdum.** Bir katman kuralı, yalnızca ihlalin bilinen
biçimine karşı yazılırsa tutmuyor.

İlk düzeltme yetmedi. Kaydı ayrı ve **atomik** bir dosyaya (`SAYIM.txt`)
taşıdım; yarım okuma bitti — ama bu kez denetim bir **önceki** koşumu
okuyordu. Sayı değiştiğinde birinci koşum kırmızı, ikincisi yeşil oluyordu.
**İki koşumda yakınsayan bir kontrol, okuyucuya "kırmızıysa bir daha koş"
alışkanlığı öğretir** — bu takımın bütün amacının tersi.

Doğru yer üçüncüsüydü: kontrol, gerçek toplamı **bayatlamadan bilen tek
yere** — `hepsi.sh`'in kendi kapanışına — kondu. Orada sayı bu koşumundur,
bir öncekinin değil. Mutasyonla doğrulandı: bayat bir sayı hem birinci hem
ikinci koşumda kırmızı kalıyor, ve basılan toplam ile çıkış kodu artık
birbirini tutuyor.

---

## Yedi buçuk artı on altı · Kapı ön kapıyı tutuyordu; §2 rampayı açık bırakmış

Kural 6 sistemin en sert kuralı: **müvekkil kimliği makineden çıkmaz.** §12'nin
sır kapısı bunu WebSearch, WebFetch ve Bash çağrılarında uyguluyor ve on
altıncı tur davranışla doğruladı: kod adı taşıyan üç çağrı da bloklanıyor.

Ama §2, kurulumun **ikinci adımında** şunu yapıyor:

    cd ~/mafirm && git init && git branch -M main
    printf '%s\n' 'cikti/' 'dosyalar/*/veri/' '.DS_Store' > .gitignore

Kurulum bir **sürüm deposudur** ve `git push` veriyi makineden **çıkarır** —
kuralın yasakladığı şeyin ta kendisi. Korunan iki yol var. Korunmayanlar:

| yol | ne tutar | durum |
|---|---|---|
| `dosyalar/<is>/` | §2: **canlı işler** — kapsam notu, taslaklar, yazışma | yalnızca `veri/` korunuyordu |
| `hafiza/muvekkil-adlari.txt` | varlık sebebi **gerçek ad** tutmak | izleniyordu |
| `hafiza/cikar-catismasi.md` | §8: her dosyanın **karşı tarafları** | izleniyordu |

Kapı ön kapıyı tutuyordu; §2 **yükleme rampasını** açık bırakmıştı. On altı tur
boyunca hiçbir takım *"sistem neyi kalıcı hâle getiriyor"* diye sormadı.

**Sızıntı olmadı — ve bu ölçüldü, varsayılmadı.** Her iki dosyanın işlenmiş
her sürümü tek tek açıldı: hepsi yalnızca yorum satırı taşıyor, `dosyalar/`
altında hiçbir dosya hiç işlenmemiş. Maruziyet **müstakbeldi**: denetim her
koşumda *"kaydı doldur"* diyor ve dolduran kişi gerçek adları izlenen bir
ağaca yazacaktı.

Üç düzeltme: üç yol `.gitignore`'a eklendi (`dosyalar/` **tamamı**), iki
dosya `git rm --cached` ile izlemeden çıkarıldı, ve mekanizma görünür kalsın
diye izlenen birer **şablon** (`*.ornek.*`) bırakıldı.

> **Ve bu, tek satırlık bir düzeltme değildi.** `.gitignore`'a bir yol
> eklemek, o yol **zaten izleniyorsa hiçbir şey yapmaz** — git izlenen bir
> dosyayı asla yoksaymaz (`check-ignore` "yoksayılmıyor" der). Bu düzeltmeyi
> naif yapan biri korunduğunu sanır ve korunmaz. `git rm --cached` şart.

### Takımın kendi üç kusuru

- **Y-04 boşa geçiyordu.** "Hiç ad işlenmemiş" bir **olumsuz iddiadır**; ilk
  sürüm **sıfır** sürüm inceleyip onu yazdı, çünkü kurulum kökündeki depo
  commit taşımıyordu. Sıfır incelenmiş sürüm kanıt değildir. Şimdi ayrım
  yazılı: *deposu hiç commit taşımıyor* (olumlu kanıt) ile *bakamadım*
  (başarısızlık) aynı şey değil.
- **Y-05'in bir kaçış maddesi vardı:** "denetim kaydı anmıyorsa geç." Anmayı
  **silmek** vakayı yeşile alıyordu — mutasyon sağ kalarak gösterdi.
  **Koruduğu şeyi kaldırarak tatmin edilebilen bir kontrol, kontrol değildir.**
- Ve mutasyon bir **gerçek** kusur daha buldu: koruma cümlesi denetimin
  yalnızca "kayıt boş" dalında yazılıyordu. Oysa dosya **doluyken** daha da
  gerekli: içinde gerçek adlar var.

Mutasyon: `.gitignore`'u §2'nin hâline döndürmek Y-02'yi, gerçek bir adı
işlemek Y-03 ile Y-04'ü, koruma cümlesini kaldırmak Y-05'i kırmızıya döndürdü.

---

## Yedi buçuk artı on yedi · Kitap ikinci kez koşulunca her yamayı geri alıyor

Kitap bir **kurulum kitabıdır**. Asıl kullanımı çalıştırılmaktır — ve on yedi
tur boyunca hiçbir takım onu **iki kez** çalıştırmadı.

§2'nin ikinci adımı **yıkıcıdır**:

    printf '%s\n' 'cikti/' 'dosyalar/*/veri/' '.DS_Store' > .gitignore

`>` üzerine yazar. Aynı şey §12'nin `kapi.py`si, §5'in `esik.py`si ve §16'nın
`denetim.sh`i için de geçerli: hepsi "yazılır" der. Kitabı yeniden izlemek —
yeni bir oturum, ikinci bir hukukçu, ya da **§0'ın dördüncü kuralının**
denetim kırmızıysa durup düzeltme talimatını izleyen kişi — **her yamayı**
geri alır. Bir önceki turda konan kural 6 koruması dâhil.

Yıkımın olması kaçınılmaz; ölçülen şey **görülüp görülmediğidir**. Sessizce
geri alınan bir koruma, hiç konmamış bir korumadır.

**Ölçüm.** Kitaba sadık `kapi.py` geri konduğunda denetim **kırmızıya
dönüyor** (Z-05) — yani mekanizma kısmen çalışıyor. Ama `.gitignore` silinince
**`DENETİM OK`** diyor: yamanın türüne göre değişen bir bütünlük, bütünlük
değildir. Denetime bir kontrol eklendi; artık kural 6 koruması eksikse
kırmızı.

### Ve en keskin hâli: denetçiyi ezmek denetimi kapatır

Kitabın kendi `denetim.sh`'ini geri koyun → **`DENETİM OK`**. Sonra kural 6
korumasını da silin → **hâlâ `DENETİM OK`**.

**Denetim kendi bütünlüğünü doğrulayamaz**, çünkü doğrulayacak kod ezilen
dosyanın içindedir. Uygulayıcı, korumasız bir sisteme yeşil bir denetimle
bakar — ve yeşili veren, kitabın kendi betiğidir.

Dış katman `sinama/`dır: **kitap oraya hiçbir şey yazmaz**, dolayısıyla
yeniden kurulumdan sağ çıkar. Denetçinin bütünlüğü oraya kondu (Z-07: yama
izleri yerinde mi; Z-08: kontrol sayısı sessizce düşmüş mü). Mutasyonda
denetçiyi geri almak **sekiz vakanın beşini** birden kırmızıya çeviriyor —
en tehlikeli değişiklik, en gürültülü sinyali veriyor.

Her şey bozuk değil ve bu da ölçüldü: `mkdir -p` adımları gerçekten
zararsızdır (Z-06). Z-02'nin bir genelleme değil bir **ölçüm** olduğunu belli
eden şey budur.

> Bu turda kendi sınamam bir kez de **geçersiz taban çizgisinde** koştu: kum
> havuzunun denetimi zaten kırmızıydı (yeni takım rapor tablosunda yoktu),
> dolayısıyla üç vaka okunamazdı. Üçüncü turda öğrendiğim kural burada işe
> yaradı: **kırmızı tabanda mutasyon okunmaz.** Taban düzeltildi, sonuç sonra
> okundu.

---

## Yedi buçuk artı on sekiz · Kapı çöktüğünde AÇIK yöne düşüyordu

Kanca her Write, Edit, Bash, WebSearch ve WebFetch çağrısının önünde durur.
§12 çıkış kodunu yazar: **2 bloklar**. PreToolUse sözleşmesinde 2 **dışında**
her sıfırdan farklı kod "bloklamayan hata"dır — araç çağrısı **devam eder**.

Bunun anlamı, on sekiz tur boyunca yazmadığım şey: **kancadaki işlenmemiş her
istisna sessizce AÇIK yönde çözülür.** Kural 6 uygulanmaz ve kimse görmez.

Bu teorik değil. Bu kurulumda **iki kez** oldu ve ikisi de benim yamalarımdı:
on dördüncü turda `bugun` dizge geldiğinde `TypeError`, on yedincide `_Bulgu`
nesnesinde `group()` yokluğunda `AttributeError`. İkisi de **düzenleyici
bağlamda yüzde geçen her belgede** kapıyı devre dışı bıraktı. O turlarda
"çöken kapı kötüdür" diye yazdım — ama **yönünü ölçmedim**. Ölçseydim,
"kötü"nün "kural 6 sessizce uygulanmıyor" demek olduğunu görürdüm.

§12'nin C-08'de yazdığı arıza politikası doğru ve iyi gerekçelendirilmişti:
*ayrıştırılamayan bir olayda kanal bilinmez, dolayısıyla dışarı giden yönde
kapalı çözülür.* Ama o politika **yalnızca ayrıştırmayı** kapsıyordu.
Ayrıştırmadan sonraki her şey korumasızdı. Politika artık gerçekten
uygulanıyor: iç arıza, kanal dışarıysa **bloklar**, yerelse uyarır ve
sürdürür — pratiği durdurmadan sırrı korur.

### Üçüncü arıza biçimi: hiç bitmemek

Bloklayan da olsa açan da olsa, **dönmeyen bir kapı pratiği durdurur** — ve
bunu hiç ölçmemiştim. Ölçtüm:

| girdi | önce | sonra |
|---|---|---|
| boşluksuz 20 000 karakter | 6 186 ms | **62 ms** |
| boşluksuz 40 000 karakter | **25 s+ (bitmedi)** | ~90 ms |
| boşluksuz 200 000 karakter | ölçülemedi | **330 ms** |
| 400 KB gerçek düzyazı | 433 ms | 406 ms |

Sebep `TAVSIYE` desenindeki üç `\w+` dalıydı: boşluksuz uzun bir dizgede
regex her başlangıç noktasından geri izliyor. Ve bu desen **kitabın değil,
benim**: kitabın kapsam kapısı sekiz sabit ifade arıyordu, Türkçe kip
çeşitliliğini kapatmak için (B-02..B-06) deseni ben genişlettim.

> **İkinci kez aynı hata.** On dördüncü turda kaçırma yüzeyini kapatmak için
> `ESIK`'i genişlettim ve **yanlış pozitif** yüzeyi açtım. Burada `TAVSIYE`'yi
> genişlettim ve **sınırsız süre** yüzeyi açtım. Bir kapıyı genişletmek, tek
> bir eksen üzerinde iyileştirme değildir; ölçülmeyen her eksende bir borçtur.
> Türkçe bir kelime otuz karakterden uzun değildir — sınır konuldu, doğruluk
> korundu (AA-05 üç davranış vakasıyla sabitliyor).

Ayrıca `[1,2,3]` ve `null` **geçerli JSON'dur ama nesne değildir**;
`.get()` çağrısı ayrıştırma `try`'ının dışında kalıyordu ve yine çıkış 1
veriyordu. Ayrıştırmanın başarılı olması, olayın **kullanılabilir** olduğu
anlamına gelmiyor.

Ve denetimin takım listesi deseni `ks_[a-z]_` idi: **iki harfli bir takım adı
sessizce kapsam dışıydı.** AA takımı eklendiğinde denetim onu istemeyecekti.
Bir kapsama kontrolünün kendisi, kapsamadığını söylemez.

---

## Yedi buçuk artı on dokuz · Kapı teşhis koyuyordu, çare söylemiyordu

§14 bir kapının nasıl öldüğünü kendisi yazar:

> *"Doğru işi bloklayan bir kapı bir gün içinde kapatılır; sonra hiçbir şey
> uygulanmaz."*

On dördüncü tur bunu **yanlış pozitif** ekseninde ölçtü. Ama ekonomi aynıdır:
**doğru** bir blok da, uyulacak yolu söylemiyorsa her seferinde zaman yakar ve
en ucuz çözüm kapıyı kapatmaktır. Teşhis koyup çare söylemeyen bir kapı,
yanlış ateşleyen bir kapıyla **aynı yerde biter**.

Bloklanan kişinin gördüğü şey buydu:

    BLOKLANDI [guncellik] eşik rakamı var ama doğrulama tarihi yok

Doğru ve eksiksiz bir teşhis — ve **hangi biçimin kabul edildiğine dair tek
kelime yok**. Üstelik bu, kitabın **iki** biçim kabul ettiği yer: yöntem
dosyalarında `Doğrulama: <tarih>`, çıktılarda `Kontrol edildi: <kaynak>
(<tarih>)`. On dördüncü tur bu ikiliğin kitabın kendi çelişkisi olduğunu
bulmuştu; bloklanan kişi hangisinin işe yaradığını **deneyerek** bulmak
zorundaydı.

Altı kapının iletisine çare eklendi. Artık:

    BLOKLANDI [guncellik] eşik rakamı var ama doğrulama tarihi yok
      → şu iki biçimden birini ekleyin: 'Doğrulama: YYYY-AA-GG' (yöntem
        dosyaları, §3/§5.3) ya da 'Kontrol edildi: <kaynak> (YYYY-AA-GG)'
        (çıktılar, §14).

Ve iki şey ölçüldü ki bunlar zaten iyiydi: çok kapılı bir blokta **bütün**
ihlaller tek seferde bildiriliyor (kullanıcı üç tur değil bir tur harcıyor,
AB-04), ve kapı **determinist** — aynı girdi beş koşumda aynı kapı kümesini
veriyor (AB-05). İkisini de hiç ölçmemiştim.

### Takımın kusuru: kendi niyetimi sınamışım

AB-03 "çare uygulanınca kapı susuyor mu" diye soruyordu ve **geçiyordu**. Ama
mutasyon onu **sağ kaldı**: kapıya kasten yanlış bir çare yazdım — *"dosyanın
sonuna 'BITTI' yazın"* — ve takım yeşil kaldı.

Sebebi şuydu: AB-03, **sınamaya benim yazdığım** düzeltilmiş metinleri
deniyordu, **iletinin önerdiği** biçimi değil. Yani sistemin iddiasını değil,
kendi niyetimi ölçüyordum. İleti ne söylerse söylesin vaka yeşil kalırdı.

AB-03b bunu düzeltti: iletideki tek tırnaklı **her biçim örneği** çıkarılıyor,
yer tutucuları dolduruluyor, ihlalli metne ekleniyor ve o kapının **susması**
bekleniyor. Yanlış çare mutasyonu artık yakalanıyor.

Ve AB-03b'nin kendisi de bir kez **boşa geçti**: kitaba sadık kapıda hiçbir
ileti çare taşımadığı için döngü hiç dönmüyor ve vaka yeşil kalıyordu.
Sınanacak bir iddianın **bulunmaması**, iddianın doğrulanması değildir; vaka
artık bunu ayrı bir sonuç olarak yazıyor.

> Bir çareyi sınamak, kendi niyetimi değil **sistemin iddiasını** sınamak
> demektir. Aradaki fark, mutasyon koşmadan görünmüyor.

---

## Yedi buçuk artı yirmi · Aynı belge, başka masa, başka karar

S takımı taşınabilirliği **yol** düzeyinde ölçmüştü: klon ile kaynak ağaç aynı
sonucu veriyor mu. Kurulumun içinde bulunduğu **ortam** — saat dilimi, yerel
ayar — hiç sorulmamıştı. Yirmi tur boyunca hiçbir takım *"aynı metin başka bir
makinede aynı cevabı alıyor mu"* demedi.

Bu sistem için soru kozmetik değil. Kitap §6'da **sınır ötesi** bir pratik
kuruyor: aynı dosyalar İstanbul, Londra, New York ve Singapur arasında dolaşır.

**Bulgu.** Bugün İstanbul'da damgalanan bir `Doğrulama:` satırı, UTC (eşgüdümlü evrensel zaman) ölçeğinde −11 saat dilimindeki
bir masada **"GELECEK tarihli (1 gün)"** diye bloklanıyordu. Belge doğru, kapı
yanlış — ve §14'e göre böyle bir kapı kapatılır.

Sebebi kavramsal: **bir takvim tarihi saat dilimi taşımaz**; makinenin "bugün"ü
taşır. İkisini doğrudan karşılaştırmak, kıyasa olmayan bir saat dilimi sokar.
Dünya UTC−12 ile UTC+14 arasına, **26 saate** yayılır; bir yerde "bugün" olan
tarih başka bir masada en çok bir gün ileride görünür. Tolerans bir gündür ve
**orada biter**: AC-04 beş gün ileri bir tarihin hâlâ bloklandığını, AC-05
bayat kontrolünün yaşadığını sabitliyor. Mutasyon iki yönde de koştu —
toleransı kaldırmak AC-01/AC-02'yi, doksan güne açmak AC-04'ü kırmızıya
çeviriyor. Bir yanlış pozitifi, kontrolü **öldürerek** çözmek en kolay ve en
yanlış yoldur.

Yerel ayar temiz çıktı: beş yerel ayarda, büyük harfli Türkçe metin dâhil,
karar değişmiyor. §12'nin İ/ı tuzağı zaten açıkça ele alınmıştı.

### Üçüncü kez aynı desen — ve artık bir kural

Kitaba sadık kapıda **gelecek tarih kontrolü hiç yok** (B-23 bunu kaçırma
olarak kaydeder). Yani bu yanlış pozitif **kitabın değil benim**: kaçırmayı
kapatmak için kontrolü ekledim ve ölçmediğim bir eksende kusur doğdu.

Bu artık üç örnekli bir desendir:

| tur | kaçırmayı kapatmak için | açılan ve ölçülmeyen eksen |
|---|---|---|
| 14 | `ESIK` genişletildi (B-13..B-18) | **yanlış pozitif** — her SPA incelemesi bloklanıyordu |
| 19 | `TAVSIYE` genişletildi (B-02..B-06) | **sınırsız süre** — 40 KB girdi kapıyı donduruyordu |
| 21 | gelecek tarih kontrolü eklendi (B-23) | **ortam bağımlılığı** — başka saat diliminde yanlış blok |

Üçünde de niyet doğruydu, üçünde de ölçüm tek eksenliydi. **Bir kapıyı
genişletmek tek eksende iyileştirme değildir; ölçülmeyen her eksende bir
borçtur.** Bunun pratik karşılığı bir kuraldır: *bir kaçırmayı kapatırken,
açabileceğin eksenleri adlandır ve onları da sına.* V (yanlış pozitif),
AA (süre ve arıza yönü) ve AC (ortam) bu üç ekseni artık kalıcı olarak
ölçüyor.

---

## Yedi buçuk artı yirmi bir · Komutların iddiaları doğruydu; hiçbiri korunmuyordu

§15 dokuz komut kurar ve her biri **başka bileşenler hakkında iddiada
bulunur**: *"`spa-inceleme` becerisindeki **sekiz adımlı** sırayı uygula"*,
*"`kurul-notu` becerisindeki **beş bölümlü** sırayı uygula"*, *"tarih **altı
aydan** eskiyse bayat"*. L takımı komutların **atıflarını** kontrol ediyordu;
**söylediklerini** hiçbir şey kontrol etmiyordu.

**Bu turda canlı bir kusur çıkmadı ve bunu olduğu gibi yazıyorum.** Beceri
gerçekten sekiz adımlı, gerçekten beş bölümlü, `BAYAT_GUN = 183` gerçekten
altı ay. Dokuz komutun andığı her beceri ve ajan mevcut. Riskli ajan dağıtan
komutların hepsi sır sınırını yazıyor — `tara.md` bunu on altıncı turda
`esik-denetcisi`'ne eklediğimden **daha önce** yapıyormuş.

Bulunan şey, kusurun **yokluğunu koruyan hiçbir şeyin olmadığıdır.** Ve bu,
bu raporun defalarca belgelediği sınıfın ta kendisi:

- §9'un "10 beceri" beklentisi, §14 on birinciyi ekleyince bayatladı.
- Bu raporun "on üç beyan" satırı, gerçek **on birken** yazılıydı.
- F matrisi üç kuralda "mekanizma yok" diyordu; **üçünün de** mekanizması vardı.

**El yazısı bir sayı, ölçtüğü şeyden bağımsız yaşar.** Bugün doğru olması,
yarın doğru kalacağı anlamına gelmiyor — ve bu üç örnekte de tam olarak öyle
olmadı. AD, komutların sayısal ve yapısal her iddiasını **kontrol edilen bir
iddiaya** çeviriyor. Mutasyon beşte beş: beceriye bir adım eklemek, bir
beceriyi silmek, `BAYAT_GUN`'u değiştirmek, bir komuttan §0 sözleşmesini
kaldırmak ve bir komuttan sır sınırını çıkarmak — hepsi yakalanıyor.

### Takımın kusuru: Türkçe ünlü uyumu

AD-01'in ilk hâli iki iddiadan **birini** doğrulayıp "doğrulandı" diyordu.
Desen `(adım|bölüm|alan)l[ıi]` arıyordu; Türkçe ünlü uyumu *adım**lı***,
*bölüm**lü*** verir. "Beş bölümlü" sessizce atlandı.

**Kapsadığını sanan bir dedektör, kapsamadığını söylemez.** On dokuzuncu turun
tek harfli takım adı kusuruyla aynı sınıf, bu kez Türkçe'nin kendi
biçimbiliminden. §12'nin İ/ı tuzağı, U-05'in ek çekimi, ve şimdi bu: **Türkçe
metni desenle okuyan her şey, üçüncü kez aynı yerden sızdı.**

---

## Yedi buçuk artı yirmi iki · Bir sınıfı örnek örnek düzeltmek, sınıfı kapatmaz

Aynı kusur **dört kez** ayrı ayrı bulunmuştu ve her seferinde yalnızca
rastladığım örnek düzeltilmişti:

- §12 — `İ`.lower() `i` + U+0307 verir; *"YETKİLİ" ≠ "yetkili"* **[B-10]**
- U-05 — Türkçe eklemeli: *defterine / Defterin / defteri* eşleşmez
- AD-01 — ünlü uyumu: *adımLI* ama *bölümLÜ*; desen ikincisini atlıyordu
- AA — takım adı **tek harf** varsayımı **üç ayrı bileşende** gömülüydü

Dördü de aynı kökten: **Türkçe metni ASCII (aksansız temel Latin
karakter kümesi) sezgisiyle okumak.** Ve dördü de
ancak o örneğe çarptığımda görüldü. Yirmi iki tur boyunca sınıfın kendisini
hiç taramadım. AE taradı — ve **üç kusur daha** çıktı.

**Bir · Yama izi deseni son dört turun kimliklerini görmüyordu.** Z-04, yeniden
kurulumun yamaları geri aldığını yakalayan kontroldür ve yama işaretlerini
`\[[A-Z]-\d{2}\]` ile arıyordu. `[AA-01]`, `[AC-01]`, `[AB-03b]` bu desene
**görünmüyor**. Z-04 yalnızca dosyalarda eski tek harfli işaretler de
bulunduğu için geçiyordu — yani **doğru sebeple değil**. Tek harf varsayımının
dördüncü yeri.

**İki · Denetimin bulgu sayacı da tek harfliydi.** `dogrulama-bulgulari.md`
içindeki bulguları `^[A-Z]-[0-9]+` ile sayıyordu; iki harfli bir bulgu kimliği
eklendiği gün sessizce sıfırdan sayacaktı.

**Üç · Ve B-10 kusurunun kendisi, benim takımımda.** U-09 satırları
`satir.lower()` ile eliyordu. `"BEKLETİCİ".lower()` → `bekleti̇ci̇` (birleşen
noktalarla), yani `"bekletici" in ...` **yanlış** döner ve satır **hiç
incelenmeden** atlanır. Büyük harfle yazılmış bir *"BEKLETİCİ … FERAGAT
EDİLEBİLİR"* ihlali — yani bir başlık ya da vurgulanmış bir hüküm — sessizce
geçiyordu. U-09 bu takımda **ikinci kez** düştü: önce sabit `True` yazılmıştı,
şimdi de Türkçe küçültme.

### Dedektörü keskinleştirirken kör ettim

AE-01'in ilk hâli fazla genişti: bir **araç adı** desenini (`Bash`, `WebFetch`
eşleyen `^[A-Z]\w*\(.*\)$`) kimlik sanıp işaretliyordu. Daralttım — ve
**fazla** daralttım: mutasyon (bir kimlik desenini tek harfe geri döndürmek)
**sağ kaldı**. Yani yanlış pozitifi kovalarken dedektörü kör ettim; on
dördüncü turda kapılar için yazdığım şeyin, dedektörler için geçerli hâli.
Ölçüt sadeleştirildi ve mutasyon artık yakalanıyor.

AE-02 de aynı yerden geçti: ilk hâli markdown etiketlerini (`[O takımı]`,
`[ayrıstirma]`) karakter sınıfı sanıyordu ve `eşi[ğk]` gibi **bilinçli** iki
harfli bir kümeyi "yarım alfabe" diye işaretliyordu. Ölçüt artık üç ya da daha
fazla Türkçe harf taşıyan — yani gerçekten **alfabe niyetli** — sınıflara
bakıyor.

---

## Yedi buçuk artı yirmi üç · Ölçen şeyi kim ölçüyor

Yirmi üç tur boyunca sistemi ölçtüm. **Ölçen şeyin kendisi** — koşum betiği,
beyan edilmiş taban, raporun ölçüm cümleleri — büyük ölçüde ölçülmedi.

**Bulgu: on beş takım korumasızdı.** On üçüncü turda bir vaka **iki kez**
sessizce kayboldu ve `BEKLENEN_VAKA` koruması eklendi — ama **yalnızca o
turdan sonra yazılan takımlara**. On bir takım korunuyordu, **on beşi
korunmuyordu**: aralarında B (34 vaka), A (24), O (17), K (15). B'de bir
vakanın kaybolması tamamen görünmez olurdu.

Düzeltme **ileriye uygulanmış, geriye doldurulmamıştı** — yirmi üçüncü turun
bulgusunun aynısı: *bir sınıfı örnek örnek düzeltmek, sınıfı kapatmaz.*
Yirmi yedi takımın hepsi artık vaka sayısını beyan ediyor.

**Ve koruma iki yerde sahteymiş.** `ks_aa` sayıyı `len(BICIMLER) + 6` diye
**hesaplıyordu** — kendi kendine atıf. Listeden bir vaka düşerse beyan da
düşer ve koruma, korumak için var olduğu şeyi göremez. Beyan, ölçtüğü şeyden
**bağımsız** olmalıdır. `ks_f` ise `sonuclar` listesi tutmuyor; toplu geriye
doldurma bunu görmedi ve **F'i çökertti** — kör bir toplu düzenlemenin bedeli,
kendi elimle.

### Beyan bir vakanın GEÇMESİNİ yakalıyordu; BAŞKA SEBEPLE düşmesini değil

`beklenen.json` bir vakanın geçmeye başlamasını yakalar (BEKLENMEDİK GEÇİŞ).
Ama bir vaka **başka bir sebeple** düşmeye başlarsa hâlâ BEKLENEN raporlanır:
**yeni bir kusur, eski bir beyanın arkasına saklanabilir.**

İlk çözümüm yanlıştı: beyan metniyle canlı ayrıntıyı kelime örtüşmesiyle
kıyasladım ve **on iki beyanın onunu** işaretledi — oysa elle kıyasladığımda
hepsi doğruydu. Beyan bir **gerekçedir** (neden bırakıldı), canlı ayrıntı bir
**ölçümdür** (ne oldu); ikisi haklı olarak farklı kelimeler kullanır. Onda
sekizi yanlış işaretleyen bir ölçüt, kırmızıyı görmezden gelmeyi öğretir.

Doğru mekanizma: beyan anında görülen ayrıntı **belirti** olarak kaydedilir ve
her koşumda karşılaştırılır. Artık *"vaka hâlâ düşüyor"* değil, *"vaka hâlâ
**aynı sebeple** düşüyor"* ölçülüyor.

> Ve AF-02'nin ilk hâli de dizge varlığına bakıyordu: beyan satırı silindiğinde
> `rapor()` içindeki **kullanım** hâlâ o dizgeyi taşıyor ve kontrol boşuna
> geçiyordu. Mutasyon tam olarak böyle sağ kaldı. Ölçüt modül düzeyinde bir
> **atamaya** bağlandı.

Temiz çıkan iki şey de ölçüldü: diskteki yirmi dokuz takımın hepsi koşum
betiği tarafından **çağrılıyor** (bir takım eklenip bağlanmazsa diskte durur,
raporda anılır ve hiç koşmaz), ve raporun ölçüm iddiaları canlı çıktıyla
uyuşuyor.

---

## Yedi buçuk artı yirmi dört · Kıyas ölçütünün kendisi eksikti

Bu raporun en ağır cümleleri bir **karşılaştırmaya** dayanır: *"kusur
kitabın"* ya da *"kusur benim"*. J-01s ve J-07s kitabın davranışını ölçer,
Z-05 kitaba sadık dosyayı geri koyup denetimin kırmızıya döndüğünü gösterir,
AA ve AB'nin atıfları o tabana bakar. Taban `yamalar/kitaba-sadik/`'tir ve
`DEGISIKLIKLER.md` onun hakkında bir **söz** verir:

> *"Karşılaştırma denetlenebilir olsun diye **hiçbiri silinmedi**."*

**Söz doğru değildi.** İki kitap dosyasının özgünü yoktu:

- **`.gitignore`** — §2'nin yazdığı dosya. On yedinci turda kural 6 için
  yeniden yazdım ve özgününü saklamadım.
- **`birimler/rekabet/yontem/tr-esikler.md`** — §5'in eşik dosyası. Üç
  ENGELLEYİCİ bulgu için yerinde `DOĞRULANAMADI` işaretleri koydum.

Yani tam da mevzuat katmanının en tartışmalı dosyası için *"kitap ne
yazıyordu"* sorusu artık kurulumdan cevaplanamıyordu. İkisinin de özgünü
**kitabın kendi metninden yeniden kuruldu**; yeniden kurulan `tr-esikler.md`
hiçbir `DOĞRULANAMADI` işareti taşımıyor — yani işaretlerin benim olduğu
ölçümle doğrulandı.

### Etiketin kendisi de sınandı

"Kitaba sadık" bir **etikettir** ve etiketler yanlış olabilir. AG-04 onu
davranışla bağlıyor: korunan `kapi.py`, kitabın **bilinen dört kusurunu**
taşımak zorunda — `json.dumps` üretim yolu (C-10), Türkçe küçültmenin
yokluğu (B-10), olumsuz iddia kapısının yokluğu (B-07), gelecek tarih
kontrolünün yokluğu (B-23). Dördü de mevcut. Mutasyonda "özgün" diye yamalı
sürümü kopyalamak AG-03 ile AG-04'ü birden kırmızıya çeviriyor: bir kıyas
ölçütünün **sessizce** yamalı sürümle değiştirilmesi, ölçümün tamamını
anlamsız kılardı ve hiçbir şey söylemezdi.

Ayrıca `__pycache__` dizinleri `.gitignore` tarafından **dışlanmıyordu**.
Depoya hiç girmemişlerdi — ama dışlanmayan bir artık, bir gün eklenen bir
artıktır.

> `DEGISIKLIKLER.md`'ye sözün bir süre tutulmadığı **yazıldı**. Kontrol
> edilmeyen bir söz, verilmemiş bir sözdür; bu belge yirmi dört tur boyunca
> kendi doğruluğunu iddia etti ve kimse bakmadı.

---

## Yedi buçuk artı yirmi beş · Cevap doğru yerde duruyordu, yanlış şeyi söylüyordu

§4 **"önce cevap"** der ve R takımı bunu **yapı** düzeyinde ölçer: ilk bölüm
cevap mı, yöntem sona mı kalmış. Yirmi beş tur boyunca geçti. Ama bir cevap,
**doğru yerde durup yanlış şey söyleyebilir.**

"Cevap" bölümü yedinci turda yazıldı ve **üç** sebep sayıyordu. Bugün on üç
**[A]** ağırlıklı bulgu var — ve dördü cevapta **hiç geçmiyordu**:

- **kural 6'nın depodan sızması** (§2 kurulumu bir sürüm deposu yapar; canlı
  iş dosyaları ve müvekkil ad kaydı izleniyordu),
- **kapının çöktüğünde AÇIK düşmesi** (2 dışında her çıkış kodu "bloklamayan
  hata"dır; her çökme kural 6'yı sessizce kapatıyordu),
- **web yetkili ajanın sorgu sınırının olmaması**,
- **yeniden kurulumun denetçiyi ezmesi** (yeşil bir denetim, korumasız bir
  sistem).

İlk ekranı okuyan bir kişi — yani raporun asıl okuyucusu — **en tehlikeli
şeyin ne olduğunu yanlış öğreniyordu.** Bu, §4'ün lafzına değil **ruhuna**
aykırı: cevap ilk sıradaydı ama güncel değildi.

Cevap iki madde ile güncellendi. **Beş** sebep sayıyor ve dördüncü madde
kapının **bakmadığı** üç yeri, beşinci madde yeniden kurulumun denetçiyi
ezmesini anlatıyor.

### Ölçütü seçerken bir kez daha aynı tuzağa girmedim

İlk aklıma gelen, [A] bulgularının başlıklarıyla cevabı **kelime örtüşmesiyle**
kıyaslamaktı. Denedim: on üç bulgunun **on birini** işaretledi — çünkü cevap
bulguları **parafraz eder** (*"öz-sınama üretim yolunu koşturmuyor"* →
*"§14, §12'nin öz-sınamasını bozuyor"*). AF-04'te tam olarak bu araçla aynı
hatayı yapmış ve düzeltmiştim; bu kez **kullanmadan önce** ölçtüm.

Onun yerine her [A] bulgusu, kendisini temsil eden cevap noktasını
**açıkça beyan ediyor** (`→CEVAP: 4`) ya da **neden temsil edilmediğini**
yazıyor. İki bulgu için gerekçeli *"YOK"* yazılı: **cevap bir özet değildir,
en tehlikeli beştir.** Beyanı sürdürmek, yeni bir ağır bulgunun cevaba girip
girmediğini fark etmeye **zorlar** — mutasyonda beyansız bir [A] eklemek
AH-03'ü, cevaptan bir sebep silmek AH-02 ile AH-04'ü kırmızıya çeviriyor.

---

## Yedi buçuk artı yirmi altı · Gerçek kişilerin ağzına konan mercek neye dayanıyordu

§7, koltuk provenansını sistemin **en yüksek itibar riski** sayar ve kuralı
kendisi yazar: *"Bir koltuğun ağzına, o kişinin belgelenmiş görüşüyle çelişen
bir söz asla konmaz."* K-14 bu kuralın hiçbir mekanizması olmadığını buldu;
K-15 altıncı kapıyı ekledi ve her koltuk artık bir `## Kaynak durumu` beyanı
taşımak zorunda.

**Kapı beyanın VARLIĞINI görür.** Beyanın kendisi ise adı geçen **eserlere**
dayanır — *Anatomy of a Merger* (1975), *A Manual of Style for Contract
Drafting*, *Tools and Weapons*. On üç koltuk, **gerçek ve çoğu yaşayan**
hukukçuların adını taşıyor.

Yirmi altı tur boyunca hiç kimse o eserlerin **var olup olmadığını** sormadı.
kural 1'in kanıt kuralı — *"Her rakam, tarih, eşik, süre ve alıntı dayanağını
yanında taşır"* — §7'nin en çok
önemsediği iddialara **uygulanmamıştı**: gerçek kişilerin ağzına konan bir
mercek, **doğrulanmamış bir bibliyografyaya** dayanıyordu.

**Altısı da doğrulandı** (2026-08-28, `ks_h_kaynaklar.md` H-20..H-26) ve
hepsi gerçek çıktı: Adams'ın ABA kılavuzu, Freund'un 1975 tarihli *Anatomy of a
Merger*'ı (koltuktaki **tarih doğru**), Freund'un *Smart Negotiating*'i,
Heineman'ın *The Inside Counsel Revolution*'ı, Smith'in *Tools and Weapons*'ı,
Ustaran'ın *The Future of Privacy*'si — ve Lipton'ın 1982'de zehir hapını
tasarladığı iddiası.

**Bir kusur çıktı:** *Tools and Weapons* **ortak yazarlıdır** (Carol Ann
Browne) ve koltuk ortak yazarı anmıyordu. Bir merceği tek kişiye atfederken
kaynağın ortak yazarlı olduğunu söylememek, §7'nin "belgelenmiş görüş"
ölçütünü sessizce genişletir. Koltuk düzeltildi ve AI-04 bunu kalıcı olarak
ölçüyor.

> Ve takım **kendi kaydımdaki bir eksiği** yakaladı: aramada *The Future of
> Privacy*'yi doğruladım ama tabloya **yazmayı unuttum**. Doğrulamak ile
> doğrulamayı KAYDETMEK ayrı işlerdir; kaydedilmeyen bir doğrulama, bir sonraki
> okuyucu için yapılmamıştır.

Mutasyon dörtte dört. En anlamlısı dördüncüsü: **boş bırakılan bir koltuğu akla
yatkın bir metinle doldurmak** — §7'nin *"bu sistemin yapabileceği en tehlikeli
çıktı"* dediği şey — artık AI-05 ile kırmızıya dönüyor.

---

## Yedi buçuk artı yirmi yedi · Çalıştığını bildiğim kanalı yirmi yedi tur kullanmadım

Üç ENGELLEYİCİ mevzuat bulgusu yirmi yedi turdur açık. Gerekçe her seferinde
aynıydı: *birincil kaynağa erişilemiyor.* O olumsuz iddia §2 uyarınca kanal
kanal kanıtlanmıştı ve tablonun son satırı şunu yazıyordu:

    | WebSearch | aynı alan adları | **çalışıyor** |

**Kayıt doğruydu. Ben yanlış okudum.** Yanındaki "arama motoru özeti
döndürür" notunu *"işe yaramaz"* diye anladım ve üç bulguyu, çalıştığı
**kayıtlı** olan bir kanalı hiç zorlamadan açık tuttum. Yirmi yedinci turda
koltuk dayanaklarını doğrulamak için o kanalı kullandım — ve o an fark ettim
ki aynı kanal, yirmi yedi turdur bekleyen üç bulgu için hiç denenmemişti.

Bu turda üçünde de sistematik olarak kullanıldı. **Üç hipotezin üçü de
bağımsız meslek kaynaklarınca doğrulandı:**

| Bulgu | Kitabın yazdığı | Kaynakların yazdığı |
|---|---|---|
| **I-01** | 250M eşiği yalnızca **B ayağına** | *"…birleşme işlemleri **ile** bu nitelikteki teşebbüslerin devralınmasında…"* — **her iki ayak** |
| **I-02** | "faaliyet gösteren ya da Ar-Ge yapan" | *"istisnanın uygulaması **'Türkiye'de yerleşik'** teşebbüslerle **sınırlanmış**"* |
| **I-03** | bekletici etki **m.11** | m.10 = *"Birleşme ve Devralmaların Kurula Bildirilmesi"* (askıya alma + 30 gün); m.11 = *"…Bildirilmemesi"* |

I-03 artık yalnızca **şüpheli değil, pozitif olarak çelişilmiş**: madde
başlıkları iki bağımsız kaynakta okundu.

### Ve üçü de KAPATILMADI

İkincil kaynak birincil metnin yerine geçmez. Doğrudan çekme dört Türk alan
adında hâlâ `EGRESS_BLOCKED` veriyor; birebir Tebliğ ve Kanun metni
okunamadı. Bir eşik ya da madde numarası düzeltmesi §9 uyarınca **insan
kararıdır**. Üçü de ENGELLEYİCİ kalıyor ve denetim hâlâ **3** ile kırmızı —
AJ-04 bir yükseltmenin statüyü düşürmesini, AJ-05 denetimin kırmızı kalmasını
ölçüyor.

Değişen şey **kanıt katmanıdır**: "doğrulanamadı" idi, artık "bağımsız meslek
kaynaklarınca doğrulandı, birincil metin bekleniyor". Bulguyu insana götüren
kişi için bu fark, "belki" ile "büyük olasılıkla, şu cümleyle" arasındaki
farktır.

> **Ders, kaydın yanlış olması değil — kaydın DOĞRU olması ve okunmaması.**
> Bir olumsuz iddiayı kanal kanal kanıtlamak yetmiyor; **çalıştığı işaretlenen
> her kanalın açık bulguları ne kadar ileri götürdüğü de ölçülmeli.** Ben
> kanalı sınıflandırdım ve geçtim. AJ-02 bunu artık her koşumda soruyor.

---

## Yedi buçuk artı yirmi sekiz · "Engelleyici değil", "doğrulanmış" demek değildir

Yirmi sekizinci tur, çalıştığı **kayıtlı** olan bir kanalın üç ENGELLEYİCİ
bulgu için yirmi yedi tur kullanılmadığını buldu ve AJ-02 bunu artık her
koşumda soruyor. **Ama AJ-02 yalnızca ENGELLEYİCİ satırlara bakıyordu.**

Kayıtta dokuz bulgu daha vardı ve hepsi *"hayır"* — engelleyici değil — diye
işaretliydi. Engelleyici olmamak, denetimi kırmızıya çevirmediğini söyler;
**doğrulanmış olduğunu söylemez.** Raporun içinde duran her açık iddia,
okuyucunun güveneceği bir iddiadır.

**Dördü bu turda doğrulandı, üçü yetkili kaynağından okundu:**

| Bulgu | Doğrulama |
|---|---|
| **G-01** | courtlistener AGPL — deponun kendi README'si: *"…copyright Free Law Project under the Affero GPL."* |
| **G-02** | *"This repository was archived by the owner on **Aug 5, 2024**."* — errata'daki tarih **birebir** doğru |
| **G-03** | kod MIT, **veri CC BY-NC 4.0** — ticari kullanım **açıkça yasak** |
| **I-04** | m.16 alt sınırı **302.484,86 TL** (2026/1 sayılı Tebliğ; %25,49 yeniden değerleme) — errata'daki rakam **birebir** doğru |

**G-03 doğrulamayla ağırlaştı.** Errata *"ticari pratikte lisans sorusu
doğurur"* diyordu. Depo *"Data files produced by OpenSanctions are licensed
under CC BY-NC 4.0"* diyor: bu bir **soru değil, yasak**. Kitap bu aracı
§13.3'te **ticari bir hukuk pratiği** için öneriyor.

### Bir bulguyu kapatmak, kanıtın TÜRÜNE bakmayı gerektirir

G-01..G-03 **depo olgusudur**; yetkili kaynağı deponun kendisidir, erişildi,
okundu — **kapatılabilir**. I-01..I-03 **hukuk metnidir**; yetkili kaynağı
birincil mevzuattır, engellidir, ve düzeltmesi §9 uyarınca insana aittir —
ikincil kaynakla ne kadar güçlenirse güçlensin **kapatılamaz**. I-04 ise
doğrulandı ama rakamı dosyaya yazmak bir mevzuat katmanı değişikliğidir;
bulgu bu yüzden silinmedi.

AK-03 bir depo olgusunun **deposundan** doğrulanmasını, AK-04 bir hukuk
bulgusunun ikincil kaynakla **kapatılmamasını** ölçüyor. Mutasyonda I-02'yi
"DOĞRULANDI" yapmak AK-04'ü kırmızıya çeviriyor — yani kanıtın türünü
karıştırmak artık sessiz kalamıyor.

### Ölçen şey, ölçtüğü şeyi kirletiyordu

Yirmi dokuzuncu turun sonunda adlandırılan eksen şuydu: otuz dört takım aynı
yardımcıyı, aynı beyan tabanını ve aynı koşum betiğini paylaşıyor — her biri
KENDİ başına mı düşüyor? Takımlar ayrı süreçler olduğu için sıra
bağımlılığının **tek kanalı dosya sistemidir**. Ölçüldü: o kanal açıktı.

**B-34 canlı ad kaydını yok ediyordu.** Vaka, kural 6'nın gerçek kişi ayağını
sınamak için `hafiza/muvekkil-adlari.txt` dosyasına bir fixture yazıyor,
aslını yalnızca bir DEĞİŞKENDE tutuyor ve `finally` ile geri koyuyordu.
`finally` SIGKILL'de (süreci hiç uyarmadan anında
sonlandıran işletim sistemi sinyali) koşmaz. Süreç o pencerede öldürüldü: dosyanın 274 baytı
gitti. Dosya `.gitignore`'da olduğu için `git checkout` ile dönülemedi —
**tek kopya ölen sürecin belleğindeydi.**

Ve arkasından gelen şey daha kötüydü. `denetim.sh` kalan sınama artığını
"1 ad" sayıyor:

| kayıt | denetimin dediği |
|---|---|
| gerçek içerik | `UYARI müvekkil ad kaydı BOŞ — kural 6'nın gerçek kişi ayağı kapsanmıyor` |
| sınama artığı | `ok    müvekkil ad kaydı    1 ad` |

**Koruma bozulurken alarm da kapandı.** Bu, kitabın §2'sindeki bir tasarım
boşluğunun ilk ölçülmüş sonucudur: gizlilik (`.gitignore`) ile dayanıklılık
(`git`) aynı mekanizmadır, biri seçilince öteki feda edilir, ve kitap bunu
söylemez. Errata'ya §2 maddesi olarak yazıldı; cevabın **altıncı** sebebi.

**S-05 canlı `sinama/` dizinine bir `.py` bırakıyordu.** Kalıntı kalınca bir
sonraki koşumda S-01 KALDI veriyor — sistemde hiçbir şey değişmemişken
uydurma bir regresyon; üstelik `sinama/*.py` sayan her şeye 34. takım gibi
görünüyor.

Doğru desen zaten ailede vardı: D `${TMPDIR}/ks_d_kum`, Z `mkdtemp` kullanıp
her şeyi kum havuzunda bozuyor. Kusur disiplinin YOKLUĞU değil, **tek tip
uygulanmamasıydı** — yirmi yedinci (AE) ve yirmi sekizinci (AF) turlarda
adlandırılan sınıfın aynısı: bir örneği düzeltmek sınıfı kapatmaz.

### Ve AL kendi kurduğu kapıdan bir bulgu daha çıkardı

AL-06 ("hiçbir takım başka bir takımın koşum kaydını okumuyor") ilk koşumda
iki bağ buldu. Biri meşru çıktı: M-03'ün okuduğu `SONUC-once.txt` **donmuş
bir arşivdir** — yamalardan önceki sadık koşumun ham çıktısı, hiçbir koşucu
onu yazmaz. Muafiyet tanındı ama **sınanmadan değil**: AL-07 tam olarak o
iddiayı ölçer (yirmi altıncı turda U-10'da sınanmamış bir muafiyetle
düştüğüm tuzak).

İkincisi gerçek ihlaldi. **AF-03, `hepsi.sh > SONUC-sonra.txt`
yönlendirmesinin kendi hedefini okuyordu** — koşum sürerken. Ölçüldü:

| AF nasıl koştu | gördüğü satır | nihai dosya |
|---|---|---|
| bağımsız | 853 (bir ÖNCEKİ koşum) | — |
| yönlendirmenin içinde | **690** | 832 |

Yani AF'den sonraki altı takım (AG, AH, AI, AJ, AK, AL) onun görüş alanının
dışındaydı. Bugün geçiyor olmasının tek sebebi beyan edilmiş her vakanın
erken bir takımda durması. **Geç bir takımda beyanlı bir vaka kaybolsa AF-03
bunu göremezdi** — tam da en çok gerekli olduğu aralığa kördü. On altıncı
turun ders ettiği katman ihlalinin veri yolundan gelen hâli, üçüncü yerde.
Çözüm de aynısı: hem beyan/BEKLENEN sağlaması hem belirti karşılaştırması
tam ve bayatlamamış günlüğü bilen tek yere — `hepsi.sh`'in epiloguna —
taşındı; AF-03 ve AF-04 o kontrolün orada DURDUĞUNU sağlar.

### Mutasyon sınaması iki kez kendi aparatımı yakaladı

Yedi vakanın yedisi de mutasyonu yakalıyor. Ama yolda iki ders çıktı:

1. **AL-01 ilk sürümde KAÇTI.** Ölçüt tam göreli yolu (`hafiza/muvekkil-
   adlari.txt`) arıyordu; kod yolu `os.path.join(_KOK_COZ, "hafiza",
   "muvekkil-adlari.txt")` diye **bileşen bileşen** kuruyor ve o dizge hiç
   geçmiyor. Ölçüt dosya adına indirildi.
2. **AL-03 sahte bir GEÇTİ verdi — sebebi ölçüm değil, benim kanıtımdı.**
   Mutasyonun indiğini kanıtlamak için T takımını koşturdum; T de mutasyon
   gereği ağaca `AL_KIRLET.txt` yazdı. Böylece dosya AL'in "önce"
   anlık görüntüsüne de girdi ve fark yok oldu. **Mutasyonun indiğini
   kanıtlama eylemi, ölçülecek farkı yok etmişti.** Kanıt ile ölçüm ayrı kum
   havuzlarına alındı; AL-03 mutasyonu yakaladı.

İkincisi, "mutasyon indiğini kanıtlamadan okuma" kuralının bir adım
ilerisidir: **kanıtın kendisi de ölçüme karışmamalıdır.**

### AL-02 şansa bağlıydı, ölçüme çevrildi

İlk tasarım takımı 0.05/0.12/0.25/0.40 saniyede öldürüp korunan dosyaya
bakıyordu. Pencere birkaç milisaniye olduğu için vuruş şansa kalıyordu — ve
mutasyonda B-34 canlı kayda döndürüldüğünde **AL-02 kırmızıya dönmedi**.
Şansa bağlı bir vaka, vaka değildir. Yeni tasarım daha güçlü bir şey ölçer:
bir gözcü iş parçacığı korunan dosyaları yüksek frekansla örnekler ve
**koşum sırasında hiçbir an değişmediğini** gösterir. Kanıt olarak alınan
örnek sayısı yazılır, yani vakuum değildir.

### Eşik değişti — hangi müvekkile artık yanlış olan bir şey söyledik?

Otuzuncu tura kadar ölçülen her şey **aparata** dairdi. Otuz birinci tur iş
ürününe bakıyor: bir eşik değişince, o eşiğe dayanarak verilmiş görüşe ne
oluyor?

Kitap riski **kendi sözleriyle** adlandırıyor. §11'in `/esik-denetle` komutu:

> "Hiçbir dosyayı düzenleme — bir eşik değişikliği insan kararıdır, çünkü
> **canlı bir dosyada verilmiş bir görüşü geçersiz kılabilir.**"

ve şöyle bitiyor:

> "Şununla bitir: kaç eşik kontrol edildi, kaçı bayat ve şu anda **hangi
> dosyalar** bayat bir rakama dayanıyor."

Ama prosedürünün birinci adımı yalnızca `birimler/*/yontem/` altını tarıyor.
Ve §2 kitabın kendi sözlüğünü kuruyor: *"`dosyalar/` **canlı işleri** …
tutar."* Yani **kapanış cümlesinin vaadi canlı işler üzerinde; prosedür o
dizini hiç açmıyor.** Komut, doktrindeki rakamın bayatladığını söyleyebilir;
o rakama dayanarak müvekkile ne söylendiğini söyleyemez.

İkinci yol da kapalıydı: `dosyalar/` kural 6 gereği `.gitignore`'dadır, yani
sürüm geçmişinden de sorulamaz. Sorunun iki cevap yolu vardı, **ikisi de
kapalıydı** — ve bu, otuzuncu turun §2 bulgusunun ikinci yüzüdür: aynı
gizlilik mekanizması orada **dayanıklılığı**, burada **geriye dönük erişimi**
feda ediyor.

Yama, komutu kendi vaadine eşitler: canlı iş katmanı eklendi, bir dosyanın
değişmiş eşiğe dayanması **ETKİLENEN**, hangi sürüme dayandığını hiç
yazmamış olması **SÜRÜMSÜZ** olarak işaretlenir. "Hiçbir dosyayı düzenleme"
aynen korundu — §11 uyarınca eşik değişikliği insan kararıdır — ve tablonun
makinede kalması kural 6 gereği açıkça yazıldı.

**Haksız suçlama yapılmadı.** AM-02 olumlu kontroldür: kitapta bayatlığı
fark eden bir mekanizma **vardır**. Bulgu "mekanizma yok" değil,
**"mekanizmanın erişimi eksik"**. AM-04 de temiz çıktı: §3'ün "altı ay"ı,
komutun "altı aydan eski"si ve kapının `BAYAT_GUN = 183`'ü aynı süreyi
söylüyor.

### Bu turda takım iki kez kendi kusurunu gösterdi

1. **AM-01 önce vakum geçti.** Ölçüt vaadi `hangi dosyalar[^\n]*bayat` diye
   arıyordu; komutun kapanış cümlesi tam da o iki kelimenin **arasında satır
   kırıyor**. Desen eşleşmedi, vaka yeşile döndü. Yirmi dokuzuncu turda AI-02
   aynı tuzağı yakalamıştı: satır kırılması bir metnin anlamını değiştirmez,
   ölçütün ona duyarlı olması bir **ölçüm kusurudur**.
2. **Sonra ölçüt yorumla tatmin oluyordu.** Yamayı açıklayan HTML (web sayfalarının
işaretleme dili) yorumu
   `dosyalar/` sözcüğünü içeriyordu; mutasyonda prosedürün tamamı silinse
   bile vaka yeşil kalıyordu — yani ölçüt **prosedürü değil, prosedürden söz
   eden bir cümleyi** ölçüyordu. AF-02'nin sınıfı. Yorumlar ölçüm dışına
   alındı; mutasyon o zaman yakalandı.

İkisi de aynı şeyi söylüyor: **bir ölçüt, ölçtüğünü sandığı şeyi ölçtüğünü
ancak mutasyon gösterdiğinde bilir.**

### Yamanın kendi kabul sınaması, yamanın açtığı deliği buldu

Bir yama, işe yaradığı **gösterilene** kadar bir iddiadır. Otuz birinci turun
yaması `/esik-denetle`'ye canlı iş katmanı ekledi; otuz ikinci tur onu
sınadı — ve önce bir hipotez **çürüttü**.

**Çürüyen hipotez de bir ölçümdür.** Hipotez şuydu: *"belki hiçbir çıktı
hangi rakama dayandığını yazmıyor; o hâlde SÜRÜMSÜZ her zaman doğru olurdu
ve yama boş bir tespit üretirdi."* Kitabın kendi çıktı sözleşmesi (§15.1)
bunu çürütüyor — çıktı *"kullanılan rakamlar ve her birinin nereden geldiği"*
ile doğrulama tarihini istiyor. Yama boşluğa değil, kitabın kendi
sözleşmesine dayanıyor. Kitabı haksız yere suçlamamak, onu doğru yerde
suçlamak kadar işin parçasıdır.

Asıl bulgu ikinci soruda çıktı. Yama, satırları **müvekkil dosya adlarını**
taşıyan bir tablo üretiyor ve "bu tablo makinede kalır" diyor. O cümle
kapıya sorulmalıydı. Soruldu:

| dışarı giden metin | kapı ne yaptı |
|---|---|
| `dosyalar/Acme-Gida-devralma/ ETKİLENEN` | **hiçbir kapı ateşlemedi** |

§12'nin sır kapısı işlem kod adına, `A.Ş.`/`Ltd. Şti.` ekli şirket unvanına,
işlem bedeline ve ad kaydına bakıyor. Bir dosya yolu bunların hiçbirine
uymaz: ASCII'ye katlanmış, tirelenmiş, eksiz. Oysa §2 sözlüğünde
`dosyalar/` **canlı işleri** tutar — altındaki somut bir ad, tanımı gereği
müvekkil kimliğidir.

**Ve boşluk yamanın açtığı bir boşluk değildi.** §9'un `dosya-ac` becerisi
her işi `dosyalar/<ad>/` klasörüyle açıyor ve çıktıları
`dosyalar/<ad>/cikti/` altına yazıyor; yani sıradan bir oturum bu biçimde
metni **zaten** üretiyor. Yama yalnızca boşluğun üstüne bir ışık tuttu.
Kapıya somut canlı iş yolu kuralı eklendi; yer tutucular (`dosyalar/`,
`dosyalar/*/`, `dosyalar/<is>/`) ateşlemez — kitabın kendi metni ve bu rapor
onları kullanıyor — ve otuz yedi takımın hiçbirinde yanlış pozitif üretmedi.

**On dördüncü, on dokuzuncu ve yirmi birinci turların sınıfı, dördüncü kez:**
bir kaçırmayı kapatmak ölçülmemiş bir eksen açar. Fark şu ki bu kez eksen,
yama hiçbir yere gitmeden önce **kendi kabul sınamasında** yakalandı.

### Ve errata izlenebilirliği yeni bir bulguyu anmayı imkânsız kılıyordu

Yeni §12 maddesi kusuru bulan vakayı — AN-05 — anınca **M-03 kırmızıya
döndü**. Sebebi haklı bir kuralın fazla dar hâliydi: M-03, her ağır errata
maddesinin atfının **kitaba sadık koşumda** KALDI olmasını istiyordu. Ama
sadık koşum yamalardan önceki ham çıktıdır; o sırada var olmayan bir takımın
vakası orada hiç görünemez. Yani kural, sonraki turlarda bulunan bir kusuru
**doğru kimliğiyle anmayı** imkânsız kılıyor ve maddeyi yanlış bir vakaya
bağlamaya itiyordu.

Ölçüt ikiye ayrıldı — ve iki dalda da gerçek bir şart var, hiçbir madde
şartsız kalmıyor:

| takım sadık koşumda | şart |
|---|---|
| **vardı** | atıf orada KALDI olmalı *(eski güç aynen)* |
| **sonradan yazıldı** | atıf, gerçekten **tanımlı** bir vaka olmalı |

Mutasyon ikisini de sınıyor: uydurma bir kimlik (`AN-99`) anmak kırmızı
veriyor; sadık koşumda **geçmiş** bir taban vakası (`B-01`) anmak da kırmızı
veriyor. Bir kuralı gevşetmek, onu ölçmez hâle getirmez.

### Fixture'ın kendisi bir kez yanılttı

AN-02 ilk koşumda kırmızıydı ve sebebi sistem değildi: "eski" örnek dosyaya
gerçekçi görünen eşik rakamları yazmıştım ve ikisi de **hâlâ yürürlükteki**
sabitlere denk geldi, dolayısıyla "artık geçerli olmayan rakam" kümesi boş
çıktı. Rakamlar açıkça uydurma olanlarla değiştirildi — çünkü sınanan şey
karşılaştırmanın **yapılabilirliğidir**, belirli tarihsel eşiklerin
doğruluğu değil; gerçek bir tarihsel rakam yazmak §11'in mevzuat katmanına
birincil kaynaksız bir iddia sokardı.

### Çatışma kontrolü tek yönlü bakıyordu — ve yalnızca bir an

§8 tek cümledir: *"Bir dosya **açılmadan önce** `hafiza/cikar-catismasi.md`
**karşı taraflar için** kontrol edilir. Çatışma bir uyarı değil, durma
sebebidir."* `/dosya-ac` bunu birebir uyguluyor: *"verilen **karşı taraf**
adlarını ara."* O cümlede iki bağ var ve ikisi de sınanmamıştı.

**Yön.** Çatışma simetriktir ve en ağır hâli tersidir: yeni dosyanın
**müvekkili**, açık bir dosyanın **karşı tarafı** olabilir — yani şu anda
aleyhine çalıştığımız kişi için çalışmaya başlarız. Kaydın kendi biçimi
(`<taraf adı> · <dosya> · <hangi tarafta> · <tarih>`) bu soruyu cevaplayacak
veriyi **zaten taşıyor**; prosedür hiç sormuyordu.

**Zaman.** Kontrol açılış anına bağlıydı. Kayda sonradan bir ad girdiğinde
çatışma **o an doğar** ve hiçbir şey geriye bakmıyordu. Bu, otuz birinci
turdaki eşik sorusunun çıkar çatışması ayağındaki hâlidir — ve aynı kök:
**kitap kontrolleri olaylara değil anlara bağlıyor.**

Kitap iki şeyi doğru yapıyor; ikisi de olumlu kontrol olarak tutuldu (boş
kayıt "temiz" sayılmıyor; eşleşme durma sebebi). §18.9 sınırı da dürüstçe
beyan ediyor — ama o sınır **açıklanmamış** ilişkilere dairdir; yön ve zaman
boşluğu **açıklanmış** ilişkilerde bile açıktı.

**Yamanın sınırı açıkça yazıldı:** neyin çatışma *sayıldığına* karar
verilmedi. O bir meslek kuralları meselesidir ve §9 uyarınca insana aittir;
yalnızca mekanik kontrolün iki yönü de kapsaması sağlandı.

### Aynı ölçüt üç kez fazla geniş çıktı

AO-02 bu turda üç kez yeşil verdi ve üçü de yanlıştı — üçü de tek bir
sınıfın örneği: **yakınlık kanıt değildir.**

| ölçek | neyi yakaladı | neden yanlıştı |
|---|---|---|
| 600 karakterlik **pencere** | "müvekkil" | üçüncü adımdan geliyordu — KAPSAM.md'ye *yazan* bir talimattan |
| **cümle** | "müvekkilinin" | yamanın *açıklama* cümlesiydi, iki nokta üst üstenin ardında |
| `ara\b` | — | Türkçe çekimi görmüyor: "aranır" = ara + ek *(AE sınıfı, beşinci kez)* |

Ölçüt sonunda **cümleciğe** indirildi: bir cümlecik hem arama fiilini, hem
müvekkili, hem de neyin içinde arandığını taşımak zorunda. Ancak o zaman
mutasyon (beceriden müvekkil aramasını çıkar) yakalandı.

**Ve AO-05 kendi yamamı yakaladı:** cümleye bir ara söz eklemek
("eşleşme varsa —hangi yönde olursa olsun— DUR") ölçütün aradığı dizgeyi
bozdu. Ölçüt bir *cümleyi* değil bir *anlamı* sınamalıydı; öyle yapıldı.

### Kök üçüncü kez göründü — ve bu kez kontrol kurulmuyordu bile

Otuz üçüncü tur bir kök adlandırdı: **kitap kontrolleri olaylara değil
anlara bağlıyor.** İki örneği vardı (§11 eşikler, kural 8 çatışma). Kök mü,
tesadüf mü? Üçüncü bir yere bakıldı: §13 araç kataloğu — kaydettiği her alan
(lisans, yıldız, son güncelleme) zamanla bozulur ve kitabın **Karar** sütunu
onlara dayanır.

Ölçüm beklediğimden ağır çıktı. **§13'ün kataloğu kurulumda hiçbir dosya
bırakmıyor.** §2 yalnızca `birimler`, `emsal`, `hafiza`, `dosyalar`, `cikti`
klasörlerini açıyor; hiçbiri araç kataloğu için değil. Kitap "Hepsi 27
Ağustos 2026 tarihinde GitHub API'siyle doğrulandı" diyor — ama o cümle
**kitapta**, kurulan sistemde değil. Kurulumu yapan hukukçunun elinde hangi
aracın incelendiğine dair yerel bir kayıt, eskiyecek bir doğrulama tarihi ve
§16'nın bakabileceği bir şey yok. Karar yazılı; kararın dayandığı olgular
bozuluyor; ikisi arasındaki bağ kurulumda hiç yok.

**Ve kitabın kendi tazeleme aracı, kararı değiştiren iki alanı hiç
okumuyor.** `once-arastir` API'den dört alan alıyor:

| alan | var mı | neden önemli |
|---|---|---|
| `license.spdx_id` | ✓ | yalnızca **kod** lisansı |
| `stargazers_count` | ✓ | — |
| `pushed_at` | ✓ | bakımın **vekili** |
| `archived` | **yok** | bakımın **olgusu** |
| veri lisansı | **yok** | ticari kullanımı yasaklayabilir |

İkisi de varsayımsal değil, yirmi dokuzuncu turda ölçüldü. §13.4'ün
`google/diff-match-patch` için yazdığı *"burada eskime bozulma değildir"*
gerekçesi, deponun **5 Ağustos 2024'te arşivlendiği bilinmeden** yazılmış —
ve kitabın kendi aracı çalıştırılsaydı **bile** bunu göremezdi, çünkü
`archived` alanını okumuyor. `opensanctions` ise kodu MIT iken **verisi
CC BY-NC 4.0**: ticari kullanıma kapalı, ve kitap onu ticari bir hukuk
pratiği için öneriyor. Tek "Lisans" sütunu bu ayrımı **yapısal olarak**
taşıyamaz.

Yama `hafiza/arac-katalogu.md` dosyasını kuruyor. Kuralı şu: her satır
**bizim** doğrulama tarihimizi taşır — kitabın beyanı bizim doğrulamamız
sayılmaz — ve doğrulanmamış bir satır "temiz" değil **kontrol edilmedi**
demektir. `once-arastir` beş alanı okuyacak ve veri lisansını ayrıca soracak
biçimde genişletildi.

### Kendi yamalarım ölçümü kirletiyordu

AP-01 ilk koşumda **yeşil** verdi ve yakaladığı dosya
`hafiza/dogrulama-bulgulari.md` idi — yani *benim* kör sınama sırasında
ürettiğim bir teslimat, kitabın kurduğu bir şey değil. **Kendi yamalarım
ağaçta dururken kitabı ölçmek, ikisini birbirine karıştırır ve kitabı
olduğundan iyi gösterir.** Ölçüt §13'ün kendi yapısına indirildi: bir
katalog, satır satır her depoyu bir lisansla ve bir kararla eşleştirir; açık
bulguları anlatan bir düzyazı dosyası bunu yapmaz.

Ve takım yazıldığı turda iki kez daha yakalandı: **AE-03** yeni takımdaki
çıplak `.lower()`'ı buldu — sınıfın altıncı sızması, ve "depo adları ASCII,
bu örnek zararsız" muhakemesi tam olarak sınıfı dört kez besleyen
muhakemedir; **AH-03** ise iki `[A]` maddesinden birinin cevap beyanı
taşımadığını gösterdi.

### Sınıf tarandı — ve en ağır sonuçlu boşluk imzayla kapanış arasındaydı

Kök üç kez göründüğüne göre artık bir sınıftı, ve yirmi yedinci turun dersi
şuydu: **bir örneği düzeltmek sınıfı kapatmaz.** Bu yüzden sistemdeki bütün
kontrol noktaları tarandı:

| kontrol | neye bağlı | hüküm |
|---|---|---|
| altı **kapı** | yazma anı | **doğru** — saklanan sonuç yok, metni üretildiği anda denetler |
| **denetim** (26 kontrol) | çağrılma anı | **doğru** — yapıya bakar; yapı dış olayla bozulmaz |
| eşik · çatışma · katalog | an | 31, 33, 34. turlarda yamalandı |
| **`yaptirim-taramasi`** | üç an | sonucu **en hızlı** bozulan kontrol |

Yaptırım taraması kitabın zaman sorusunu **en iyi sorduğu** yerdir: üç
kontrol noktası verir — *"gizlilik sözleşmesinden önce, münhasırlıktan önce,
imzadan önce."* Ama üçü de **imzaya kadardır.** Ve kitabın kendi §5.1'i
şunu yazıyor:

> "…Kurul açıkça ya da inceleme süresinin dolmasıyla zımnen karar vermeden
> hukuken geçerlilik kazanmaz. **İmza serbesttir; kapanış değildir.**"

Yani en uzun maruziyet aralığını **kitabın kendi tasarımı** yaratıyor: izin
beklemesi ayları bulabilir, yaptırım listelerine atama ise haftalıktır. Ve
kapanış kontrol listesinde yeniden tarama adımı **yok** — liste izin
yazısını ve organ kararlarını teyit ediyor, tarafların **hâlâ temiz olup
olmadığını** sormuyor.

**Bu, incelemede bulunan en ağır sonuçlu boşluktur.** Yanlış bir eşik hesabı
bir bildirim yükümlülüğünü etkiler; bu boşluk işlemin **tamamlanmasının
hukuka uygun olup olmadığını** etkiler. Kontrol noktaları dörde çıkarıldı ve
`kapanis-listesi`ne 0. adım olarak yeniden tarama eklendi — tarama yine bir
karar değil, ve sorgu soyutlama kuralı orada da mutlak.

Kitabın burada doğru yaptığı şey olumlu kontrol olarak tutuldu:
*"Tarama karar değildir. Bir ad eşleşmesi bir ipucudur."*

**Düzeltme (kırk birinci tur).** Bu paragraf önce kitaba ikinci bir cümle
daha atfediyordu — *"eşleşmenin yokluğu temizlik kanıtı değildir"* — ve
kitabı boş sonuç tuzağını kapattığı için övüyordu. **O cümle kitapta yok.**
Onu `yaptirim-taramasi` becerisini yazarken ben ekledim ve altı tur sonra
kendi yamamı kitabın metni sanıp kitaba kredi verdim. Otuz dördüncü turda
AP-01'in kendi teslimatımı kitabın eseri sanmasıyla aynı sınıf: **kendi
yamalarım ağaçta dururken kitabı ölçmek ikisini karıştırır** — orada kitabı
olduğundan iyi göstermişti, burada da öyle.

### Yakınlık tuzağı bu oturumda dördüncü kez — hep kendi ölçütümde

AQ-01 ilk sürümde başlıktan sonraki **300 karaktere** bakıyordu. Yama o
pencereye bir açıklama paragrafı ekleyince, mutasyonda kontrol noktası geri
alınsa bile pencerede "kapanış" kaldığı için vaka yeşil kalıyordu. AQ-03 ise
`re.I` yüzünden bir **başlığa** ("İzin Alın") takılıyordu — kuralın kendisine
değil.

Dördüncü kez aynı ders, artık kural olarak yazıldı: **iddiayı taşıyan en
küçük sözdizimsel birimi ölç — cümle ya da cümlecik — asla bir karakter
penceresi. Pencere, komşuyu kanıt sanar.**

Ve mutasyonun kendisi de iki kez satır kırılmasına takıldı: dosyada
`geçerlilik\nkazanmaz` diye bölünmüş olan ifadeyi ham metinde aradığım için
mutasyon inmedi. Takım metni düzleştirip baktığı için **doğru** olan taraftı;
yanılan ölçüm değil, mutasyondu.

### Onay ihtiyacının beyanı, onayın kendisi değildir

Otuz beşinci turun taraması her kontrolü *neye bağlı* diye sınıfladı.
Sormadığı soru şuydu: bir kontrol, **onay gerektiğini söylemekle onayın
verildiğini kaydetmeyi** ayırt edebiliyor mu?

kural 9 açık: *"Şu çıktılar **adı belli bir insan onaylamadan kullanılmaz**:
müvekkile ya da karşı tarafa gidecek her şey, her başvuru metni, yönetim
kuruluna sunulacak her rakam ve süreye bağlı bir adımda dayanılacak her Türk
hukuku beyanı."* §12'nin kapsam kapısı ise *"Yetkili avukat görüşü gereken
konular"* **başlığının** varlığını arıyor — ve o başlık bir onay kaydı değil,
onay **ihtiyacının beyanıdır.** Tam tersi.

Ölçüldü, iddia edilmedi. Müvekkile giden, başlığı usulünce taşıyan, hiçbir
onay kaydı olmayan bir metin `disari=True` ile kapılara verildi:

| metin | ateşleyen kapı |
|---|---|
| müvekkile giden, başlıklı, **onaysız** | **hiçbiri** |

Kitap onay verecek kişinin **adını** kaydediyor (KAPSAM.md'de "İnsan onayı
verecek kişi"). Yani sistem **kimin onaylayacağını** biliyor; **onayladığını**
hiçbir yerde kaydetmiyor.

**Yedinci kapı eklendi — ve kuralı dikkatle seçildi.** Kusur onayın *yokluğu*
değildir: bir taslak taslak olduğunu söyleyebilir, bir inceleme
onaylanmadığını yazabilir. **Kusur, onay durumu hakkındaki sessizliktir** —
onaylanmış gibi görünen sessizlik. Kapı ya bir onay kaydı
(`Onay: <ad soyad> · <YYYY-AA-GG>`) ya da açık bir durum beyanı (`TASLAK` /
`onaylanmamıştır`) ister.

Bu ayrım keyfî değil, bu incelemenin kendi durumunu da doğru sınıflandırıyor:
**bu rapor onaylanmamıştır ve bunu açıkça yazar** — dolayısıyla kapıdan
geçer. Kuralı kendi teslimatını haksız yere bloklayacak biçimde yazmak da,
kendi teslimatına muafiyet tanıyacak biçimde yazmak da yanlış olurdu; ölçüt
ikisini de yapmıyor. AR-04 raporun bu beyanı taşımaya devam ettiğini her
koşumda sınar; mutasyonda beyan kaldırılınca kırmızıya döner.

Ve AR-05 ters yönü tutuyor: onay kaydı taşıyan **aynı** metin susmalı. Kapıyı
fazla geniş yapan bir mutasyon (onay kaydını da yok say) AR-05'i kırmızıya
çeviriyor — V takımının dersi, yedinci kapıya uygulanmış hâli.

### Kitabın merkezî kusurunu, kitabı yamalarken ben de işledim

Bu raporun **birinci** bulgusu şudur: §14 beşinci kapıyı ekler ve §12'nin
dokuz vakalık öz-sınamasının beklenen kümelerini güncellemez; zincir §16'yı
kırmızıya, oradan kurulumu durdurmaya götürür.

Otuz altıncı turda **yedinci kapıyı ekledim ve öz-sınamaya tek bir vaka
yazmadım.**

| kapı | öz-sınamada beklenen olarak geçtiği vaka |
|---|---|
| kapsam · kanit · koltuk | 1 |
| sir | 2 |
| guncellik · arastirma | 3 |
| **onay** | **0** |

Öz-sınama `SELFTEST OK (20 vaka)` demeye devam etti — **kapı eklenmeden önce
de 20 diyordu.** Yani yeni kapı hiç sınanmadan yeşil göründü. Kırk bir takımın
hiçbiri görmedi, çünkü görecek bir ölçüt yoktu.

Bu, incelemenin en özeleştirel bulgusu ve aynı zamanda en öğretici olanı:
**bir kusuru teşhis etmek, ona bağışıklık kazandırmıyor.** Kitabın §14'te
yaptığını, kitabın §14'ünü eleştiren rapor yazılırken ben yaptım.

Yama iki katmanlı. Örnek: yedinci kapı için dört yönlü öz-sınama vakası
eklendi — sessizlik ateşler, onay kaydı susturur, taslak beyanı susturur,
içeride hiç ateşlemez (öz-sınama artık 24 vaka). **Sınıf:** AS-01,
`denetle()`'nin çağırdığı kapıları **kaynaktan okuyup** her birinin
öz-sınamada beklenen olarak geçtiğini her koşumda sorar. Elle yazılmış bir
kapı listesi de bayatlardı (AF'nin dersi); liste koddan türetiliyor.

Ve AS-05 kapsamanın bir **sayım değil davranış** olduğunu tutuyor: her kapı
için ateşleyen ve susan birer metin verilir, kapı ikisini ayırmalı. Kapıyı
fazla geniş yapan mutasyon AS-05'i kırmızıya çeviriyor.

### Denetimin 26 kontrolünden dokuzu hiç sınanmamıştı

Otuz yedinci tur "her kapının bir öz-sınama vakası olmalı" sınıfını kapattı.
Aynı soru bir katman aşağıda hiç sorulmamıştı: **denetimin kontrollerinden
kaçı mutasyonla sınanıyor?**

Çıkarım yapılmadı, ölçüldü. D'nin on beş mutasyonu tek tek koşuldu ve her
birinin **hangi** kontrolü HATA'ya düşürdüğü kaydedildi:

| | |
|---|---|
| sınanan kontrol | **17** |
| **hiç sınanmamış** | **9** |

Sınanmayanlar: uzmanlık birimleri · her birimin INDEX.md'si · koltuk kapısı
gerçekten bloklıyor · errata izlenebilir · olumsuz iddia kanıtlı · raporun
beyan sayısı · her takım tabloda · teslimatlar tarih taşıyor · kimlik yolları
`.gitignore`'da.

Bu, raporun **üçüncü** bulgusunun ölçüm tarafındaki hâlidir — kitabın on bir
kontrolünden altısının hiçbir koşulda başarısız olamaması. Kitabı o ölçütle
eleştirirken kendi denetimimin dokuz kontrolünü aynı ölçüte tabi
tutmamıştım. **Doğru ifade "dokuz kontrol bozuk" değil, "dokuz kontrol
sınanmamış"tır**: üçünün çalıştığını bu oturumda kendi gözümle gördüm —
ama görmek sağlama değildir.

### Mutasyon "kırmızıya döndü mü" diye soruyordu, "hangisi" diye değil

İkinci kusur ölçümün kendisindeydi. D yalnızca denetimin çıkış koduna
bakıyordu. Ölçüldü ki *"bütün becerileri sil"* mutasyonu hem hedeflenen
`beceriler (>=11)` kontrolünü **hem de alakasız** bir kontrolü kırmızıya
çeviriyor. Yani hedef kontrol hiç çalışmasa bile mutasyon "yakalandı"
sayılabilirdi — **iddia ettiği şeye bakmayan bir kontrolün, ölçüm tarafındaki
hâli.** Artık her mutasyon hedef kontrolünü beyan ediyor ve D o kontrolün
HATA verdiğini doğruluyor. Küme 15'ten **27'ye** çıktı.

### Ve takımın cevabı çağıranın ortamına bağlıydı

Sayıları güncellerken AF-05 kırmızıya döndü: rapor "27/27" diyordu, AF ise
"24/27" görüyordu. Sebep bir bookkeeping hatası değildi.

| koşum | sonuç |
|---|---|
| `bash ks_d_denetim.sh` | **27/27** |
| `MAFIRM=… bash ks_d_denetim.sh` | **24/27** |

Dışarıdan `MAFIRM` verildiğinde (ki `hepsi.sh` ve AF öyle yapıyor) kum
havuzundaki `denetim.sh` onu **miras alıyor** ve canlı ağacı denetliyordu.
Denetimin üç kontrolü Python takımlarına devrediyor; o takımlar da kökü
`MAFIRM`'den çözüyor — dolayısıyla kum havuzuna uygulanan mutasyon
görünmüyordu. Yirmi birinci turda kurulan AC sınıfı (ortam bağımsızlığı),
bu kez mutasyon harnessinin içinde. Kum havuzu kökü sabitlendi; her iki
koşum da 27/27.

### Teslimat listesi elle yazılmıştı ve dört tur boyunca bayattı

Yeni mutasyonlardan biri —*"bir teslimattan doğrulama tarihini sil"*—
denetimi **kırmızıya çevirmedi.** Sebebi: P'nin teslimat listesi elle
yazılmıştı ve otuz dördüncü turda eklediğim `hafiza/arac-katalogu.md` o
listeye hiç konmamıştı. **Kendi eklediğim teslimat, dört tur boyunca kendi
güncellik kuralımın dışında durdu.**

İncelemenin ikinci sınıfı (elle yazılmış sayı ve listeler ölçtükleri şeyden
ayrışır), yine kendi aparatımda. Liste **tersine çevrildi**: teslimatlar
keşfedilir, muafiyetler beyan edilir. Muafiyet listesi küçük ve durağandır
(kitabın CLAUDE.md'si, canlı çatışma kaydı ve şablonu); teslimat listesi
büyüyen taraftır. Yeni bir teslimat eklendiğinde artık hiçbir şey yapmak
gerekmiyor — kural kendiliğinden ona da uygulanıyor.

### "Pahalı olduğu için ölçmedim" bir gerekçe değildir

Otuz sekizinci tur denetimin 26 kontrolüne "her kontrolün kanıtlanmış bir
mutasyonu olmalı" ölçütünü uyguladı. Aynı ölçüt bir katman **yukarıda** hiç
uygulanmamıştı: koşum betiğinin epilogu dört kontrol taşıyor ve hiçbiri
mutasyonla sınanmamıştı.

Sebebi teknikti ve dürüstçe adlandırmak gerekir: bir epilog kontrolünü kırmak
**o turdaki kırk üç takımın tamamını** koşturmayı gerektiriyordu (~60 sn). Dört kontrol
için dört tam koşum — dört dakika. Ölçüt uygulanmadı çünkü **pahalıydı.** Bu,
incelemenin baştan beri kabul etmediği gerekçedir.

Çözüm kontrolü zayıflatmak değil, **saf bir fonksiyona çevirmek** oldu.
`sinama/epilog.py` artık `(günlük, taban, rapor)` alıp uyarı üretiyor;
`hepsi.sh` onu hâlâ tam günlüğü bilen tek yerden çağırıyor — **katman
korundu** — ama sınama sentetik bir günlükle yapılabiliyor:

| | önce | sonra |
|---|---|---|
| epilog kontrollerinin sınanması | 4 tam koşum ≈ **4 dk** | 7 vaka · **32 ms** |

Sınanan şey bir **kopya değil**: üretimde koşan kodun kendisi. AU-07 çağrının
yerinde durduğunu ve gömülü kopyanın kalmadığını sağlıyor — yoksa takım bir
kopyayı sınayıp hiçbir şey kanıtlamazdı.

Ve ayrıştırmanın yan faydası hemen görüldü: **AE'nin desen taraması o kodu
hiç görmüyordu**, çünkü AE `.py` tarar ve kod bir `.sh` içindeydi. Dosyaya
çıkar çıkmaz AE Türkçe metin üzerinde **çıplak `.lower()`** buldu — sınıfın
yedinci sızması, dört tur boyunca taramanın kör noktasında duruyordu.

### Bir ölçüt kırmızı verdiğinde, önce ölçütü sına

Bu turda M-03 dört kez yanlış cevap verdi ve dördü de aynı sınıfın örneği —
**anmak, tanımlamak değildir**:

| ölçüt | hata | neden |
|---|---|---|
| önek listesi `"ABCE"` | fazla dar | takımlar A..E iken doğruydu; bugün AU'ya gidiyor, `ZZ-99` ölçütün dışında kaldı |
| tüm `ks_*` dosyalarını tara | fazla geniş | uydurma kimlik **D'nin fixture'ında**, **AU'nun beyanında** ve **M'nin kendi yorumunda** geçiyordu |
| her takım kendi önekini tanımlar | neredeyse doğru | J kimlikleri **çalışma anında** kuruyor: `vaka("J-07%s" % etiket)` |
| taban ekleri de tanınır | doğru | `J-07s` → tabanı `J-07` tanımlı; `ZZ-99` hiçbir yerde yok |

Üçüncü satır önemli: ölçüt kırmızı verdiğinde errata'daki `J-07s` atfını
"düzeltmeye" gidebilirdim. Gerçek bir atfı bozacaktım. **Bir ölçüt kırmızı
verdiğinde ilk şüpheli ölçütün kendisidir** — özellikle o ölçütü az önce
kendim değiştirdiysem.

Ve AE'nin kendisi de aynı sınıfa düştü: belge dizgelerini atlamadığı için
`epilog.py`'nin kusuru **anlatan** docstring'ini kusur sandı. Yorum,
açıklama cümlesi, belge dizgesi, fixture, kendi yorumum — beş ayrı kılıkta
tek bir ders: **bir şeyden söz etmek, o şey olmak değildir.**

### Sınıfı arayan araç, sınıfı dört kez işledi

Son yedi turda bulunan ölçüm kusurlarının çoğu tek bir sınıfa indi ve sınıf
beş kılıkta göründü: yamayı açıklayan **HTML yorumu** prosedürün yerine
geçti (AN-05); yamanın **açıklama cümlesi** arama talimatının yerine geçti
(AM-01); kusuru anlatan **belge dizgesi** kusurun kendisi sanıldı (AE-03);
uydurma bir kimlik, onu anan **fixture ve yorum** sayesinde "tanımlı" oldu
(M-03); 300 karakterlik bir **pencere** komşu cümleyi kanıt saydı (AQ-01).

AE Türkçe desen sınıfını tarıyor; bu sınıf için hiçbir tarama yoktu. Bu tur
onu kurdu — ve **tarama yazılırken sınıf dört kez daha göründü, her seferinde
taramanın kendisinde:**

| tarama sürümü | hata | ne oldu |
|---|---|---|
| dizge + dosya aynı kaynakta | **yanlış atıf** | altı adayın **beşi** taramanın kendi hatasıydı: `"mutasyon" in a` bir **dosya adı**, `"SELFTEST OK" in r.stdout` bir **alt süreç çıktısı**, `"json.dumps"` **başka** bir dosya |
| "yalnız yorumlu dosyalarda" | **fazla dar** | AP-02'nin gerçek tuzağını kaçırdı: oradaki kirletici bir yorum değil, becerinin **açıklama düzyazısıydı** |
| tek adımlı veri akışı | **kör** | AF `_hepsi = _ham + …` yazıyor; ölçüt eşleşmeyi kuramadı |
| yayılma, ayıklamadan habersiz | **yanlış pozitif** | ayıklamayı **zaten yapmış** olan AF'yi suçladı |

Yani sınıfı avlamak için yazılan araç, sınıfın kendisine dört kez düştü.
Bu tesadüf değil: **"aynı yerde geçiyor" ile "o şey oluyor" arasındaki fark,
otomatikleştirmesi en zor ayrımdır** — ve tam da bu yüzden elle yazılan her
ölçüt ona düşmeye eğilimlidir.

### İki gerçek tuzak bulundu; ikisi de benimdi

**AF-04.** `"belirti" in hepsi.sh`. Belirti mantığının **tamamı**
`epilog.py`'den silindiğinde ölçüt hâlâ geçiyordu — dizge hepsi.sh'in bir
yorumunda duruyordu, ve o yorumu **otuz dokuzuncu turda ayrıştırmayı
anlatmak için ben yazmıştım.** Kapsamayı koruyan şey kod değil, kodu anlatan
cümleydi.

**AP-02.** `archived` alanı curl komutundan silindiğinde ölçüt hâlâ geçiyordu
— sözcük, otuz dördüncü turda yazdığım **açıklama paragrafında** duruyordu,
700 karakterlik pencerenin içinde. Beceri alanı okumayı bıraksa bile ölçüt
bunu görmezdi.

### Ve bir pencere her zaman yanlış değildir

AV-02'nin ilk hâli 100+ karakterlik **her** pencereyi işaretledi ve K-12'yi
yakaladı. Ama K-12 koltuk dosyalarında bir tırnaklı sözün yakınında **atıf**
arıyor — ve atıf gerçekten bir yakınlık olgusudur; orada pencere bir vekil
değil, **ölçülen olgunun kendisidir.** Ayrım otomatikleştirilemez, bu yüzden
ölçüt **beyan ister**: geniş pencere kullanan her satır gerekçesini yazar
(P'nin MUAF deseni). K-12 gerekçesini yazdı; beyansız yeni bir pencere
kırmızı verir.

### Ve doğrulama sırasında bir tuzak daha açıldı

Kırkıncı turu doğrularken D taban çizgisi **"5 hata"** verdi ve mutasyon
sınaması geçersiz sayıldı — oysa canlı denetim yeşildi ve sistemde hiçbir şey
bozuk değildi. Sebep: D'nin kum havuzu yolu **sabitti**
(`${TMPDIR}/ks_d_kum`), ve o sırada arka planda koşan başka bir D örneği aynı
havuzu kullanıyordu. **İki koşum birbirini eziyordu.**

Bu, otuzuncu turun yan etki sınıfının **ağacın dışındaki** hâlidir: AL-01..03
ağacı koruyor, ama `/tmp` altındaki paylaşılan bir yol onların görüş alanının
dışında. AL-08 o boşluğu kapatır ve her koşum kendi havuzunu alır.

Ders, bu incelemenin en sık tekrar edeni: **bir takım kırmızı verdiğinde ilk
şüpheli sistem değil, ölçümün kendi koşullarıdır.** Burada "5 hata" ne kitabın
ne yamanın kusuruydu — ölçümün kendi eşzamanlılığıydı.

### Kitabı kendi yamamla övmüşüm

Kırk turdur kitabı **kendi cümleleriyle** eleştiriyorum: §8'in tek cümlesi,
§5.1'in *"İmza serbesttir; kapanış değildir"*i, §9'un dört çıktı türü,
§13'ün Karar sütunu. **Bulguların çoğu bu alıntılara dayanıyor** — ve hiçbir
şey alıntıların doğru olduğunu sınamıyordu. Yanlış bir alıntı, üstüne
kurulan bulguyu da götürür.

Ölçüm bir hata buldu ve hata bana aitti. Otuz beşinci turda kitabı şu cümle
için **övmüştüm**:

> *"eşleşmenin yokluğu temizlik kanıtı değildir"*

— yaptırım taramasının boş sonuç tuzağını kapattığı gerekçesiyle. **O cümle
kitapta yok.** Kitabın §13.3'ü yalnızca *"Tarama karar değildir. Bir ad
eşleşmesi bir ipucudur"* diyor. Cümleyi `yaptirim-taramasi` becerisini
yazarken **ben eklemiştim** ve altı tur sonra kendi yamamı kitabın metni
sanıp kitaba kredi verdim.

Otuz dördüncü turda AP-01 kendi teslimatımı kitabın eseri sanmıştı; orada
kitabı olduğundan **iyi** göstermişti. Aynı sınıf, ikinci kez: **kendi
yamalarım ağaçta dururken kitabı ölçmek ikisini karıştırır.**

Ve düzeltme bir bulgu doğurdu. Kitap *"boş bir arama yokluğun kanıtı
değildir"* ilkesini §14'te **GitHub aramaları** için kuruyor; en yüksek
bedelli yere — yaptırım taramasına — taşımıyor. §13.3 eşleşme **bulunduğunda**
ne yapılacağını söylüyor, **bulunmadığında** ne anlama geldiğini söylemiyor;
oysa kendi cümlesiyle oradaki kaçırma *"cezai sorumluluk sorunudur"* ve yine
kendi cümlesiyle *"Türkçe adlar birkaç biçimde çevrilir"*. Boşluk gerçek —
ama kitabın kapattığı değil, **benim kapattığım** bir boşluk.

### Üç alıntı daha yanlıştı

| yazdığım | kitabın yazdığı |
|---|---|
| *"dayanağı olmayan bir iddia yazılmaz"* (§1) | *"Her rakam, tarih, eşik, süre ve alıntı dayanağını yanında taşır"* |
| *"Boş bir arama yokluğun kanıtı değildir"* (§14) | *"Boş bir **GitHub araması** yokluğun kanıtı değildir"* |
| *"eskime burada bozulma değildir"* (§13.4) | *"**burada eskime** bozulma değildir"* |

Üçü de küçük; üçü de düzeltildi. Ama küçük olmaları önemli değil: **bir
eleştiri, eleştirdiği metni doğru aktarmak zorundadır** — yoksa eleştirinin
kendisi, eleştirdiği kusurun bir örneği olur.

AW artık kitaba atfedilen her alıntıyı kitabın **kaynak dosyasına** karşı
sınıyor (13 alıntı doğrulandı). Kitaptan olmayan alıntılar — raporun kendi
cümleleri, mevzuat metinleri, madde başlıkları — **beyan edilmiş bir muafiyet
listesinde** gerçek kaynaklarıyla duruyor; AW-02 o listenin bir kaçış deliğine
dönüşmediğini sağlıyor: listede olup da kitapta **geçen** bir cümle kırmızı
verir. Ve kitap kaynağı bulunamazsa AW sessizce geçmez, **kırmızı** olur —
doğrulanamayan bir alıntı doğrulanmış sayılamaz.

### Sayılar doğru çıktı — ve doğrulanmış olmak sınanmamış olmaktan farklıdır

Kırk birinci tur raporun **alıntılarını** kitaba karşı sınadı ve dört yanlış
buldu. Kardeş eksen sınanmamıştı: raporun kitabın **yapısı** hakkındaki
**sayısal** iddiaları. Rapor sürekli sayı veriyor ve bulguların ağırlığı bu
sayılara asılı.

| iddia | kitapta ölçülen | sonuç |
|---|---|---|
| §16'nın **on bir** kontrolü | 11 *(imza şablonu hariç)* | ✓ |
| §18'in **dokuz** sınırı | 9 numaralı madde | ✓ |
| §12 **dört** kapı kuruyor | `kapsam · kanit · sir · guncellik` + metinde "dört kapı" | ✓ |
| §14 beşinciyi ekliyor, **yedi** vaka | *"…diğer dördün yanına eklenir ve `_selftest` şu **yedi** vakayla genişletilir"* | ✓ |

**Dördü de doğru.** Bu takım bir kusur bulmadı; bir iddiayı **doğruladı** ve
doğrulamayı kalıcı hâle getirdi. İkisi aynı şey değil — kırk birinci tur tam
olarak bunu gösterdi: o güne kadar alıntılar da "doğru sanılıyordu".

İki bölüm başlığı da yerini buldu: §18 kitapta *"Bu sistemin bilerek
yapmadıkları"*, §19 ise *"İlk dosya"* (*"Denetim yeşile döndükten sonra bir
kez çalıştırılır"*). Rapor onlara kendi kısa adlarıyla atıfta bulunuyor;
numaralar doğru, adlar parafraz. AX-05 artık raporun andığı **her** bölüm
numarasının kitapta gerçekten bir bölüm olduğunu sınıyor.

### Ve sayarken üç kez kendi ölçütüm yanıldı

| ölçüt hatası | ne oldu |
|---|---|
| `kontrol "` sayımı **12** verdi | birincisi fonksiyonun **imza yorumuydu** (`kontrol "<ad>" "<komut>"`) — şablonu kontrol saymak |
| §18 maddeleri **10** çıktı | bölüm **başlığı** da `18.` ile başlıyor ve madde sanıldı |
| "N kontrol" kalıbı **26** buldu | o benim **yamalı** denetimimin sayısı, kitabınki değil |

Üçü de tek bir şeyin türevi: **tanım ile örneği, başlık ile maddeyi, kendi
sistemim ile kitabı karıştırmak.** Kırkıncı turun "anmak tanımlamak
değildir" sınıfının sayı tarafındaki hâli.

Ve bir dördüncüsü mutasyonda çıktı: ölçüt **ilk** eşleşmeyi alıyordu, oysa
aynı iddia iki teslimatta iki kez geçiyor ve biri **satır kırılmasıyla**
bölünmüştü. Mutasyon birini bozduğunda ölçüt ötekini bulup yeşil kalıyordu.
Artık **tüm** eşleşmelerin aynı sayıyı söylemesi isteniyor — iki teslimat
birbirinden ayrışırsa da kırmızı verir.

### On iki atıf, bir kural numarasını bölüm numarası sanıyordu

AW alıntıları, AX sayıları sınadı. Üçüncü kardeş en tehlikelisiydi: raporun
kitabın **ne söylemediğine** dair iddiaları. Kitabın kendi 2. kuralı olumsuz
iddiadan daha yüksek bir kanıt eşiği ister — ve kırk birinci tur, kitap
olgularını ters yönde de yanlış bilebildiğimi göstermişti.

**Birinci bulgu: çürütücü, iddianın kapsamında aranmalı.** *"§11'in eşik
denetimi `dosyalar/` dizinini taramıyor"* iddiasını kitabın **tamamında**
arayınca `dosyalar/*/` bulundu ve iddia çürümüş göründü. Oysa o dize §2'nin
`.gitignore` satırında (`'dosyalar/*/veri/'`), §11'in komut metninde değil.
**İddia ayakta — ama ölçüt yanlış yerde arıyordu.** Olumsuz bir iddia ancak
kendi bölümünde çürütülebilir.

**İkinci bulgu daha ağır.** Rapor, çıkar çatışması kuralını **sekizinci
bölüm**, insan onayını **dokuzuncu bölüm** diye anıyordu. Kitapta o numaralar
başka şeyler:

| işletim sözleşmesi kuralı | rapor onu şöyle anıyordu | kitapta o numara gerçekte |
|---|---|---|
| çıkar çatışması *(kural 8)* | bölüm sekiz | **İşlem el kitapları** |
| insan onayı *(kural 9)* | bölüm dokuz | **Beceriler** |
| kanıt kuralı *(kural 1)* | bölüm bir | **Ne kuruyoruz** |
| yön / başlık sırası *(kural 4)* | bölüm dört | **Uzmanlık birimleri** |

Çatışma, onay, kanıt ve yön **işletim sözleşmesinin kurallarıdır** ve
sözleşme kitabın **§3**'ünde durur. Yani rapor **on iki yerde** bir kural
numarasını bölüm numarası gibi yazmıştı. Rapor zaten "kural 6" ve "kural 2"
diye doğru yazıyordu — yani doğru gösterim vardı, **tek tip
uygulanmamıştı**; bu incelemenin en sık tekrar eden şekli.

**AX-05 bunu göremezdi**, ve sebebi öğretici: AX-05 anılan bölümün kitapta
*var olduğunu* sınıyor. §8 ve §9 gerçekten var — sadece iddia edilen konuda
değil. **Var olmak, o konuda olmak değildir** — kırkıncı turun sınıfının
atıf tarafındaki hâli. AY-03 artık bölüm haritasını başlıklarıyla sınıyor;
bir atıf yanlış bölümü gösterirse kırmızı verir.

On iki atıf `kural N` biçimine çevrildi. `CLAUDE.md §1` gibi açıkça
nitelenmiş olanlar olduğu gibi bırakıldı: orada hangi belgenin §1'i olduğu
zaten yazıyor.

### "Kitaba sadık" sıfatı kırk üç tur boyunca sınanmamıştı

Kırk bir, iki ve üçüncü turlar raporun kitap hakkındaki **sözlerini** sınadı.
Dördüncüsü tabana bakıyor: raporun bütün **önce/sonra** karşılaştırması
`yamalar/kitaba-sadik/` altındaki kopyalara dayanıyor. AG-01..05 o dosyaların
*var olduğunu*, canlı sürümden *farklı* olduğunu ve kitabın bilinen
kusurlarını *taşıdığını* ölçüyor — ama hiçbiri **kitabın metniyle**
karşılaştırmıyordu.

Karşılaştırıldı: **262 esaslı satırın 258'i** kitapta birebir bulundu.

Kalan dördü `kapi.py`nin `denetle()` bölümünde ve sebebi öğretici: §12
fonksiyonu **dört** kapıyla basıyor, §14 beşinciyi verip *"denetle() içine
diğer dördün yanına eklenir"* diyor. **Kitap sonucu basmıyor, talimatı
veriyor.** Beş kapılı `denetle()` metnini kitaptan kopyalamak mümkün değil;
talimatı uygulayarak yazmak gerekiyor. O dört satır uydurma değil — ama
kitabın harfi de değil, ve fark yazılmak zorunda: kırk birinci turda kendi
yamamı kitabın metni sanıp kitaba kredi vermiştim.

Beyan `yamalar/kitaba-sadik/TURETME.md` içinde: hangi satır, hangi talimattan.
AZ-01 beyansız her satırın kitapta birebir bulunmasını ister; AZ-03 beyanın
bir **kaçış deliğine** dönüşmediğini sağlar — beyan edilen bir satır kitapta
*geçiyorsa* kırmızı verir.

### Ve küçük bir kitap kusuru daha çıktı

§16 denetim betiği kapı öz-sınamasını `kontrol "dört kapı"` etiketiyle
çağırıyor. §14 beşinciyi ekledikten sonra sistemde **beş** kapı vardır;
etiket güncellenmiyor ve denetim var olmayan bir yapıyı adlandırıyor.

Küçük — davranış doğru, yalnızca ad bayat — ama sınıfı §14'ün merkezî
kusuruyla aynı: **yeni bir kapı eklenirken ona bağlı hiçbir şey
güncellenmiyor.** Beklenen kümeler güncellenmiyordu (birinci bulgu),
öz-sınama kapsaması sorulmuyordu (AS-01), kontrolün adı da düzeltilmiyor.
Üçü tek bir eksikliğin üç görünümü.

### Kendi kaydımı üçüncü kez yanlış okudum — ve kayıt yine haklıydı

Bu tur şu gözlemle açıldı: *"ortam engellenen egress için bir çare
belgeliyor ve ben onu hiç okumadım."* **Yanlıştı.** `hafiza/egress-kaniti.md`
vekil durum uç noktasını zaten kaydediyordu ve README'ye (bir deponun ana açıklama dosyası) iki kez atıf
yapıyordu.

Yirmi sekizinci turda WebSearch satırını *"işe yaramaz"* diye yanlış
okumuştum; burada da kendi kaydımı okumadan bir eksiklik varsaydım.
**Kayıt tutmak yetmiyor; kaydı okumak ayrı bir iştir** — ve bu, raporun
kitaba yönelttiği eleştirinin (yazılı ama bakılmayan kontrol) bendeki
karşılığıdır. Üçüncü kez.

**Ama turda gerçek bir kazanım da var.** Reddin anlamı şimdiye kadar tek bir
yetkiye dayanıyordu: aracın kendi ret iletisi. Ortamın **kendi belgesi**
aynı şeyi bağımsız olarak söylüyor — TLS (bağlantıyı şifreleyen güvenlik
katmanı) doğrulamasını kapatmayı ve vekili devre dışı bırakmayı yasaklayarak
(`/root/.ccr/README.md`, satır 18-19):

> *"Never disable TLS verification, never unset HTTPS_PROXY, and do not retry
> organization policy denials (403/407) — report them instead."*

İkisi de bu raporun yaptığı şeyi **buyuruyor**: politika reddi yeniden
denenmez, raporlanır. Yani üç ENGELLEYİCİ bulgunun açık bırakılması bir
eksiklik değil, **ortamın açıkça istediği davranıştır.** Bu, raporun en ağır
üç bulgusunun neden kapatılamadığını savunmaktan çıkarıp **belgelenmiş bir
kurala uymaya** dönüştürüyor.

Vekilin kendi kaydı da yeniden doğrulandı: dört Türk birincil kaynağı
(`mevzuat`, `rekabet`, `resmigazete`, `spk`) için dört
`connect_rejected · 403` kaydı — benim çağrı dökümüme değil, **altyapının
kendisine** ait bir kayıt.

N-09 artık iki bağımsız yetkiyi birden istiyor: **tek bir yetkiye dayanan
olumsuz iddia, o yetki yanlış okunduğunda çöker** — ve bu turda kendi
kaydımı yanlış okuduğumu bir kez daha gördüm.

### Üç örnek bir sınıftır — ve sınıf, örnekleri düzelterek kapanmaz

Aynı hatayı üç kez yaptım: dördüncü–yirmi sekizinci turda kaydın *çalışıyor*
dediği kanalı *"işe yaramaz"* diye okudum; kırk beşinci turda kaydın zaten
içerdiği bir şeyi *"hiç sorgulamadım"* diye açtım; daha önce *"hiçbiri
silinmedi"* sözü bir süre doğru değildi. Yirmi yedinci turun kendi kuralı
buydu: **üç örnek bir sınıftır ve sınıf ancak duran bir sağlamayla kapanır.**
Üçünü de tek tek düzeltmiştim; sınıfı kapatmamıştım.

Sınanamayan ile sınanabileni ayırmak gerekti. *"Yazar kaydını doğru okudu
mu"* ölçülemez. Ölçülebilen **sonucudur**: kayıt bir şeyin çalıştığını ya da
doğrulandığını söylüyorken, teslimatın onu çalışmıyor/doğrulanmamış gibi
anması. Üç olayın üçü de tam olarak bu biçimdeydi. BA takımı bunu ölçüyor:
`egress-kaniti.md`'nin *çalışıyor* dediği kanalları ve
`dogrulama-bulgulari.md`'nin *DOĞRULANDI* dediği bulguları toplayıp RAPOR ile
KİTAP-ERRATA'nın her cümleciğinde arıyor.

**Bugün gerçek çelişki yok.** Değerli olan, ölçütün üç kez yanılması oldu — ve
üçü de bu incelemenin en sık tekrar eden tuzaklarıydı:

* **Pencere ölçeği iki yanlış pozitif verdi.** Biri WebSearch'ün *çalıştığını*
  söyleyen cümleydi; öteki I-04'ün doğrulandığını söylerken yanındaki
  cümleden "kapatılamaz" kelimesini kapıyordu. Yirmi dokuzuncu turun kuralı
  yine geçerli: **pencere, komşuyu kanıt sanar.** Ölçüt cümleciğe indi ve
  BA-04 artık pencerenin geri gelmesini yakalıyor.
* **Satır kaydırması muafiyeti sessizce iptal etti.** Geçmiş hatayı *anlatan*
  cümleler muaftır — ama kaynakta `yanlış\nokumuştum` yazıyordu ve
  `yanlış okum` kalıbı hiç eşleşmedi. Muafiyet çalışmadı; kimse fark etmezdi,
  çünkü sonuç yalnızca "kırmızı" görünüyordu. Aynı delik otuz dokuzuncu turda
  AM-01'de de çıkmıştı. Her cümlecik artık eşleştirmeden önce tek boşluğa
  normalleştiriliyor.
* **Muafiyetin öz-sınaması kesilmiş metni ölçüyordu.** BA-02, muaf tutulan
  cümleciğin geçmiş-hata işareti taşıyıp taşımadığına bakıyordu; ama elindeki
  şey gösterim için 70 karaktere **kesilmiş** hâliydi ve işaret kesiğin
  ötesindeydi. Düzeltince ikinci kusur göründü: soru zaten **totolojiydi** —
  cümlecik o işareti taşıdığı için muaf tutulmuştu. BA-02 yeniden yazıldı ve
  artık sınanabilir olanı soruyor: **muafiyet büyüdü mü?** Muaf tutulan her
  hedef sayısıyla beyan edilir; beyandan fazla muafiyet de, hiçbir şeyi
  örtmeyen bayat bir beyan da vakayı kırar. Kaçış deliği böylece sessizce
  genişleyemez.

**Ve takım ilk tam koşusunda kendi apparatına yakalandı.** AE-01,
`ks_ba_kayit_celiski.py`'nin bulgu kimliklerini `[A-Z]-\d+` ile aradığını
gördü: **AA/BA gibi iki harfli kimlikler bu desene görünmez.** Bugün öyle bir
bulgu yok, ama olsaydı BA-01 onu sessizce sınamayacaktı — yani takım, ölçtüğü
şeyi ölçmediğini hiç söylemeden yeşil kalacaktı. Otuz beşinci turda kendim
için yazdığım kontrol, kırk altıncı turda yine kendimi yakaladı. Düzeltildi.

Bu turun kalıcı kuralı: **kesilmiş metin gösterim içindir; ölçen hiçbir şey
onu okumamalıdır** — ve **bir muafiyet, gerekçesi sayıyla yazılmadıkça
muafiyet değil, kör noktadır.**

### Kırk altı tur depoyu sınadı; okuyucunun açtığı belge sınanmamıştı

Kırk yedinci tur şunu sordu: **teslimattaki sayılar, ölçtükleri şeye hâlâ
eşit mi?** Bu, incelemenin en sık ikinci sınıfıdır — elle yazılan sayı,
ölçtüğü şeyden sürüklenir — ve raporun kendi metnine hiç uygulanmamıştı.

Dört sürüklenmiş sayı bulundu, dördü de okuyucunun gördüğü yerde:

| Nerede | Ne diyordu | Gerçek |
|---|---|---|
| RAPOR, takım tablosunun başlığı | kırk yedinci turda "Dokuz takım, 96 vaka:" diyordu | altındaki tablo 53 satırdı |
| RAPOR, "nasıl yeniden koşulur" | kırk yedinci turda `# 34 çalıştırılabilir takım` diyordu | 50 |
| ARTIFACT, giriş cümlesi | kırk yedinci turda sadık kurulum "doksan altı vakayla" sınandı diyordu | sadık koşum 85'ti; 96 YAMALI koşumun sayısıydı |
| RAPOR + ARTIFACT | "kırk üç takımın tamamı" | o turda doğruydu, indissizdi |

İkincisi öğreticidir: kırk yedinci turda eskimiş takım sayısını taşıyan o
satırın **hemen altındaki** vaka satırı bir tur önce güncellenmişti. İki sayı,
komşu iki satır, biri bakıldı öteki bakılmadı. Üçüncüsünün kırk altı tur boyunca
nasıl hayatta kaldığı ise daha keskin bir cevap veriyor: sayı rakamla değil,
**"doksan altı"** diye yazıyla yazılmıştı. Rakam arayan hiçbir ölçüt onu
göremezdi. BB artık Türkçe sayı sözcüklerini — ekleriyle ve yüzlükleriyle —
okuyor.

**Ve ölçüt dokuz kez yanıldı; her yanılgı bir sınıfın adını verdi.**

* **Referans ekseni.** "B (34 vaka)" bir B iddiasıdır, takımın tamamı hakkında
  değil. Yirmi dokuzuncu turun kuralı ("iddiayı taşıyan en küçük birim")
  bir eksen daha kazandı: **iddianın neye dair olduğu da ölçülmeli.** Ölçüt
  yalnızca TOPLAM çerçevesindeki sayımları denetliyor.
* **Çıplak küçültme.** Ölçüt ilk koşusunda `KeyError: 'i̇ki'` ile çöktü:
  `İki` harfi `.lower()` altında bozuluyor. AE-03'ün yasakladığı şey, onu
  yazan takımı vurdu.
* **Eklemeli birim.** Birim sözcüğü ek aldığında ("…vakayla sınandı") sözcük
  sınırı hiç eşleşmez — AO-02'nin "ara"/"aranır" tuzağı, bu kez birimde.
* **Sıfat araya girer.** Sayı ile birimin arasına bir sıfat girdiğinde
  bitişiklik arayan ölçüt sayımı hiç göremedi. Bu, **artifact'in üst bilgisindeki iddianın ta kendisiydi**:
  ölçüt, en çok ölçmesi gereken cümleyi atlıyordu. Yalnızca mutasyon gösterdi.
* **Yüzlükler.** Yazıyla yazılmış yüzlü bir toplam kaçtı; toplamlar tam
  olarak yüzlü sayılardır, yani delik ölçütün en çok gerektiği yerdeydi.
* **Markdown yapışması.** Vurgu noktaya yapışınca cümlecik bölücüsü ateşlemedi
  ve iki ayrı koşumun cümlesi tek cümlecik oldu; tablo satırları da tek bir
  dev cümlecikti, bir satırın zaman indisi yandakini örtüyordu.
* **İlk eşleşme.** Başlık denetimi metindeki İLK eşleşmeyi alıyordu ve bu turun
  kendi düzeltme tablosundaki alıntıyı başlık sandı. Bir kusuru arayan ölçüt,
  o kusuru **belgeleyen** düzyazıyı da yakalar; bu, sınıfın beşinci takımdaki
  görünümü. Ölçüt satır başına çapalandı, düzyazı da kusuru adlandıracak —
  kullanmayacak — biçimde yeniden yazıldı.
* **Kimlik rakamı.** `XX-00` gibi bir vaka kimliğindeki rakam bir sayım değildir;
  sol sınırı olmayan ölçüt kendi vaka kimliklerini toplam sandı.
* **Artikel.** Türkçede "bir" hem sayıdır hem belirsiz artikeldir. Sayı
  okuyucusu tek başına duran her "bir"i rakama çevirince, ölçütün kendi
  açıklama cümleleri toplam iddiası gibi göründü. Dizinin parçasıyken sayı,
  tek başınayken artikel sayılıyor.

**En ağırı sona kaldı: AL-06 takımı yakaladı.** BB, vaka sayısını
`sinama/SAYIM.txt`'ten okuyordu — yani **içinde bulunduğu koşumun kaydından.**
Koşum sırasında o dosya henüz önceki koşumun sayısını taşır; BB koşumun
içinde kırmızı, koşumdan sonra yeşil görünüyordu. Onuncu ve on altıncı
turların katman kuralı — *denetim, kendini denetleyen takımı denetleyemez* —
**üçüncü kez**, bu kez veri yoluyla çiğnenmişti. Sayı artık durağan ölçülüyor:
`hepsi.sh`'e bağlı her takımın kendi `BEKLENEN_VAKA` beyanı toplanıyor
— bugün toplam 387 vaka — ve her takımın kendi sıfırıncı vakası o beyanın
gerçeğe eşit olduğunu ayrıca güvenceye alıyor. Bozulmuş bir `SAYIM.txt` ile BB'nin çıktısı
**birebir aynı** kalıyor; bağımsızlık ölçülerek gösterildi.

Turun kalıcı kuralı: **bir sayı ya bugün ölçülebilen değere eşittir, ya da
hangi koşuma ait olduğunu söyler.** İndissiz bir tarihsel sayı, güncel bir
iddiadan ayırt edilemez — ve okuyucu ayırt etmek zorunda bırakılamaz.

### Üç terim soruldu, on yedi terim vardı

§10 açık: *"Piyasada karşılığı yerleşmiş İngilizce terimler korunur ve **ilk
geçtiklerinde açıklanır**."* R-06 bunu kırk yedi tur boyunca sınadı ve her
turda "temiz" dedi. Sınadığı şey **elle yazılmış üç terimdi**: NFKC, CONNECT,
homoglif. Yani ölçüt yalnızca açıklandığını zaten bildiği terimleri soruyordu.

Raporun düzyazısında **on yedi** açıklanmamış terim vardı. Bu, "elle yazılan
liste ölçtüğü şeyden sürüklenir" sınıfının **üçüncü** örneğidir — P takımının
teslimat listesi ve M-03'ün önek listesinden sonra — ve yirmi yedinci turun
kuralı gereği sınıf artık duran bir sağlamayla kapanıyor: BC listeyi
**keşfe** çevirdi.

Keşfin tek zor yanı Türkçeydi. Rapor vurgu için büyük harf kullanıyor
(DAYANAK, KURULUMA), İngilizce terimler de büyük harf. Ayıran ölçüt basit:
**küçük harfli hâli belgede sıradan bir Türkçe sözcük olarak geçiyorsa, o
büyük harf vurgudur.** `dayanak` geçiyor, `nfkc` geçmiyor.

**En ağır bulgu AGPL.** §13'ün engelleyici lisans bulgusunun **anlamı** bu
kısaltmayı bilmeye bağlıydı: bir hukukçu okuyucu için, ağ üzerinden hizmet
verse bile kaynak kodu açmayı zorunlu kılan bulaşıcı bir lisans ile izin
verici bir lisans arasındaki fark, bulgunun tamamıdır. Rapor bunu hiç
açıklamamıştı. Şimdi on yedisi de ilk geçtikleri yerde açıklanıyor.

**Ölçüt üç kez yanıldı, biri öğretici.** Gevşetilmiş bir sürüm — "açıklama
cümlenin içinde, terimden sonraki on iki sözcükte olsun" — **yedi yanlış
geçiş** verdi: DOI bir virgüllü listenin iki noktasıyla, HTTPS yanındaki
CONNECT parantezinin içinden, UTC ilgisiz bir *"(1 gün)"* ile "açıklanmış"
sayıldı. **Noktalama, anlamın vekili değildir.** Bu yüzden ölçüt
gevşetilmedi, **belge sıkılaştırıldı**: açıklama terimin hemen ardında durur.
Ölçütün tahmin etmesi gereken hiçbir şey kalmadı.

Öteki ikisi dedektörün kendi kusuruydu: keşif sözcük sınırı kullanırken ölçüm
düz alt dizi araması yapıyordu, bu yüzden bir kısaltmanın ilk geçişi başka
bir sözcüğün **içinde** bulunuyordu — ikisi iki farklı şeyi ölçüyordu. Ve
markdown vurgusunu soymak, alt çizgili bir ortam değişkeni adından
**var olmayan yeni bir terim uydurdu**.

**Ve mutasyon sınamasında yeni bir geçersizlik biçimi çıktı.** Keşfi köreltme
mutasyonu ilk denemede "kaçtı" göründü. Kaçmamıştı: **mutasyon hiç
inmemişti.** İniş kanıtı olarak dosyaya ayrıca eklenen bir işaret aranıyordu
ve o işaret mutasyondan **bağımsız** olarak yerleşmişti. Otuzuncu turun
kuralı bir madde kazandı: *bir mutasyon indiği kanıtlanmadan okunamaz* — ve
**kanıt, mutasyonun kendisi olmalıdır; yanına konan bir işaret değil.**
Kalıp doğrudan doğrulanınca vaka gerektiği gibi kırmızıya döndü.

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
3. **Uydurma alıntı dedektörünü iki kez yanlış yazdım.** Birinci sürüm her
   tırnaklı diziyi alıntı saydı ve anılan ESER ADLARINI ("A Manual of Style for
   Contract Drafting") uydurma söz diye işaretledi — oysa bir eser adını anmak
   §7'nin istediği dayanağın ta kendisidir. İkinci sürüm söyleme fiili aradı ama
   "<kitap> kitabında … yazdı" cümlesi hâlâ eşleşti. Ayrıca tırnaklar
   eşleştirilmediği için hayalet aralıklar üretiliyordu. Üçüncü sürüm doğru.
4. **Teslim ettiğim takım taşınabilir değildi — ve bu, kitapta bulduğum
   kusurun aynısıydı.** Bütün betikler `~/mafirm` yolunu sabitliyordu;
   dolayısıyla depoyu klonlayan biri KENDİ ağacını değil, makinedeki kurulumu
   ölçüyordu. Kanıtlandı: klondaki `kapi.py` tamamen boşaltıldı ve klonun
   denetimi hâlâ **DENETİM OK** dedi — tıpkı D takımının kitapta bulduğu gibi,
   iddia ettiği şeye bakmayan bir kontrol. Her betik artık kökü kendi
   konumundan çözüyor. Klondan koşum ayrıca kaynak ağaçtan koşumun yapısal
   olarak göremeyeceği ikinci bir kusuru yakaladı (B-34 ad kaydını yanlış
   ağaca yazıyordu).
5. **Referans dedektörünü iki kez yanlış yazdım.** Birinci sürüm düzyazıdaki
   çıplak dosya adlarını ("esik.py çalıştırılır") bağlantı saydı: 32 sahte
   kırık. İkinci sürüm GÖRECELİ atıfları köke göre çözdü: bir birim INDEX'i
   içindeki "yontem/..." biçimi, INDEX'in kendi dizinine göre çözülür — 12 sahte
   kırık daha. Üçüncü sürüm doğru; gerçek kırık sayısı sıfır.

   Üçüncü sürüm de bir sınır taşıyor ve bu sınır bir YAZIM KURALI doğurdu:
   dedektör, bağlantı olarak kullanılan bir yolu ile düzyazıda ÖRNEK olarak
   anılan bir yolu ayırt edemez. Dolayısıyla örnek yollar kod sözdizimiyle
   yazılmaz — bu cümlenin kendisi o kuralın ilk uygulamasıdır. Kuralın
   alternatifi, dedektörü gevşetmekti; gevşemiş bir kontrol hiçbir şey
   yakalamaz.
6. **Bir mutasyon sınamam sessizce hiçbir şeyi bozmadı.** İşaret kontrolünü
   sınarken `sed` deseni hedefi tutturamadı ve dosya hiç değişmediği hâlde
   "kontrol ateşlemedi" sonucuna varıyordum. Mutasyonun gerçekten tuttuğunu
   doğrulayan bir adım eklendi. Bu, D takımında bir kez daha yaşandığı için
   artık bir alışkanlık: **bir mutasyon sınaması, mutasyonun olduğunu
   kanıtlamadan geçerli değildir.**
7. **Koşum betiğim bir takımın çıkış kodunu elle 0 yazıyordu.** F çöktüğünde
   takım "0 SİNYAL" diyordu — kitabın denetiminde bulduğum `| wc -l` kusurunun
   kendi betiğimdeki hâli. Ve düzeltmeyi sınarken mutasyonum yine tutmadı;
   aynı kuralı üçüncü kez hatırladım.
8. **Kapımın kendi raporumu reddettiğini gördüm ve üzerinden geçtim.**
   Sekizinci turda `RAPOR.md [kapsam] avukat başlığı yok` çıktısı ekrandaydı;
   okudum, başka bir şeye baktım. Bir turu bu yüzden kaybettim ve kitabın §12'de
   tarif ettiği kusuru birebir yaşadım.
9. **İzlenebilirlik denetleyicimin ayrıştırıcısını da yanlış yazdım** —
   aralık atıflarını ve dinamik kimlikleri görmüyordu, yedi maddeyi haksız yere
   "dayanaksız" ilan etti. Bu, bu oturumdaki yedinci ayrıştırıcı kusurum ve
   hepsi aynı yönde: **bir dedektör, ölçtüğü şeyin gerçek biçimini görmeden
   yazılırsa, bulduğu şey kendi körlüğüdür.**
8. **İki mevzuat/depo şüphem yanlıştı** (G-06, I-06). Kitap her ikisinde de
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
| D · mutasyon | 11 kaçtı | **temiz — 27/27 yakalandı** (ilk ölçüm 15 mutasyonluydu; küme otuz sekizinci turda genişletildi) |
| E · beklenen değerler | 4 kaldı | 3 kaldı (kitabın kendi değerleri) |
| J · §19 kabul sınaması | doğru cevap da bloklu | 2 kaldı (**bilerek** — kitaba sadık karşılaştırma) |
| K · yönlendirme + koltuk | 3 kaldı | **temiz** |
| L · referans bütünlüğü | 1 kaldı (kendi regresyonum) | **temiz** |
| M · errata izlenebilirliği | 3 kaldı (kendi raporum) | **temiz** |
| N · olumsuz iddia kanıtı | kanıtsızdı | **temiz** |
| V · kapıların yanlış pozitifi | *hiç ölçülmemişti* | **temiz** — 17 meşru metin, 0 yanlış pozitif |
| W · sessizce boş arama kaynağı | *hiç sorulmamıştı* | **temiz** — boş banka artık sesli |
| X · yetki ↔ kapsam | *hiç sorulmamıştı* | **temiz** — beyan ile uygulama hizalandı |
| Y · sırrın kalıcı deposu | *hiç sorulmamıştı* | **temiz** — üç yol dışlandı, geçmiş temiz |
| Z · kurulum bütünlüğü | *kitap iki kez hiç koşulmamıştı* | **temiz** — sessiz geri alma artık görülüyor |
| AA · kapının arıza yönü | *hiç ölçülmemişti* | **temiz** — her arıza 0 ya da 2, süre sınırlı |
| AB · blok iletisinin çaresi | *teşhis vardı, çare yoktu* | **temiz** — altı kapı da çare gösteriyor |
| AC · ortam bağımsızlığı | *hiç ölçülmemişti* | **temiz** — yedi dilim, beş yerel ayar, tek karar |
| AD · komutların iddiaları | *hiç okunmamıştı* | **temiz** — canlı kusur yok; iddialar artık kilitli |
| AE · desen sınıfı | *örnek örnek düzeltiliyordu* | **temiz** — sınıf tarandı, üç kusur çıktı |
| AF · aparatın iddiaları | *15 takım korumasızdı* | **temiz** — koruma geriye dolduruldu |
| AG · kitaba sadık taban | *iki özgün eksikti* | **temiz** — kitabın metninden yeniden kuruldu |
| AH · cevabın güncelliği | *dört ağır bulgu cevapta yoktu* | **temiz** — cevap güncellendi, eşleme beyanlı |
| AI · koltuk dayanakları | *hiç doğrulanmamıştı* | **temiz** — altı eser doğrulandı, kayda bağlandı |
| AJ · çalışan kanalın kullanımı | *kanal 27 tur kullanılmadı* | **temiz** — üç bulgunun kanıtı yükseltildi |
| AK · bulgu statüsü | *dokuz bulgu doğrulanmamıştı* | **temiz** — dördü doğrulandı, üçü yetkili kaynağından |
| AL · takımların yan etkisi / bağımsızlık | *B-34 canlı ad kaydını yok ediyor, AF-03 kendi koşumunu okuyor* | **temiz** — iki yan etki kapatıldı, sağlama epiloga taşındı |
| AM · kararın hukuki sürümü | *eşik denetimi canlı dosyaları hiç açmıyor* | **temiz** — tarama kapsamı vaadine eşitlendi |
| AN · yamanın kabul sınaması | *yamanın tablosu kapıya görünmüyordu* | **temiz** — sır kapısına canlı iş yolu kuralı eklendi |
| AO · çatışmanın yönü ve zamanı | *kontrol tek yönlü ve yalnız açılışta* | **temiz** — iki yönlü ve geriye dönük hâle getirildi |
| AP · araç kataloğunun kurulumdaki hâli | *katalog kurulumda hiç yok; arşiv ve veri lisansı okunmuyor* | **temiz** — katalog kuruldu, iki alan eklendi |
| AQ · yaptırım taramasının zaman ekseni | *son kontrol noktası imza; kapanışta yeniden tarama yok* | **temiz** — dördüncü nokta ve kapanış adımı eklendi |
| AR · onay durumu (yedinci kapı) | *onaysız §9 çıktısı hiçbir kapıya takılmıyordu* | **temiz** — yedinci kapı eklendi |
| AS · kapıların öz-sınama kapsaması | *yedinci kapının öz-sınama vakası yoktu* | **temiz** — dört vaka eklendi, kapsama sağlamaya bağlandı |
| AT · denetimin mutasyon kapsaması | *26 kontrolün 9'u hiç sınanmamıştı* | **temiz** — 12 mutasyon eklendi, hedef beyanı zorunlu |
| AU · epilog kontrollerinin sınaması | *dört epilog kontrolü hiç sınanmamıştı* | **temiz** — saf fonksiyona çevrildi, 7 vaka 32 ms |
| AV · anma/tanım sınıfı taraması | *iki ölçüt yorumla/düzyazıyla tatmin oluyordu* | **temiz** — ikisi de koda bağlandı, sınıf taranıyor |
| AW · kitap alıntılarının doğruluğu | *dört alıntı yanlış; biri kitaba ait olmayan bir cümleyi kitaba mal ediyordu* | **temiz** — düzeltildi, 13 alıntı doğrulandı |
| AX · kitap yapısı iddiaları | *sayısal iddialar hiç sınanmamıştı* | **temiz** — dördü de doğru çıktı, doğrulama kalıcı |
| AY · kitap hakkında olumsuz iddialar | *on iki atıf kural numarasını bölüm numarası sanıyordu* | **temiz** — atıflar düzeltildi, çürütücüler bölüm kapsamlı |
| AZ · kitaba sadık kopyaların sadakati | *"sadık" sıfatı hiç sınanmamıştı* | **temiz** — 258/262 birebir, kalan dördü beyanlı |
| BA · kayıt ile iddianın çelişmesi | *kaydın "çalışıyor" dediğini teslimat "işe yaramaz" diye anmıştı — üç kez* | **temiz** — bugün çelişki yok, muafiyet beyanlı |
| BB · sayıların zaman indisi | *kırk yedinci turda görüldü, "Dokuz takım, 96 vaka" başlığı 53 satırlık tablonun üstünde duruyordu* | **temiz** — dört sürüklenmiş sayı düzeltildi |
| BC · §10 terim açıklaması | *R-06 üç terimlik elle yazılmış listeyi soruyordu; düzyazıda on yedi açıklanmamış terim vardı* | **temiz** — on yedisi de ilk geçişte açıklandı |
| U · birimler arası tutarlılık | *hiç sınanmamıştı* | 1 kaldı (**bilerek** — U-02, insana bırakıldı) |

Doktrin kapsaması, yamadan sonra (on bir kural):
**tam mekanizmalı 1 · kısmi 9 · bozuk 1 · hiç kapsanmayan 0** — kitaba sadık
hâldeki 0 / 4 / 1 / 6'ya karşı.

Bu sayıya varmak için matrisin **kendisini** düzeltmek gerekti ve düzeltme bir
bulgudur. Matris üç kuralda **"YOK"** yazıyordu — 2 (olumsuz iddia), 8 (çıkar
çatışması) ve 7 (iki hukuk) — ve **üçünün de mekanizması vardı**: sırasıyla
N-01..N-08, denetimin çıkar çatışması kontrolü (mutasyonla doğrulandı: dosya
silinince `DENETİM BAŞARISIZ`) ve K-13. Notlar, mekanizmalar eklendikten
sonra bayatlamıştı.

Sebebi kitabın kendi kuralıdır. **"YOK" bir olumsuz iddiadır** ve CLAUDE.md §2
olumsuz iddiadan olumludan yüksek kanıt ister. Matris o iddiayı üç kez
**kanıtsız** yazdı — yani raporun §12 için kurduğu ölçüm, kendi §2'sini
çiğniyordu. Artık çiğnemiyor: F-01 matriste adı geçen her mekanizmanın
gerçekten var olduğunu, F-02 ise her "YOK" iddiasının aramanın boş dönmesiyle
kanıtlandığını denetliyor. İkisi de mutasyonla kırmızıya döndürüldü.

Kalan tek **BOZUK** kural 11'dir ve bu kitaba sadık hâlin kaydıdır; yamalı
sistemde çalışır. Dokuz "kısmi"nin her biri kanıtlanmış bir boşlukla yazılı:
kısmi, "yeterli" demek değildir.

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
./sinama/hepsi.sh                 # 52 çalıştırılabilir takım:
                                  #   387 vaka + 27 mutasyon (D)
                                  #   + 12 bağımlılık doğrulaması (E)
                                  # ayrıca 3 belge takımı (G, H, I)
./denetim.sh --yapisal            # mühendislik katmanı
./denetim.sh                      # mevzuat bulguları dâhil
```
Betikler kökü kendi konumundan çözer; klon da kaynak ağaç da aynı sonucu
verir (`MAFIRM` ile geçersiz kılınabilir).

Ham çıktılar: `sinama/SONUC-once.txt` (kitaba sadık) ve
`sinama/SONUC-sonra.txt` (yamalı). Dış doğrulamalar: `sinama/ks_g_depolar.md`,
`ks_h_kaynaklar.md`, `ks_i_mevzuat.md`.
Kitabın metni için düzeltme listesi: **`KITAP-ERRATA.md`** — bölüm bölüm,
ağırlık işaretli, her madde onu bulan sınama vakasıyla.

---

---

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

Elli beş takım, 387 vaka:

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
| J | **§19 kabul sınaması** — kitabın kendi son kapısı, uçtan uca | §19 |
| K | Yönlendirme, üst bilgi ve koltuk sağlaması | §7, §9, §10, §11 |
| L | Çapraz referans bütünlüğü ve taşınabilirlik | §4'ün düzen gerekçesi |
| M | **Errata ↔ sınama izlenebilirliği** — raporun kendisine kanıt kuralı | CLAUDE.md §1 |
| N | **Olumsuz iddia kanıtı** — raporun kendisine olumsuz iddia kuralı | CLAUDE.md §2 |
| O | **Sır kapısının kaçırma yüzeyi** — Unicode | CLAUDE.md §6 |
| P | **Teslimatların güncelliği** — raporun kendisine güncellik kuralı | CLAUDE.md §3 |
| Q | **Rapor kendi kapılarından geçiyor mu** | CLAUDE.md §5, §14 |
| R | **Yön, insan onayı ve dil** — raporun kendi biçimi | CLAUDE.md §4, §9, §10 |
| S | **Yalıtım** — klon gerçekten yalnız mı | §16'nın taşınabilirliği |
| T | **§18'in dokuz sınırı doğru mu** | §18, CLAUDE.md §2 |
| U | **Birimler arası tutarlılık** — bir birim ötekiyle çelişiyor mu | §4, §6, §5.3 |
| V | **Kapıların yanlış pozitifi** — doğru iş bloklanıyor mu | §12, §14 |
| W | **Sessizce boş arama kaynağı** — 'bulunamadı' ne demek | §2, §14, §10 |
| X | **Alt ajan yetkisi ↔ kapı kapsamı** — yetki var, kural var mı | §10, §12, kural 6 |
| Y | **Sırrın kalıcı deposu** — sistem neyi versiyonluyor | §2, kural 6 |
| Z | **Kurulum bütünlüğü** — kitap ikinci kez koşulursa | §2, §0 kural 4 |
| AA | **Kapının arıza yönü** — çökünce açık mı kapalı mı | §12, kural 6 |
| AB | **Blok iletisinin çaresi** — bloklanan ne yapacağını öğreniyor mu | §14, §12 |
| AC | **Ortam bağımsızlığı** — cevap makineye göre değişiyor mu | §6, §3, §12 |
| AD | **Komutların iddiaları** — §15 başka bileşenler hakkında ne söylüyor | §15, §9, §0 |
| AE | **Desen sınıfı taraması** — Türkçeyi ve kendi kimliklerini okumak | §12, B-10, U-05, AD-01 |
| AF | **Aparatın kendi iddiaları** — ölçen şeyi kim ölçüyor | §16, beklenen.json |
| AG | **Kitaba sadık taban** — kıyas ölçütü eksiksiz mi | yamalar/, §2, §5 |
| AH | **Cevabın güncelliği** — ilk ekran en tehlikeliyi söylüyor mu | §4, KITAP-ERRATA |
| AI | **Koltuk dayanakları** — gerçek kişilerin ağzına konan mercek neye dayanıyor | §7, §1 |
| AJ | **Çalışan kanalın kullanımı** — açık bulgu neyle ilerletilebilirdi | §2, §11 |
| AK | **Bulgu statüsü ve kanıt türü** — neyi neyle kapatabilirsin | §1, §9, §13 |
| AL | **Takımların yan etkisi ve bağımsızlığı** — takım kendi ölçtüğü ağacı kirletiyor mu | §8, kural 6, §12 |
| AM | **Kararın hukuki sürümü** — eşik değişince verilmiş görüşe ne oluyor | §3, §5.1, §11 |
| AN | **Yamanın kabul sınaması** — eklenen katman gerçekten karar verdiriyor mu | §15.1, kural 6 |
| AO | **Çıkar çatışmasının yönü ve zamanı** — kontrol simetrik mi, geriye bakıyor mu | §8, §9, §18.9 |
| AP | **Araç kataloğunun kurulumdaki hâli** — §13'ün kararları nerede yaşıyor | §13, §14, §3 |
| AQ | **Yaptırım taramasının zaman ekseni** — imza ile kapanış arasında ne oluyor | §9, §5.1, §6 |
| AR | **Onay durumu** — onay ihtiyacının beyanı ile onayın kendisi | §9, §12 |
| AS | **Kapıların öz-sınama kapsaması** — kitabın §14 kusurunu ben de işledim mi | §12, §14, §16 |
| AT | **Denetimin mutasyon kapsaması** — 26 kontrolün kaçı sınanıyor | §16, §12 |
| AU | **Epilog kontrollerinin sınaması** — koşumu bilen katman nasıl sınanır | §16, §12 |
| AV | **Anma/tanım sınıfı taraması** — ölçüt kodu mu, kodu anlatan cümleyi mi ölçüyor | §12, §16 |
| AW | **Kitap alıntılarının doğruluğu** — raporun kitaba atfettiği her cümle kitapta var mı | §1, §13.3, §14 |
| AX | **Kitap yapısı iddiaları** — raporun verdiği sayılar kitapla uyuşuyor mu | §12, §14, §16, §18 |
| AY | **Kitap hakkında olumsuz iddialar** — "kitap bunu söylemiyor" doğru mu, ve § atıfları doğru bölümü mü gösteriyor | §3, §8, §9, §16 |
| AZ | **Kitaba sadık kopyaların sadakati** — raporun "önce" tabanı gerçekten kitabın metni mi | §12, §14, §16 |
| BA | **Kayıt–iddia çelişkisi** — kayıt bir şeyin çalıştığını/doğrulandığını söylerken teslimat onu olumsuzluyor mu | §4, §17, §19 |
| BB | **Sayıların zaman indisi** — teslimattaki her toplam ya bugün ölçülene eşit ya da hangi koşuma ait olduğunu söylüyor mu | §12, §19 |
| BC | **§10 terim açıklaması** — düzyazıdaki her İngilizce/teknik terim ilk geçtiğinde açıklanmış mı (liste değil, keşif) | §10 |

**Sonuç: kitaba sadık kurulumda 85 vaka koşuldu, 56'sı kaldı.** Yamalı hâlde
**387 vaka + 27 mutasyon + 12 bağımlılık doğrulaması, 0 SİNYAL**. **On iki**
bilinen sapma `sinama/beklenen.json` içinde gerekçesiyle beyan edilmiş ve
BEKLENEN olarak raporlanıyor; her biri ya kitabın davranışının bilerek
bırakılmış kaydıdır, ya belgelenmiş bir öntanımlı boşluktur, ya da (U-02)
insana bırakılmış bir hukuki nitelendirmedir. Hiçbiri yamalı sistemde
çözülmemiş bir mühendislik kusuru değildir.

> Bu satırdaki sayılar bir kez **bayatladı**: rapor "on üç" diyordu, gerçek
> on birdi. El yazısı bir sayı, ölçtüğü şeyden bağımsız yaşar — kitabın
> §9'daki "10 beceri" beklentisiyle aynı kusur. `denetim.sh` artık bu üç
> sayıyı `beklenen.json` ve `hepsi.sh` çıktısıyla karşılaştırıyor.

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
5. **§6 `mimari.md`'nin 5. maddesine karar verin.** Kapanış öncesi koşul
   listesi, Ltd. Şti.'de TTK m.595/2 genel kurul onayını bir *koşul* sayıyor;
   kitabın kendi §5.3'ü onu devri *tamamlayan kurucu işlem* sayıyor. İkisi bir
   arada olamaz. Önerilen tek satırlık düzeltme `KITAP-ERRATA.md` §6'da yazılı
   ve kum havuzunda U-01 ile U-02'yi birlikte yeşile aldığı gösterildi;
   uygulanması bir hukuki nitelendirme kararıdır ve bu yüzden **yapılmadı**.
6. **Bir sonraki kurulumda `sinama/hepsi.sh` koşun.** 0 SİNYAL, raporun hâlâ
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
- **Ltd. Şti.'de TTK m.595/2 genel kurul onayının niteliği** (U-02): kapanış
  öncesi bir *koşul* mu, yoksa kapanış günü devri tamamlayan *kurucu* işlem mi?
  Cevap kapanış sırasını ve nihai tarih hesabını değiştirir; kitabın §6'sı ile
  §5.3'ü bu noktada birbiriyle çelişiyor.
- **§5'teki her eşiğin bugünkü değeri.** Bu raporun mevzuat katmanı
  **birincil kaynakla doğrulanmadı**; kanıt katmanı arama motoru özetidir ve
  bunun gerekçesi `hafiza/egress-kaniti.md` içinde kanıtlıdır.
- **Bu raporun bulgularına dayanarak canlı bir dosyada atılacak her adım.**

Kontrol edildi: rekabet.gov.tr arama sonuçları (2026-08-27) · GitHub MCP depo
çözümlemesi (2026-08-27) · yayıncı kayıtları (2026-08-27) · vekil egress ret
kaydı (2026-08-28) · yerel kurulum ve sınama takımı (2026-08-28) · birimler arası
tutarlılık taraması, 18 çalıştırılabilir takım (2026-08-28) ·
bulunamayan: 4054 sayılı Kanun ve 2026/2 sayılı Tebliğ'in birebir Resmî Gazete
metni (kuruluş egress politikası reddi)
