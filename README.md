# 책잇다

공공도서관 대출 데이터 기반 도서 추천 웹 서비스.
<<<<<<< HEAD
<<<<<<< HEAD
**"책과 도서관, 그리고 당신을 잇다"** — 취향에 맞는 *다음 책*을, 내 주변 도서관에서 **지금 빌릴 수 있는지** 지도로 함께 보여준다.

## 기술 스택
- **Backend**: Django 5 · Django REST Framework · dj-rest-auth(Token 인증) · SQLite
- **Frontend**: Vue 3 · Vite · Pinia · Vue Router · Bootstrap 5 · Leaflet(지도)
- **Data/AI**: 도서관 정보나루 · 알라딘 · 네이버 도서 API · SSAFY GMS(LLM 추천·임베딩)

---

## 빠른 시작 (git clone 후 사전작업)

### 0. 사전 설치 (PC마다 한 번)
Git · **Python 3.11+** · **Node.js LTS** — 설치 확인: `python --version`, `node --version`.

### 1. 클론
```bash
git clone https://github.com/jaehy25n/first_pjt.git
cd first_pjt
```

### 2. 백엔드 (first_pjt 폴더에서)
```bash
# 1) 가상환경
python -m venv venv
.\venv\Scripts\Activate.ps1        # mac·Linux: source venv/bin/activate
#    줄 앞에 (venv) 가 붙으면 성공

# 2) 패키지
pip install -r requirements.txt

# 3) 환경변수 — .env 만들고 값 채우기 (아래 '환경변수' 표 참고)
copy .env.example .env             # mac·Linux: cp .env.example .env

# 4) DB 준비 (db.sqlite3 는 git에 없음 → 직접 생성·적재)
python manage.py migrate
python manage.py loaddata interests seed embeddings   # 관심사·책(2153)·도서관(355)·소장·대출신호·임베딩
python manage.py createsuperuser                       # (선택) 관리자 계정

# 5) 실행
python manage.py runserver
```

### 3. 프론트엔드 (새 터미널, first_pjt/frontend 폴더에서)
```bash
cd frontend
npm install
npm run dev      # → http://localhost:5173
```
백엔드(8000)와 프론트(5173)는 **각각 다른 터미널**에서 동시에 띄운다.

---

## 환경변수 (.env)
| 키 | 필수 | 용도 |
|---|:---:|---|
| `DJANGO_SECRET_KEY` | ✅ | Django 시크릿. 생성: `python -c "import secrets;print(secrets.token_urlsafe(50))"` |
| `DJANGO_DEBUG` | – | `True`/`False` (기본 `False`) |
| `LIBRARY_API_KEY` | 권장 | 정보나루 — 책 상세 지도/가용성 실시간 조회. 없으면 '상태 미확인'으로 폴백(앱은 동작) |
| `GMS_KEY` / `GMS_URL` / `GMS_MODEL` | 권장 | SSAFY GMS — LLM 추천. 없으면 인기순 폴백 |
| `ALADIN_TTB_KEY` · `NAVER_CLIENT_ID/SECRET` | 수집 시 | 카탈로그·메타 수집 스크립트용. **앱 실행엔 불필요** |

> ⚠️ `.env`는 절대 git/채팅에 올리지 말 것.

---

## 데이터(fixtures)
커밋된 fixtures는 **현재 카탈로그 전체**입니다 — 책 **2,153권** · 서울 **355개관** · 대출/베스트셀러 신호 · 책 임베딩(2026-06-25 동결). 위 `loaddata interests seed embeddings` 한 번이면 전부 적재됩니다.

> 데이터를 새로 수집·가공해 갱신하면(`scripts/` · `load_*` 관리명령), 작업 DB에서 `python manage.py dumpdata …`로 `seed.json`·`embeddings.json`을 다시 동결해 커밋하세요.

---

## 자주 나는 오류
- `'python'/'node' 인식 안 됨` → 재설치(PATH 체크) 후 터미널 새로 열기.
- venv가 안 켜짐(PowerShell) → `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned` 후 재시도.
- `No module named ...` → venv 켰는지(`(venv)`) + `pip install -r requirements.txt`.
- 프론트 `CORS/Network Error` → 백엔드 서버가 켜져 있는지 확인.
- `port 8000 already in use` → 기존 서버 종료 또는 `runserver 8001`.

## 협업
- `main` 보호, 기능별 `feature/*` 브랜치 → Pull Request 리뷰 후 머지.
=======

## 기술 스택
- Backend: Django 5, Django REST Framework, dj-rest-auth, SQLite
- Frontend: Vue 3, Vite, Pinia, Vue Router, Bootstrap 5, Leaflet
- Data/AI: 정보나루, 알라딘, 네이버 도서 API, SSAFY GMS

## 실행 방법

### 백엔드
```
python -m venv venv
.\venv\Scripts\Activate.ps1          # mac/Linux: source venv/bin/activate
pip install -r requirements.txt
copy .env.example .env               # mac/Linux: cp .env.example .env  (값 입력)
python manage.py migrate
python manage.py loaddata interests seed embeddings
python manage.py runserver
```
관리자/데모 계정(선택): `python manage.py createsuperuser`, `python manage.py seed_demo` (demo / demo1234)

### 프론트엔드
```
cd frontend
npm install
npm run dev
```

## 환경변수
`.env.example`를 `.env`로 복사해 채운다. `DJANGO_SECRET_KEY`는 필수이고, `LIBRARY_API_KEY`(도서관 가용성)·`GMS_*`(LLM 추천)는 없으면 폴백으로 동작한다.

## 데이터
`fixtures/seed.json`, `fixtures/embeddings.json`에 카탈로그(책 2,153 / 도서관 355)와 임베딩이 들어 있어 `loaddata`로 적재된다.

## 협업
`main` 보호, 기능별 `feature/*` 브랜치 → Pull Request 머지.
>>>>>>> ab6f5ceef0359848ed99b9b63857f186b621d237
=======

## 기술 스택
- Backend: Django 5, Django REST Framework, dj-rest-auth, SQLite
- Frontend: Vue 3, Vite, Pinia, Vue Router, Bootstrap 5, Leaflet
- Data/AI: 정보나루, 알라딘, 네이버 도서 API, SSAFY GMS

## 실행 방법

### 백엔드
```
python -m venv venv
.\venv\Scripts\Activate.ps1          # mac/Linux: source venv/bin/activate
pip install -r requirements.txt
copy .env.example .env               # mac/Linux: cp .env.example .env  (값 입력)
python manage.py migrate
python manage.py loaddata interests seed embeddings
python manage.py runserver
```
관리자/데모 계정(선택): `python manage.py createsuperuser`, `python manage.py seed_demo` (demo / demo1234)

### 프론트엔드
```
cd frontend
npm install
npm run dev
```

## 환경변수
`.env.example`를 `.env`로 복사해 채운다. `DJANGO_SECRET_KEY`는 필수이고, `LIBRARY_API_KEY`(도서관 가용성)·`GMS_*`(LLM 추천)는 없으면 폴백으로 동작한다.

## 데이터
`fixtures/seed.json`, `fixtures/embeddings.json`에 카탈로그(책 2,153 / 도서관 355)와 임베딩이 들어 있어 `loaddata`로 적재된다.

## 협업
`main` 보호, 기능별 `feature/*` 브랜치 → Pull Request 머지.
>>>>>>> ab6f5ceef0359848ed99b9b63857f186b621d237
