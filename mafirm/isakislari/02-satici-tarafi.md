# Satıcı tarafı iş akışı — Türk satıcı, yabancı alıcı

Doğrulama: 2026-08-27.

Kontrol edildi: `birimler/sinir-otesi/yontem/elkitabi-satici.md` ·
`birimler/tr-sirketler/yontem/pay-devri.md` ·
`birimler/rekabet/yontem/tr-esikler.md` · `birimler/is-hukuku/yontem/isci-devri.md` ·
`birimler/uyusmazlik/yontem/tahkim-ve-tenfiz.md` · `birimler/_araclar/katalog.md` ·
`.claude/skills/`, `.claude/agents/`, `.claude/commands/` içindeki gerçek adlar
(2026-08-27) · bulunamayan: Türk ihale uygulamasına dair bağımsız veri ve bu
büronun geçmiş dosyalarından çıkarılmış gerçek tur süreleri — ihale takvimi
dosyaya girerken gerçek rakamla yazılır.

## Ne zaman bu iş akışı

Türk bir satıcı (kurucu ortaklar, aile şirketi ya da fon) hedefini yabancı bir
alıcıya satacaksa bu akış çalıştırılır. Alıcı akışının aynı yapısıdır, ters
yönde. Satıcının hedefi tek cümledir: **temiz ayrılmak** — bedeli almak ve
kapanıştan sonra geri dönmeyen bir sorumluluk bırakmamak. Bu akışın ayırt edici
kuralı zamanlamadır: satıcı, alıcının bulacağı her şeyi **önce kendisi bulur**,
çünkü bir kusur veri odası açılmadan önce ucuz, müzakere masasında pahalı,
kapanıştan sonra ise bir talep konusudur. İkinci ayırt edici kuralı, açıklama
mektubunun beyanlarla **aynı anda** yürütülmesidir; sonraya bırakıldığında imza
baskısı altında eksik yapılır ve satıcının asıl koruması orada kaybedilir.

## Adımlar

| # | Adım | Ne çalıştırılır | Çıktı nereye | Geçilemeyen kapı |
|---|---|---|---|---|
| 1 | Aşama 0 · Dosyanın açılması ve çıkar çatışması kontrolü | `/dosya-ac <dosya adı>` (beceri: `dosya-ac`); `hafiza/cikar-catismasi.md` alıcı adayları ve onların danışmanları için de okunur | `dosyalar/<dosya>/kapsam.md` + `dosyalar/<dosya>/taraflar.md` | Kayıtta eşleşme varsa **DUR**. Satıcı tarafında eşleşme yalnızca alıcıda değil, süreçteki her aday alıcıda aranır (§8) |
| 2 | Aşama 0 · Satıcının **kendi tarafını** taraması | `/tara "<taraf>"` (beceri: `yaptirim-taramasi`) → `python3 ~/mafirm/birimler/_araclar/kod/tarama.py "<ad>" --liste <liste>`; satıcı ortakları, gerçek lehtarları, yönetimi, hedefin müşteri ve tedarikçi yoğunlaşması, ürün sınıflandırması | `dosyalar/<dosya>/tarama/<tarih>-satici-tarafi.md` | Alıcının bulacağı bir eşleşmeyi satıcı önce bulmalıdır. Giderilemeyen bir eşleşme varsa süreç başlatılmaz; sürecin ortasında ortaya çıkan eşleşme fiyatı değil işlemi öldürür |
| 3 | Aşama 0 · Satış nesnesinin tanımı | `birimler/sinir-otesi/yontem/elkitabi-satici.md` Aşama 0 + `birimler/tr-sirketler/yontem/pay-devri.md` (şirket türü, senetlerin bastırılıp bastırılmadığı) | `dosyalar/<dosya>/cikti/satis-nesnesi.md` | Hangi tüzel kişi, hangi varlıklar, hangi iştirakler **dahil** ve hangileri **hariç** — bu, ilk teklif alınmadan netleşir. Tanımsız satış nesnesi, müzakerenin ortasında fiyat kırma sebebidir |
| 4 | Aşama 0 · Yapı: pay mı varlık mı (satıcı yönü) | `birimler/sinir-otesi/yontem/elkitabi-satici.md` Aşama 0 + `birimler/is-hukuku/yontem/isci-devri.md` | `dosyalar/<dosya>/cikti/yapi-notu.md` | Satıcı için vergi sonucu genellikle belirleyicidir ve alıcının tercihiyle **çatışır**. Bu çatışma müzakereden önce yazılı olarak tespit edilir, masada keşfedilmez |
| 5 | Aşama 1 · Veri odası hazırlığı — eksikleri önce satıcı bulur | Beceri: `inceleme-bayraklari` (satıcı yönü) + `python3 ~/mafirm/birimler/_araclar/kod/token-butce.py <veri-odasi-klasoru>`; Türkiye'ye özgü kontrol: pay senetleri bastırılmış mı, pay defteri güncel mi, genel kurul ve yönetim kurulu kararları tescil edilmiş mi, sicil kayıtları güncel mi, özlük dosyaları tam mı, tapu temiz mi | `dosyalar/<dosya>/cikti/veri-odasi-eksikler.md` | Bulunamayan pay defteri ya da imzalanmamış bir kira sözleşmesi **şimdi** çözülür, müzakerede değil. Kişisel veri için hukuki dayanak ve maskeleme kararı verilmeden özlük dosyası ve müşteri verisi veri odasına konmaz |
| 6 | Aşama 2 · Satıcı incelemesi — her bulgu için üç seçenekten biri | `/inceleme-ayir <klasör>` — alt ajan `inceleme-okuyucu` paralel; sonra her bulguya karar: **gider** (kapanıştan önce düzelt) · **açıkla** (açıklama mektubuna yaz) · **taşı** (fiyata ya da tazminata gireceğini kabul et) | `dosyalar/<dosya>/cikti/satici-incelemesi.md` | Hiçbir bulgu kararsız bırakılmaz. Giderilebilecek bir kusuru açıklamak para bırakmaktır; giderilemeyecek bir kusuru açıklamamak kapanış sonrası talep davetidir. Veri odası, bu tablo kapanmadan açılmaz |
| 7 | Aşama 2 · Alıcı adaylarının izin riskinin erken ölçülmesi | Beceri: `rekabet-esigi` → `python3 ~/mafirm/birimler/rekabet/kod/esik.py --self-test`, sonra **her aday alıcı için ayrı** gerçek ciro hesabı | `dosyalar/<dosya>/cikti/aday-izin-riski.md` | Rekabet izni alamayacak bir alıcı, en yüksek teklifi verse bile en kötü alıcıdır. Bu hesap yapılmadan aday listesi kısaltılmaz; eşik hafızadan cevaplanamaz ve kullanılan rakamların doğrulama tarihi yazılır |
| 8 | Aşama 3 · İhale takvimi ve süreç mektubu | `birimler/sinir-otesi/yontem/elkitabi-satici.md` Aşama 3; teklif turları, bilgi paketi ve tur kapanış tarihleri | `dosyalar/<dosya>/cikti/ihale-takvimi.md` | Takvim, adım 5 ve 6 kapanmadan yayımlanmaz. Eksik bir veri odasıyla açılan süreç, ilk turdan sonra fiyat kırma zemini üretir |
| 9 | Aşama 3 · Münhasırlık kararı | Alt ajan `madde-avcisi` (münhasırlık, kırılma bedeli, ayartmama maddeleri) + alt ajan `emsal-bulucu` (önceki biçim) | `dosyalar/<dosya>/cikti/munhasirlik.md` | Münhasırlık satıcının **en pahalı tavizidir**: verildiği anda rekabet biter ve fiyat baskısı yön değiştirir. Karşılığında ne alındığı **yazılı** olmadan münhasırlık verilmez |
| 10 | Aşama 4 · Açıklama mektubu çalışması — beyanlarla **aynı anda** | Beceri: `aciklama-mektubu`; her beyan tek tek okunur, karşısına gerçek durum yazılır. Beyan taslağı ile açıklama tablosu tek takvimde yürütülür | `dosyalar/<dosya>/cikti/aciklama-mektubu-calismasi.md` | Açıklama çalışması beyanların sonrasına **bırakılamaz**. Beyan turu kapanmadan açıklama satırı boş kalan hiçbir beyan onaylanmaz |
| 11 | Aşama 4 · Veri odasının genel açıklama sayılıp sayılmayacağı | Beceri: `aciklama-mektubu` (satıcının en büyük tek kazanımı; alıcı direnir) + beceri: `spa-inceleme` açıklama maddesi | `dosyalar/<dosya>/cikti/aciklama-mektubu-calismasi.md` (aynı dosya) | Konu ağır müzakere edilir ve sonucu tek cümleyle yazılır. Belirsiz bırakılan genel açıklama hükmü, kapanış sonrası uyuşmazlığın kendisidir |
| 12 | Aşama 5 · Sorumluluğun sınırlandırılması | `/spa-incele <dosya>` (beceri: `spa-inceleme`) satıcı açısından — tavan, alt sınır, asgari tutar, beyan sınıfı başına süre | `dosyalar/<dosya>/cikti/spa-inceleme-satici.md` | Her beyan sınıfı için ayrı süre yazılmadan sorumluluk paketi kapanmaz. Sınırsız süre bırakılan bir sınıf, temiz ayrılmayı ortadan kaldırır |
| 13 | Aşama 5 · Tahsil kaynağının sınırlandırılması | Beceri: `spa-inceleme` (emanet / W&I / satıcı taahhüdü) + `birimler/uyusmazlik/yontem/tahkim-ve-tenfiz.md` | `dosyalar/<dosya>/cikti/tahsil-kaynagi.md` | Satıcı bir fonsa, **fonun ömrü ile beyan sürelerinin uyumu** kontrol edilir; fon dağılmışsa talep muhatapsız kalır ama dağıtılmış bedeli geri isteyen bir hüküm ortakları yakalayabilir. Bu kontrol yapılmadan yapı onaylanmaz |
| 14 | Müzakere turlarının karşılaştırılması | `python3 ~/mafirm/birimler/_araclar/kod/karsilastir.py <eski> <yeni>` (beceri: `madde-karsilastirma`) | `dosyalar/<dosya>/cikti/tur-<n>-fark.md` | Alıcıdan gelen değişiklik seti göz ile değil kod ile karşılaştırılır. Karşılaştırılmamış tur imzaya götürülmez |
| 15 | İmza kararı · karar notu | `/kurul-notu <dosya>` (beceri: `kurul-notu`) — satıcı ortaklarına ya da fon yatırım komitesine | `dosyalar/<dosya>/cikti/kurul-notu-<tarih>.md` | Adı belli bir insan onaylamadan imzaya gidilmez (§9) |
| 16 | İmzadan kapanışa · koşulların satıcı tarafındaki adımları | `/kosul-listesi <dosya>` (beceri: `kosul-takibi`) — satıcının kontrolündeki koşullar ayrı işaretlenir | `dosyalar/<dosya>/cikti/kosullar.md` | Rekabet izni koşulundan feragat edilemez (4054 m.10, Tebliğ m.10). Satıcı bu dönemde alıcıyla bütünleşme adımı atmaz, fiyat paylaşmaz, ortak müşteri görüşmesi yapmaz — yasak iki taraflıdır |
| 17 | Kapanış — Türk şeklinin satıcı tarafındaki adımları | `/kapanis <dosya>` (beceri: `kapanis-listesi`) + `birimler/tr-sirketler/yontem/pay-devri.md`; noter randevusu, genel kurul, pay defteri kaydı, tescil ve ilan | `dosyalar/<dosya>/cikti/kapanis-listesi.md` | **Şekil, devrin kendisidir.** Ltd. Şti.'de noter onaylı devir sözleşmesi ve genel kurul onayı; A.Ş.'de ciro + zilyetliğin devri ya da yazılı temlik, her hâlde pay defterine kayıt. Noter ve sicil müsaitliği fiziksel kısıttır; aynı gün kapanış varsayılmaz |
| 18 | Temiz ayrılma · kapanış sonrası satıcı takvimi | `04-kapanis-sonrasi.md` iş akışına devredilir; ayrıca rekabet etmeme ve ayartmama taahhüdünün süresi, coğrafyası ve **başlangıç tarihi** yazılır | `dosyalar/<dosya>/cikti/kapanis-sonrasi-takvim.md` | Aşırı geniş bir rekabet etmeme taahhüdü hem uygulanamaz hem de ayrı bir rekabet hukuku sorusu doğurur; süre ve coğrafya yazılmadan taahhüt kabul edilmez |

## Duran noktalar

Karar, adı `dosyalar/<dosya>/kapsam.md` içinde **gerçek adıyla** yazılı olan
kişiye gider; ad yazılı değilse akış zaten orada durur.

| Duran nokta | Adım | Ne olur | Kim karar verir |
|---|---|---|---|
| **Çıkar çatışması eşleşmesi** | 1 | Dosya açılmaz; süreçteki bir aday alıcıyla eşleşme çıkarsa o aday süreçten çıkarılır ya da dosya bırakılır | Dosya sorumlusu ortak; karar gerekçesiyle `hafiza/cikar-catismasi.md` içine işlenir |
| **Giderilemeyen yaptırım eşleşmesi (satıcının kendi tarafında)** | 2 | Süreç başlatılmaz. Satıcı tarafında bir eşleşme, alıcı adaylarının çoğu için diskalifiye edicidir | Uyum sorumlusu ile dosya sorumlusu ortak birlikte |
| **Satış nesnesinde giderilemeyen mülkiyet kusuru** | 3, 5, 6 | Satılamayacak bir şey satışa çıkarılmaz; kusur giderilene kadar akış durur | Dosya sorumlusu ortak ve satıcı ortakların karar vericisi |
| **Kararsız bırakılan inceleme bulgusu** | 6 | Gider / açıkla / taşı üçlüsünden biri seçilmeden veri odası açılmaz | Dosya sorumlusu ortak |
| **Alıcının izin alamayacağının anlaşılması** | 7 | O aday, teklifi ne olursa olsun listeden çıkarılır ya da işlem yeniden yapılandırılır | Satıcı ortakların karar vericisi; hesap `esik.py` çıktısıyla belgelenir |
| **Münhasırlığın karşılıksız istenmesi** | 9 | Verilmez. Karşılığında ne alındığı yazılı değilse akış durur | Satıcı ortakların karar vericisi |
| **Rekabet izni alınmadan kapanış** | 16 | Kapanış yapılmaz. Bu koşuldan feragat edilemez (4054 m.10, Tebliğ m.10); erken kapanan işlem hukuken geçerlilik kazanmaz ve ceza grup cirosu üzerinden hesaplanır (m.16) | Hiç kimse "evet" diyemez. Karar Rekabet Kurulu'nundur |
| **Satıcının kabul edemeyeceği sorumluluk yapısı** | 12, 13 | Sınırsız süre, tavansız sorumluluk ya da fon ömrünü aşan beyan süresi kabul edilmez | Satıcı ortakların karar vericisi |
| **Türk şekil şartının karşılanmaması** | 17 | Kapanış yapılmaz. Noter onayı olmayan Ltd. Şti. devri geçersizdir; pay defterine kaydedilmemiş A.Ş. devri şirkete karşı hüküm ifade etmez | Kapanışı yürüten Türk hukukçusu |
| **Kapanış sonrası muhatap kalmaması** | 13, 18 | Fon dağılacaksa ya da satıcı tüzel kişiliği sona erecekse, taleplerin muhatabı kapanıştan önce belirlenir | Satıcı ortakların karar vericisi |

## Şimdi ne yapılmalı

Veri odası açılmadan önce adım 5 ve 6 tamamlanır. Sonra açılan bir veri odası,
müzakere gücünü satıcıda tutar; eksik açılan bir veri odası, gücü ilk turda
alıcıya verir. Adım 10 (açıklama mektubu) takvime beyanlarla **aynı hafta**
girilir, sonraya bırakılmaz. Adım 7, aday listesi kısaltılmadan önce
çalıştırılır. Atlanan her adım "yapılmadı" olarak işaretlenir ve gerekçesi
`cikti/` altına yazılır.

## Yetkili avukat görüşü gereken konular

Açıklama mektubunun **her satırı** · veri odasının genel açıklama sayılmasına
ilişkin hükmün Türk hukuku karşısındaki etkisi · sorumluluk sınırlamalarının ve
süre kısaltmalarının geçerliliği · rekabet etmeme taahhüdünün süresi, coğrafyası
ve rekabet hukuku bakımından değerlendirilmesi · kişisel verinin veri odasına
konmasının hukuki dayanağı · satış nesnesindeki her mülkiyet sorusu · fon
ömrü ile beyan sürelerinin uyumu ve tahsil kaynağının yeterliliği · satıcının
kapanış sonrası kalan her yükümlülüğü · ve her Türk şekil şartı.
