# Alıcı tarafı iş akışı — yabancı alıcı, Türk hedef

Doğrulama: 2026-08-27.

Kontrol edildi: `birimler/sinir-otesi/yontem/elkitabi-alici.md` ·
`birimler/rekabet/yontem/tr-esikler.md` · `birimler/tr-sirketler/yontem/pay-devri.md` ·
`birimler/tr-sermaye-piyasasi/yontem/pay-alim-teklifi.md` ·
`birimler/is-hukuku/yontem/isci-devri.md` · `birimler/_araclar/katalog.md` ·
`.claude/skills/`, `.claude/agents/`, `.claude/commands/` içindeki gerçek adlar
(2026-08-27) · bulunamayan: noter randevusu ve Ticaret Sicili Müdürlüğü tescil
sürelerine dair güncel uygulama verisi ve Rekabet Kurulu'nun bugünkü fiilî
inceleme süreleri — aşağıdaki "saat" değerlendirmeleri dosyaya girerken
gerçek rakamla değiştirilir.

## Ne zaman bu iş akışı

Yabancı bir alıcı Türkiye'de yerleşik bir hedefin paylarını ya da varlıklarını
devralacaksa bu akış baştan sona çalıştırılır. Sıra bir tavsiye değil bağımlılık
zinciridir: şirket türü bilinmeden devir mekaniği yazılamaz, hedefin halka açık
olup olmadığı bilinmeden yapı seçilemez, yapı seçilmeden ciro rakamları doğru
ayrıştırılamaz, ciro ayrıştırılmadan rekabet eşiği hesaplanamaz ve eşik
hesaplanmadan kapanışın ne zaman mümkün olduğu bilinemez. Akış, imza kararını
değil imzaya kadarki her kapıyı üretir; imza kararı adı belli bir insanın
kararıdır. Sadece "izin gerekiyor mu" sorusu varsa bu dosya değil
`03-hizli-esik.md` çalıştırılır.

## Adımlar

| # | Adım | Ne çalıştırılır | Çıktı nereye | Geçilemeyen kapı |
|---|---|---|---|---|
| 1 | Aşama 0 · Dosyanın açılması ve çıkar çatışması kontrolü | `/dosya-ac <dosya adı>` (beceri: `dosya-ac`); komutun birinci adımı `hafiza/cikar-catismasi.md` dosyasını karşı taraflar için okur | `dosyalar/<dosya>/kapsam.md` + `dosyalar/<dosya>/taraflar.md` | Kayıtta eşleşme varsa **DUR**: klasör açılmaz, temas kurulmaz. Eşleşme uyarı değil durma sebebidir (§8) |
| 2 | Aşama 0 · Gizlilik sözleşmesinden **önce** ilk yaptırım taraması | `/tara "<taraf>"` (beceri: `yaptirim-taramasi`) → `python3 ~/mafirm/birimler/_araclar/kod/tarama.py "<ad>" --liste <liste>`; hedef, ana ortaklar, gerçek lehtarlar, yöneticiler | `dosyalar/<dosya>/tarama/<tarih>-<taraf>.md` | Kimlik doğrulamasından sonra hâlâ duran bir eşleşme varsa gizlilik sözleşmesi **imzalanmaz**. Tarama NDA'dan sonraya bırakılamaz |
| 3 | Aşama 0 · Şirket türü tespiti: A.Ş. mi Ltd. Şti. mi | `birimler/tr-sirketler/yontem/pay-devri.md` + esas sözleşme ve ticaret sicili kaydı üzerinden `python3 ~/mafirm/birimler/_araclar/kod/belge.py <esas-sozlesme> --yapi` | `dosyalar/<dosya>/cikti/sirket-turu.md` | Tür **belgeden** doğrulanmadan devir mekaniği yazılmaz. Beyan yeterli değildir; tür yanlışsa kapanış mekaniğinin tamamı yanlıştır |
| 4 | Aşama 0 · Halka açık mı — SPK saati başlıyor mu | `birimler/tr-sermaye-piyasasi/yontem/pay-alim-teklifi.md`; imtiyazlı pay sınıfları için esas sözleşme yeniden okunur | `dosyalar/<dosya>/cikti/spk-saati.md` | Hedef halka açıksa zorunlu pay alım teklifi ve kamuyu aydınlatma yükümlülüğü **değerlendirilmeden** yapı kararına geçilmez. Yönetim kurulu imtiyazı taşıyan azınlık payı bile yükümlülük doğurabilir |
| 5 | Aşama 1 · Yapı: pay mı varlık mı | `birimler/sinir-otesi/yontem/elkitabi-alici.md` Aşama 1 + `birimler/is-hukuku/yontem/isci-devri.md` (varlık devrinde 4857 m.6 kıdem yükü kendiliğinden geçer) | `dosyalar/<dosya>/cikti/yapi-notu.md` | Vergi ve hukuk sonucu **aynı notta** yoksa karar verilmez. Kıdem yükü fiyatlanmadan varlık devri seçilmez |
| 6 | Aşama 1 · Rekabet eşiği — hafızadan asla | Beceri: `rekabet-esigi` → `python3 ~/mafirm/birimler/rekabet/kod/esik.py --self-test`, sonra gerçek ciro rakamlarıyla `bildirilmeli(...)`. Teknoloji ayağı düşünülüyorsa önce üç olgu (yerleşiklik, işlem türü, alan cirosu) | `dosyalar/<dosya>/cikti/esik-<tarih>.md` | `--self-test` HATA dönerse hesap yapılmaz. Eşik hafızadan cevaplanamaz; kullanılan rakamların **doğrulama tarihi** yazılmadan sonuç kullanılmaz. "Bildirim gerekmez" sonucu, hangi hükmün arandığını göstermeden yazılmaz (§2) |
| 7 | Aşama 1 · Uygulanacak hukuk, tahkim yeri ve başvuru paketi | `birimler/uyusmazlik/yontem/tahkim-ve-tenfiz.md`; W&I düşünülüyorsa sigortacı **şimdi** devreye alınır | `dosyalar/<dosya>/cikti/yapi-notu.md` (aynı not) | Kaleme almaya başlamadan önce kararlaştırılır. Kararsız bırakılan tahkim yeri, sonradan tenfiz sorusunu doğurur |
| 8 | Aşama 2 · İnceleme kapsamının fiyata göre yazılması ve veri odasının ölçülmesi | Beceri: `inceleme-bayraklari` + `python3 ~/mafirm/birimler/_araclar/kod/token-butce.py <veri-odasi-klasoru>` | `dosyalar/<dosya>/cikti/inceleme-kapsami.md` | Kapsam genel bir kontrol listesinden kopyalanmaz; rakamı ya da yapıyı değiştirmeyecek kalemler kapsam **dışı** olarak yazılır. Kapsam dışı bırakılan her kalem yazılır |
| 9 | Aşama 2 · Veri odasının paralel okunması | `/inceleme-ayir <klasör>` — alt ajan `inceleme-okuyucu` konu başlıklarına paralel dağıtılır; Türkiye'ye özgü kalemler ayrı bölüm: esas sözleşme ve imtiyazlı sınıflar, pay defteri, sicil gazetesi, özlük dosyaları ve kıdem, tapu ve yabancı edinme kısıtı, ilişkili taraf sözleşmeleri | `dosyalar/<dosya>/cikti/inceleme-bulgulari.md` | Kaç belgeye bakıldığı ve kaçının **okunamadığı** yazılmadan tablo kapanmaz. Alt ajanlar belge metni değil referans döndürür (§6) |
| 10 | Aşama 2 · Bulguların sınıflandırılması ve madde taraması | Beceri: `inceleme-bayraklari` (FİYAT · TAZMİNAT · KOŞUL · ÇEKİLME) + alt ajan `madde-avcisi` (kontrol değişikliği, devir yasağı, münhasırlık, rekabet etmeme) | `dosyalar/<dosya>/cikti/inceleme-bulgulari.md` (aynı tablo) | ÇEKİLME sınıfına giren bir bulgu tespit edildiyse akış durur ve karar insana gider. Karşı tarafın vermeyeceği bir kontrol değişikliği onayı, kapanışı imkânsız kılabilir |
| 11 | Aşama 3 · SPA ve devir belgelerinin incelenmesi | `/spa-incele <dosya>` (beceri: `spa-inceleme`); önce `python3 ~/mafirm/birimler/_araclar/kod/belge.py <spa> --yapi` | `dosyalar/<dosya>/cikti/spa-inceleme-<tur>.md` | Ara dönem taahhütleri **değer koruma** olarak yazılır, kontrol olarak değil. Fiilî kontrol veren her taahhüt 4054 sayılı Kanun m.10 ve 2010/4 sayılı Tebliğ m.10 bakımından izinsiz kapanış riski doğurur ve işaretlenmeden geçilmez |
| 12 | Aşama 3 · Gelen açıklama mektubunun beyan paketini ne kadar boşalttığının ölçülmesi | Beceri: `aciklama-mektubu` (alıcı yönü) | `dosyalar/<dosya>/cikti/aciklama-degerlendirmesi.md` | Veri odasının tamamının "genel açıklama" sayılıp sayılmadığı karara bağlanmadan beyan paketi kapanmaz; bunun alıcıya maliyeti rakamla yazılır |
| 13 | Aşama 3 · Kapanış öncesi koşul tablosu | `/kosul-listesi <dosya>` (beceri: `kosul-takibi`); ısırma sırasına göre, en uzun saat önce | `dosyalar/<dosya>/cikti/kosullar.md` | Rekabet izni koşulundan **feragat edilemez**. Nihai tarih yalnızca birinci aşamayı değil ikinci aşamayı da karşılamıyorsa tablo onaylanmaz |
| 14 | Aşama 3 · Tur değişikliklerinin karşılaştırılması | `python3 ~/mafirm/birimler/_araclar/kod/karsilastir.py <eski> <yeni>` (beceri: `madde-karsilastirma`) + alt ajan `emsal-bulucu` | `dosyalar/<dosya>/cikti/tur-<n>-fark.md` | Değişiklik seti göz ile değil kod ile karşılaştırılır. Karşılaştırılmamış bir tur imzaya götürülmez |
| 15 | İmza kararı · karar notu | `/kurul-notu <dosya>` (beceri: `kurul-notu`) — en fazla iki sayfa, kötü haber ilk sayfada | `dosyalar/<dosya>/cikti/kurul-notu-<tarih>.md` | Adı belli bir insan onaylamadan imzaya gidilmez (§9). Not, karşı görüşü kendi en güçlü hâliyle taşımıyorsa kurula girmez |
| 16 | Aşama 4 · İmzadan kapanışa · bildirim ve bekleme | Beceri: `rekabet-esigi` (bildirim paketi ve takvim) + `/kosul-listesi` çıktısının haftalık takibi | `dosyalar/<dosya>/cikti/kosullar.md` (güncellenir) | **4054 sayılı Kanun m.10 ve 2010/4 sayılı Tebliğ m.10: izin gelmeden kapanış yok.** Bu dönemde bütünleşme başlatılmaz, fiyat paylaşılmaz, hedefin müşterilerine birlikte gidilmez, ortak fiyatlandırma yapılmaz. İhlalin cezası (m.16) işlem değerine değil grup cirosuna bağlıdır |
| 17 | Aşama 4 · Yaptırım taramasının imzadan önce yenilenmesi | `/tara "<taraf>"` → `python3 ~/mafirm/birimler/_araclar/kod/tarama.py "<ad>" --liste <liste>` | `dosyalar/<dosya>/tarama/<tarih>-imza-oncesi.md` | Aşama 0'daki tarama tarihi geçmişse tekrar edilir. Yeni bir eşleşme kapanışı durdurur |
| 18 | Aşama 5 · Kapanış — Türk şeklinde | `/kapanis <dosya>` (beceri: `kapanis-listesi`) + `birimler/tr-sirketler/yontem/pay-devri.md` | `dosyalar/<dosya>/cikti/kapanis-listesi.md` | **Şekil, devrin kendisidir.** Ltd. Şti.: noter onaylı devir sözleşmesi yoksa devir geçersiz; ardından genel kurul onayı. A.Ş.: senet bastırılmışsa ciro + zilyetliğin devri, bastırılmamışsa yazılı temlik; her hâlde pay defterine kayıt. Esas sözleşme yönetim kurulu onayı arıyorsa o karar |
| 19 | Aşama 5 · Kapanış sonrası takvimin kurulması | `04-kapanis-sonrasi.md` iş akışına devredilir | `dosyalar/<dosya>/cikti/kapanis-sonrasi-takvim.md` | — |

## Duran noktalar

Aşağıdaki her satırda makine devam etmez. Karar, adı `dosyalar/<dosya>/kapsam.md`
içinde **gerçek adıyla** yazılı olan kişiye gider; ad yazılı değilse akış zaten
orada durur, çünkü kararı verecek kişi belli değildir.

| Duran nokta | Adım | Ne olur | Kim karar verir |
|---|---|---|---|
| **Çıkar çatışması eşleşmesi** | 1 | Klasör açılmaz, gizlilik sözleşmesi imzalanmaz, karşı tarafla temas kurulmaz. Eşleşme bir uyarı değildir (§8) | Dosya sorumlusu ortak; bilgi duvarı ya da feragat kararı onundur ve gerekçesiyle `hafiza/cikar-catismasi.md` içine işlenir |
| **Giderilemeyen yaptırım eşleşmesi** | 2, 17 | Kimlik doğrulaması, maruziyetin niteliği ve alıcının kendi rejiminin sonucu incelendikten sonra eşleşme hâlâ duruyorsa iş akışı durur | Uyum sorumlusu ile dosya sorumlusu ortak birlikte; karar `dosyalar/<dosya>/tarama/` altına tarihiyle yazılır |
| **ÇEKİLME sınıfına giren inceleme bulgusu** | 10 | Fiyatla ya da tazminatla kapanmayan bir bulgu müzakereye götürülmez, karara götürülür | Dosya sorumlusu ortak ve müvekkilin karar vericisi |
| **Rekabet izni alınmadan kapanış** | 16 | Kapanış yapılmaz. Bu koşuldan feragat edilemez ve ticari baskıyla geçilemez (4054 m.10, Tebliğ m.10); erken kapanan işlem hukuken geçerlilik kazanmaz | Hiç kimse "evet" diyemez. Karar Rekabet Kurulu'nundur; büro içindeki tek karar, iznin beklenmesidir |
| **İzin, alıcının katlanamayacağı bir taahhütle verilirse** | 16 | Nihai tarih ve fiyat yeniden açılır | Müvekkilin karar vericisi; kurul notu (`/kurul-notu`) yenilenir |
| **Türk şekil şartının karşılanmaması** | 18 | Kapanış yapılmaz. Noter onayı olmayan bir Ltd. Şti. devri geçersizdir; pay defterine kaydedilmemiş bir A.Ş. devri şirkete karşı hüküm ifade etmez | Kapanışı yürüten Türk hukukçusu; eksik giderilene kadar kapanış ertelenir |
| **Paylarda mülkiyet ya da şekil kusuru** | 9, 18 | Devredilecek şeyin devredilebilir olduğu doğrulanana kadar akış durur | Dosya sorumlusu ortak |
| **Alınamayan kontrol değişikliği onayı** | 10, 13 | Koşul karşılanamıyorsa kapanış mimarisi yeniden kurulur | Müvekkilin karar vericisi |

## Şimdi ne yapılmalı

Adım 1'den başlanır ve satırlar sırayla kapatılır. Aşama 0 (adım 1-4) hiçbir
koşulda atlanmaz: en ucuz aşama odur ve atlandığında en pahalı keşfi üretir.
Adım 6 çalıştırılmadan hiçbir takvim müvekkile verilmez; bildirime tabi olmak
yapısal bir olgudur, geç fark edilecek bir şey değil. Bir adım atlanacaksa
"yapılmadı" olarak işaretlenir ve gerekçesi `cikti/` altına yazılır — sessizce
geçilen kapı hiç olmamış kapıdır.

## Yetkili avukat görüşü gereken konular

Şirket türünün ve esas sözleşmedeki devir sınırlamalarının somut tespiti ·
senetlerin bastırılıp bastırılmadığı ve buna bağlı devir mekaniği · hedefin
halka açık olması hâlinde zorunlu pay alım teklifi yükümlülüğünün doğup
doğmadığı · yapı kararının vergi sonucu · adım 6'daki eşik hesabının birincil
mevzuat metninden teyidi ve özellikle bildirime tabi **olmadığı** sonucuna
varılan her işlem (olumsuz iddia kuralı, §2) · ara dönem taahhütlerinin 4054
m.10 karşısındaki durumu · sorumluluk sınırlamalarının Türk hukuku karşısındaki
geçerliliği · her Türk şekil şartı · ve kapanışın hukuken tamamlandığı anın
tespiti.
