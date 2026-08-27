# Kapanış sonrası iş akışı — tescil, süre, emanet, bütünleşme

Doğrulama: 2026-08-27.

Kontrol edildi: `birimler/tr-sirketler/yontem/pay-devri.md` (TTK m.490, 499,
595) · `birimler/rekabet/yontem/tr-esikler.md` (4054 sayılı Kanun m.11 ve m.16) ·
`birimler/is-hukuku/yontem/isci-devri.md` (4857 m.6) ·
`birimler/sinir-otesi/yontem/elkitabi-alici.md` Aşama 5 ve
`birimler/sinir-otesi/yontem/elkitabi-satici.md` Aşama 6 ·
`birimler/uyusmazlik/yontem/tahkim-ve-tenfiz.md` · `.claude/skills/` ve
`.claude/commands/` içindeki gerçek adlar (2026-08-27) · bulunamayan: Ticaret
Sicili Müdürlüğü tescil ve Türkiye Ticaret Sicili Gazetesi ilan sürelerine dair
güncel uygulama verisi; ayrıca TTK madde numaraları bu kurulumda birincil
kanun metninden teyit edilmedi (ağ çıkışı engelli).

## Ne zaman bu iş akışı

Kapanış imzaları atıldıktan sonra çalıştırılır ve dosyanın en çok terk edilen
bölümüdür: para geçmiştir, ekip dağılmıştır ve kalan iş idari görünür.
Görünmediği şey şudur — Türkiye'de devrin tamamlanması kapanış masasında değil
tescil ve pay defteri kaydıyla olur; beyan talep süreleri sessizce dolar ve
dolduğunda geri gelmez; emanet, kimse bir tarih yazmadıysa serbest bırakılmaz
ya da erken bırakılır; ve bütünleşme, iznin tarihinden önce başlarsa kapanışın
kendisi 4054 sayılı Kanun madde 11 bakımından sorgulanır. Bu akış, kapanıştan
sonraki her yükümlülüğü **tarihli bir takvime** çevirir ve dosyayı kapatır.

## Adımlar

| # | Adım | Ne çalıştırılır | Çıktı nereye | Geçilemeyen kapı |
|---|---|---|---|---|
| 1 | Kapanış listesinin gerçekleşene karşı sayılması | `/kapanis <dosya>` çıktısı ile fiilen imzalanan set karşılaştırılır: `python3 ~/mafirm/birimler/_araclar/kod/karsilastir.py <kapanis-listesi> <imzalanan-set>` (beceri: `kapanis-listesi`) | `dosyalar/<dosya>/cikti/kapanis-tutanagi.md` | Eksik ya da imzasız kalan her belge **adıyla** yazılır. "Sonra imzalatırız" bir takvim satırıdır, bir varsayım değil |
| 2 | Türk şekil zincirinin tamamlandığının belgeyle doğrulanması | `birimler/tr-sirketler/yontem/pay-devri.md`; A.Ş.: ciro + zilyetliğin devri ya da yazılı temlik, **pay defterine kayıt** (TTK m.499), esas sözleşme arıyorsa yönetim kurulu kararı. Ltd. Şti.: noter onaylı devir sözleşmesi (TTK m.595/1), genel kurul onayı (m.595/2), pay defteri | `dosyalar/<dosya>/cikti/sekil-zinciri.md` | **Şekil, devrin kendisidir.** Zincirdeki bir halka belgeyle gösterilemiyorsa devir tamamlanmamıştır ve dosya kapatılmaz. Beyan yeterli değildir |
| 3 | Ticaret Sicili Müdürlüğü tescili ve Gazete ilanı | `/kapanis <dosya>` listesinin tescil kalemleri (beceri: `kapanis-listesi`); Ltd. Şti. pay devri, yönetim değişikliği, unvan ve esas sözleşme değişiklikleri, temsile yetkililer | `dosyalar/<dosya>/cikti/tescil-takvimi.md` | Her tescil kaleminin **son tarihi** ve sorumlusu yazılır. Tescil ve ilan tamamlanmadan "kapandı" denmez; sicil zamanlaması fiziksel kısıttır |
| 4 | Bütünleşmenin başlangıcı — ancak izinden sonra | `birimler/rekabet/yontem/tr-esikler.md` "Bekletici etki"; Rekabet Kurulu izin kararının **tarihi ve sayısı** dosyaya yazılır (beceri: `rekabet-esigi`) | `dosyalar/<dosya>/cikti/butunlesme-izni.md` | **İzin kararının tarihi belgelenmeden hiçbir bütünleşme adımı başlamaz** (4054 m.11): ortak fiyatlandırma, müşteri listelerinin birleştirilmesi, rekabete duyarlı bilgi paylaşımı, ortak satın alma, personel ve sistem entegrasyonu. İzin şarta bağlıysa, şart karşılanana kadar ilgili adımlar ayrıca beklemededir |
| 5 | Beyan talep sürelerinin sınıf sınıf takvime işlenmesi | Beceri: `kosul-takibi` (süre ve sahip mantığı) + `/spa-incele <dosya>` madde 5 çıktısı; her beyan sınıfı için ayrı bitiş tarihi | `dosyalar/<dosya>/cikti/beyan-sureleri.md` | Tek bir "beyan süresi" satırı yazılmaz: genel beyanlar, vergi beyanları, temel beyanlar ve özel tazminatlar **ayrı** sürelerdir. Süresi yazılmayan bir sınıf, dolduğunda geri gelmez |
| 6 | Emanet serbest bırakma tarihleri ve tutarları | Beceri: `kosul-takibi` + emanet sözleşmesi; her dilim için tarih, tutar, serbest bırakma şartı ve talimatı kimin vereceği | `dosyalar/<dosya>/cikti/emanet-takvimi.md` | Serbest bırakma tarihi ile **beyan talep süresinin bitişi** karşılaştırılmadan takvim onaylanmaz: emanetin beyan süresinden önce boşalması, kalan tek tahsil kaynağını ortadan kaldırır. W&I varsa poliçe süresiyle de karşılaştırılır |
| 7 | Rekabet etmeme ve ayartmama süresinin **başlangıcının** tespiti | Alt ajan `madde-avcisi` (rekabet etmeme, ayartmama, gizlilik maddeleri) + `dosyalar/<dosya>/cikti/kapanis-tutanagi.md` | `dosyalar/<dosya>/cikti/rekabet-etmeme-takvimi.md` | Sürenin **imza tarihinden mi kapanış tarihinden mi** başladığı madde metninden tespit edilir; ikisi arasında izin bekleme süresi kadar fark vardır. Kapsam ve coğrafya aşırı genişse ayrı bir rekabet hukuku sorusu doğar ve işaretlenir |
| 8 | İşçi devri sonrası yükümlülükler (varlık devri yapıldıysa) | `birimler/is-hukuku/yontem/isci-devri.md` (4857 m.6); devirden önce doğmuş borçlarda devreden ile devralanın birlikte sorumluluğu ve devredenin sorumluluk süresi | `dosyalar/<dosya>/cikti/isci-devri-takvimi.md` | Kıdemin devralan yanında sürdüğü ve devirle sıfırlanmadığı takvime yazılır. Pay devri yapıldıysa yük yok olmaz, yalnızca devir hükümleri tetiklenmemiştir — bu da yazılır |
| 9 | Kapanış sonrası fiyat düzeltmesi ve kazanç payı takvimi (varsa) | Beceri: `spa-inceleme` fiyat mekaniği + `python3 ~/mafirm/birimler/_araclar/kod/belge.py <kapanis-hesaplari> --cetvel` ve `python3 ~/mafirm/birimler/_araclar/kod/cetvel.py <cetvel.csv>` | `dosyalar/<dosya>/cikti/fiyat-duzeltmesi.md` | İtiraz süresi ve bağımsız uzmana gitme tarihi yazılmadan takvim kapanmaz; kaçırılan itiraz süresi hesabı kesinleştirir |
| 10 | Kapanış sonrası yaptırım taramasının yenilenmesi | `/tara "<taraf>"` (beceri: `yaptirim-taramasi`) → `python3 ~/mafirm/birimler/_araclar/kod/tarama.py "<ad>" --liste <liste>` | `dosyalar/<dosya>/tarama/<tarih>-kapanis-sonrasi.md` | Hedef artık alıcının grubundadır; müşteri, tedarikçi ve ödeme yolu maruziyeti alıcının kendi rejimine göre yeniden ölçülür. Yeni bir eşleşme bütünleşme adımlarını durdurur |
| 11 | Uyuşmazlık altyapısının canlı tutulması | `birimler/uyusmazlik/yontem/tahkim-ve-tenfiz.md`; tahkim yeri, tebligat adresleri ve satıcının gerçek mal varlığına erişim | `dosyalar/<dosya>/cikti/uyusmazlik-notu.md` | Satıcı bir fonsa ve fon dağılacaksa, talep muhatabının kim olacağı **beyan süreleri dolmadan** tespit edilir. Muhatapsız bir talep hakkı, hak değildir |
| 12 | Dosyanın kapatılması ve çıkar çatışması kaydının beslenmesi | `hafiza/cikar-catismasi.md` içine bu dosyanın tarafları işlenir: müvekkil, hedef, karşı taraf, gerçek lehtarlar, finansman verenler, karşı tarafın avukatları | `hafiza/cikar-catismasi.md` | Bu adım atlanırsa kayıt beslenmez ve bir sonraki dosyanın çıkar çatışması kontrolü **bu dosyayı göremez**. Kayıt, ancak içine yazılanlar kadar iyidir |

## Duran noktalar

Karar, adı `dosyalar/<dosya>/kapsam.md` içinde gerçek adıyla yazılı olan kişiye
gider.

| Duran nokta | Adım | Ne olur | Kim karar verir |
|---|---|---|---|
| **Türk şekil şartının karşılanmaması** | 2, 3 | Devir tamamlanmamıştır. Dosya kapatılmaz, "kapandı" denmez, müvekkile tamamlandı bilgisi verilmez; eksik halka giderilene kadar akış durur | Kapanışı yürüten Türk hukukçusu |
| **Rekabet izni alınmadan (ya da izin tarihinden önce) bütünleşme** | 4 | Bütünleşme adımları durdurulur. İzin kararının tarihi belgelenmeden hiçbir entegrasyon, fiyat paylaşımı ya da rekabete duyarlı bilgi akışı başlamaz (4054 m.11); ihlalin cezası grup cirosu üzerinden hesaplanır (m.16) | Hiç kimse "başlayalım" diyemez. Tarih, Kurul kararının tarihidir; büro içindeki tek karar beklemektir |
| **İznin şarta bağlı verilmiş olması** | 4 | Şartın kapsadığı adımlar, şart karşılandığı belgelenene kadar ayrıca beklemededir | Dosya sorumlusu ortak ve müvekkilin karar vericisi |
| **Giderilemeyen yaptırım eşleşmesi (kapanış sonrası)** | 10 | Yeni bir eşleşme, bütünleşmeyi ve ilgili ticari akışları durdurur; alıcının kendi rejiminde bir uyum olayı doğabilir | Uyum sorumlusu ile dosya sorumlusu ortak |
| **Emanetin beyan süresinden önce boşalacak olması** | 5, 6 | Takvim onaylanmaz; iki tarih hizalanana kadar serbest bırakma talimatı verilmez | Dosya sorumlusu ortak; talimat müvekkilin karar vericisinden çıkar |
| **Talep muhatabının kalmayacak olması** | 11 | Fon dağılacaksa ya da satıcı tüzel kişiliği sona erecekse, beyan süreleri dolmadan muhatap belirlenir | Müvekkilin karar vericisi |
| **Çıkar çatışması kaydının beslenmemesi** | 12 | Dosya kapatılmış sayılmaz. Kayda yazılmayan taraf bir sonraki dosyada görünmez ve o dosyanın kontrolü sessizce yanlış cevap verir (§8) | Dosya sorumlusu ortak |

## Şimdi ne yapılmalı

Kapanış günü bitmeden adım 1, 2 ve 4 yapılır: ne imzalandığı sayılır, şekil
zinciri belgeyle doğrulanır ve izin kararının tarihi dosyaya yazılır. Adım
5, 6 ve 7 aynı hafta içinde **tarihli** takvime çevrilir; bu üçü ertelendiğinde
sessizce dolar. Adım 12 dosya kapatılırken değil, kapatılmasının **şartı**
olarak yapılır. Takvime giren her tarihin bir sahibi vardır ve sahibi adıyla
yazılır; sahibi olmayan tarih hatırlatılmaz.

## Yetkili avukat görüşü gereken konular

Devrin hukuken tamamlandığı anın tespiti ve şekil zincirindeki her halka ·
tescil ve ilan yükümlülüklerinin kapsamı ve süreleri · izin kararının kapsamı
ve bütünleşmenin hangi adımlarının hangi tarihten itibaren serbest olduğu ·
beyan sürelerinin ve sorumluluk sınırlamalarının Türk hukuku karşısındaki
geçerliliği · emanet serbest bırakma şartlarının yorumu · rekabet etmeme
taahhüdünün süresi, coğrafyası ve rekabet hukuku bakımından değerlendirilmesi ·
varlık devrinde işçi alacaklarından birlikte sorumluluğun kapsamı ve süresi ·
ve kapanış sonrası doğan her talebin muhatabı ile tahsil kaynağı.
