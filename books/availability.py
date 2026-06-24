"""정보나루 온디맨드 (⑦c·⑧, D33) — 가용성(bookExist/libSrchByBook) + 이용분석(usageAnalysisList). 런타임 lazy + Holding TTL 캐시.

화면에 보이는 소수 책 × 선택 도서관만 bookExist로 확인하고, Holding을 snapshot_at TTL로
재사용(반복호출·throttle 방지). 책 상세는 libSrchByBook(region=11)로 서울 소장관 목록.
호출 실패/throttle 시 조용히 폴백(갱신 생략 = 기존 캐시 유지 / 없으면 '확인 불가').

엔드포인트 스펙(실측 2026-06-24):
  bookExist     {authKey, libCode, isbn13, format} → response.result.{hasBook,loanAvailable} (Y/N)
  libSrchByBook {authKey, isbn,  region,  format} → response.libs[].lib.{libCode,libName,address,latitude,longitude,...}
  ※ 파라미터명 주의: bookExist=isbn13, libSrchByBook=isbn
"""
import math
import os
from datetime import timedelta

import requests
from django.utils import timezone

from .models import Holding, Library

BOOK_EXIST_URL = "http://data4library.kr/api/bookExist"
LIB_BY_BOOK_URL = "http://data4library.kr/api/libSrchByBook"
USAGE_URL = "http://data4library.kr/api/usageAnalysisList"

HOLDING_TTL = timedelta(hours=6)      # 이보다 오래된 Holding만 재조회 (데모용·조절 가능)
MAX_CALLS_PER_REQUEST = 20            # 한 요청에서 bookExist 최대 호출 수 (지연·throttle 방어)


def _get(url, params, timeout=8):
    """정보나루 GET → response(dict). 키 없음/HTTP·본문 에러/throttle이면 None(조용히 폴백)."""
    key = os.environ.get("LIBRARY_API_KEY")
    if not key:
        return None
    try:
        r = requests.get(url, params={**params, "authKey": key, "format": "json"}, timeout=timeout)
        r.raise_for_status()
        data = r.json()
        resp = data.get("response", {}) if isinstance(data, dict) else {}
        if isinstance(resp, dict) and not resp.get("error"):
            return resp
    except (requests.exceptions.RequestException, ValueError):
        pass
    return None


def refresh_holdings(isbns, libraries, ttl=HOLDING_TTL):
    """보여줄 책(isbns) × 선택 도서관(libraries)의 Holding을 TTL 기준으로 갱신(upsert).
    최근 snapshot_at(<ttl)인 조합은 호출 생략, 미보유/만료분만 bookExist 1콜씩(상한 적용).
    호출부는 이후 Holding을 다시 읽으면 됨. 실패분은 건너뜀(기존 값/없음 유지 = 폴백)."""
    isbns = [i for i in isbns if i]
    if not isbns or not libraries:
        return
    fresh_after = timezone.now() - ttl
    fresh = set(
        Holding.objects
        .filter(library__in=libraries, book_id__in=isbns, snapshot_at__gte=fresh_after)
        .values_list('library_id', 'book_id')
    )
    calls = 0
    for lib in libraries:
        for isbn in isbns:
            if (lib.id, isbn) in fresh:
                continue
            if calls >= MAX_CALLS_PER_REQUEST:
                return
            resp = _get(BOOK_EXIST_URL, {"libCode": lib.lib_code, "isbn13": isbn})
            calls += 1
            if resp is None:
                continue  # 실패 → 기존 Holding 유지(또는 없음). 배지는 폴백.
            result = resp.get("result", {})
            Holding.objects.update_or_create(
                library=lib, book_id=isbn,
                defaults={
                    "has_book": result.get("hasBook") == "Y",
                    "loan_available": result.get("loanAvailable") == "Y",
                },
            )


def badge_map(isbns, libraries):
    """보여줄 책 × 선택 도서관의 가용성 배지 {isbn: {'library_name','status'}}.
    status: available(대출가능) > loaned(소장·대출중) > none(미소장). 도서관 미선택이면 {}(→배지 null).
    build_candidates와 같은 어휘·우선순위 (D33). refresh_holdings 직후 호출하면 fresh 값."""
    if not isbns or not libraries:
        return {}
    held = {}
    for h in (Holding.objects
              .filter(library__in=libraries, book_id__in=isbns, has_book=True)
              .select_related('library')):
        rank = 2 if h.loan_available else 1
        cur = held.get(h.book_id)
        if not cur or rank > cur[0]:
            held[h.book_id] = (rank, h.library.name)
    out = {}
    for isbn in isbns:
        if isbn in held:
            rank, name = held[isbn]
            out[isbn] = {"library_name": name, "status": "available" if rank == 2 else "loaned"}
        else:
            out[isbn] = {"library_name": "", "status": "none"}
    return out


def libs_for_book(isbn, region="11", page_size=400):
    """책 1권의 (서울) 소장 도서관 목록 — libSrchByBook. [{lib_code,name,address,latitude,longitude}] · 실패 시 [].
    libSrchByBook 기본 pageSize=10에 잘리므로 page_size를 크게 줘 전 소장관을 1콜로 받는다(서울 도서관 총 ~355곳).
    페이지 수만 늘 뿐 호출 횟수는 책당 1콜 유지(쿼터 영향 없음)."""
    if not isbn:
        return []
    resp = _get(LIB_BY_BOOK_URL, {"isbn": isbn, "region": region, "pageSize": page_size})
    if not resp:
        return []
    out = []
    for item in resp.get("libs", []) or []:
        lib = item.get("lib", {}) if isinstance(item, dict) else {}
        out.append({
            "lib_code": lib.get("libCode"),
            "name": lib.get("libName"),
            "address": lib.get("address"),
            "latitude": lib.get("latitude"),
            "longitude": lib.get("longitude"),
        })
    return out


def book_usage(isbn):
    """책 1권의 이용분석(usageAnalysisList) — 연관 키워드 + 월별 대출 추이 (+ 연령·성별, 있으면).
    ⑧(D33 정보나루 B): 책 상세에서 lazy 1콜. 실패/빈값이면 빈 구조. ※ usageAnalysisList는 isbn13 파라미터."""
    empty = {"keywords": [], "loan_history": [], "loan_groups": []}
    if not isbn:
        return empty
    resp = _get(USAGE_URL, {"isbn13": isbn})
    if not resp:
        return empty

    keywords = []
    for item in resp.get("keywords", []) or []:
        k = item.get("keyword", {}) if isinstance(item, dict) else {}
        word = (k.get("word") or "").strip()
        if not word:
            continue
        try:
            weight = float(k.get("weight") or 0)
        except (TypeError, ValueError):
            weight = 0.0
        keywords.append({"word": word, "weight": weight})
    keywords.sort(key=lambda x: x["weight"], reverse=True)
    keywords = keywords[:20]

    loan_history = []
    for item in resp.get("loanHistory", []) or []:
        lo = item.get("loan", {}) if isinstance(item, dict) else {}
        month = lo.get("month")
        if not month:
            continue
        try:
            cnt = int(lo.get("loanCnt") or 0)
        except (TypeError, ValueError):
            cnt = 0
        loan_history.append({"month": month, "loanCnt": cnt})

    loan_groups = []
    for item in resp.get("loanGrps", []) or []:
        g = item.get("loanGrp", item) if isinstance(item, dict) else {}
        loan_groups.append({
            "age": g.get("age"),
            "gender": g.get("gender"),
            "loan_count": g.get("loanCnt"),
        })

    return {"keywords": keywords, "loan_history": loan_history, "loan_groups": loan_groups}


def _haversine(la1, lo1, la2, lo2):
    """두 좌표 간 거리(km)."""
    R = 6371.0
    p1, p2 = math.radians(la1), math.radians(la2)
    dphi = math.radians(la2 - la1)
    dlmb = math.radians(lo2 - lo1)
    a = math.sin(dphi / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dlmb / 2) ** 2
    return 2 * R * math.asin(math.sqrt(a))


def _to_float(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def borrow_map(isbn, lat=None, lng=None, live_n=8, gray_n=30):
    """책 상세 '빌릴 수 있는 도서관' 지도용 (D36).
    소장관(libSrchByBook) + 내 위치 가까운 N개관 live 상태 + 인근 미소장(회색).
    status: available(대출가능)·loaned(대출중)·held_unknown(소장·상태미확인)·none(미소장).
    외부호출 = libSrchByBook 1콜 + bookExist 최대 live_n콜(가까운 소장관만, throttle 방어 = D33③).
    위치(lat/lng) 없으면 live 0 → 소장관 전부 held_unknown(내 위치 줄 때만 색칠)."""
    has_location = lat is not None and lng is not None
    live_n = max(0, min(live_n, MAX_CALLS_PER_REQUEST))

    # 1) 서울 소장관 + 좌표 (libSrchByBook 1콜). 일단 전부 held_unknown.
    holding, holding_codes = [], set()
    for lib in libs_for_book(isbn):
        code = lib.get("lib_code")
        la, lo = _to_float(lib.get("latitude")), _to_float(lib.get("longitude"))
        holding_codes.add(code)
        dist = round(_haversine(lat, lng, la, lo), 2) if (has_location and la is not None and lo is not None) else None
        holding.append({
            "lib_code": code, "name": lib.get("name"), "address": lib.get("address"),
            "latitude": la, "longitude": lo, "distance_km": dist,
            "has_book": True, "status": "held_unknown",
        })

    # 2) 내 위치 가까운 N개관만 bookExist live → available/loaned (실패 시 held_unknown 유지)
    live_checked = 0
    if has_location and live_n:
        checkable = sorted((h for h in holding if h["distance_km"] is not None), key=lambda h: h["distance_km"])
        for h in checkable[:live_n]:
            resp = _get(BOOK_EXIST_URL, {"libCode": h["lib_code"], "isbn13": isbn})
            live_checked += 1
            if resp is None:
                continue
            result = resp.get("result", {})
            if result.get("hasBook") == "Y":
                h["status"] = "available" if result.get("loanAvailable") == "Y" else "loaned"
            else:  # 소장 목록엔 있으나 실시간으론 미소장 → 회색
                h["has_book"], h["status"] = False, "none"

    # 3) 회색(미소장) = DB Library 355 중 소장관 제외, 내 위치 가까운 gray_n (위치 있을 때만)
    gray = []
    if has_location and gray_n:
        for lib in (Library.objects
                    .filter(latitude__isnull=False, longitude__isnull=False)
                    .exclude(lib_code__in=holding_codes)):
            gray.append({
                "lib_code": lib.lib_code, "name": lib.name, "address": lib.address,
                "latitude": lib.latitude, "longitude": lib.longitude,
                "distance_km": round(_haversine(lat, lng, lib.latitude, lib.longitude), 2),
                "has_book": False, "status": "none",
            })
        gray.sort(key=lambda x: x["distance_km"])
        gray = gray[:gray_n]

    libraries = holding + gray
    libraries.sort(key=lambda x: (x["distance_km"] is None, x["distance_km"] or 0))
    return {
        "isbn13": isbn, "has_location": has_location,
        "holding_count": len(holding), "live_checked": live_checked,
        "libraries": libraries,
    }
