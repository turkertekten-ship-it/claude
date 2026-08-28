#!/usr/bin/env bash
# KÖR SINAMA TAKIMI — hepsi
# Kitabın kendi öz-sınamalarından bağımsız. Her vaka kitabın DÜZYAZISINDAN
# türetildi, kodundan değil.
set -u
S="${MAFIRM_SINAMA:-$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)}"
declare -a ad kod
topla() { ad+=("$1"); kod+=("$2"); }

# [X · katman ihlali, ikinci kez] denetim.sh raporun vaka sayısını doğrularken
# bir KAYIT dosyası okur. O kayıt olarak SONUC-sonra.txt kullanılınca şu döngü
# doğdu: hepsi.sh > SONUC-sonra.txt yönlendirmesi dosyayı BAŞTA kesiyor,
# hepsi.sh içinden koşan D takımı denetim.sh'i çağırıyor, denetim yarım kalmış
# kaydı okuyup kırmızıya dönüyor, D'nin taban çizgisi bozuluyor. Betiğin
# kendisini çağırmadan, yalnızca ONUN YAZDIĞI dosya üzerinden kurulan bir
# özyineleme — aynı katman ihlalinin veri yolundan gelen hâli.
# Çözüm: sayım, yönlendirme hedefinden AYRI bir dosyaya ve ATOMİK yazılır.
_ana() {
echo "###############################################################"
echo "#  KÖR SINAMA TAKIMI — $(date -u +%Y-%m-%dT%H:%M:%SZ)"
echo "###############################################################"
echo
python3 "$S/ks_a_esik.py";     topla "A · rekabet eşiği mantığı" $?
echo
python3 "$S/ks_b_kapilar.py";  topla "B · beş kapı / on bir kural" $?
echo
python3 "$S/ks_c_uretim.py";   topla "C · üretim yolu (kanca JSON)" $?
echo
bash   "$S/ks_d_denetim.sh";   topla "D · denetim mutasyon sınaması" $?
echo
bash   "$S/ks_e_tutarlilik.sh"; topla "E · kitabın kendi beklenen değerleri" $?
echo
# [kendi kusurum] Bu satır F'in çıkış kodunu 0 diye SABİTLİYOR ve üstelik
# tail'e boruluyordu — boru hattının kodu tail'inkidir. F çöktüğünde takım
# hâlâ "0 SİNYAL" diyordu. Kitabın denetiminde bulduğum `| wc -l` kusurunun
# kendi koşum betiğimdeki hâli. Çıktı bir dosyaya alınır, kod korunur.
_f_cikti=$(python3 "$S/ks_f_kapsama.py" 2>&1); _f_kod=$?
echo "$_f_cikti" | tail -8
topla "F · doktrin kapsama matrisi" "$_f_kod"
echo
python3 "$S/ks_j_kabul.py";    topla "J · §19 kabul sınaması (uçtan uca)" $?
echo
python3 "$S/ks_k_yonlendirme.py"; topla "K · yönlendirme ve koltuk sağlaması" $?
echo
python3 "$S/ks_l_referans.py";    topla "L · çapraz referans bütünlüğü" $?
echo
python3 "$S/ks_m_izlenebilirlik.py"; topla "M · errata izlenebilirliği" $?
echo
python3 "$S/ks_n_olumsuz.py";     topla "N · olumsuz iddia kanıtı" $?
echo
python3 "$S/ks_o_kacirma.py";     topla "O · sır kapısı kaçırma yüzeyi" $?
echo
python3 "$S/ks_p_guncellik.py";  topla "P · teslimatların güncelliği" $?
echo
python3 "$S/ks_q_kendi_kapisi.py"; topla "Q · rapor kendi kapılarından geçiyor mu" $?
echo
python3 "$S/ks_r_yon.py";         topla "R · yön, onay ve dil kuralları" $?
echo
python3 "$S/ks_s_yalitim.py";     topla "S · yalıtım (klon yalnız mı)" $?
echo
python3 "$S/ks_t_sinirlar.py";   topla "T · §18'in dokuz sınırı" $?
echo
python3 "$S/ks_u_birimler_arasi.py"; topla "U · birimler arası tutarlılık" $?
echo
python3 "$S/ks_v_yanlis_pozitif.py"; topla "V · kapıların yanlış pozitifi" $?
echo
python3 "$S/ks_w_bos_kaynak.py"; topla "W · sessizce boş arama kaynağı" $?
echo
python3 "$S/ks_x_yetki.py"; topla "X · alt ajan yetkisi / kapı kapsamı" $?
echo
python3 "$S/ks_y_sirrin_deposu.py"; topla "Y · sırrın kalıcı deposu" $?
echo
python3 "$S/ks_z_kurulum_butunlugu.py"; topla "Z · kurulum bütünlüğü" $?
echo
python3 "$S/ks_aa_dayaniklilik.py"; topla "AA · kapının arıza yönü" $?
echo
python3 "$S/ks_ab_care.py"; topla "AB · blok iletisinin çaresi" $?
echo
python3 "$S/ks_ac_ortam.py"; topla "AC · ortam bağımsızlığı" $?
echo
python3 "$S/ks_ad_komut.py"; topla "AD · komutların iddiaları" $?
echo
python3 "$S/ks_ae_desen.py"; topla "AE · desen sınıfı taraması" $?
echo
python3 "$S/ks_af_aparat.py"; topla "AF · aparatın kendi iddiaları" $?
echo
python3 "$S/ks_ag_referans.py"; topla "AG · kitaba sadık taban" $?
echo
python3 "$S/ks_ah_cevap.py"; topla "AH · cevabın güncelliği" $?
echo
python3 "$S/ks_ai_koltuk_dayanak.py"; topla "AI · koltuk dayanakları" $?
echo
python3 "$S/ks_aj_kanal.py"; topla "AJ · çalışan kanalın kullanımı" $?
echo
python3 "$S/ks_ak_bulgu_statu.py"; topla "AK · bulgu statüsü ve kanıt türü" $?
echo
python3 "$S/ks_al_yan_etki.py"; topla "AL · takımların yan etkisi / bağımsızlık" $?
echo
python3 "$S/ks_am_surum.py"; topla "AM · kararın hukuki sürümü" $?
echo
python3 "$S/ks_an_kabul.py"; topla "AN · yamanın kabul sınaması" $?
echo
python3 "$S/ks_ao_catisma.py"; topla "AO · çatışmanın yönü ve zamanı" $?
echo
python3 "$S/ks_ap_katalog.py"; topla "AP · araç kataloğunun kurulumdaki hâli" $?
echo
python3 "$S/ks_aq_zaman.py"; topla "AQ · yaptırım taramasının zaman ekseni" $?
echo
python3 "$S/ks_ar_onay.py"; topla "AR · onay durumu (yedinci kapı)" $?
echo
python3 "$S/ks_as_kapi_kapsama.py"; topla "AS · kapıların öz-sınama kapsaması" $?
echo
python3 "$S/ks_at_denetim_kapsama.py"; topla "AT · denetimin mutasyon kapsaması" $?
echo
python3 "$S/ks_au_epilog.py"; topla "AU · epilog kontrollerinin sınaması" $?
echo
python3 "$S/ks_av_anma.py"; topla "AV · anma/tanım sınıfı taraması" $?
echo
python3 "$S/ks_aw_alinti.py"; topla "AW · kitap alıntılarının doğruluğu" $?
echo
python3 "$S/ks_ax_yapi.py"; topla "AX · kitap yapısı iddiaları" $?
echo
python3 "$S/ks_ay_olumsuz_kitap.py"; topla "AY · kitap hakkında olumsuz iddialar" $?
echo
python3 "$S/ks_az_sadik.py"; topla "AZ · kitaba sadık kopyaların sadakati" $?
echo
python3 "$S/ks_ba_kayit_celiski.py"; topla "BA · kayıt ile iddianın çelişmesi" $?
echo
echo "###############################################################"
echo "#  ÖZET"
echo "###############################################################"
t=0
for i in "${!ad[@]}"; do
  printf "  %-38s %s\n" "${ad[$i]}" \
    "$([ "${kod[$i]}" -eq 0 ] && echo 'temiz' || echo "${kod[$i]} SİNYAL")"
  t=$((t + kod[i]))
done
echo "  ------------------------------------------------------------"
printf "  %-38s %s\n" "TOPLAM SİNYAL" "$t"
  echo
  if [ "$t" -eq 0 ]; then
    echo "  Beyan edilmiş tabanla eşleşiyor: bilinen ve gerekçeli sapmalar"
    echo "  BEKLENEN olarak raporlandı (sinama/beklenen.json), beyan edilmemiş"
    echo "  hiçbir başarısızlık ve hiçbir beklenmedik geçiş yok."
  else
    echo "  SİNYAL VAR: ya beyan edilmemiş bir başarısızlık (regresyon), ya da"
    echo "  beyanlı olup artık GEÇEN bir vaka (beyan bayat / sınama çürüdü)."
  fi
echo
echo "  G · §13 depo kataloğu       -> sinama/ks_g_depolar.md"
echo "  H · §17 kaynak doğrulaması  -> sinama/ks_h_kaynaklar.md"
echo "  I · §5 mevzuat doğrulaması  -> sinama/ks_i_mevzuat.md"
return "$t"
}

_kok=$(cd "$S/.." && pwd)
_gunluk=$(mktemp)
_ana | tee "$_gunluk"
_t=${PIPESTATUS[0]}

# SAYIM.txt: denetimin okuduğu KAYIT. Geçici dosyaya yazılıp mv ile yerine
# konur; hiçbir okuyucu yarım hâlini göremez.
_toplam=$(grep -oE '^[0-9]+ vaka' "$_gunluk" | awk '{s+=$1} END {print s+0}')
_gecici=$(mktemp)
{
  echo "# hepsi.sh koşum kaydı — denetim.sh bu dosyayı okur."
  echo "# ATOMİK yazılır (mktemp + mv): yarım hâli hiçbir zaman görünmez."
  echo "tarih: $(date -u +%Y-%m-%dT%H:%M:%SZ)"
  echo "vaka: $_toplam"
  echo "sinyal: $_t"
} > "$_gecici"
mv -f "$_gecici" "$S/SAYIM.txt"

# [AL-06 · otuzuncu tur] Beyan edilmiş her vaka koşumda BEKLENEN olarak
# görünüyor mu, belirtisi kaymış mı, ve raporun EL YAZISI vaka sayısı bu
# koşumun gerçek toplamıyla uyuşuyor mu? Üçü de BURADA yapılır çünkü burası
# tam ve bayatlamamış günlüğü bilen TEK yerdir. (AF-03 önce SONUC-sonra.txt'yi
# okuyordu — yani bu betiğin KENDİ yönlendirme hedefini, koşum sürerken:
# bağımsızken 853 satır, yönlendirme içinde 690, nihai 832. On altıncı turun
# katman dersi, üçüncü yerde.)
#
# [AU · otuz dokuzuncu tur] Kontroller artık sinama/epilog.py içinde. Gömülü
# heredoc oldukları sürece MUTASYONLA SINANAMIYORLARDI: bir epilog kontrolünü
# kırmak kırk üç takımın tamamını koşturmayı gerektiriyordu. Ayrıştırma katman
# ihlali değildir — kontrol hâlâ buradan, tam günlüğü bilen yerden çağrılıyor;
# değişen tek şey (günlük, taban) ikilisinin SAF BİR FONKSİYONU hâline gelmesi.
_epilog=$(python3 "$S/epilog.py" "$_gunluk" "$_kok" 2>&1); _uyari=$?
if [ -n "$_epilog" ]; then
  echo "$_epilog"
  _t=$((_t + _uyari))
  echo
  printf "  %-38s %s\n" "TOPLAM SİNYAL (düzeltilmiş)" "$_t"
fi

rm -f "$_gunluk"
exit "$_t"
