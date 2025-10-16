from sqlmodel import Session, select
from app.question.model import Company, InterviewQuestion
from app.interview.model import Grade
from app.interview.dto.interview_dto import (
    InterviewStartResponse,
    InterviewQuestionItem,
    EvaluationRequest,
    EvaluationResponse,
    EvaluationBatchRequest,
    EvaluationBatchResponse,
    QuestionType,
    TailQuestionResponse
)
import google.generativeai as genai
import os
import json
import re


class InterviewService:
    def __init__(self, session: Session):
        self.session = session
        # Gemini API 설정
        api_key = os.getenv("GEMINI_API_KEY")
        if api_key:
            genai.configure(api_key=api_key)

    def start_interview(self, company_id: int) -> InterviewStartResponse:
        """회사의 컬처핏을 기반으로 AI가 생성한 면접 질문으로 면접 시작"""

        # 회사 정보 조회
        company = self.session.get(Company, company_id)
        if not company:
            raise ValueError("Company not found")

        # 해당 회사의 기존 면접 질문 조회
        statement = select(InterviewQuestion).where(InterviewQuestion.company_id == company_id)
        existing_questions = self.session.exec(statement).all()

        # 예시 질문 준비
        example_questions = []
        for q in existing_questions[:10]:  # 최대 10개의 예시 사용
            if q.question:
                example_questions.append({
                    "question": q.question,
                    "category": q.category or "General"
                })

        # Gemini를 사용하여 질문 생성
        try:
            generated_questions = self._generate_questions_with_gemini(
                company_name=company.name,
                culture_fit=company.culture_fit or "",
                example_questions=example_questions
            )
        except Exception as e:
            # Fallback: Gemini 실패 시 기존 질문 사용
            print(f"Gemini API error: {e}")
            if not existing_questions:
                raise ValueError("No interview questions available")

            import random
            selected = random.sample(existing_questions, min(5, len(existing_questions)))
            generated_questions = [
                {"question": q.question or "", "category": q.category or "General"}
                for q in selected
            ]

        # 응답 형식으로 변환
        question_items = [
            InterviewQuestionItem(
                question=q["question"]
            )
            for idx, q in enumerate(generated_questions)
        ]

        return InterviewStartResponse(
            company_id=company.id,
            questions=question_items
        )

    def _generate_questions_with_gemini(
        self,
        company_name: str,
        culture_fit: str,
        example_questions: list
    ) -> list:
        """Gemini API를 사용하여 면접 질문 생성"""

        # 예시 질문 텍스트 준비
        examples_text = "\n".join([
            f"- [{q['category']}] {q['question']}"
            for q in example_questions[:5]
        ])

        # 프롬프트 생성
        prompt = f"""당신은 면접관입니다. 다음 회사에 대한 면접 질문 5개를 생성해주세요.

회사명: {company_name}
회사 문화/특징: {culture_fit}

기존 질문 예시:
{examples_text}

요구사항:
1. 총 5개의 질문을 생성하세요
2. 회사의 문화와 특징을 고려하세요
3. 다양한 카테고리(기술, 인성, 경험, 지원동기 등)를 포함하세요
4. 질문은 간결하고 핵심만 물어야 합니다
5. 불필요한 설명이나 배경 설명 없이 직접적으로 물어보세요
6. 지나치게 친절하거나 장황한 표현은 피하세요

다음 JSON 형식으로만 응답하세요:
[
  {{"question": "질문 내용", "category": "카테고리"}},
  {{"question": "질문 내용", "category": "카테고리"}},
  ...
]
"""

        # Gemini API 호출 (최신 모델 사용)
        model = genai.GenerativeModel('gemini-2.5-flash')
        response = model.generate_content(prompt)

        # 응답 파싱
        response_text = response.text.strip()

        # JSON 추출 (마크다운 코드 블록 처리)
        json_match = re.search(r'```json\s*(.*?)\s*```', response_text, re.DOTALL)
        if json_match:
            response_text = json_match.group(1)
        else:
            # JSON 배열 직접 찾기
            json_match = re.search(r'\[.*\]', response_text, re.DOTALL)
            if json_match:
                response_text = json_match.group(0)

        # JSON 파싱
        questions = json.loads(response_text)

        # 검증 및 5개로 제한
        if not isinstance(questions, list):
            raise ValueError("Invalid response format from Gemini")

        return questions[:5]


    def evaluate_answers_batch(
        self,
        batch_request: EvaluationBatchRequest,
        user_id: int
    ) -> EvaluationBatchResponse:
        """면접 답변 5개를 종합적으로 평가하고 저장"""

        # 질문과 답변 개수가 동일한지 검증
        if len(batch_request.question) != len(batch_request.answer):
            raise ValueError("question과 answer의 개수가 일치해야 합니다.")
        
        # 최소 5개 이상 필요
        if len(batch_request.question) < 5:
            raise ValueError("최소 5개 이상의 질문과 답변이 필요합니다.")

        # 회사 컬처핏 조회
        company = self.session.get(Company, batch_request.company_id)
        if not company:
            raise ValueError("Company not found")

        try:
            # Gemini로 종합 평가 수행
            overall_result = self._evaluate_overall_with_gemini(
                company_name=company.name,
                culture_fit=company.culture_fit or "",
                questions=batch_request.question,
                answers=batch_request.answer
            )
        except Exception as e:
            print(f"Gemini API error: {e}")
            overall_result = {
                "score": 3,
                "feedback": "평가를 일시적으로 수행할 수 없습니다.",
                "overall_evaluation": "평가 대기 중입니다.",
                "improvements": "다시 시도해주세요."
            }

        # 데이터베이스에 저장
        grade = Grade(
            user_id=user_id,
            company_id=batch_request.company_id,
            value=float(overall_result.get("score", 3)),
            evaluation=overall_result.get("overall_evaluation", "")
        )

        self.session.add(grade)
        self.session.flush()

        # Feedback과 Strength 여러 개 저장
        from app.interview.model import Feedback, Strength

        feedbacks = overall_result.get("feedback", [])
        if isinstance(feedbacks, str):
            feedbacks = [feedbacks]

        for fb_text in feedbacks:
            feedback = Feedback(
                grade_id=grade.id,
                text=fb_text
            )
            self.session.add(feedback)

        strengths = overall_result.get("strength", [])
        if isinstance(strengths, str):
            strengths = [strengths]

        for st_text in strengths:
            strength = Strength(
                grade_id=grade.id,
                text=st_text
            )
            self.session.add(strength)

        self.session.commit()

        from app.user.model import User
        user = self.session.get(User, user_id)
        if user:
            user.star_count += overall_result.get("star_count", 0)
            self.session.add(user)
            self.session.commit()

        # 응답 구성
        from app.interview.dto.interview_dto import OverallEvaluationResult

        return EvaluationBatchResponse(
            company_id=batch_request.company_id,
            evaluations=[],  # 기존 호환성 유지
            result=OverallEvaluationResult(
                score=int(overall_result.get("score", 3)),
                feedback=feedbacks if isinstance(feedbacks, list) else [feedbacks],
                overall_evaluation=overall_result.get("overall_evaluation", ""),
                strength=strengths if isinstance(strengths, list) else [strengths]
            )
        )

    def _evaluate_overall_with_gemini(
        self,
        company_name: str,
        culture_fit: str,
        questions: list[str],
        answers: list[str]
    ) -> dict:
        """Gemini API로 면접 질문/답변에 대한 종합 평가 (기본 질문 5개 + 꼬리질문 포함)"""

        # 기본 질문과 꼬리질문 분리
        main_qa_pairs = []
        tail_qa_pairs = []
        
        for i, (q, a) in enumerate(zip(questions, answers)):
            if q.startswith("tail_"):
                # 꼬리질문
                original_q = q.replace("tail_", "", 1)
                tail_qa_pairs.append(f"  - 꼬리질문: {original_q} / 답변: {a}")
            else:
                # 기본 질문
                main_qa_pairs.append(f"질문 {len(main_qa_pairs)+1}: {q} / 답변 {len(main_qa_pairs)+1}: {a}")

        # 기본 질문 텍스트
        main_text = "\n\n".join(main_qa_pairs)
        
        # 꼬리질문 텍스트 (있을 경우만)
        tail_text = ""
        if tail_qa_pairs:
            tail_text = "\n\n[추가 꼬리질문과 답변]\n" + "\n\n".join(tail_qa_pairs)

        prompt = f"""너는 AI 면접 평가자이다.
다음 회사의 컬처핏을 기반으로 지원자의 면접 질문/답변을 종합적으로 평가하라.
지원자는 고등학교 졸업예정자이다.

회사명: {company_name}
회사 컬처핏/가치: {culture_fit}

[기본 면접 질문과 답변]
{main_text}{tail_text}

평가 지침:
1. 기본 질문 5개의 답변을 중심으로 종합 평가를 수행
2. 꼬리질문이 있다면, 해당 답변은 기본 질문에 대한 보충 설명으로 간주하여 함께 평가
3. 질문이 "tail_"로 시작하는 경우 이는 이전 질문에 대한 꼬리질문임
4. 고등학생 수준을 고려하여 평가 (전문 경력자 기준 적용 X)

요구사항:
1. 모든 답변을 종합하여 하나의 평가를 작성
2. score: 1~5 사이의 종합 점수 (회사 컬처핏 적합도 기준)
3. feedback: 피드백을 문자열 배열로 2-3개 제공
4. overall_evaluation: 2-3문장으로 전체적인 평가
5. strength: 강점이나 개선사항을 문자열 배열로 2-3개 제공

반드시 아래 JSON 형식으로만 응답하라:
{{
  "score": 1~5 사이의 정수,
  "feedback": ["피드백1", "피드백2"],
  "overall_evaluation": "전체적인 평가 2-3문장",
  "strength": ["강점/개선사항1", "강점/개선사항2"]
}}
"""

        model = genai.GenerativeModel('gemini-2.5-flash')
        response = model.generate_content(prompt)

        response_text = response.text.strip()

        json_match = re.search(r'```json\s*(.*?)\s*```', response_text, re.DOTALL)
        if json_match:
            response_text = json_match.group(1)
        else:
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if json_match:
                response_text = json_match.group(0)

        evaluation_data = json.loads(response_text)

        return evaluation_data

    def generate_tail_question(
        self,
        company_id: int,
        question: str,
        answer: str
    ) -> TailQuestionResponse:
        """답변을 분석하여 필요한 경우에만 꼬리질문 생성"""

        # 회사 컬처핏 조회
        company = self.session.get(Company, company_id)
        if not company:
            raise ValueError("Company not found")

        try:
            tail_question_result = self._generate_tail_question_with_gemini(
                company_name=company.name,
                culture_fit=company.culture_fit or "",
                question=question,
                answer=answer
            )
        except Exception as e:
            print(f"Gemini API error: {e}")
            tail_question_result = {"question": ""}

        return TailQuestionResponse(
            question=tail_question_result.get("question", "")
        )

    def _generate_tail_question_with_gemini(
        self,
        company_name: str,
        culture_fit: str,
        question: str,
        answer: str
    ) -> dict:
        """Gemini API로 꼬리질문 생성 (필요할 때만)"""

        prompt = f"""너는 AI 면접관이다.
지원자의 답변을 분석하여 꼬리질문이 필요한지 판단하고, 필요한 경우에만 추가 질문을 생성하라.

회사명: {company_name}
회사 컬처핏/가치: {culture_fit}

면접 질문: {question}
지원자 답변: {answer}

꼬리질문 생성 기준:
1. 답변이 모호하거나 구체성이 부족한 경우
2. 더 깊이 있는 설명이 필요한 경우
3. 답변에서 언급된 경험이나 역량을 확인하고 싶은 경우
4. 회사 컬처핏과 관련하여 추가 검증이 필요한 경우

꼬리질문이 불필요한 경우:
1. 답변이 이미 충분히 구체적이고 명확한 경우
2. 질문의 의도에 완벽히 부합하는 답변을 한 경우
3. 더 이상 물어볼 것이 없는 경우

반드시 아래 JSON 형식으로만 응답하라:
{{
  "question": "꼬리질문 내용 (불필요하면 빈 문자열 \\"\\")"
}}

중요: 꼬리질문은 간결하고 직접적으로 작성하라. 불필요한 설명 없이 핵심만 물어라.
"""

        model = genai.GenerativeModel('gemini-2.5-flash')
        response = model.generate_content(prompt)

        response_text = response.text.strip()

        json_match = re.search(r'```json\s*(.*?)\s*```', response_text, re.DOTALL)
        if json_match:
            response_text = json_match.group(1)
        else:
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if json_match:
                response_text = json_match.group(0)

        tail_question_data = json.loads(response_text)
        return tail_question_data

    def get_interview_progress(self, user_id: int, company_id: int) -> EvaluationBatchResponse:
        """면접 진행 상황 조회"""
        company = self.session.get(Company, company_id)
        if not company:
            raise ValueError("Company not found")

        # 유저 id와 회사 id로 Grade 조회
        statement = select(Grade).where(Grade.user_id == user_id).where(Grade.company_id == company_id)
        grades = self.session.exec(statement).all()

        if not grades:
            # 아직 평가가 없는 경우
            raise ValueError("No interview evaluations found for this user and company")

        # 가장 최근 평가 가져오기
        latest_grade = grades[-1]
        
        # Feedback과 Strength 조회
        from app.interview.model import Feedback, Strength
        from app.interview.dto.interview_dto import OverallEvaluationResult
        
        feedback_statement = select(Feedback).where(Feedback.grade_id == latest_grade.id)
        feedbacks = self.session.exec(feedback_statement).all()
        
        strength_statement = select(Strength).where(Strength.grade_id == latest_grade.id)
        strengths = self.session.exec(strength_statement).all()

        return EvaluationBatchResponse(
            company_id=company_id,
            evaluations=[],
            result=OverallEvaluationResult(
                score=int(latest_grade.value),
                feedback=[f.text for f in feedbacks] if feedbacks else [],
                overall_evaluation=latest_grade.evaluation or "",
                strength=[s.text for s in strengths] if strengths else []
            )
        )
