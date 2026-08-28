# Ölçülmüş kanıt ve bilerek yapılmayanlar

Doğrulama: 2026-08-27.

Kontrol edildi: kurulum kitabı §17 ve §18 (2026-08-27) · Schwarcz ve
arkadaşlarının çalışmasının künyesi, DOI'si ve özet bulguları, web araması
(2026-08-27) · bulunamayan: çalışmaların TAM METİNLERİ — journals.sagepub.com
ve SSRN bu makineden engelli; aşağıdaki tablo kitaptan alınmıştır ve
**yayımlanmış özetle bir noktada çelişmektedir** (bkz. aşağıdaki uyarı).

Bu dosya sistemin satış broşürü değil, sınır beyanıdır. Sınırları yazılmamış
bir sistem, o sınırların ötesinde kullanılır ve sınırı ilk bulan kişi onu bir
müvekkilin karşısında bulur.

## §17.1 Hukuk işinde ölçülmüş etki

Kaynak: Daniel Schwarcz, Sam Manning, J.J. Prescott, Patrick Barry,
David R. Cleveland, Beverly Rich. *AI-Powered Lawyering: AI Reasoning Models,
Retrieval Augmented Generation, and the Future of Legal Practice.* Journal of
Law & Empirical Analysis, cilt 3, sayı 1, 2026. DOI 10.1177/2755323X261427048.

**Künye doğrulandı** (2026-08-27): yazarlar, dergi, cilt, sayı, yıl ve DOI
yayımlanmış kayıtla birebir uyuşuyor. Çalışma, üst sınıf hukuk öğrencilerini
erişim destekli bir hukuk aracı (Vincent AI), bir akıl yürütme modeli
(o1-preview) ve AI'sız kola rastgele atayan ilk kontrollü deneydir.

Tasarım: rastgele atamalı kontrollü deney. 153 kayıtlı, 137 hukuk öğrencisi,
125'i altı görevin tamamını bitirdi. Altı görev uygulamacı avukatlarla birlikte
tasarlandı. Üç kol: AI yok, erişim destekli hukuk aracı, akıl yürütme modeli.

| Ölçü | Erişim destekli araç | Akıl yürütme modeli |
|---|---|---|
| Süre düşüşü (altı görevin beşinde) | %20–28 | %20–34 |
| Kalite düzeltilmiş verim | +%50 ila +%110 | +%75 ila +%131 |
| Genel kalite (1–7) | +0,26 | +0,53 |
| Açıklık | +0,47 | +0,61 |
| Düzen | +0,25 | +0,63 |
| Profesyonellik | +0,43 | +0,95 |

> **UYARI — verim rakamları çelişiyor.** Yayımlanmış özet, verim kazancını
> erişim destekli araç için yaklaşık **%38–115**, akıl yürütme modeli için
> **%34–140** olarak veriyor. Yukarıdaki tablo kitaptan alınmıştır ve
> %50–110 / %75–131 der. İki aralık aynı değildir; muhtemelen farklı bir ölçüt
> ya da makalenin farklı bir sürümü (SSRN ön baskısı) söz konusudur. **Tam
> metin bu makineden okunamadı; bu rakamlara sunumda dayanılmadan önce makale
> açılmalıdır.** Aşağıdaki "nerede hiçbir şey almadı" bulguları ise yayımlanmış
> özetle **doğrulanmıştır** ve bu sistemin dayandığı kısım odur.

### Asıl önemli kısım: nerede hiçbir şey almadı

1. **Doğruluk artmadı.** Dava dilekçesi çözümlemesi dışında hiçbir görevde,
   hiçbir araçla doğrulukta anlamlı iyileşme yok. Kazanç açıklıkta, düzende ve
   profesyonellikte; **doğru olmakta değil.**
2. **Gizlilik sözleşmesi kaleme almada sıfır.** İki araç da hiçbir kalite
   boyutunda anlamlı kazanç üretmedi. Bu, bu kitabın kapsadığı işe **en yakın**
   görevdir: işlemsel belge kaleme alma. **Doğrulandı (2026-08-27):** yayımlanmış
   özet, yüksek düzeyde yapılandırılmış ya da şablona dayalı görevlerin —
   özellikle gizlilik sözleşmesi kaleme almanın — kalite iyileşmesi bakımından
   AI'dan çok daha az yararlandığını söylüyor.
3. Hukuki mütalaada genel kalite artışı istatistiksel olarak anlamlı değildi.
4. **Uydurma sayısı:** erişim destekli araçta 3, akıl yürütme modelinde 11,
   AI kullanmayan kontrol kolunda 4. Akıl yürütme modeli, hiç AI kullanmayan
   insandan **daha fazla uydurdu. Doğrulandı (2026-08-27):** yayımlanmış özet,
   akıl yürütme modelinin çözümleme derinliğini artırdığını ama uydurmaya yol
   açtığını, erişim destekli araç kullananların ise AI kullanmayanlarla
   **kabaca aynı** sayıda uydurma ürettiğini söylüyor. Sayıların tam değerleri
   tam metinden teyit edilemedi; yön ve büyüklük sırası doğrulandı.

## §17.2 Bunun bu sisteme doğrudan sonucu

Dördüncü bulgu, §12'deki kapıların neden bir belgedeki kural değil çalışan bir
otomatik kontrol olduğunu tek başına açıklar: **en yetenekli kol, en çok
uyduran koldu.** Uydurmayı azaltan şey modelin zekâsı değil, cevabın bir
kaynağa bağlanmasıydı.

İkinci bulgu, bu kurulumun ne vaat ettiğini sınırlar. Bu sistem, kaleme alma
hızını artıracağı için kurulmadı. Yöntemi yazıya döktüğü, her rakamı dayanağına
bağladığı ve kuralın uygulandığını denetlediği için kuruldu.

## §17.3 Sınırın kendisi ölçülmüştür

Kaynak: Fabrizio Dell'Acqua, Edward McFowland III, Ethan Mollick, Hila
Lifshitz-Assaf, Katherine Kellogg, Saran Rajendran, Lisa Krayer, François
Candelon, Karim Lakhani. *Navigating the Jagged Technological Frontier: Field
Experimental Evidence of the Effects of Artificial Intelligence on Knowledge
Worker Productivity and Quality.* Organization Science, 2026.
DOI 10.1287/orsc.2025.21838. Künye doğrulandı: 2026-08-27.

**Katılımcılar 758 yönetim danışmanıdır** (Boston Consulting Group danışman
kadrosunun yaklaşık yüzde yedisi), genel anlamda "bilgi çalışanı" değil.
Kitap bunu "758 bilgi çalışanı" diye aktarıyor; örneklem tek bir danışmanlık
firmasından geldiği için sonuçların bir hukuk pratiğine taşınması zaten
temkin ister.

Modelin yapabildiği işte (sınırın **içinde**): tamamlanan görev **%12,2**, hız
**%25,1**, kalite **%40** artmıştır. Kitap kalite rakamını atlıyor.

Modelin yeteneğinin **dışında** kalan bir görevde ise AI kullanan danışmanlar,
kullanmayanlara göre **19 yüzde puanı** daha kötü sonuç üretmiştir.

> **Düzeltme:** kitap bunu "%19 daha düşük" diye yazıyor. Doğrusu **19 yüzde
> puanı**dır ve bu aynı şey değildir: yüzde puan farkı, oranın kendisine göre
> çok daha büyük bir göreli düşüşe karşılık gelebilir. Bir kurul sunumunda bu
> iki ifadeyi karıştırmak, ölçülmüş bir bulguyu yanlış aktarmaktır.

Kayıp, kazanç kadar gerçektir ve kullanıcı onu fark etmez. Sınır ötesi bir
işlemde bu sınır coğrafidir: modelin İngiliz hukuku sözleşme kalıplarında
olduğu yer ile Türk tescil şekil şartında olduğu yer aynı değildir. §7'deki
Türk hukukçu koltuğunun bilerek boş bırakılmasının ölçülmüş gerekçesi budur.

## §17.4 Genel verimlilik kanıtı

Kaynak: Shakked Noy ve Whitney Zhang, *Experimental evidence on the
productivity effects of generative artificial intelligence*, Science 381(6654),
2023. DOI 10.1126/science.adh2586. Künye ve rakamlar doğrulandı: 2026-08-27.

453 üniversite mezunu profesyonele mesleklerine özgü, teşvikli yazma görevleri
verilmiş; yarısı rastgele ChatGPT'ye maruz bırakılmıştır. Ortalama süre **%40**
düşmüş, çıktı kalitesi **%18** artmıştır. Çalışanlar arasındaki eşitsizlik de
azalmıştır. Kitabın verdiği iki rakam da doğrudur.

Bu hukuka özgü **değildir** ve hukuka özgüymüş gibi sunulmamalıdır.

## §18 Bu sistemin bilerek yapmadıkları

1. **Hukuki görüş vermez ve bir hukuk bürosu değildir.** Yalnızca karar
   desteği. Kapsam kuralı ve §12'deki kapı, en çok önem taşıyan kusur bu olduğu
   için vardır.
2. **Türk uygulamacı koltuğu yoktur.** `_koltuklar/turk-hukukcu.md` açıkça
   boştur. Türk hukuku soruları doğrulanmış yöntem dosyalarından cevaplanır ya
   da hiç cevaplanmaz.
3. **Vergi koltuğu yoktur** ve işlem yapısı vergi kaynaklıdır. Aynı muamele.
4. **Türkiye rakamlarının raf ömrü vardır.** Her şey 2026-08-27'de
   doğrulanmıştır; altı aydan eskisi bayattır. `/esik-denetle` yeniden çeker,
   **düzenlemez** — bir eşik değişikliği canlı bir dosyada verilmiş görüşü
   geçersiz kılabilir.
5. **`eyecite` ve `courtlistener` yalnızca ABD'dir.** Yargıtay ya da Rekabet
   Kurulu emsalinden haberleri yoktur. Bu sistemde Türk içtihadı YOKTUR.
6. **Üç sözleşme çözümleme deposundan ikisi bakımsızdır, biri AGPL-3.0'dır.**
   İkisi de `_araclar/katalog.md` içinde yazılıdır, atlanmamıştır.
7. **İşlemsel belge kaleme almada ölçülmüş kazanç yoktur** (§17.1, ikinci
   bulgu). Kaleme alma hızını vaat eden bir sunum, elindeki kanıtın söylemediği
   bir şeyi söylüyor demektir.
8. **Doğruluğu artırdığına dair kanıt yoktur** (§17.1, birinci bulgu).
   Doğruluğu sağlayan şey §12'deki kapılar ve yetkili avukat onayıdır, modelin
   kendisi değil.
9. **Kendisine söylenmemiş bir çıkar çatışmasını kontrol edemez.**
   `hafiza/cikar-catismasi.md` yalnızca içine yazılan kadar iyidir.

## Bu kuruluma özgü onuncu sınır

10. **Türk mevzuatının birincil metinleri hâlâ okunmadı — ama artık çapraz
    doğrulandı.** Resmî Gazete, mevzuat.gov.tr, rekabet.gov.tr, spk.gov.tr ve
    journals.sagepub.com ağ çıkışı politikasıyla engellidir; hiçbir kanun
    metni birincil kaynaktan **okunmamıştır**.

    İkinci turda (2026-08-28) her esaslı atıf, birbirinden bağımsız ikincil
    kaynaklarla **çapraz doğrulandı** ve dört gerçek hata bulundu:

    | Konu | Kitapta / ilk sürümde | Doğrulanan |
    |---|---|---|
    | Bekletici şart | 4054 m.11 | **4054 m.10 + 2010/4 Tebliğ m.10** |
    | Dell'Acqua kaybı | "%19 daha düşük" | **19 yüzde puanı** |
    | Kıdem tavanı | yazılmadı | **73.729,87 TL** (Tem-Ara 2026) |
    | İdari para cezası alt sınırı | yoktu | **302.484,86 TL** (2026) |

    Ayrıca kitapta hiç bulunmayan dört kural eklendi: cezanın devralmada
    **yalnızca devralana** verilmesi; 4857 m.6'daki iki yıllık sınırın **kıdem
    tazminatında işlememesi**; II-26.1'deki **imtiyaz nedeniyle kontrol
    elde edilememesi** istisnası; ve New York Sözleşmesi'ne Türkiye'nin
    **karşılıklılık ve ticari ilişki çekinceleri**.

    **Çapraz doğrulama, birincil metin okumanın yerine geçmez.** Her yöntem
    dosyası kendi "Kontrol edildi" satırında hangisinin yapıldığını yazar.
    Süreye bağlı bir adımda ya da bir kurum başvurusunda dayanılacak her ifade
    için birincil metin hâlâ okunmalıdır.

## Şimdi ne yapılmalı

Bu dosya, sistemi birine tanıtan her sunumun yanında durur. Kazanç kısmı
söylenirken §17.1'in "nerede hiçbir şey almadı" başlığı da söylenir.

## Yetkili avukat görüşü gereken konular

Bu sistemin bir müvekkil işinde kullanılıp kullanılamayacağı, hangi çıktının
insan onayından geçmesi gerektiği ve yukarıdaki üç çalışmanın künyelerinin
teyidi.
