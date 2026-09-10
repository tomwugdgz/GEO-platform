#!/usr/bin/env bash
# push-all.sh —— 一次推送本仓库到 GitHub / Gitee / GitCode / CNB 四个远端
#
# 用法：
#   ./push-all.sh              # 推送当前分支到全部远端
#   ./push-all.sh gitee cnb    # 只推指定的远端
#
# 本机环境的三个坑（脚本已内置处理）：
#   1) GitHub 直连不通，必须走本地代理；且 Git for Windows 默认 schannel TLS 后端
#      会让 push 必然失败（curl 56 / Connection was reset），必须切 openssl。
#   2) Gitee / CNB / GitCode 是国内站，走代理反而卡死 —— 必须显式绕开代理。
#      注意环境里还有 WorkBuddy 自己的 http_proxy=127.0.0.1:53330，光清 git config 不够，
#      要用 `env -u` 把 http_proxy/https_proxy/HTTP_PROXY/HTTPS_PROXY 全部摘掉。
#   3) 无界面环境下凭据助手（GCM）会弹窗等待导致卡死 —— 必须禁用凭据交互。
#      远端 URL 里已内嵌 token（见 .git/config），所以禁用交互不影响鉴权。
#
# 大二进制包（截图等）可能随机断连，故每个远端默认重试 3 次。

set -uo pipefail

BRANCH="${BRANCH:-main}"
MAX_RETRY="${MAX_RETRY:-3}"
RETRY_SLEEP="${RETRY_SLEEP:-4}"

# 目标远端：名字 → 类型（gh=走代理 / dom=绕代理 / ssh=SSH 直连）
declare -A KIND=(
  [origin]=gh
  [gitee]=dom
  [cnb]=dom
  [gitcode]=ssh
)

ALL=(origin gitee cnb gitcode)

# 未指定则推全部；指定则只推给的这些（保持顺序）
if [ "$#" -gt 0 ]; then
  TARGETS=("$@")
else
  TARGETS=("${ALL[@]}")
fi

cd "$(git rev-parse --show-toplevel)" || exit 1

# ---- 前置检查 ----------------------------------------------------------------

if ! git rev-parse --verify --quiet HEAD >/dev/null; then
  echo "✗ 当前分支没有提交，无需推送"; exit 1
fi

LOCAL_SHA="$(git rev-parse HEAD)"
echo "本地 HEAD : ${LOCAL_SHA:0:7}  (分支 ${BRANCH})"

# 工作区是否干净（只提示，不阻断）
if [ -n "$(git status --porcelain)" ]; then
  echo "⚠ 工作区有未提交改动（不影响推送已提交内容）"
fi

# GitHub 走代理必须用 openssl TLS 后端；顺手固化
if git config http.sslBackend >/dev/null 2>&1; then :; else
  git config http.sslBackend openssl
fi

echo

# ---- 单远端推送（含重试） ----------------------------------------------------

push_one() {
  local name="$1" kind="${KIND[$1]:-dom}" attempt=0

  if ! git remote get-url "$name" >/dev/null 2>&1; then
    printf '%-8s ✗ 远端未配置，跳过\n' "$name"; return 1
  fi

  while [ "$attempt" -lt "$MAX_RETRY" ]; do
    attempt=$((attempt + 1))
    local out
    case "$kind" in
      gh)   # GitHub：保留代理 + openssl
            out=$(GIT_TERMINAL_PROMPT=0 git \
                    -c http.sslBackend=openssl \
                    push "$name" "$BRANCH:$BRANCH" 2>&1) ;;
      dom)  # 国内 HTTPS：摘掉所有代理 + 禁用凭据交互
            out=$(env -u http_proxy -u https_proxy -u HTTP_PROXY -u HTTPS_PROXY \
                    GIT_TERMINAL_PROMPT=0 GCM_INTERACTIVE=never git \
                    -c http.proxy= -c https.proxy= \
                    -c credential.helper= -c credential.interactive=false \
                    push "$name" "$BRANCH:$BRANCH" 2>&1) ;;
      ssh)  # SSH：不涉及 HTTP 代理
            out=$(GIT_TERMINAL_PROMPT=0 git push "$name" "$BRANCH:$BRANCH" 2>&1) ;;
    esac

    if [ $? -eq 0 ]; then
      printf '%-8s ✓ 已同步 %s\n' "$name" "${LOCAL_SHA:0:7}"
      return 0
    fi

    # 已是最新也是成功
    if printf '%s' "$out" | grep -q "Everything up-to-date"; then
      printf '%-8s ✓ 已是最新\n' "$name"; return 0
    fi

    if [ "$attempt" -lt "$MAX_RETRY" ]; then
      printf '%-8s … 第 %d 次失败，%ds 后重试\n' "$name" "$attempt" "$RETRY_SLEEP"
      sleep "$RETRY_SLEEP"
    else
      printf '%-8s ✗ 推送失败（已重试 %d 次）\n' "$name" "$MAX_RETRY"
      printf '%s\n' "$out" | tail -6 | sed 's/^/          | /'
      return 1
    fi
  done
}

# ---- 执行 --------------------------------------------------------------------

FAILED=()
for r in "${TARGETS[@]}"; do
  push_one "$r" || FAILED+=("$r")
done

# ---- 核验（远端 ref 是否 == 本地 HEAD） ---------------------------------------

echo
echo "---- 核验 ----"
for r in "${TARGETS[@]}"; do
  case "${KIND[$r]:-dom}" in
    gh)   remote_sha=$(timeout 45 git ls-remote --heads "$r" 2>/dev/null | awk '{print $1}' | head -1) ;;
    dom)  remote_sha=$(timeout 45 env -u http_proxy -u https_proxy -u HTTP_PROXY -u HTTPS_PROXY \
                        GIT_TERMINAL_PROMPT=0 git -c http.proxy= -c https.proxy= \
                        -c credential.helper= ls-remote --heads "$r" 2>/dev/null | awk '{print $1}' | head -1) ;;
    ssh)  remote_sha=$(timeout 45 git ls-remote --heads "$r" 2>/dev/null | awk '{print $1}' | head -1) ;;
  esac
  if [ "$remote_sha" = "$LOCAL_SHA" ]; then
    printf '%-8s ✓ 远端 = 本地 (%s)\n' "$r" "${LOCAL_SHA:0:7}"
  else
    printf '%-8s ✗ 远端 %s ≠ 本地 %s\n' "$r" "${remote_sha:0:7}" "${LOCAL_SHA:0:7}"
    FAILED+=("$r")
  fi
done

echo
if [ "${#FAILED[@]}" -eq 0 ]; then
  echo "✅ 全部远端已同步到 ${LOCAL_SHA:0:7}"
  exit 0
else
  echo "❌ 以下远端未同步：${FAILED[*]}"
  exit 1
fi
