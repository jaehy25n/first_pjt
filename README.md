# 책잇다

공공도서관 대출 데이터 기반 도서 추천 웹 서비스.

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
