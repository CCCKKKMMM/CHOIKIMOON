# Security Editor Agent

## 개요
- **이름**: Security Editor
- **슬래시 커맨드**: `/security-editor`
- **목적**: 코드 보안 취약점 탐지 → 테스트 작성 → 수정 (TDD 방식)
- **기준**: OWASP Top 10
- **출력**: `report/security_report_YYYYMMDD_HHMMSS.md`

## 커맨드 파일 위치
`.claude/commands/security-editor.md`

## 사용법
```
/security-editor                         # 현재 디렉토리 전체 분석
/security-editor Database_Design/rag/    # 특정 폴더 분석
/security-editor Database_Design/rag/config.py  # 특정 파일 분석
```

## 작업 흐름 (TDD)
1. 코드 분석 → 취약점 분류 (Critical/High/Medium/Low)
2. 보안 테스트 코드 작성 (Red)
3. 취약점 수정 (Green)
4. 테스트 통과 확인
5. `report/` 에 보고서 저장

## 탐지 항목 (OWASP Top 10)
| # | 항목 | 예시 |
|---|------|------|
| 1 | Injection | SQL/Command/LDAP 인젝션 |
| 2 | Broken Authentication | 세션, 토큰 취약점 |
| 3 | Sensitive Data Exposure | API 키, 비밀번호 평문 |
| 4 | XXE | XML 외부 엔티티 |
| 5 | Broken Access Control | 권한 우회 |
| 6 | Security Misconfiguration | 잘못된 설정값 |
| 7 | XSS | 크로스 사이트 스크립팅 |
| 8 | Insecure Deserialization | 안전하지 않은 역직렬화 |
| 9 | Known Vulnerabilities | 취약한 의존성 |
| 10 | Insufficient Logging | 로깅 부재 |

## 생성 일자
2026-03-09
