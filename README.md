# trip-graph-rescue

항공 지연, 공급자 취소, 날씨, 현지 이슈처럼 복수 여행 구성요소에 영향을 줄 수 있는 사건을 합성 데이터로 분석하는 Codex 플러그인 MVP

## 문제 정의

마이리얼트립처럼 항공·숙소·투어·교통 등 복수 여행 구성요소를 조합하는 플랫폼에서 고난도 예외 상황이 발생하면 운영자는 시간·위치·선후행·명시 정책을 함께 검토해야 함

이 프로젝트는 자동 환불이나 자동 재예약을 하지 않음
사람이 승인해야 할 판단을 더 빠르게 준비하도록 영향 범위와 제약을 구조화함

## 공개 근거와 해석 경계

- [마이리얼트립 소개](https://about.myrealtrip.com/)는 항공·숙소·투어·액티비티·이동을 다루는 여행 플랫폼이라고 설명함
- [마이팩 회고](https://blog.myrealtrip.com/mypack-product-retrospective/)는 항공·숙소·투어·교통 등 여행 요소의 조합과 일정 변경·조건 조정의 영향 범위를 설명함
- [AICX 사례](https://blog.myrealtrip.com/aicx-cs-automation-75k-monthly/)는 구조화된 CS 자동화와 현지 이슈·분쟁성 클레임·안전 이슈의 사람 응대 경계를 설명함
- 이 근거는 마이리얼트립에 여행 그래프 도구가 없다는 증거가 아님
- 따라서 본 프로젝트는 해결 실패 주장이 아니라 사람 승인형 운영 판단 보조 기회를 검증하는 합성 MVP임

## 실행

```bash
python scripts/analyze_trip.py fixtures/paris_flight_delay.json
python -m unittest discover -s tests -v
```

## 데모 fixture

- 인천→파리 항공편이 14:00 도착 예정에서 5시간 지연돼 19:00 도착
- 공항→호텔 최소 이동 시간은 60분
- 호텔 체크인 뒤 첫날 투어 집결지까지 최소 이동 시간은 35분
- 첫날 투어 집결 시각은 18:00
- 계산 결과 투어에 가장 빨리 도착 가능한 시각은 20:35이므로 기존 투어는 제외
- 숙소 late check-in 정책은 확인 필요로 표시

## 안전 경계

- 입력은 합성·비식별 JSON만 허용
- 외부 항공·재고·가격·환불·예약·메시지 API를 호출하지 않음
- 환불, 재예약, 고객 발송은 모두 금지된 자동 액션으로 출력
- 안전, 분쟁, 현지 이슈는 운영 리드 또는 안전 담당자 승인을 요구
- 비어 있는 시간, 위치, 정책 데이터를 LLM 추정으로 채우지 않음

## 구조

```text
.codex-plugin/plugin.json
skills/trip-graph-rescue/SKILL.md
trip_graph_rescue/analyzer.py
scripts/analyze_trip.py
fixtures/paris_flight_delay.json
tests/test_analyzer.py
```

## 근거 → 기능 → 테스트

| 근거 또는 제약 | 기능 | 테스트 |
| --- | --- | --- |
| 여행 구성요소 조합과 일정 변경 영향 범위 | 의존성 그래프를 따라 지연 전파 | `test_delay_propagates_to_transfer_checkin_and_first_day_tour` |
| 시간·위치·선후행은 코드 계산 | 19:00 도착 + 60분 이동 + 35분 이동으로 20:35 계산 | `test_first_day_tour_is_unavailable_with_explicit_time_evidence` |
| 정책 누락은 자동 결론 금지 | late check-in 확인 상태와 상담사 승인 | `test_late_checkin_missing_policy_requires_counselor_confirmation` |
| 불가능한 대안 강제 추천 금지 | 기존 18:00 투어를 제외하고 시간 충족 후보만 표시 | `test_only_non_conflicting_alternatives_are_candidates` |
| 자동 실행 금지 | 금지된 액션 목록을 명시 | `test_output_has_no_execution_capability` |
| 안전·분쟁·현지 이슈는 사람 응대 | 안전 이벤트에 사람 승인 gate 추가 | `test_safety_event_always_adds_human_approval` |

## 현재 한계

- 실제 마이리얼트립 운영 시스템과 연결하지 않음
- 실제 여행 운영에서 이 도구가 비어 있는 공백을 증명하지 않음
- 실제 공급자 정책과 재고를 조회하지 않음
