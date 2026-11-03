#!/bin/bash
set -euo pipefail
version=v1.0.0
bin_dir="$HOME/.local/bin"
skill_dir=''
die() { printf 'fhd-proxy: %s\n' "$*" >&2; exit 1; }
while [ "$#" -gt 0 ]; do
  case "$1" in
    --bin-dir|--skill-dir|--version)
      [ "$#" -ge 2 ] || die "$1 값이 필요합니다."
      case "$1" in --bin-dir) bin_dir=$2;; --skill-dir) skill_dir=$2;; --version) version=$2;; esac
      shift 2;;
    --help) printf '%s\n' 'bash install.sh [--bin-dir ~/.local/bin] [--skill-dir ~/.codex/skills] [--version v1.0.0]'; exit 0;;
    *) die "알 수 없는 옵션: $1";;
  esac
done
[[ "$version" =~ ^v[0-9]+\.[0-9]+\.[0-9]+$ ]] || die '버전 형식이 올바르지 않습니다.'
for folder in "$bin_dir" "${skill_dir:-/tmp}"; do
  case "$folder" in /*) ;; *) die '설치 경로는 절대 경로여야 합니다.';; esac
  case "$folder" in *$'\n'*|*$'\r'*) die '줄바꿈이 있는 경로는 지원하지 않습니다.';; esac
done
command -v python3 >/dev/null || die 'Python 3.9 이상이 필요합니다.'
python3 -c 'import sys; sys.exit(sys.version_info < (3,9))' || die 'Python 3.9 이상이 필요합니다.'
if [ -e "$bin_dir/fhd-proxy" ] && ! grep -q '^# fhd-proxy by leeyekrj$' "$bin_dir/fhd-proxy"; then die '같은 이름의 다른 파일이 있습니다. --bin-dir로 다른 경로를 지정하세요.'; fi
if [ -n "$skill_dir" ] && [ -e "$skill_dir/fhd-proxy" ]; then die '기존 스킬 폴더를 보존했습니다. 다른 --skill-dir을 지정하세요.'; fi
tmp=$(mktemp -d "${TMPDIR:-/tmp}/fhd-proxy-install.XXXXXX")
trap 'rm -rf "$tmp"' EXIT
asset="fhd-proxy-${version#v}.tar.gz"
base="https://github.com/leeyekrj/fhd-proxy/releases/download/$version"
curl -fL --retry 3 --proto '=https' --tlsv1.2 "$base/$asset" -o "$tmp/$asset"
curl -fL --retry 3 --proto '=https' --tlsv1.2 "$base/SHA256SUMS.txt" -o "$tmp/SHA256SUMS.txt"
expected=$(awk -v file="$asset" '$2 == file {print $1}' "$tmp/SHA256SUMS.txt")
[[ "$expected" =~ ^[0-9a-f]{64}$ ]] || die 'SHA256을 확인할 수 없습니다.'
actual=$(shasum -a 256 "$tmp/$asset" | awk '{print $1}')
[ "$actual" = "$expected" ] || die '다운로드 검증 실패. 설치하지 않았습니다.'
# Extract only the known files, not arbitrary members of an archive.
tar -xzf "$tmp/$asset" -C "$tmp" bin/fhd-proxy skills/fhd-proxy/SKILL.md LICENSE THIRD_PARTY_NOTICES.md
grep -q '^# fhd-proxy by leeyekrj$' "$tmp/bin/fhd-proxy" || die '도구 식별자가 다릅니다.'
[ "$(python3 "$tmp/bin/fhd-proxy" --version)" = "${version#v}" ] || die '버전이 다릅니다.'
mkdir -p "$bin_dir"
stage=$(mktemp "$bin_dir/.fhd-proxy.XXXXXX")
cp "$tmp/bin/fhd-proxy" "$stage"; chmod 755 "$stage"
mv "$stage" "$bin_dir/fhd-proxy"
if [ -n "$skill_dir" ]; then
  mkdir -p "$skill_dir"
  cp -R "$tmp/skills/fhd-proxy" "$skill_dir/fhd-proxy"
  printf '스킬 설치: %s/fhd-proxy\n' "$skill_dir"
fi
printf '설치 완료: %s/fhd-proxy\n' "$bin_dir"
printf '%s\n' 'FFmpeg 준비: brew install ffmpeg' '명령을 찾지 못하면 설치 폴더를 PATH에 추가하거나 전체 경로로 실행하세요.'
