#!/usr/bin/env bash
# KÖR SINAMA TAKIMI — hepsi
# Kitabın kendi öz-sınamalarından bağımsız. Her vaka kitabın DÜZYAZISINDAN
# türetildi, kodundan değil.
set -u
S="${MAFIRM_SINAMA:-$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)}"
declare -a ad kod
topla() { ad+=("$1"); kod+=("$2"); }

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
exit "$t"
