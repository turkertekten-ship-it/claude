# KÖR SINAMA G — §13 depo kataloğu, bağımsız yeniden çözümleme

> **Doğrulama: 2026-08-27 · Bozulma sınıfı: GÜNLÜK**
>
> Yıldız sayıları ve son itme tarihleri her gün değişir; lisans ve arşiv
> durumu aylarca dayanır. Bu dosyanın SAYISAL iddiaları bir gün sonra
> bayattır — kitabın §13'üne yönelttiğim G-05 eleştirisi bu dosyaya da
> aynen uygulanır. Yeniden çekmeden hiçbir yıldız sayısına dayanılmaz.

Yöntem: 16 girdinin tamamı GitHub MCP `search_repositories` (minimal_output:false)
ile yeniden çözüldü; lisans dosyaları `raw.githubusercontent.com` üzerinden
metin düzeyinde okundu; 3, 4, 8, 10, 12, 14 numaralı girdiler ayrıca depo HTML
sayfasından çapraz kontrol edildi. Ham `curl https://api.github.com/...` bu
ortamda 403 döndüğü için kitabın §14'te önerdiği komut doğrudan çalışmaz —
bu da başlı başına bir bulgudur (bkz. G-07).

Çözülme oranı: 16/16. Kitabın hiçbir deposu uydurma değil.

## Onaylanan
- docling ve pdfplumber lisansları dosya düzeyinde MIT olarak doğrulandı.
  §13.7'nin "PyMuPDF AGPL, bu ikisi değil" karşıtlığı bu iki depo için tutuyor.
- PyMuPDF AGPL-3.0 doğrulandı (COPYING = GNU AGPL v3; ayrıca ticari lisans
  seçeneği var).
- lexpredict-lexnlp AGPL-3.0, 795 yıldız, son itme 2024-05-27 — birebir doğru.
- nomenklatura (265), pandera (4.442), opensanctions (789) yıldız sayıları birebir.

## Bulgular

### G-01 · courtlistener lisansı maddi olarak yanlış — KALDI
Kitap: "açık (depoya bakın)". Gerçek: **AGPL-3.0-or-later**
(LICENSE.txt: Free Law Project, GNU AGPL v3). GitHub API'si dosyadaki özel
önsöz yüzünden `NOASSERTION` döndürüyor; muğlak ifade büyük olasılıkla oradan
geliyor.
Neden önemli: §13.7 tam olarak bu soruyu soruyor ve PyMuPDF'i AGPL diye
eliyor. Aynı listede, aynı lisanslı ikinci bir depo "açık" diye geçiyor.
Kitabın kendi lisans muhakemesi kendi tablosunda tutarsız.

### G-02 · diff-match-patch arşivlenmiş, yazılmamış — KALDI
Kitap: "Kullan. Kararlı algoritma; burada eskime bozulma değildir."
Gerçek: depo **2024-08-05'te sahibi tarafından arşivlendi**, salt okunur.
Yıldız, tarih ve lisans birebir doğru; arşiv durumu yok.
"Eskime bozulma değildir" savunulabilir bir yargıdır — ama arşivlenmiş bir
depo artık bir yargı konusu değil, bir olgudur ve §14'ün dört alanı arasında
"arşivlendi mi" yok.

### G-03 · opensanctions ikili lisans, yazılmamış — KALDI
Kitap: "MIT". Gerçek: **kod MIT, VERİ CC BY-NC 4.0** ve `datasets/` altındaki
bazı dosyalar için depo "hiç lisanslayamıyoruz" diyor.
Neden önemli: NC = ticari kullanım dışı. §13.3 bu ikiliyi "bu katalogda bir
Türk pratiği için en kullanışlı olan" diye öneriyor. Bir hukuk bürosu ticari
bir kuruluştur. Bu, §13.7'nin AGPL için ayırdığı "asıl sahibin kararı"
kategorisine giren bir lisans sorusudur ve tabloda görünmüyor.

### G-04 · Agent-Reach: var, ama konuyla ilgisi tartışmalı — KISMİ
`Panniantong/Agent-Reach` gerçekten var: 75.887 yıldız, MIT, etkin.
Ancak bir sosyal medya kazıma aracı (Twitter, Reddit, YouTube, Bilibili,
XiaoHongShu) ve README'si çerez tabanlı kimlikle hesap kapatma riski uyarısı
taşıyor. §13.2 onu "karşı taraf istihbaratı" başlığına koyuyor ve yalnızca
yazma fiillerini yasaklıyor; hesap riski ve müvekkil gizliliği açısından
okuma fiilleri de sorunlu olabilir.

### G-05 · yıldız sayıları karışık: kimi birebir, kimi kaymış — KISMİ
Dokuz girdi birime kadar tutuyor (aynı gün çekilmiş olmalı), yedisi tutmuyor:
docling +61, crawl4ai +79, Agent-Reach −487, OpenContracts +3,
great_expectations +4, eyecite +1, python-docx −1.
Hepsinin "27 Ağustos 2026'da doğrulandığı" ifadesiyle uyuşmuyor; katalog
farklı zamanlarda derlenmiş görünüyor. Kitabın kendi güncellik kuralı
(CLAUDE.md §3) tam olarak bunu yasaklıyor: tek bir doğrulama tarihi taşıyan
bir tablo, kontrol edilmiş gibi durur.

### G-06 · İKİ ŞÜPHEM YANLIŞ ÇIKTI — kitap haklı
Kör sınamanın kendi hatası olarak kaydedilir:
- `great-expectations/great_expectations` artık **fivetran/great_expectations**
  adresine yönleniyor (aynı depo kimliği 103071520). Kitabın yazdığı yol
  DOĞRU; benim hatırladığım yol bayat.
- `JSv4/OpenContracts` → **Open-Source-Legal/OpenContracts** yönlendirmesi
  var (aynı depo kimliği 556553471). Kitabın yazdığı yol DOĞRU.
Bu, §14'ün kendi kuralının kanıtı: "bir ad, var olduğunun kanıtı değildir"
kadar "hatırladığın ad, doğru ad değildir" de geçerli.

### G-07 · §14'ün önerdiği doğrulama komutu bu ortamda çalışmıyor — KALDI
once-arastir becerisi şunu söylüyor:
`curl -s "https://api.github.com/repos/<sahip>/<depo>"`
Bu ortamda ajan vekili bu çağrıya **HTTP 403** döndürüyor. Beceri, kendi
belgelediği yöntemle çalıştırıldığında boş döner ve §14'ün ikinci tuzağı
("boş bir GitHub araması yokluğun kanıtı değildir") tam da bu duruma denk
gelir. Doğrulama yalnızca MCP araçlarıyla yapılabildi.

## Özet
16 depo · 16'sı çözüldü · 4 maddi bulgu (G-01, G-02, G-03, G-07) ·
2 kısmi (G-04, G-05) · 2 yanlış şüphe (G-06, kör sınamanın kendi hatası)
