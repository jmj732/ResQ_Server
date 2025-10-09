# AGENT.md — Interview Evaluation Orchestrator (Gemini 기반)

이 문서는 **면접 평가 에이전트**가 해야 할 일을 한 파일로 정의합니다.  
에이전트는 기존 API와 DB 스키마를 사용해 **질문 제공 → 답변 수집 → AI 평가 저장 → 진행도 관리**를 수행합니다.

---

## 0) 핵심 목표

1. **질문 제공**: 회사/세션/후보자 기준으로, 아직 평가되지 않은 질문을 **순서대로** 반환.  
2. **AI 평가 저장**: 후보자의 답변을 **Gemini**로 평가하고, 결과를 `grade`/`grade_item`에 저장.  
3. **재개/중복 방지**: 이미 평가(진행·완료)가 존재하면 **이어하기/요약 반환**. 중복 저장 금지(멱등성).  
4. **진행도/보상**: 세션 완료 시 `progress`(별자리) 업데이트 이벤트 발행.

> 회사는 이미 존재하고(예: 핀다=1, 달파=2, 더스팟=3), 질문도 미리 등록되어 있다고 가정합니다.

---

## 1) 환경 변수 / 외부 의존성

- `GEMINI_BASE_URL` : Gemini 평가 마이크로서비스 주소 (예: `http://localhost:8000`)
  - `/ai/evaluate`, `/ai/follow-up` 사용 (JSON Structured Output).
- `DB_*` : 애플리케이션 DB 연결 정보.
- `JWT_SECRET` : 인증 토큰 검증 시 사용(선택).

---

## 2) 데이터 모델 매핑 (요지)

- **question(company_id, year, category, body)**: 질문 마스터.  
- **template_question(template_id, question_id, position, weight)**: 질문 순서/가중치.  
- **interview_session(session_id, company_id, candidate_id, grader_id, template_id, status)**: 세션 메타.  
- **grade(session_id, candidate_id, grader_id, value, evaluation)**: 요약(평균점/총평).  
- **grade_item(grade_id, question_id, score, comment, position)**: **문항별 점수/코멘트(원천 데이터)**.  
- **progress(user_id, company_id, cleared_stages, is_completed, stars JSON)**: 별자리/진행도.

---

## 3) 요청 처리 플로우 (의사코드)

### 3.1 질문 리스트 제공 (GET /interview)
입력: `{ "company_id": <int>, "user_id": "<uid>" }`

```
ensure_session(user_id, company_id):
  # 1) 미완료 세션 찾기
  sess = SELECT * FROM interview_session
         WHERE company_id=? AND candidate_id=? AND status IN ('READY','RUNNING')
         ORDER BY id DESC LIMIT 1;
  if not sess:
     # 템플릿 선택(회사별 최신/활성)
     tpl = SELECT id FROM question_template
           WHERE company_id=? AND is_active=1 ORDER BY id DESC LIMIT 1;
     create sess(status='READY', template_id=tpl.id)

  # 2) 이 세션에서 이미 평가된 문항 조회
  answered_qids = SELECT gi.question_id
                  FROM grade g JOIN grade_item gi ON gi.grade_id=g.id
                  WHERE g.session_id=sess.id AND g.candidate_id=user_id;

  # 3) 템플릿 순서대로 다음 질문 찾기
  next_q = SELECT q.id, q.body, tq.position
           FROM template_question tq JOIN question q ON q.id=tq.question_id
           WHERE tq.template_id=sess.template_id
           AND q.id NOT IN answered_qids
           ORDER BY tq.position ASC
           LIMIT 1;

  if next_q exists:
    return { "status": "IN_PROGRESS", "question": next_q.body, "question_id": next_q.id, "position": next_q.position, "session_id": sess.id }

  else:
    # 모든 문항 완료 → 요약/진행도 반환
    summary = SELECT value, evaluation FROM grade
              WHERE session_id=sess.id AND candidate_id=user_id
              ORDER BY id DESC LIMIT 1;
    return { "status": "COMPLETED", "summary": summary, "session_id": sess.id }
```

> **포인트**: 회사에 대한 평과가 **있는지/없는지** 확인하여,  
> - 있으면 **다음 질문** 또는 **완료 요약**을 반환,  
> - 없으면 새 세션을 만들고 **첫 질문**을 반환.

### 3.2 답변 제출 및 평가 (POST /interview)
입력 예:
```json
{
  "company_id": 1,
  "user_id": "dohun",
  "question_id": 44,
  "answer_text": "…",
  "answer_audio_url": null,
  "type": "기술"  // 인성/기술/프로젝트
}
```

의사코드:
```
1) 세션 확인: ensure_session(user_id, company_id) -> sess
2) 멱등성 체크:
   already = SELECT 1 FROM grade g JOIN grade_item gi ON gi.grade_id=g.id
             WHERE g.session_id=sess.id AND g.candidate_id=? AND gi.question_id=?;
   if already: return { saved: true, duplicate: true }

3) 평가 요청 (Gemini):
   POST {GEMINI_BASE_URL}/ai/evaluate
     body: { "type": <type>, "question": <question body>, "answer": <answer_text> }
   -> resp: { type, scores{logic,emotion,specific,time}, feedback{...}, overall, improve_one }

4) DB 저장 트랜잭션:
   a) grade upsert:
      g = SELECT * FROM grade WHERE session_id=? AND candidate_id=? FOR UPDATE;
      if not g: INSERT grade (session_id, candidate_id, value=0, evaluation="") RETURNING id
   b) INSERT grade_item(grade_id, question_id, score=가중합/혹은 logic 중심, comment=overall or feedback.specific, position)
   c) grade.value 재계산(평균):
      UPDATE grade SET value = (
        SELECT ROUND(AVG(score),2) FROM grade_item WHERE grade_id=grade.id
      ), evaluation = resp.overall;
   d) 커밋

5) 다음 질문 탐색:
   next = find_next_question(sess)
   if next:
      return { "saved": true, "next_question_id": next.id, "next": next.body }
   else:
      # 세션 완주 → 진행도/별자리 업데이트
      mark_progress(user_id, company_id)
      return { "saved": true, "completed": true, "summary": { "avg": grade.value, "overall": grade.evaluation } }
```

> 점수 산정 규칙은 간단히 `score = round( (w_logic*logic + w_emotion*emotion + w_specific*specific + w_time*time)/sum(w), 2 )` 를 권장.  
> 유형별 가중치(예):  
> - 인성: emotion 0.4, logic 0.3, specific 0.2, time 0.1  
> - 기술: logic 0.4, specific 0.3, emotion 0.2, time 0.1  
> - 프로젝트: specific 0.4, logic 0.3, emotion 0.2, time 0.1

---

## 4) 에이전트 인터페이스 (핵심 엔드포인트 프로토콜)

### 4.1 질문 받아오기 (`GET /interview`)
- **입력**: `{ "company_id": <int>, "user_id": "<uid>" }`
- **출력 (진행 중)**:
```json
{
  "status": "IN_PROGRESS",
  "session_id": 9001,
  "question_id": 44,
  "position": 3,
  "question": "질문 본문",
  "has_prev_evaluation": true
}
```
- **출력 (완료)**:
```json
{
  "status": "COMPLETED",
  "session_id": 9001,
  "summary": { "avg": 4.10, "overall": "핵심을 잘 짚었다." },
  "has_prev_evaluation": true
}
```

### 4.2 답변 제출 (`POST /interview`)
- **입력**: 상단 3.2 예시 참고  
- **출력 (다음 질문 존재)**:
```json
{
  "saved": true,
  "duplicate": false,
  "next_question_id": 45,
  "next": "다음 질문 본문"
}
```
- **출력 (세션 완료)**:
```json
{
  "saved": true,
  "completed": true,
  "summary": { "avg": 3.95, "overall": "경험이 명확함" }
}
```

### 4.3 꼬리 질문 (`GET /interview/taile`)
- 내부에서 Gemini `/ai/follow-up` 호출:
```json
POST {GEMINI_BASE_URL}/ai/follow-up
{
  "type": "기술",
  "question": "원 질문",
  "answer": "후보 답변",
  "n": 2
}
→ { "followUps": ["구체적 예시는?", "장단점 비교해보면?"] }
```

---

## 5) SQL 스니펫 (PostgreSQL/MySQL 공통 개념)

### 5.1 회사/사용자 기준 평가 존재 여부
```sql
SELECT COUNT(*) AS cnt
FROM grade g
JOIN interview_session s ON s.id = g.session_id
WHERE s.company_id = :companyId
  AND g.candidate_id = :userId;
```

### 5.2 다음 질문 조회
```sql
SELECT q.id, q.body, tq.position
FROM template_question tq
JOIN question q ON q.id = tq.question_id
WHERE tq.template_id = :templateId
  AND q.id NOT IN (
    SELECT gi.question_id
    FROM grade g
    JOIN grade_item gi ON gi.grade_id = g.id
    WHERE g.session_id = :sessionId
      AND g.candidate_id = :userId
  )
ORDER BY tq.position ASC
LIMIT 1;
```

### 5.3 grade upsert & 평균 업데이트 (개념)
```sql
-- (1) grade 확보
SELECT id FROM grade WHERE session_id=:sid AND candidate_id=:uid FOR UPDATE;
-- 없으면 INSERT

-- (2) grade_item 삽입
INSERT INTO grade_item(grade_id, question_id, score, comment, position)
VALUES (:gid, :qid, :score, :comment, :position);

-- (3) 평균/총평 업데이트
UPDATE grade
SET value = (SELECT ROUND(AVG(score), 2) FROM grade_item WHERE grade_id = :gid),
    evaluation = :overall
WHERE id = :gid;
```

---

## 6) 에러/멱등/동시성 규칙

- **멱등성 키**: `(session_id, candidate_id, question_id)` 중복 삽입 금지  
  → `UNIQUE KEY uq_gi (grade_id, question_id)` 권장.
- **동시 요청**: `grade` 행을 **FOR UPDATE** 로 잠그고 갱신(평균 재계산 경쟁 방지).
- **타임아웃**: Gemini 응답 지연 시 3초 타임아웃, 429/5xx는 2회 지수 백오프.
- **검증**: `type`은 인성/기술/프로젝트 중 하나, 점수는 1~5 정수(JSON 스키마 강제).
- **보안**: XSS 필터(텍스트만 저장), 오디오 URL은 인증된 스토리지 경로만 허용.

---

## 7) 상태 전이 (세션)

```
READY ──(start)──> RUNNING ──(모든 질문 완료)──> DONE
                     │
                     ├─(중단/오류)→ FAILED
                     └─(운석 이벤트)→ RUNNING(시간 패널티 적용)
```

---

## 8) 테스트 시나리오 (간단)

1) 도훈 유저가 더스팟(3)을 선택하고 로그인.  
2) `GET /interview {company_id:3, user_id:"dohun"}` → 첫 질문/세션 생성.  
3) `POST /interview {question_id, answer_text, type}` → Gemini 평가 → 저장.  
4) 2~3 반복 → 모든 질문 완료 시 `COMPLETED` + summary 반환.  
5) 동일 요청 재시도 → **중복 저장 없이** 다음 질문 또는 완료 상태 유지.

---

## 9) 관측/로그

- 요청/응답 JSON, 평가 점수, 경과시간(ms) 로깅.  
- 에러: Gemini 실패/DB Deadlock/스키마 검증 실패 분류.  
- 메트릭: 질문당 평균 평가 시간, 세션 완료율, 평균 점수 분포.

---

## 10) 확장 아이디어

- **임기응변 모드**: 운석 이벤트 시 `/ai/follow-up`으로 즉석 꼬리질문 전환.  
- **평가자 편향 탐지**: grader_id 기준 분포/편차 대시보드.  
- **난이도 추정**: 문항 평균점 낮을수록 난이도↑ → 질문 셔플/가중치 조정.

---

## 11) 예제 응답 합본 (프론트 연동 샘플)

### 질문 요청 응답
```json
{
  "status": "IN_PROGRESS",
  "session_id": 9102,
  "question_id": 77,
  "position": 1,
  "question": "트랜잭션 전파 옵션을 설명해 주세요.",
  "has_prev_evaluation": false
}
```

### 답변 제출 후 응답 (다음 질문)
```json
{
  "saved": true,
  "duplicate": false,
  "next_question_id": 78,
  "next": "동일 트랜잭션에서 Checked/Unchecked 예외 처리 차이는?"
}
```

### 완료 후 응답
```json
{
  "saved": true,
  "completed": true,
  "summary": { "avg": 4.12, "overall": "핵심을 명확히 설명함" }
}
```

---

## 12) 구현 체크리스트

- [ ] `ensure_session()` / `find_next_question()` 유틸 구현  
- [ ] Gemini 평가 마이크로서비스 베이스 URL 주입  
- [ ] `grade_item` UNIQUE 제약, 트랜잭션/락 처리  
- [ ] API 스펙과 응답 키 **영문/한글** 혼용 최소화(일관성 유지)  
- [ ] 통합 로그/메트릭 대시보드 기초