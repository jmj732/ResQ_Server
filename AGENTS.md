# Repository Guidelines

## 프로젝트 구조 & 모듈 구성
- `main.py`: FastAPI 진입점. 라우터 등록, `create_db_and_tables()` 호출.
- `app/`: 도메인 패키지
  - `auth/`, `user/`, `question/`, `interview/`, `common/`
  - 패턴: `api/*_controller.py`(APIRouter `router`), `application/*_service.py`(비즈니스 로직), `dto/*.py`(요청/응답), `model.py`(SQLModel 테이블)
  - `app/database.py`: SQLModel 엔진/세션. `.env`의 `DATABASE_URL` 사용
- `test_app.py`: 예시 스크립트(테스트 사용자 생성 등)

## 빌드 · 테스트 · 로컬 실행
- 환경 설정: `cp .env.example .env`
  - 예: `DATABASE_URL=sqlite:///./interview.db`, `SECRET_KEY=changeme`, `ALGORITHM=HS256`
- 실행(핫리로드): `uvicorn main:app --reload`
  - 대안: `python main.py`
- 초기화/시드(선택): `python test_app.py`
- 문서: 실행 후 `/docs` 접속

## 코딩 스타일 & 네이밍
- Python 3.x, PEP 8, 4칸 들여쓰기, 필요 시 타입 힌트
- 네이밍: 패키지/모듈 `snake_case`, 클래스 `PascalCase`, 함수/변수 `snake_case`
- DTO는 `Request`/`Response` 접미사 사용(예: `LoginRequest`)
- 컨트롤러는 얇게 유지, 로직은 `application/*_service.py`에 배치

## 테스트 가이드
- 현재는 `test_app.py`만 포함. 테스트 추가 시 `pytest` 권장
- 위치/이름: `tests/test_*.py`
- 서비스 레이어 커버리지 우선. `app.database`의 `Session(engine)` 사용, 임시 DB로 격리
- 실행 예: `pytest -q`(pytest 도입 시)

## 커밋 & PR 가이드
- 짧고 명령형 메시지 권장. Conventional Commits 권장
  - 예: `feat(auth): add login endpoint`, `fix(db): rollback on error`
- PR 포함 사항: 목적/요약, 관련 이슈, 재현/테스트 방법, 로그/스크린샷

## 보안 & 설정 팁
- 비밀정보 커밋 금지. `.env`는 git‑ignore 대상
- 강한 `SECRET_KEY` 설정 및 주기적 교체
- 쿠키는 `secure=True`. 프로덕션은 HTTPS 필수. 로컬 HTTP에서는 리프레시 쿠키 전송이 제한될 수 있어 본문 액세스 토큰으로 개발/검증

