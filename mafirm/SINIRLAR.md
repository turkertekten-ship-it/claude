# Ölçülmüş kanıt ve bilerek yapılmayanlar

Doğrulama: 2026-08-27.

Kontrol edildi: kurulum kitabı §17 ve §18 (2026-08-27) · bulunamayan: aşağıdaki
üç çalışmanın tam metinleri — DOI ve künye kitaptan alınmıştır, bu makineden
birincil kaynaktan TEYİT EDİLMEMİŞTİR. Rakamlara dayanmadan önce çalışmalar
okunmalıdır.

Bu dosya sistemin satış broşürü değil, sınır beyanıdır. Sınırları yazılmamış
bir sistem, o sınırların ötesinde kullanılır ve sınırı ilk bulan kişi onu bir
müvekkilin karşısında bulur.

## §17.1 Hukuk işinde ölçülmüş etki

Kaynak: Daniel Schwarcz, Sam Manning, J.J. Prescott, Patrick Barry,
David R. Cleveland, Beverly Rich. *AI-Powered Lawyering: AI Reasoning Models,
Retrieval Augmented Generation, and the Future of Legal Practice.* Journal of
Law & Empirical Analysis, cilt 3, sayı 1, 2026. DOI 10.1177/2755323X261427048.

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

### Asıl önemli kısım: nerede hiçbir şey almadı

1. **Doğruluk artmadı.** Dava dilekçesi çözümlemesi dışında hiçbir görevde,
   hiçbir araçla doğrulukta anlamlı iyileşme yok. Kazanç açıklıkta, düzende ve
   profesyonellikte; **doğru olmakta değil.**
2. **Gizlilik sözleşmesi kaleme almada sıfır.** İki araç da hiçbir kalite
   boyutunda anlamlı kazanç üretmedi. Bu, bu kitabın kapsadığı işe **en yakın**
   görevdir: işlemsel belge kaleme alma.
3. Hukuki mütalaada genel kalite artışı istatistiksel olarak anlamlı değildi.
4. **Uydurma sayısı:** erişim destekli araçta 3, akıl yürütme modelinde 11,
   AI kullanmayan kontrol kolunda 4. Akıl yürütme modeli, hiç AI kullanmayan
   insandan **daha fazla uydurdu.**

## §17.2 Bunun bu sisteme doğrudan sonucu

Dördüncü bulgu, §12'deki kapıların neden bir belgedeki kural değil çalışan bir
otomatik kontrol olduğunu tek başına açıklar: **en yetenekli kol, en çok
uyduran koldu.** Uydurmayı azaltan şey modelin zekâsı değil, cevabın bir
kaynağa bağlanmasıydı.

İkinci bulgu, bu kurulumun ne vaat ettiğini sınırlar. Bu sistem, kaleme alma
hızını artıracağı için kurulmadı. Yöntemi yazıya döktüğü, her rakamı dayanağına
bağladığı ve kuralın uygulandığını denetlediği için kuruldu.

## §17.3 Sınırın kendisi ölçülmüştür

Kaynak: Fabrizio Dell'Acqua ve arkadaşları, *Navigating the Jagged
Technological Frontier*, Organization Science, 2026. 758 bilgi çalışanı.

Modelin yapabildiği işte tamamlanan görev **%12,2** ve hız **%25,1** artmıştır.
Modelin yeteneğinin **dışında** kalan bir görevde ise, AI kullanan
katılımcıların doğru sonuç üretme olasılığı **%19 daha düşük** çıkmıştır.

Kayıp, kazanç kadar gerçektir ve kullanıcı onu fark etmez. Sınır ötesi bir
işlemde bu sınır coğrafidir: modelin İngiliz hukuku sözleşme kalıplarında
olduğu yer ile Türk tescil şekil şartında olduğu yer aynı değildir. §7'deki
Türk hukukçu koltuğunun bilerek boş bırakılmasının ölçülmüş gerekçesi budur.

## §17.4 Genel verimlilik kanıtı

Kaynak: Shakked Noy ve Whitney Zhang, *Experimental evidence on the
productivity effects of generative artificial intelligence*, Science 381(6654),
2023. 453 profesyonel. Yazma görevinde süre %40 düşmüş, çıktı kalitesi %18
artmıştır.

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

10. **Türk mevzuatının birincil metinleri bu makineden doğrulanamadı.** Resmî
    Gazete, mevzuat.gov.tr, rekabet.gov.tr ve spk.gov.tr ağ çıkışı
    politikasıyla engellidir. Bu sistemdeki her Türk hukuku ifadesi ikincil
    kaynaklara ve kurulum kitabına dayanır; her yöntem dosyası bunu kendi
    "Kontrol edildi" satırında yazar. Kıdem tazminatı tavanı gibi doğrulanamayan
    tutarlara **hiç rakam yazılmamıştır.**

## Şimdi ne yapılmalı

Bu dosya, sistemi birine tanıtan her sunumun yanında durur. Kazanç kısmı
söylenirken §17.1'in "nerede hiçbir şey almadı" başlığı da söylenir.

## Yetkili avukat görüşü gereken konular

Bu sistemin bir müvekkil işinde kullanılıp kullanılamayacağı, hangi çıktının
insan onayından geçmesi gerektiği ve yukarıdaki üç çalışmanın künyelerinin
teyidi.
