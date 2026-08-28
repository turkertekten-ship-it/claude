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

# Raporun EL YAZISI vaka sayısı, BU koşumun gerçek toplamıyla karşılaştırılır.
# Burada yapılır çünkü burası toplamı bayatlamadan bilen tek yerdir: denetime
# konulduğunda kontrol iki koşumda yakınsıyordu ve bu, kırmızıyı görmezden
# gelmeyi öğretir.
_kok=$(cd "$S/.." && pwd)
if [ -f "$_kok/RAPOR.md" ]; then
  _iddia=$(grep -oE '\*\*[0-9]{3}$|^vaka, [0-9]+ mutasyon|[0-9]{3} vaka \+ 15 mutasyon' \
             "$_kok/RAPOR.md" | grep -oE '[0-9]{3}' | sort -u)
  _yanlis=""
  for _i in $_iddia; do [ "$_i" != "$_toplam" ] && _yanlis="$_yanlis $_i"; done
  if [ -n "$_yanlis" ]; then
    echo
    echo "  ------------------------------------------------------------"
    echo "  UYARI raporun vaka sayısı bayat:$_yanlis (gerçek: $_toplam)"
    _t=$((_t + 1))
    printf "  %-38s %s\n" "TOPLAM SİNYAL (düzeltilmiş)" "$_t"
    echo "  Bu satır yukarıdaki özetten SONRA hesaplanır: gerçek toplam ancak"
    echo "  bütün takımlar koştuktan sonra bilinir. Çıkış kodu bu sayıdır."
  fi
fi
rm -f "$_gunluk"
exit "$_t"
