from sqlmodel import SQLModel
from typing import List
from enum import Enum


class QuestionType(str, Enum):
    """질문 유형"""
    PERSONALITY = "인성"
    TECHNICAL = "기술"
    PROJECT = "프로젝트"


class InterviewStartRequest(SQLModel):
    """Request to start an interview with a company"""
    company_id: int


class InterviewQuestionItem(SQLModel):
    """Individual interview question"""
    question: str


class InterviewStartResponse(SQLModel):
    """Response with generated interview questions"""
    company_id : int
    questions: List[InterviewQuestionItem]


class EvaluationRequest(SQLModel):
    """면접 답변 평가 요청"""
    company_id: int  # 회사 ID
    question_type: QuestionType
    question: str
    answer: str


class EvaluationResponse(SQLModel):
    """면접 답변 컬처핏 기반 간단 평가 결과"""
    evaluation_id: int  # 평가 ID
    score: int  # 1~5 단일 점수
    feedback: str  # 간단 피드백



class EvaluationBatchRequest(SQLModel):
    """면접 답변 5개 일괄 평가 요청"""
    company_id: int
    question: List[str]  # 5개의 질문
    answer: List[str]  # 5개의 답변


class OverallEvaluationResult(SQLModel):
    """종합 평가 결과"""
    score: int  # 1~5 종합 점수
    feedback: List[str]  # 피드백 리스트
    overall_evaluation: str  # 전체적인 평가
    strength: List[str]  # 강점/개선사항 리스트


class EvaluationBatchResponse(SQLModel):
    """면접 답변 일괄 평가 결과"""
    company_id: int
    result: OverallEvaluationResult  # 새로운 종합 평가


class TailQuestionResponse(SQLModel):
    """꼬리질문 응답"""
    question: str  # 꼬리질문 (필요 없으면 빈 문자열)
