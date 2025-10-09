# API 명세 (통합본)

> 생성: 2025-09-25 04:47:26
> 통합 대상: 10개 파일 병합

## 목차
- [목차
- [로그인](#로그인)
- [질문 등록(단건)](#질문-등록-단건)
- [꼬리 질문 받아오기](#꼬리-질문-받아오기)
- [질문 받아오기](#질문-받아오기)
- [전체 질문 검색](#전체-질문-검색)
- [진행도 불러오기](#진행도-불러오기)
- [답변 제출](#답변-제출)
- [제목 없음](#제목-없음)
- [제목 없음](#제목-없음)
- [제목 없음](#제목-없음)



## 로그인](#로그인)
- [질문 등록(단건)](#질문-등록-단건)
- [꼬리 질문 받아오기](#꼬리-질문-받아오기)
- [질문 받아오기](#질문-받아오기)
- [전체 질문 검색](#전체-질문-검색)
- [진행도 불러오기](#진행도-불러오기)
- [답변 제출](#답변-제출)
- [질문 삭제](#질문-삭제)
- [질문 수정](#질문-수정)
- [질문 형식 파일 업로드](#질문-형식-파일-업로드)



## 목차
- [로그인](#로그인)
- [질문 등록(단건)](#질문-등록-단건)
- [꼬리 질문 받아오기](#꼬리-질문-받아오기)
- [질문 받아오기](#질문-받아오기)
- [전체 질문 검색](#전체-질문-검색)
- [진행도 불러오기](#진행도-불러오기)
- [답변 제출](#답변-제출)
- [제목 없음](#제목-없음)
- [제목 없음](#제목-없음)
- [제목 없음](#제목-없음)



## 로그인
<a id="로그인"></a>

### 로그인

HTTP 메서드: POST
URL: /login
domain: 인증
상태: 시작 전

설명

로그인을 진행합니다.

### Request

```json
{
	"user_id" : "dohun08",
	"password" : "q1w2e3"
}
```

### Response(200)

```json
{
	"message" : "로그인에 성공했습니다."
}
```



## 질문 등록(단건)
<a id="질문-등록-단건"></a>

### 질문 등록(단건)

HTTP 메서드: POST
URL: /question/addition
domain: 질문관리
상태: 시작 전

설명

질문 등록을 하나씩 하는 단건 질문등록 api

### Request

```json
{
	"category" : "Backend",
	"company_id" : 1,
	"question" : "여자친구 있나요?",
	"year" : "2025",
}
```

### Response(200)

```json
{
	"question_id" : 1
}
```



## 꼬리 질문 받아오기
<a id="꼬리-질문-받아오기"></a>

### 꼬리 질문 받아오기

HTTP 메서드: GET
URL: /interview/taile
domain: 면접
상태: 시작 전

설명

### Request

```json
{
	"company_id" : "핀다",
	"question" : "질문",
	"answer" : "답변",
}
```

### Response(200)

```json
{
	"question" : "질문2"
}
```



## 질문 받아오기
<a id="질문-받아오기"></a>

### 질문 받아오기

HTTP 메서드: GET
URL: /interview
domain: 면접
상태: 시작 전

설명

### Request

```json
{
	"company_id" : "핀다",
}
```

### Response(200)

```json
{
	"question" : "일반고 - 대학교 진학에 비해 마이스터고가 갖는 차별점 및 강점"
}
```



## 전체 질문 검색
<a id="전체-질문-검색"></a>

### 전체 질문 검색

HTTP 메서드: GET
URL: /question/search?company=&year=&category=
domain: 질문관리
상태: 시작 전

설명

### Request Param

| company | String |  |
| --- | --- | --- |
| year | Long |  |
| category | String |  |

```json
{

}
```

### Response(200)

```json
[
	{
		"question_id" : 1,
		"question" : "여자친구 있으신가요?",
		"company" : "더스팟",
		"year" : 2024,
		"category" : "Backend"
	},
	{
		"question_id" : 2,
		"question" : "여자친구 있으신가요?",
		"company" : "더스팟",
		"year" : 2024,
		"category" : "Backend"
	},
	{
		"question_id" : 3,
		"question" : "여자친구 있으신가요?",
		"company" : "더스팟",
		"year" : 2024,
		"category" : "Backend"
	},
	{
		"question_id" : 4,
		"question" : "여자친구 있으신가요?",
		"company" : "더스팟",
		"year" : 2024,
		"category" : "Backend"
	},
]
```



## 진행도 불러오기
<a id="진행도-불러오기"></a>

### 진행도 불러오기

HTTP 메서드: GET
URL: /progress
domain: 별자리
상태: 시작 전

설명

### Request

```json
{
	"user_id" : "dohun"
}
```

### Response(200)

```json
{
	"result" : 1
}
```

1 ~ 3까지



## 답변 제출
<a id="답변-제출"></a>

### 답변 제출

HTTP 메서드: POST
URL: /interview
domain: 면접
상태: 시작 전

설명

### Request

```json
{
	"company_id" : 1,
	"question" : ["", "", "", "", ""],
	"answer" : ["", "", "", "", ""]
}
```

### Response(200)

```json
{
	"result" : {
		"score" : 1,
		"feedback" : "졸라 못하시네요",
		"overall_evaluation" : "엄청 못하십니다"
		"improvements" : "다시태어나시죠"
	}
}
```



## 질문 삭제
<a id="질문-삭제"></a>

### 질문 삭제

HTTP 메서드: DELETE
URL: /question/delete
domain: 질문관리
상태: 시작 전

설명

### Request

```json
{
	"question_id" : 1
}
```

### Response(204)

```json
{ }
```


## 질문 수정
<a id="질문-수정"></a>

### 질문 수정

HTTP 메서드: PATCH
URL: /question/update
domain: 질문관리
상태: 시작 전

설명

### Request

```json
{
	"question_id" : 1,
	"content" : "바꾸는 내용"
}
```

### Response(204)

```json
{ }
```


## 질문 형식 파일 업로드
<a id="질문-형식-파일-업로드"></a>

### 질문 형식 파일 업로드

HTTP 메서드: POST
URL: /question/upload
domain: 질문관리
상태: 시작 전

### Request

form-data

| sheet | “구글 시트 파일” |  |
| --- | --- | --- |
|  |  |  |
|  |  |  |

```json
// 
```

### Response(200)

```json
{ }
```
