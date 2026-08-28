#!/usr/bin/env python3
"""Türkiye'de birleşme denetimi bildirim eşiği testi.

Bu neden kod, neden hafıza değil. Testin iki ayağı var, her ayakta iki koşul
var ve teknoloji istisnası yalnızca bir ayaktaki bir rakamı değiştiriyor.
Bunu düzyazıda akıl yürüterek çözmek, hatanın yapıldığı yerdir; hata da iki
yönde de pahalıdır: gereksiz bildirim haftalara mal olur, gereken bildirimin
yapılmaması kapanışı geçersiz kılar.

Rakamlar: 2026/2 sayılı Tebliğ (RG 11.02.2026, sayı 33165), doğrulama
2026-08-27.

KÖR SINAMA SONRASI SÜRÜM. Kitaba sadık sürüm yamalar/kitaba-sadik/esik.py.
Kapatılan kusurlar, kör sınama kimlikleriyle:

  A-07  para birimi modeli yoktu: TL cinsinden bir eşiğe avro rakamı
        verildiğinde SESSİZCE "tabi değil" dönüyordu (§19 pilotunun ta kendisi)
  A-09  aynı işlem iki bağlantısız biçimde giriliyordu; hedefin cirosunu
        A ayağına yazmayı unutmak bildirimi sessizce yok ediyordu
  A-10  cevap iki değerliydi; beceri üç değerli istiyor (belirlenemiyor)
  A-11  bilinmeyen ciro None verilince TypeError
  A-12  negatif ciro sessizce kabul ediliyordu
  A-13  hedef kendi dünya cirosuyla B ayağını karşılayabiliyordu
  A-14  gerçek rakamlarla komut satırından hesap YAPILAMIYORDU — oysa §8,
        §9 ve §15.1 "gerçek ciro rakamlarıyla çalıştırılır" diyor
  A-15  devralma / birleşme ayrımı modellenmiyordu
"""
import argparse
import sys

# Tutarların hepsi TL. Adlandırıldı ki bir fark hangisinin oynadığını göstersin.
BIRLESIK_TR = 3_000_000_000       # A eşiği: Türkiye ciroları toplamı
IKI_TARAF_TR = 1_000_000_000      # A eşiği: en az iki tarafın her biri
HEDEF_TR = 1_000_000_000          # B eşiği: devre konu varlık / bir taraf
HEDEF_TR_TEKNOLOJI = 250_000_000  # B eşiği: teknoloji teşebbüsü hedef
DIGER_DUNYA = 9_000_000_000       # B eşiği: diğer taraflardan birinin dünya
DOGRULAMA = "2026-08-27"

BILINMIYOR = None
EVET, HAYIR, BELIRSIZ = "evet", "hayır", "belirlenemiyor"


class CiroHatasi(ValueError):
    """Bir ciro rakamı kullanılamaz durumda."""


# --- [A-07] Para birimi ----------------------------------------------------
def tl(tutar, birim="TL", kur=None, kaynak=None):
    """Bir tutarı TL'ye çevirir ve kaynağını zorunlu kılar.

    Eşiklerin hepsi TL cinsindendir. Yabancı para birimindeki bir ciroyu
    çevirmeden karşılaştırmak, §19'daki pilot işlemde cevabı TERSİNE çevirir:
    2,4 milyar avroluk bir alıcı, 2.400.000.000 sayısı olarak 9 milyar TL
    eşiğinin ALTINDA kalır ve işlem "bildirime tabi değil" görünür.

    Bu yüzden çeviri sessizce yapılmaz: kur ve kaynağı istenir.
    """
    if tutar is BILINMIYOR:
        return BILINMIYOR
    _sayi_dogrula(tutar, "tutar")
    birim = (birim or "TL").upper()
    if birim in ("TL", "TRY", "₺"):
        return float(tutar)
    if kur is None:
        raise CiroHatasi(
            "%s cinsinden tutar TL'ye çevrilmeden kullanılamaz: kur verilmedi. "
            "Eşikler TL cinsindendir (2026/2 sayılı Tebliğ)." % birim)
    if kaynak is None:
        raise CiroHatasi(
            "kur verildi ama KAYNAĞI verilmedi. Kanıt kuralı (CLAUDE.md §1): "
            "her rakam dayanağını yanında taşır.")
    _sayi_dogrula(kur, "kur")
    return float(tutar) * float(kur)


def _sayi_dogrula(d, ad):
    """[A-11, A-12] Bilinmeyen sıfır değildir; negatif ciro yoktur."""
    if isinstance(d, bool) or not isinstance(d, (int, float)):
        raise CiroHatasi("%s sayı olmalı, %r verildi. Bilinmiyorsa None kullanın "
                         "— 0 'bilinmiyor' demek DEĞİLDİR." % (ad, d))
    if d < 0:
        raise CiroHatasi("%s negatif olamaz: %r" % (ad, d))


class Taraf:
    """İşlemin bir tarafı. Rakamlar TL, bilinmeyen None.

    [A-09] İşlem tek bir taraf listesiyle modellenir; A ve B ayakları AYNI
    veriden türetilir. Kitabın sürümünde aynı işlem iki ayrı biçimde
    giriliyordu ve tutarlılığı hiçbir şey kontrol etmiyordu.
    """

    def __init__(self, ad, tr_ciro=BILINMIYOR, dunya_ciro=BILINMIYOR,
                 rol="taraf", teknoloji=False, yerlesik=BILINMIYOR):
        if rol not in ("devralan", "hedef", "devreden", "birlesen", "taraf"):
            raise CiroHatasi("bilinmeyen rol: %r" % rol)
        for d, ad_ in ((tr_ciro, "tr_ciro"), (dunya_ciro, "dunya_ciro")):
            if d is not BILINMIYOR:
                _sayi_dogrula(d, ad_)
        if (tr_ciro is not BILINMIYOR and dunya_ciro is not BILINMIYOR
                and tr_ciro > dunya_ciro):
            raise CiroHatasi(
                "%s: Türkiye cirosu (%s) dünya cirosundan (%s) büyük olamaz"
                % (ad, tr_ciro, dunya_ciro))
        self.ad, self.rol, self.teknoloji = ad, rol, teknoloji
        # [BH · elli beşinci tur] Teknoloji istisnasının ÖLÇÜTÜ itirazlıdır:
        # kitap "Türkiye'de faaliyet gösteren ya da Ar-Ge yürüten" diyor,
        # I-02'nin kayıtlı alternatifi "Türkiye'de YERLEŞİK" olabilir diyor.
        # Tek bir teknoloji doğru/yanlış alanı bu ayrımı SÖYLEYEMİYORDU ve
        # kullanıcı, itiraz edilen ölçütün karşılandığını istemeden beyan
        # etmiş oluyordu. Üçüncü bir değer (bilinmiyor) ayrımı görünür kılar.
        self.yerlesik = yerlesik
        self.tr_ciro, self.dunya_ciro = tr_ciro, dunya_ciro

    def __repr__(self):
        return "Taraf(%r, tr=%s, dunya=%s, rol=%r)" % (
            self.ad, self.tr_ciro, self.dunya_ciro, self.rol)


class Sonuc:
    def __init__(self, sonuc, ayak, gerekce, eksik, kullanilan, itiraz=None):
        self.sonuc, self.ayak = sonuc, ayak
        self.gerekce, self.eksik, self.kullanilan = gerekce, eksik, kullanilan
        # [BG · elli dördüncü tur] KAYITLI bir açık sorunun bu olguda cevabı
        # TERSİNE çevirdiği hâller. Uyarı yöntem dosyasında duruyordu ama
        # çıktıya hiç ulaşmıyordu; üstelik mevzuat belirsizliği yalnızca
        # EVET cevabına ekleniyordu. İşletim sözleşmesinin 2. kuralı tam
        # tersini ister: "bildirime tabi değil" cümlesi daha yüksek kanıt
        # eşiğine tabidir.
        self.itiraz = itiraz or []

    def yazdir(self):
        print("Bildirime tabi mi : %s" % self.sonuc.upper())
        print("Hangi ayak        : %s" % self.ayak)
        print("Gerekçe           : %s" % self.gerekce)
        print("Kullanılan rakamlar:")
        for k in self.kullanilan:
            print("  - %s" % k)
        if self.eksik:
            print("Bilinmeyen ve cevabı değiştirebilecek rakamlar:")
            for e in self.eksik:
                print("  - %s" % e)
        print("Eşiklerin doğrulama tarihi: %s" % DOGRULAMA)
        if self.itiraz:
            print()
            print("AÇIK MEVZUAT SORUSU — BU CEVABI TERSİNE ÇEVİREBİLİR:")
            for i in self.itiraz:
                print("  ! %s" % i)
        print()
        print("Şimdi ne yapılmalı")
        if self.sonuc == EVET:
            print("  Bildirim hazırlanır. İZİNDEN ÖNCE KAPANIŞ YAPILMAZ "
                  "(4054 sayılı Kanun; madde numarası DOĞRULANAMADI — "
                  "bkz. hafiza/dogrulama-bulgulari.md I-03).")
        elif self.sonuc == BELIRSIZ:
            print("  Yukarıdaki bilinmeyen rakamlar temin edilir. Bu hâliyle "
                  "cevap verilmez.")
        elif self.itiraz:
            print("  Eşik, KİTABIN YAZDIĞI okumaya göre aşılmıyor. Yukarıdaki "
                  "açık soru çözülmeden 'bildirim gerekmez' sonucuna "
                  "DAYANILMAZ ve kapanış yapılmaz; teyit, adı belli bir "
                  "yetkili avukatın kararıdır (insan onayı).")
        else:
            print("  Eşik aşılmıyor. Rakamların kaynağı ve tarihi kayda geçirilir.")
        print()
        print("Yetkili avukat görüşü gereken konular")
        print("  Ciro rakamlarının hangi mali tablodan ve hangi kurdan alındığı; "
              "kontrol değişikliği niteliği; ortak girişim analizi; "
              "olumsuz sonucun teyidi.")
        for i in self.itiraz:
            print("  - %s" % i)


# --- Geriye dönük uyumlu ilkel ayaklar --------------------------------------
def esik_a(tr_cirolar):
    """Toplam Türkiye cirosu ve en az iki tarafın tabanı aşması."""
    bilinen = [c for c in tr_cirolar if c is not BILINMIYOR]
    for c in bilinen:
        _sayi_dogrula(c, "tr_ciro")
    toplam = sum(bilinen)
    tabani_asan = [c for c in bilinen if c > IKI_TARAF_TR]
    return toplam > BIRLESIK_TR and len(tabani_asan) >= 2


def esik_b(hedef_tr, diger_dunya_cirolari, teknoloji=False):
    """Devre konu tarafın Türkiye cirosu, DİĞER tarafların dünya cirosuna karşı."""
    if hedef_tr is BILINMIYOR:
        return False
    _sayi_dogrula(hedef_tr, "hedef_tr")
    esik = HEDEF_TR_TEKNOLOJI if teknoloji else HEDEF_TR
    bilinen = [c for c in diger_dunya_cirolari if c is not BILINMIYOR]
    return hedef_tr > esik and any(c > DIGER_DUNYA for c in bilinen)


def bildirilmeli(tr_cirolar, hedef_tr, diger_dunya_cirolari, teknoloji=False):
    """(bildirime tabi mi, hangi ayak) döner. Geriye dönük uyumluluk için.

    UYARI: bu imza aynı işlemi İKİ ayrı biçimde ister ve tutarlılığı kontrol
    etmez [A-09]; ayrıca üç değerli cevap veremez [A-10]. Yeni işler için
    degerlendir() kullanın.

    [A-07 kalıntısı] Bu fonksiyon birim taşımaz. Belgelemek yetmedi: kusur
    kodda CANLI kaldığı sürece biri onu çağırır ve §19'un sessiz yanlış
    cevabını alır. Artık sessiz değil — birim belirsizliği yakalanabilecek
    her yerde uyarıyor ve hiçbir eşiğin karşılanmadığı hâlde büyük bir
    rakamın verildiği durumu ayrıca işaretliyor.
    """
    import warnings
    warnings.warn(
        "bildirilmeli() birim taşımaz ve üç değerli cevap veremez; "
        "yabancı para birimindeki bir ciro çevrilmeden verilirse cevap "
        "SESSİZCE tersine döner (§19 pilotu). degerlendir() kullanın.",
        DeprecationWarning, stacklevel=2)
    # Birim tuzağı: B ayağı karşılanmadı ama devre konu taraf eşiği aşıyor ve
    # 'diğer dünya' rakamı DIGER_DUNYA'nın hemen altında kalıyorsa, bu tipik
    # olarak çevrilmemiş bir yabancı para tutarıdır.
    _bilinen = [c for c in diger_dunya_cirolari if c is not BILINMIYOR]
    if (hedef_tr not in (BILINMIYOR, 0) and hedef_tr > HEDEF_TR_TEKNOLOJI
            and _bilinen and max(_bilinen) < DIGER_DUNYA
            and max(_bilinen) > DIGER_DUNYA / 100):
        warnings.warn(
            "OLASI BİRİM HATASI: devre konu taraf eşiği aşıyor ama 'diğer "
            "dünya cirosu' (%s) %s eşiğinin altında. Bu rakam TL mi? "
            "Yabancı para ise tl(tutar, birim, kur, kaynak) ile çevirin."
            % (max(_bilinen), DIGER_DUNYA), RuntimeWarning, stacklevel=2)
    a = esik_a(tr_cirolar)
    b = esik_b(hedef_tr, diger_dunya_cirolari, teknoloji)
    if a and b:
        return True, "her iki eşik"
    if a:
        return True, "A eşiği (yurt içi)"
    if b:
        return True, "B eşiği (devre konu)" + (" + teknoloji" if teknoloji else "")
    return False, "hiçbir eşik"


# --- [A-09, A-10, A-13, A-15] Asıl değerlendirme ---------------------------
def degerlendir(taraflar, islem_turu="devralma"):
    """Tek bir taraf listesinden iki ayağı da hesaplar. Üç değerli cevap verir."""
    if islem_turu not in ("devralma", "birlesme"):
        raise CiroHatasi("islem_turu 'devralma' ya da 'birlesme' olmalı")
    if len(taraflar) < 2:
        raise CiroHatasi("en az iki taraf gerekir; verilen: %d" % len(taraflar))

    kullanilan, eksik = [], []

    # ---- A ayağı --------------------------------------------------------
    tr = [(t.ad, t.tr_ciro) for t in taraflar]
    bilinen_tr = [v for _, v in tr if v is not BILINMIYOR]
    for ad, v in tr:
        (kullanilan if v is not BILINMIYOR else eksik).append(
            "%s Türkiye cirosu: %s" % (ad, _bicim(v)))
    toplam = sum(bilinen_tr)
    asan = [v for v in bilinen_tr if v > IKI_TARAF_TR]
    a_var = toplam > BIRLESIK_TR and len(asan) >= 2
    a_belirsiz = (not a_var) and len(bilinen_tr) < len(tr)

    # ---- B ayağı --------------------------------------------------------
    if islem_turu == "devralma":
        konu = [t for t in taraflar if t.rol == "hedef"]
        if not konu:
            raise CiroHatasi(
                "devralma işleminde rol='hedef' olan bir taraf gerekir. "
                "Devre konu varlığı belirtmeden B ayağı hesaplanamaz.")
    else:
        konu = [t for t in taraflar if t.rol in ("birlesen", "taraf")] or taraflar

    b_var, b_belirsiz, b_gerekce = False, False, ""
    b_itiraz = []
    for k in konu:
        esik = HEDEF_TR_TEKNOLOJI if k.teknoloji else HEDEF_TR
        # [A-13] DİĞER taraflar: devre konu tarafın kendisi hariç.
        digerleri = [t for t in taraflar if t is not k]
        dunya_bilinen = [(t.ad, t.dunya_ciro) for t in digerleri
                         if t.dunya_ciro is not BILINMIYOR]
        dunya_eksik = [t.ad for t in digerleri if t.dunya_ciro is BILINMIYOR]
        if k.tr_ciro is BILINMIYOR:
            b_belirsiz = True
            continue
        if k.tr_ciro > esik:
            asanlar = [ad for ad, v in dunya_bilinen if v > DIGER_DUNYA]
            if asanlar:
                b_var = True
                b_gerekce = ("%s Türkiye cirosu %s > %s; %s dünya cirosu > %s"
                             % (k.ad, _bicim(k.tr_ciro), _bicim(esik),
                                asanlar[0], _bicim(DIGER_DUNYA)))
                if k.teknoloji:
                    b_gerekce += " (teknoloji teşebbüsü istisnası uygulandı)"
                    if k.yerlesik is not True:
                        b_itiraz.append(
                            "I-02 · %s için teknoloji istisnası (%s) "
                            "uygulandı, ama istisnanın ÖLÇÜTÜ itirazlıdır: "
                            "kitap \"Türkiye'de faaliyet gösteren ya da Ar-Ge "
                            "yürüten\" diyor; güncel ölçüt \"Türkiye'de "
                            "YERLEŞİK\" olabilir. Hedef yerleşik DEĞİLSE "
                            "istisna uygulanmaz, eşik %s olur ve bu olguda "
                            "cevap TERS DÖNER (bildirime tabi olmayabilir). "
                            "Yerleşiklik bu girdide %s. Dayanak DOĞRULANAMADI; "
                            "bkz. birimler/rekabet/yontem/tr-esikler.md ve "
                            "hafiza/dogrulama-bulgulari.md I-02."
                            % (k.ad, _bicim(HEDEF_TR_TEKNOLOJI),
                               _bicim(HEDEF_TR),
                               "beyan edilmemiş" if k.yerlesik is BILINMIYOR
                               else "HAYIR diye beyan edilmiş"))
                break
            if dunya_eksik:
                b_belirsiz = True
        elif dunya_eksik:
            b_belirsiz = True
    for t in taraflar:
        if t.dunya_ciro is not BILINMIYOR:
            kullanilan.append("%s dünya cirosu: %s" % (t.ad, _bicim(t.dunya_ciro)))
        else:
            eksik.append("%s dünya cirosu: bilinmiyor" % t.ad)

    # ---- Birleştirme ----------------------------------------------------
    if a_var and b_var:
        return Sonuc(EVET, "her iki eşik",
                     "A: toplam %s > %s ve iki taraf tabanı aşıyor. B: %s"
                     % (_bicim(toplam), _bicim(BIRLESIK_TR), b_gerekce),
                     eksik, kullanilan, b_itiraz)
    if a_var:
        return Sonuc(EVET, "A eşiği (yurt içi)",
                     "toplam Türkiye cirosu %s > %s ve %d taraf ayrı ayrı %s'yi "
                     "aşıyor" % (_bicim(toplam), _bicim(BIRLESIK_TR), len(asan),
                                 _bicim(IKI_TARAF_TR)),
                     eksik, kullanilan)
    if b_var:
        return Sonuc(EVET, "B eşiği (devre konu)", b_gerekce, eksik,
                     kullanilan, b_itiraz)
    if a_belirsiz or b_belirsiz:
        return Sonuc(BELIRSIZ, "belirlenemedi",
                     "bilinen rakamlar hiçbir ayağı karşılamıyor, ancak "
                     "bilinmeyen rakamlar cevabı DEĞİŞTİREBİLİR. "
                     "Olumsuz iddia kuralı (CLAUDE.md §2): bu hâliyle "
                     "'bildirim gerekmez' YAZILMAZ.",
                     eksik, kullanilan)
    # ---- İTİRAZLI BANT: kayıtlı açık soru cevabı tersine çevirir mi ----
    # I-01: teknoloji indirimi (250 milyon) A ayağının ikinci bacağına da
    # uygulanıyorsa, burada "aşmıyor" görünen hedef aşıyor demektir ve A
    # ayağı KARŞILANIR. Bu bir hukuki nitelendirmedir; kod cevabı
    # DEĞİŞTİRMEZ, yalnızca soruyu görünür kılar (§9 · insan onayı).
    itiraz = []
    if not a_var and toplam > BIRLESIK_TR:
        for t in taraflar:
            if (t.teknoloji and t.tr_ciro is not BILINMIYOR
                    and HEDEF_TR_TEKNOLOJI < t.tr_ciro <= IKI_TARAF_TR
                    and len([v for v in bilinen_tr if v > IKI_TARAF_TR]) >= 1):
                itiraz.append(
                    "I-01 · %s Türkiye cirosu %s: teknoloji indirimi (%s) A "
                    "ayağının 'ayrı ayrı' bacağına da uygulanıyorsa A eşiği "
                    "KARŞILANIR ve işlem BİLDİRİME TABİDİR — bu okumada cevap "
                    "TERS DÖNER. Dayanak DOĞRULANAMADI (birincil metin egress "
                    "ile engelli); bkz. birimler/rekabet/yontem/tr-esikler.md "
                    "ve hafiza/dogrulama-bulgulari.md I-01."
                    % (t.ad, _bicim(t.tr_ciro), _bicim(HEDEF_TR_TEKNOLOJI)))
    return Sonuc(HAYIR, "hiçbir eşik",
                 "bütün rakamlar bilindi ve iki ayak da karşılanmadı",
                 eksik, kullanilan, itiraz)


def _bicim(v):
    if v is BILINMIYOR:
        return "bilinmiyor"
    return "{:,.0f} TL".format(v).replace(",", ".")


# --- [A-14] Komut satırı ---------------------------------------------------
def _taraf_ayristir(m):
    """ad,tr=...,dunya=...,rol=...,teknoloji  · tutarlara birim eklenebilir."""
    parcalar = [p.strip() for p in m.split(",")]
    ad, alan = parcalar[0], {}
    for p in parcalar[1:]:
        if p == "teknoloji":
            alan["teknoloji"] = True
            continue
        if "=" not in p:
            raise CiroHatasi("anlaşılmayan alan: %r" % p)
        k, v = p.split("=", 1)
        alan[k.strip()] = v.strip()
    return ad, alan


def _tutar_coz(ham, kurlar):
    if ham in (None, "", "bilinmiyor", "?"):
        return BILINMIYOR
    birim = "TL"
    for b in ("TL", "TRY", "EUR", "USD"):
        if ham.upper().endswith(b):
            birim, ham = b, ham[:-len(b)]
            break
    ham = ham.replace(".", "").replace("_", "").strip()
    try:
        tutar = float(ham)
    except ValueError:
        raise CiroHatasi("tutar okunamadı: %r" % ham)
    kur, kaynak = kurlar.get(birim, (None, None))
    return tl(tutar, birim, kur, kaynak)


def main(argv=None):
    ap = argparse.ArgumentParser(
        description="Türkiye birleşme denetimi bildirim eşiği testi.",
        epilog="Örnek:\n"
               "  esik.py --taraf 'Alıcı,dunya=2400000000EUR,rol=devralan' \\\n"
               "          --taraf 'Hedef,tr=1400000000,rol=hedef' \\\n"
               "          --kur EUR=47:'TCMB gösterge 2026-08-27'",
        formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("--taraf", action="append", default=[],
                    help="ad,tr=..,dunya=..,rol=devralan|hedef|birlesen[,teknoloji][,yerlesik=1|0]")
    ap.add_argument("--kur", action="append", default=[],
                    help="BIRIM=kur:kaynak  (ör. EUR=47:'TCMB 2026-08-27')")
    ap.add_argument("--birlesme", action="store_true",
                    help="devralma yerine birleşme olarak değerlendir [A-15]")
    a = ap.parse_args(argv)

    if a.self_test:
        return _selftest()
    if not a.taraf:
        print(__doc__.strip())
        print("\nGerçek bir işlem hesaplamak için --taraf kullanın; "
              "--help örneği gösterir.")
        return 0

    kurlar = {}
    for k in a.kur:
        birim, geri = k.split("=", 1)
        deger, _, kaynak = geri.partition(":")
        kurlar[birim.upper()] = (float(deger), kaynak or None)

    taraflar = []
    for m in a.taraf:
        ad, alan = _taraf_ayristir(m)
        taraflar.append(Taraf(
            ad,
            tr_ciro=_tutar_coz(alan.get("tr"), kurlar),
            dunya_ciro=_tutar_coz(alan.get("dunya"), kurlar),
            rol=alan.get("rol", "taraf"),
            teknoloji=bool(alan.get("teknoloji")),
            yerlesik=(BILINMIYOR if alan.get("yerlesik") is None
                      else alan.get("yerlesik") not in ("0", "hayir", "hayır"))))
    s = degerlendir(taraflar, "birlesme" if a.birlesme else "devralma")
    s.yazdir()
    return 0 if s.sonuc != BELIRSIZ else 3


def _selftest():
    h = 0
    # Öz-sınama eski API'yi BİLEREK çalıştırıyor (geriye dönük uyum kaydı);
    # kullanımdan kaldırma uyarısı burada gürültüdür. Birim uyarısı ayrıca
    # sınanır, bkz. aşağıdaki "birim tuzağı" vakası.
    import warnings
    warnings.filterwarnings("ignore", category=DeprecationWarning,
                            module=__name__)

    def esit(ad, bekle, ger):
        nonlocal h
        if bekle != ger:
            print("  HATA %s: beklenen %r, gerçek %r" % (ad, bekle, ger)); h += 1

    # Kitabın kendi altı vakası, aynen korunur.
    ok, sebep = bildirilmeli([2_000_000_000, 1_500_000_000], 0, [])
    if not ok or "A" not in sebep:
        print("  HATA A eşiği olumlu"); h += 1
    ok, _ = bildirilmeli([2_900_000_000, 500_000_000], 0, [])
    if ok:
        print("  HATA A eşiği İKİ tarafın tabanı aşmasını ister"); h += 1
    ok, sebep = bildirilmeli([0], 1_200_000_000, [10_000_000_000])
    if not ok or "B" not in sebep:
        print("  HATA B eşiği olumlu"); h += 1
    ok, _ = bildirilmeli([0], 300_000_000, [10_000_000_000])
    if ok:
        print("  HATA 300 milyonluk hedef olağan B eşiğini geçmemeli"); h += 1
    ok, sebep = bildirilmeli([0], 300_000_000, [10_000_000_000], teknoloji=True)
    if not ok or "teknoloji" not in sebep:
        print("  HATA teknoloji istisnası uygulanmadı"); h += 1
    ok, _ = bildirilmeli([0], HEDEF_TR, [10_000_000_000])
    if ok:
        print("  HATA eşiğe tam eşit olmak aşmak sayılmamalı"); h += 1

    # [A-07] Para birimi: çevrilmemiş avro SESSİZCE kabul edilmemeli.
    try:
        tl(2_400_000_000, "EUR")
        print("  HATA kursuz avro kabul edildi"); h += 1
    except CiroHatasi:
        pass
    try:
        tl(2_400_000_000, "EUR", kur=47)
        print("  HATA kaynaksız kur kabul edildi"); h += 1
    except CiroHatasi:
        pass
    esit("A-07 çevrilmiş avro", 112_800_000_000.0,
         tl(2_400_000_000, "EUR", 47, "TCMB 2026-08-27"))

    # [A-11, A-12] Bilinmeyen ve negatif.
    for hatali in (None, -1, "1000", True):
        try:
            _sayi_dogrula(hatali, "t"); print("  HATA %r kabul edildi" % hatali); h += 1
        except CiroHatasi:
            pass

    # [A-09, A-10] §19 pilotu tek modelden, üç değerli.
    pilot = degerlendir([
        Taraf("Alman alıcı", dunya_ciro=tl(2_400_000_000, "EUR", 47, "TCMB"),
              rol="devralan"),
        Taraf("Türk hedef", tr_ciro=1_400_000_000, rol="hedef")])
    esit("A-08 §19 pilotu", EVET, pilot.sonuc)
    esit("A-08 ayak", "B eşiği (devre konu)", pilot.ayak)

    # [A-10] Bilinmeyen ciro 'hayır' değil 'belirlenemiyor' üretir.
    belirsiz = degerlendir([
        Taraf("Alıcı", tr_ciro=BILINMIYOR, dunya_ciro=BILINMIYOR, rol="devralan"),
        Taraf("Hedef", tr_ciro=BILINMIYOR, rol="hedef")])
    esit("A-10 bilinmeyen", BELIRSIZ, belirsiz.sonuc)

    # Bütün rakamlar bilinip eşik aşılmıyorsa 'hayır' meşrudur.
    hayir = degerlendir([
        Taraf("Alıcı", tr_ciro=10_000_000, dunya_ciro=20_000_000, rol="devralan"),
        Taraf("Hedef", tr_ciro=5_000_000, dunya_ciro=5_000_000, rol="hedef")])
    esit("hepsi bilinen olumsuz", HAYIR, hayir.sonuc)

    # [A-13] Devre konu taraf kendi dünya cirosuyla B'yi karşılayamaz.
    kendi = degerlendir([
        Taraf("Alıcı", tr_ciro=1_000, dunya_ciro=1_000, rol="devralan"),
        Taraf("Hedef", tr_ciro=1_200_000_000, dunya_ciro=50_000_000_000,
              rol="hedef")])
    esit("A-13 kendi kendine B", HAYIR, kendi.sonuc)

    # [A-15] Birleşme: hedef rolü olmadan da değerlendirilebilmeli.
    birlesme = degerlendir([
        Taraf("X", tr_ciro=1_200_000_000, dunya_ciro=1_200_000_000, rol="birlesen"),
        Taraf("Y", tr_ciro=100_000_000, dunya_ciro=10_000_000_000, rol="birlesen")],
        islem_turu="birlesme")
    esit("A-15 birleşme", EVET, birlesme.sonuc)

    # Tutarlılık: Türkiye cirosu dünya cirosunu aşamaz.
    try:
        Taraf("Z", tr_ciro=10, dunya_ciro=1)
        print("  HATA tutarsız ciro kabul edildi"); h += 1
    except CiroHatasi:
        pass

    # [A-07 kalıntısı] Eski API, §19 pilotunda birim uyarısı vermeli.
    with warnings.catch_warnings(record=True) as yakalanan:
        warnings.simplefilter("always")
        bildirilmeli([], 1_400_000_000, [2_400_000_000])
    if not any("BİRİM HATASI" in str(w.message) for w in yakalanan):
        print("  HATA eski API §19 pilotunda birim uyarısı vermedi"); h += 1
    # Ve TL cinsinden meşru bir işlemde uyarı VERMEMELİ (iki yönlü sınama).
    with warnings.catch_warnings(record=True) as yakalanan2:
        warnings.simplefilter("always")
        bildirilmeli([0], 1_200_000_000, [10_000_000_000])
    if any("BİRİM HATASI" in str(w.message) for w in yakalanan2):
        print("  HATA meşru TL işleminde yanlış birim uyarısı"); h += 1

    print("SELFTEST %s (rakamlar %s tarihinde doğrulandı)"
          % ("OK" if not h else "HATA %d" % h, DOGRULAMA))
    return h


if __name__ == "__main__":
    sys.exit(main())
