#!/usr/bin/env bash
# Pratiği KULLANICI düzeyine kurar: her oturum, her terminal, her istem.
#
# Neden ayrı bir betik. Proje düzeyindeki ~/mafirm/.claude yalnızca o klasörde
# çalışan bir oturumu bağlar. Bu betik aynı doktrini ~/.claude altına taşır ve
# makinedeki her Claude Code oturumu onu okur.
#
# KİP FARKI — bilerek. Pratiğin içinde kapılar BLOCK kipindedir. Genel amaçlı
# oturumlarda Write/Edit için WARN kipindedir: doğru işi bloklayan bir kapı bir
# gün içinde kapatılır ve ondan sonra hiçbir şey uygulanmaz. Dışarı giden
# çağrıda (WebSearch/WebFetch/mcp__*) sır kapısı her kipte bloklar; geri
# alınamayan tek kusur odur.
#
# Kapatma anahtarı:  export MAFIRM_KAPI=off
set -eu
KOK="${MAFIRM_KOK:-$HOME/mafirm}"
HEDEF="$HOME/.claude"
mkdir -p "$HEDEF"/{skills,agents,commands,hooks}

echo "=== beceriler ==="
for d in "$KOK"/.claude/skills/*/; do
  ad=$(basename "$d")
  rm -rf "$HEDEF/skills/$ad"; cp -r "$d" "$HEDEF/skills/$ad"
  echo "  $ad"
done

echo "=== alt ajanlar ==="
for f in "$KOK"/.claude/agents/*.md; do
  cp "$f" "$HEDEF/agents/"; echo "  $(basename "$f")"
done

echo "=== komutlar ==="
for f in "$KOK"/.claude/commands/*.md; do
  cp "$f" "$HEDEF/commands/"; echo "  $(basename "$f")"
done

echo "=== kapılar ==="
cp "$KOK/.claude/hooks/kapi.py" "$HEDEF/hooks/kapi.py"
chmod +x "$HEDEF/hooks/kapi.py"
echo "  kapi.py"

echo "=== ~/.claude/settings.json ==="
python3 - "$HEDEF/settings.json" <<'PY'
import json, os, sys
yol = sys.argv[1]
d = {}
if os.path.exists(yol):
    try:
        d = json.load(open(yol, encoding="utf-8"))
    except Exception:
        d = {}
kanca = {
    "matcher": "WebSearch|WebFetch|Write|Edit",
    "hooks": [{
        "type": "command",
        # warn kipi: Write/Edit uyarır, dışarı giden çağrı yine bloklanır
        "command": "MAFIRM_KAPI=${MAFIRM_KAPI:-warn} python3 ~/.claude/hooks/kapi.py",
    }],
}
h = d.setdefault("hooks", {})
pre = h.setdefault("PreToolUse", [])
pre = [k for k in pre if "kapi.py" not in json.dumps(k)]   # yeniden kurulabilir
pre.append(kanca)
h["PreToolUse"] = pre
izin = d.setdefault("permissions", {})
deny = izin.setdefault("deny", [])
for k in ("Bash(agent-reach * post *)", "Bash(agent-reach * comment *)",
          "Bash(agent-reach * follow *)", "Bash(agent-reach * delete *)"):
    if k not in deny:
        deny.append(k)
json.dump(d, open(yol, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
print("  PreToolUse kancası: %d · deny kuralı: %d" % (len(h["PreToolUse"]), len(deny)))
PY

echo "=== ~/.claude/CLAUDE.md ==="
cat > "$HEDEF/CLAUDE.md" <<'MD'
# Genel işletim kuralları

Bu dosya makinedeki her Claude Code oturumunda geçerlidir.

Sınır ötesi birleşme ve devralma pratiğinin tam işletim sözleşmesi
`~/mafirm/CLAUDE.md` içindedir ve o klasörde çalışılırken kendiliğinden okunur.
Aşağıdakiler klasörden bağımsız olarak her yerde geçerlidir.

## 1. Kanıt kuralı
Her rakam, tarih, eşik, süre ve alıntı dayanağını yanında taşır. Dayanağı
olmayan bir eşik yazılmaz; bulunamıyorsa "eşik doğrulanamadı" yazılır ve cümle
yerinde bırakılır.

## 2. Önce araştır, sonra cevap ver
Cevabı eğitim verisinden bu yana değişmiş olabilecek hiçbir soru hafızadan
cevaplanmaz: eşik, harç, oran, süre, bir düzenleyicinin şu anki uygulaması, bir
aracın var olup olmadığı ve lisansı, piyasa uygulaması, canlı bir dosyanın
durumu. Sıra: web → GitHub → makine → cevap.

Esaslı çıktı şu satırı taşır:

    Kontrol edildi: <kaynak> (<tarih>) · bulunamayan: <ne>

"Bulunamayan" zorunludur. Boş dönen bir arama bir bulgudur.

## 3. Sır saklama
Müvekkili tanıtan hiçbir bilgi makineden çıkmaz: ad, hedef, kod adı, fiyat,
belge metni. Dışarıdan arama gerektiğinde sorgu soyutlanır. Bu kural
`~/.claude/hooks/kapi.py` ile uygulanır ve dışarı giden çağrıda her kipte
bloklar.

## 4. Kapsam
Bu makinedeki hiçbir çıktı hukuki görüş değildir. Hukuki bir konuda üretilen
her esaslı çıktı iki başlıkla biter: **Şimdi ne yapılmalı** ve **Yetkili avukat
görüşü gereken konular**.

## 5. Kapılar
`~/.claude/hooks/kapi.py` beş kapı çalıştırır: kapsam · kanit · sir ·
guncellik · arastirma. Genel oturumlarda Write/Edit için UYARI, dışarı giden
çağrıda BLOK. Kapatmak için: `export MAFIRM_KAPI=off`.

## 6. Yönlendirme
- Türk hukuku sorusu → `~/mafirm/birimler/tr-*/yontem/`
- Rekabet eşiği → asla hafızadan; `~/mafirm/birimler/rekabet/kod/esik.py`
- Bir araç ya da depo sorusu → `~/mafirm/birimler/_araclar/katalog.md`
- Uzun belge bağlama girecekse → `token-verimliligi` becerisi
- Uçtan uca bir iş → `~/mafirm/isakislari/`
MD
echo "  yazıldı"

echo "=== terminal (~/.mafirmrc) ==="
cp "$KOK/mafirmrc" "$HOME/.mafirmrc"
# Etkileşimsizlik korumasından ÖNCE sourcelanmalı ki betikler de görsün.
grep -q ".mafirmrc" "$HOME/.bashrc" 2>/dev/null || \
  sed -i '1i [ -f "$HOME/.mafirmrc" ] && . "$HOME/.mafirmrc"' "$HOME/.bashrc"
grep -q ".mafirmrc" "$HOME/.profile" 2>/dev/null || \
  echo '[ -f "$HOME/.mafirmrc" ] && . "$HOME/.mafirmrc"' >> "$HOME/.profile"
echo "  ~/.mafirmrc kuruldu, .bashrc ve .profile bağlandı"

echo
echo "GENEL KURULUM TAMAM"
echo "  beceriler : $(ls -d $HEDEF/skills/*/ | wc -l)"
echo "  ajanlar   : $(ls $HEDEF/agents/*.md 2>/dev/null | wc -l)"
echo "  komutlar  : $(ls $HEDEF/commands/*.md 2>/dev/null | wc -l)"
