#!/usr/bin/env python3
"""
index.html에 있는 모든 외부 링크(https://)를 실제로 접속해서 살아있는지 확인하는 스크립트.

이 스크립트는 반드시 "본인 컴퓨터"에서 실행해야 합니다 — Claude가 작업하는
샌드박스 환경은 외부 도메인 접속이 정책상 차단돼 있어서(egress proxy), 여기서는
이 점검을 할 수 없습니다.

사용법:
    pip install requests
    python3 scripts/check_links.py

결과:
    - 터미널에 요약(정상/의심/실패 개수)
    - link_check_report.csv 파일에 전체 결과 저장(URL, 상태코드, 비고)

구글맵 검색 링크(google.com/maps, google.com/search)는 검색어가 틀려도 검색
결과 화면 자체는 항상 뜨기 때문에("낮은 위험") 기본적으로 건너뜁니다.
전체를 다 확인하려면 --all 옵션을 쓰세요.
"""
import csv
import re
import sys
import time
from pathlib import Path

try:
    import requests
except ImportError:
    print("requests 모듈이 필요합니다: pip install requests")
    sys.exit(1)

HERE = Path(__file__).resolve().parent
INDEX_HTML = HERE.parent / "index.html"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"
}
TIMEOUT = 12
SLEEP_BETWEEN = 0.3  # 서버에 예의상 약간의 텀을 둠


def extract_links(html_path: Path, include_low_risk: bool):
    text = html_path.read_text(encoding="utf-8")
    urls = re.findall(r'href="(https://[^"]+)"', text)
    seen = set()
    result = []
    for u in urls:
        if u in seen:
            continue
        seen.add(u)
        is_low_risk = ("google.com/maps" in u) or ("google.com/search" in u)
        if is_low_risk and not include_low_risk:
            continue
        result.append(u)
    return result


def check_url(url: str):
    try:
        r = requests.head(url, headers=HEADERS, timeout=TIMEOUT, allow_redirects=True)
        if r.status_code >= 400 or r.status_code == 405:
            # 일부 사이트는 HEAD를 막아두므로 GET으로 재시도
            r = requests.get(url, headers=HEADERS, timeout=TIMEOUT, allow_redirects=True, stream=True)
        return r.status_code, r.url
    except requests.exceptions.SSLError as e:
        return "SSL_ERROR", str(e)[:120]
    except requests.exceptions.ConnectTimeout:
        return "TIMEOUT", ""
    except requests.exceptions.ConnectionError as e:
        return "CONN_ERROR", str(e)[:120]
    except Exception as e:
        return "ERROR", str(e)[:120]


def main():
    include_low_risk = "--all" in sys.argv
    if not INDEX_HTML.exists():
        print(f"index.html을 찾을 수 없습니다: {INDEX_HTML}")
        sys.exit(1)

    links = extract_links(INDEX_HTML, include_low_risk)
    print(f"점검할 링크: {len(links)}개"
          + ("" if include_low_risk else " (구글맵 검색 링크 397개는 낮은 위험으로 제외 — 전체 포함하려면 --all)"))
    print()

    rows = []
    ok, warn, fail = 0, 0, 0
    for i, url in enumerate(links, 1):
        status, extra = check_url(url)
        if isinstance(status, int) and status < 400:
            tag = "OK"
            ok += 1
        elif isinstance(status, int) and status < 500:
            tag = "WARN"  # 401/403/404 등 — 봇 차단일 수도, 진짜 죽은 링크일 수도
            warn += 1
        else:
            tag = "FAIL"
            fail += 1
        rows.append({"url": url, "status": status, "tag": tag, "note": extra})
        print(f"[{i}/{len(links)}] {tag:5} {status!s:12} {url}")
        time.sleep(SLEEP_BETWEEN)

    out_path = HERE.parent / "link_check_report.csv"
    with out_path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["url", "status", "tag", "note"])
        w.writeheader()
        w.writerows(rows)

    print()
    print(f"완료: OK {ok} · WARN {warn}(진짜 문제인지 직접 확인 필요, 일부 사이트는 봇 접속을 403으로 막음) · FAIL {fail}")
    print(f"전체 결과: {out_path}")


if __name__ == "__main__":
    main()
