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
python3 "$S/ks_f_kapsama.py" | tail -8; topla "F · doktrin kapsama matrisi" 0
echo
python3 "$S/ks_j_kabul.py";    topla "J · §19 kabul sınaması (uçtan uca)" $?
echo
python3 "$S/ks_k_yonlendirme.py"; topla "K · yönlendirme ve koltuk sağlaması" $?
echo
python3 "$S/ks_l_referans.py";    topla "L · çapraz referans bütünlüğü" $?
echo
echo "###############################################################"
echo "#  ÖZET"
echo "###############################################################"
t=0
for i in "${!ad[@]}"; do
  printf "  %-38s %s\n" "${ad[$i]}" \
    "$([ "${kod[$i]}" -eq 0 ] && echo 'temiz' || echo "${kod[$i]} kaldı")"
  t=$((t + kod[i]))
done
echo "  ------------------------------------------------------------"
printf "  %-38s %s\n" "toplam başarısız vaka" "$t"
echo
echo "  G · §13 depo kataloğu       -> sinama/ks_g_depolar.md"
echo "  H · §17 kaynak doğrulaması  -> sinama/ks_h_kaynaklar.md"
echo "  I · §5 mevzuat doğrulaması  -> sinama/ks_i_mevzuat.md"
exit "$t"
