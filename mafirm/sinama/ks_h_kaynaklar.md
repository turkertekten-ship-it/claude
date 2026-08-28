# KÖR SINAMA H — §17 akademik kaynak doğrulaması

> **Doğrulama: 2026-08-27 · Bozulma sınıfı: YILLIK**
>
> Yayımlanmış makalelerin künyesi ve bulguları kalıcıdır. Değişebilecek
> olan tek şey erişilebilirlik ve ön baskı revizyonlarıdır.

Yöntem: WebSearch. **WebFetch bu ortamda journals.sagepub.com, papers.ssrn.com,
doi.org, api.crossref.org, api.openalex.org, arxiv.org, hbs.edu dâhil denenen
her alan adına engellendi.** Dolayısıyla hiçbir makalenin tam metni okunamadı;
aşağıdakiler arama motorunun yüzeye çıkardığı, bir kısmı makalenin gövde
metninden birebir alıntı olan pasajlara dayanır. Hiçbir rakam çıkarımla
üretilmedi; erişilemeyen her rakam DOĞRULANAMADI olarak işaretlendi.

## H-01 · Künye tamamen sağlam — GEÇTİ
Schwarcz ve ark., "AI-Powered Lawyering", *Journal of Law & Empirical Analysis*
cilt 3 sayı 1 (2026), s. 220–250, DOI 10.1177/2755323X261427048, ilk yayım
9 Nisan 2026. DOI çözülüyor. Yazar sırası, dergi, cilt, sayı, yıl doğru.
Tasarım (rastgele atamalı kontrollü deney), üç kol, altı görev, Minnesota ve
Michigan — hepsi doğru. Örneklem: 153 kayıtlı / 137 en az bir görevi bitiren /
125 hepsini bitiren. Kitabın "137 hukuk öğrencisi" ifadesi makul bir özet ama
tam görev kümesinin analiz örneklemi 125'tir.

## H-02 · Dört OLUMSUZ bulgunun dördü de doğrulandı — GEÇTİ
Kitabın asıl savını taşıyan bulgular bunlardır ve hepsi tutuyor:
- Doğrulukta anlamlı iyileşme yok; tek istisna dava dilekçesi çözümlemesi.
  Makale metni: "The one exception to the overall lack of significant accuracy
  improvements is that o1-preview improved accuracy when the assigned task
  required participants to focus their analysis on a single document."
- Gizlilik sözleşmesi kaleme almada hiçbir kalite boyutunda kazanç yok.
  Makale metni: "For transactional drafting, neither o1-preview nor Vincent AI
  produces significant gains on any quality attribute."
- Hukuki mütalaada genel kalite artışı anlamlı değil.
- Uydurma sayıları 3 / 11 / 4 — ve **akıl yürütme modeli, hiç AI kullanmayan
  insan kolundan daha fazla uydurdu (11'e 4)**. Kitabın §17.2'de üzerine
  kurduğu cümle doğrudur.

## H-03 · Süre düşüşü aralıkları hiçbir kaynakla uyuşmuyor — KALDI
Kitap: %20–28 (erişim destekli) ve %20–34 (akıl yürütme).
Bulunan her ikincil kaynak: **%14–37 (Vincent AI) ve %12–28 (o1-preview)**.
Kitabın rakamları iki kolun hiçbirine uymuyor; dahası kitap GENİŞ aralığı akıl
yürütme modeline veriyor, kaynaklar ise erişim destekli araca veriyor —
sıralama ters çevrilmiş olabilir. Tam metin açılamadığı için DOĞRULANAMADI
olarak işaretlendi, ama basılmadan önce tablo düzeyinde okunması gerekir.
Ek karışıklık: SSRN ön baskısı (4 Mart 2025) **27 Mayıs 2026'da**, yani dergi
yayımından SONRA revize edilmiş; ön baskı dönemi haberleri aşılmış rakamları
anlatıyor olabilir.

## H-04 · +0,26 puan bir KARIŞTIRMA — KALDI
Kitap: "Genel kalite (1–7 ölçeği): erişim destekli +0,26 · akıl yürütme +0,53".
Makale: iki araç da kaliteyi "**0,25** ile 0,53 puan arasında" artırıyor; ve
ayrıca "o1-preview ile Vincent AI etkileri arasındaki **0,26 puanlık FARK**
istatistiksel olarak ayırt edilebilir."
Kitap, iki AI kolu ARASINDAKİ farkı almış ve erişim destekli kolun kontrol
grubuna karşı etkisi olarak yazmış. Büyüklükler neredeyse aynı (0,25'e 0,26)
olduğu için aşağı akışta bir şey kırılmıyor; ama etiket yanlış ve kaynağı
kontrol eden okuyucu bunu yakalar.

## H-05 · Boyut düzeyi rakamları doğrulanamadı — DOĞRULANAMADI
Açıklık +0,47/+0,61 · Düzen +0,25/+0,63 · Profesyonellik +0,43/+0,95.
Hiçbir kamuya açık kaynakta boyut düzeyinde nokta tahminleri bulunamadı.
Yanlış oldukları söylenmiyor; doğrulanamadıkları söyleniyor.

## H-06 · "%19 daha düşük" yanlış ifade — KALDI, ve riski KÜÇÜLTÜYOR
Dell'Acqua ve ark. yayımlanmış sürümü: "reduced correctness by **19 percentage
points**" — 19 YÜZDE PUANI. Kitap "%19 daha düşük" yazıyor.
Bu fark önemsiz değil: bir doğruluk tabanından 19 yüzde puan düşmek, göreli
%19'luk bir düşüşten çok daha büyük bir etkidir. Kitap, tam da kanıtlamak için
alıntıladığı riski kendi ifadesiyle küçültmüş oluyor.

## H-07 · Dell'Acqua künyesi DOĞRU — şüphem yanlış çıktı
*Organization Science* cilt 37 sayı 2 (2026), s. 403–423,
DOI 10.1287/orsc.2025.21838. Çalışma HBS Working Paper 24-013 (Eylül 2023)
olarak başlamış ama **sonradan dergide yayımlanmış**. Kitabın verdiği künye
doğru. n=758, +%12,2 ve +%25,1 doğrulandı.

## H-08 · "+%40 kalite"nin atlanması DOĞRU bir karar
2023 çalışma tebliği "%40'tan fazla" diyor; **hakemli 2026 sürümü "%30'un
üzerinde"** diyor. Organization Science 2026 künyesine karşı +%40 alıntılamak
hatalı olurdu. Kitap bunu atlamakla doğru davranmış.

## H-09 · Noy & Zhang her unsurda temiz — GEÇTİ
*Science* 381(6654), s. 187–192, 14 Temmuz 2023, DOI 10.1126/science.adh2586.
n=453, süre −%40, kalite +%18. Dördü de doğrulandı.

## H-10 · §17.2'nin çıkarımı olgudan fazlasını söylüyor — KALDI
Kitap: "En yetenekli kol, en çok uyduran koldu. Uydurmayı azaltan şey modelin
zekâsı değil, cevabın bir kaynağa bağlanmasıydı."
Olgu doğru. Çıkarım dört noktada aşıyor:
1. 11'e 4 ham SAYIDIR, oran değil; ~125 katılımcı × 6 görevde yedi olaylık bir
   fark ve istatistiksel olarak sınandığına dair bir kanıt bulunamadı.
2. Bu bir MEKANİZMA karşılaştırması değil ÜRÜN karşılaştırmasıdır. Vincent AI
   "o1-preview artı erişim" değildir: farklı model, farklı arayüz, hukuka özgü
   derlem, güdümlü akış. İki kollu tasarım "kaynağa bağlama"yı ayrıştıramaz.
3. "En yetenekli" gizli iş görüyor: o1-preview açıklık, düzen ve
   profesyonellikte öndeydi ama DOĞRULUKTA (dava dilekçesi hariç) anlamlı bir
   üstünlüğü gösterilmedi. Uydurmanın ait olduğu boyutta üstün değildi.
4. Yazarların kendi okuması ters yöne işaret ediyor: erişim ile akıl yürütmenin
   birleşiminin "sinerjik iyileşme" verebileceğini söylüyorlar — yani ikisini
   ödünleşim değil tamamlayıcı sayıyorlar.
Ayrıca çalışma bir OTOMATİK KAPIYI hiç sınamadı. §17.2'nin "bu bulgu §12'deki
kanıt denetiminin neden bir kapı olduğunu tek başına açıklar" cümlesi, alıntının
taşıyabileceğinden fazlasını taşıyor.

## Özet
Künye ve olumsuz bulgular sağlam; kitap makaleyi gerçekten okumuş. Hatalar
uydurma değil AKTARIM hatası: iki etki büyüklüğü yanlış (H-03, H-04), bir birim
yanlış (H-06) ve bir çıkarım fazla geniş (H-10).

---

## Koltuk dayanakları — §7 (yirmi yedinci turda eklendi)

§7 koltuk provenansını sistemin **en yüksek itibar riski** sayar. K-15 kapısı
her koltuğun bir `## Kaynak durumu` beyanı taşımasını zorunlu kılar. Ama beyan
**adı geçen eserlere** dayanır ve o eserlerin gerçekten var olup olmadığı,
doğru kişiye ait olup olmadığı **yirmi altı tur boyunca hiç doğrulanmadı** —
yani §1'in kanıt kuralı, §7'nin en çok önemsediği iddialara uygulanmamıştı.

Doğrulama: 2026-08-28 · yöntem: web araması, yayıncı ve kütüphane kayıtları.

| # | Eser | Atfedilen | Doğrulama |
|---|---|---|---|
| H-20 | *A Manual of Style for Contract Drafting* | Kenneth A. Adams | **Doğrulandı** — ABA yayını; 1. baskı 2004, 5. baskı 2023. |
| H-21 | *Anatomy of a Merger* (1975) | James C. Freund | **Doğrulandı** — 1975; yazar Skadden, Arps'ta. Koltuktaki **1975 tarihi doğru**. |
| H-22 | *Smart Negotiating* | James C. Freund | **Doğrulandı** — Simon & Schuster, 1992. |
| H-23 | *The Inside Counsel Revolution* | Ben W. Heineman, Jr. | **Doğrulandı** — yazar GE baş hukuk müşaviri 1987–2003; koltuktaki "uzun süreli baş hukuk müşaviri" ifadesi doğru. |
| H-24 | *Tools and Weapons* (2019) | Brad Smith | **Doğrulandı** — Penguin Press; yazar Microsoft başkanı. **Not:** eser Carol Ann Browne ile **ortak yazarlıdır**; koltuk ortak yazarı anmıyor. |
| H-25 | "Zehir hapı"nı 1982'de tasarlayan kişi | Martin Lipton | **Doğrulandı** — Wachtell, Lipton, Rosen & Katz kurucu ortağı; pay sahibi hakları planını 1982'de geliştirdi. |
| H-26 | *The Future of Privacy* (2013) | Eduardo Ustaran | **Doğrulandı** — DataGuidance, 2013; yazar Hogan Lovells veri koruma ortağı. |

Kontrol edildi: yayıncı ve kitapçı kayıtları (2026-08-28) · Microsoft ve
Hogan Lovells kurumsal sayfaları (2026-08-28) · Harvard Law School Forum on
Corporate Governance (2026-08-28) · bulunamayan: yok

**Kalan kusur:** H-24'te ortak yazar anılmıyor. Bir koltuğun dayanağı
ORTAK YAZARLI bir eserse, mercek tek bir kişiye atfedilirken bu söylenmelidir;
aksi hâlde koltuk, kitabın tamamını tek kişinin görüşü gibi sunar.
