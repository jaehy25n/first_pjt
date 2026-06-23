import os
import json
import requests
from django.conf import settings
from accounts.models import ReadingLog, BookPreference
from books.models import Book

def get_similar_books(target_candidate, all_candidates, book_map):
    """같은 KDC 앞자리(주제)를 공유하는 다른 후보 도서 2권을 찾습니다."""
    similar = []
    target_kdc_prefix = str(target_candidate.get('kdc_code', ''))[:1]
    
    for c in all_candidates:
        if c['isbn13'] != target_candidate['isbn13']:
            kdc_prefix = str(c.get('kdc_code', ''))[:1]
            if kdc_prefix == target_kdc_prefix:
                book_obj = book_map.get(c['isbn13'])
                cover_url = book_obj.cover_url if book_obj else ""
                similar.append({
                    "isbn13": c['isbn13'],
                    "title": c['title'],
                    "author": c['author'],
                    "cover_url": cover_url
                })
            if len(similar) >= 2:
                break
    return similar

def fallback_selection(candidates, limit, book_map):
    """GMS 호출 실패/타임아웃 시 데이터 랭킹(순서)대로 반환하는 폴백 로직"""
    out = []
    seen = set()
    for c in candidates:
        if c['isbn13'] in seen:
            continue
        seen.add(c['isbn13'])
        
        book_obj = book_map.get(c['isbn13'])
        cover_url = book_obj.cover_url if book_obj else ""
        
        reason = c.get('signal', "관심사 및 인기 대출 기록을 바탕으로 추천해 드립니다.")
        
        out.append({
            "isbn13": c['isbn13'],
            "title": c['title'],
            "author": c['author'],
            "cover_url": cover_url,
            "reason": reason,
            "availability": {
                "library_name": c.get('library_name', ''),
                "status": "available"
            },
            "similar": get_similar_books(c, candidates, book_map),
            "order_note": None,
        })
        
        if len(out) >= limit:
            break
            
    for i, item in enumerate(out, 1):
        item['rank'] = i
        
    return out


def _is_grounded(reason, cand):
    """이유가 구체 근거(어느 좋아한 책의 이웃인지)를 짚는지 검사.
    via_title이 있는데 그 제목을 안 짚는 막연한 상투어면 False → 규칙 이유로 교체."""
    r = (reason or '').strip()
    if len(r) < 8:
        return False
    via = cand.get('via_title')
    if via:
        key = via.split(' :')[0].split('(')[0].strip()
        return bool(key) and key in r
    return True


def select_with_reasons(candidates, profile, limit=5, seed_isbn13=None):
    """
    미니스펙 Phase 4: GMS(LLM)을 이용한 최종 N권 선별 및 이유 생성
    """
    if not candidates:
        return []
        
    # 후보에 쓰인 모든 책 정보를 한 번에 미리 가져옴 (커버 이미지 등 필요)
    isbn_list = [c['isbn13'] for c in candidates]
    books = Book.objects.filter(isbn13__in=isbn_list)
    book_map = {b.isbn13: b for b in books}
        
    GMS_URL = os.getenv('GMS_URL', 'https://gms.ssafy.io/gmsapi/api.openai.com/v1')
    GMS_KEY = os.getenv('GMS_KEY')
    GMS_MODEL = os.getenv('GMS_MODEL', 'gpt-5-nano')
    
    if not GMS_KEY:
        print("GMS_KEY is missing. Using fallback.")
        return fallback_selection(candidates, limit, book_map)
        
    system_prompt = """너는 공공도서관 사서야. 사용자에게 '다음에 읽을 책'을 추천해.
규칙:
1) 반드시 아래 [후보 목록]에 있는 책 중에서만 고른다. 목록에 없는 책은 절대 언급하지 않는다.
2) 각 추천 이유(1~2문장, 한국어)는 그 후보의 [신호](예: 사용자가 좋아한 책과 함께 대출됨)를 **구체적으로 인용**한다. 좋아한 책 제목을 직접 언급해라. "흥미롭습니다/좋은 책입니다" 같은 막연한 칭찬만 쓰지 않는다. 사용자가 '별로'라고 한 책이 있으면 그와 어떻게 다른지 대조해도 좋다.
3) 후보의 KDC가 800번대(문학)면 비슷한 분위기·주제의 read-alike 이유만 쓴다.
4) 800번대가 아니면(비문학·학습형) order_note에 '입문→심화' 관점 한 줄을 덧붙인다. 문학이면 order_note는 null.
5) 출력은 지정한 JSON만. 책은 후보 '번호(n)'로 가리킨다."""

    interests_str = ", ".join([i.name for i in profile.interests.all()])
    recent_book_str = ""
    
    if seed_isbn13:
        recent_log = ReadingLog.objects.filter(user=profile.user, book__isbn13=seed_isbn13).select_related('book').first()
        if recent_log:
            recent_book_str = f"- 방금 완독한 책: 《{recent_log.book.title}》({recent_log.book.author})\n"

    disliked_titles = list(Book.objects.filter(
        isbn13__in=BookPreference.objects.filter(user=profile.user, sentiment='dislike').values_list('book_id', flat=True)
    ).values_list('title', flat=True))
    disliked_str = ("- 별로라고 한 책: " + ", ".join(disliked_titles) + "\n") if disliked_titles else ""

    candidates_str = ""
    candidates_by_n = {}
    for c in candidates:
        n = c['n']
        candidates_by_n[n] = c
        candidates_str += f"{n}. {c['title']} / {c['author']} / {c.get('kdc_code', '')} / {c.get('signal', '')}\n"
        
    user_prompt = f"""[사용자]
- 관심사: {{{interests_str}}}
{recent_book_str}{disliked_str}
[후보 목록]  (n. 제목 / 저자 / KDC / 신호)
{candidates_str}
[지시] 위 후보 중 {limit}권을 골라 아래 JSON으로만 답해.
{{"picks":[{{"n":1,"reason":"한국어 1~2문장","order_note":null}}]}}
- n은 후보 번호. order_note는 비문학일 때만 한 줄, 문학이면 null."""

    try:
        headers = {
            "Authorization": f"Bearer {GMS_KEY}",
            "Content-Type": "application/json"
        }
        data = {
            "model": GMS_MODEL,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            "temperature": 0.3,
            "response_format": {"type": "json_object"}
        }
        
        response = requests.post(f"{GMS_URL}/chat/completions", headers=headers, json=data, timeout=12)
        response.raise_for_status()
        result_json = response.json()
        
        content = result_json['choices'][0]['message']['content']
        parsed = json.loads(content)
        picks = parsed.get('picks', [])
        
    except Exception as e:
        print("GMS Request failed or parse error:", e)
        # 예외 발생 시 규칙 기반 추천(데이터 점수순)으로 폴백
        return fallback_selection(candidates, limit, book_map)
        
    # 후처리 (환각 차단, 포맷팅)
    out = []
    seen = set()
    
    for p in picks:
        n = p.get('n')
        c = candidates_by_n.get(n)
        
        # 1. 환각 차단: 목록에 없는 n을 반환하면 무시
        if not c:
            continue 
            
        # 2. 중복 차단
        if c['isbn13'] in seen:
            continue 
            
        seen.add(c['isbn13'])
        book_obj = book_map.get(c['isbn13'])
        cover_url = book_obj.cover_url if book_obj else ""
        
        # 3. 비문학 order_note 처리
        order_note = None
        if not str(c.get('kdc_code', '')).startswith("8"):
            order_note = p.get('order_note')
            
        reason = p.get('reason') or ''
        if not _is_grounded(reason, c):
            reason = c.get('signal') or "도서관 대출 기록을 바탕으로 추천합니다."

        out.append({
            "isbn13": c['isbn13'],
            "title": c['title'],
            "author": c['author'],
            "cover_url": cover_url,
            "reason": reason,
            "availability": {
                "library_name": c.get('library_name', ''),
                "status": "available"
            },
            "similar": get_similar_books(c, candidates, book_map),
            "order_note": order_note,
        })
        
        if len(out) >= limit:
            break
            
    # LLM이 N권을 채우지 못했을 경우 랭킹순으로 채움 (백필)
    if len(out) < limit:
        remaining_candidates = [c for c in candidates if c['isbn13'] not in seen]
        needed = limit - len(out)
        out.extend(fallback_selection(remaining_candidates, needed, book_map))
        
    # 랭크 부여
    for i, item in enumerate(out, 1):
        item['rank'] = i
        
    return out
