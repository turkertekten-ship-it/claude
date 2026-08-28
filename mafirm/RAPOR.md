# Kör sınama raporu · Uluslararası M&A Hukuku Kurulum Kitabı

> **Doğrulama: 2026-08-28 · Bozulma sınıfı: KURULUMA BAĞLI**
>
> Bulgular, sınandıkları kurulum için geçerlidir. Kitabın metni ya da
> kurulum değişirse `sinama/hepsi.sh` yeniden koşulmalıdır: 0 SİNYAL,
> raporun hâlâ ölçtüğü sistemi anlattığının kanıtıdır.

Sürüm 1.0 · 2026-08-27 · OODA döngüsü: gözlem → yönelim → karar → eylem → döngü

## Cevap

**Kitap iyi bir kitap ve harfiyen izlendiğinde çalışmıyor.** Kitaba sadık,
eksiksiz kurulumda 85 kör sınama vakasının 56'sı başarısız oldu ve kitabın
kendi §16 denetimi yeşile dönmedi.

Üç cümlede sebebi:

1. **§14, §12'nin öz-sınamasını bozuyor** ve düzeltilmiyor; zincir §16'yı
   kırmızıya, §0'ın dördüncü kuralını da kurulumu durdurmaya götürüyor. §19'daki
   ilk dosya hiç çalışmıyor.
2. **Kapılar biçimi denetliyor, muhakemeyi değil** — ve kitaba sadık hâlleriyle
   §19'un DOĞRU cevabını da YANLIŞ cevabını da bloklıyorlar, yani §19'un
   "kurulumun tamamının sebebi" dediği farkı ifade edemiyorlar.
3. **Denetim on beş bozmadan on birini görmüyor**; sıfır beceri, kancasız
   ayarlar ve tamamen boş bir `esik.py` taşıyan bir sistemde "DENETİM OK" diyor.

**Yamalı hâlde sistem çalışıyor:** yirmi bir çalıştırılabilir takım — **212
vaka, 15 mutasyon, 12 bağımlılık doğrulaması, 0 sinyal**;
denetimin mutasyon yakalaması 4/15 → 15/15, birimler arası tutarlılık takımının
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
**Bu oturumda dört Türk birincil kaynağı alan adına HTTPS, kuruluş
egress politikasıyla CONNECT aşamasında 403 ile reddedildi** (CONNECT: bir
vekil üzerinden şifreli bağlantı açma isteği; ret, bağlantı kurulmadan
önce orada verildi) (kanıt: `hafiza/egress-kaniti.md`): `mevzuat.gov.tr`,
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
erişilemedi" yanlış olurdu; GitHub MCP ile on altı depo çözüldü).

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
oluşur.** PDF ya da Word'den kopyala yapıştır rutin olarak yumuşak tire,
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

Düzeltme yalnızca sır kapısında: biçim karakterlerini at, NFKC ile birleştir (Unicode'un uyumluluk normalleştirmesi: ayrışmış aksanları tek karaktere indirger),
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

Aynı turda §9 ve §10 da uygulandı: raporun **onaysız olduğu ilk bölümde**
yazılı (sessizlik onaylanmış gibi okunur), ve NFKC, CONNECT, homoglif gibi
terimler ilk geçtiklerinde açıklandı.

### Ve bu, kitapta bir kusur daha gösterdi

F matrisinde §4, §9 ve §10 "hiç kapsanmayan" diye duruyordu — kitap onları
"biçim kuralı, kapı konusu değil" diye geçmişti. Oysa üçü de kısmen makinece
kontrol edilebilir: §4 bir başlık sırası kuralıdır, §9 onayın kendisini değil
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
sayıyordu. Yani **her SPA incelemesi ve her ortaklık yapısı notu** üç kapıyı
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
| D · mutasyon | 11 kaçtı | **temiz — 15/15 yakalandı** |
| E · beklenen değerler | 4 kaldı | 3 kaldı (kitabın kendi değerleri) |
| J · §19 kabul sınaması | doğru cevap da bloklu | 2 kaldı (**bilerek** — kitaba sadık karşılaştırma) |
| K · yönlendirme + koltuk | 3 kaldı | **temiz** |
| L · referans bütünlüğü | 1 kaldı (kendi regresyonum) | **temiz** |
| M · errata izlenebilirliği | 3 kaldı (kendi raporum) | **temiz** |
| N · olumsuz iddia kanıtı | kanıtsızdı | **temiz** |
| V · kapıların yanlış pozitifi | *hiç ölçülmemişti* | **temiz** — 17 meşru metin, 0 yanlış pozitif |
| W · sessizce boş arama kaynağı | *hiç sorulmamıştı* | **temiz** — boş banka artık sesli |
| X · yetki ↔ kapsam | *hiç sorulmamıştı* | **temiz** — beyan ile uygulama hizalandı |
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
./sinama/hepsi.sh                 # 21 çalıştırılabilir takım:
                                  #   212 vaka + 15 mutasyon (D)
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

**Sonuç: kitaba sadık kurulumda 85 vaka koşuldu, 56'sı kaldı.** Yamalı hâlde
**212 vaka + 15 mutasyon + 12 bağımlılık doğrulaması, 0 SİNYAL**. **On iki**
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
