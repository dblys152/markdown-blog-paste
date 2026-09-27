# 운영 모니터링 정책

애플리케이션은 구조화된 JSON 로그와 상태 확인 API를 제공하고, 운영 환경은 이를 수집해
메트릭과 알림으로 연결합니다. 아래 값은 현재 트래픽 규모에서 시작할 초기 기준이며 실제
관측 결과에 따라 조정합니다.

## 관찰 신호

| 대상 | 신호 | 초기 알림 기준 |
|---|---|---|
| API 오류 | Cloud Run `request_count`의 5xx 응답 | 5분 동안 5건 이상 |
| API 지연 | Cloud Run `request_latencies`의 p95 | 요청이 있는 상태에서 10분 동안 2초 초과 |
| 인스턴스 시작 | Cloud Run `container/startup_latencies`와 Revision 오류 로그 | 시작 지연 p95 10초 초과 또는 시작 실패 1건 |
| Outbox | `outbox.message.failed` | `retry_count=5`인 최종 실패 1건 |
| 내부 Scheduler | `scheduler.job.failed`, `scheduler.job.missed` | 1건 |
| DB 연결 | `/health/database` | 외부 가용성 확인이 연속 2회 실패 |

낮은 트래픽에서는 비율 기반 5xx 알림이 한 건의 실패에도 과도하게 반응할 수 있으므로
초기에는 건수 기준을 사용합니다. 트래픽이 늘어나면 최소 요청 수 조건과 5xx 비율을 함께
적용합니다.

## 애플리케이션 로그 필터

Outbox가 재시도를 모두 소진한 경우:

```text
resource.type="cloud_run_revision"
resource.labels.service_name="md2blog-api"
jsonPayload.event="outbox.message.failed"
jsonPayload.retry_count=5
```

내부 Scheduler 실행 실패 또는 실행 누락:

```text
resource.type="cloud_run_revision"
resource.labels.service_name="md2blog-api"
(jsonPayload.event="scheduler.job.failed" OR jsonPayload.event="scheduler.job.missed")
```

이 두 사건은 발생 빈도를 관찰하는 지표가 아니라 즉시 확인해야 하는 희소 사건이므로
로그 기반 단건 알림으로 구성합니다. 요청 오류와 지연은 Cloud Run 기본 메트릭을 사용하며
별도의 사용자 정의 로그 기반 메트릭을 만들지 않습니다.

## Cloud Run 설정 순서

1. Cloud Monitoring에서 알림을 받을 이메일 등의 Notification Channel을 등록합니다.
2. Cloud Run 기본 메트릭으로 5xx, p95 지연과 시작 지연 알림을 생성합니다.
3. 위 필터로 Outbox와 Scheduler 로그 기반 알림을 생성합니다.
4. 알림을 테스트한 뒤 임계치, 평가 기간과 자동 종료 시간을 기록합니다.
5. 알림 발생 시 `trace_id`, `event`, Revision 이름을 기준으로 관련 로그를 조회합니다.

Cloud Run 완전 관리형 서비스는 기본적으로 Cloud Monitoring과 통합되며 요청 수, 요청
지연과 컨테이너 시작 지연 등의 기본 메트릭을 제공합니다. 사용자 정의 로그 기반 메트릭은
별도 비용이 발생할 수 있으므로 기본 메트릭이나 단건 로그 알림으로 해결할 수 없는 경우에만
도입합니다.

참고 문서:

- [Cloud Run 상태 및 성능 모니터링](https://docs.cloud.google.com/run/docs/monitoring)
- [Cloud Logging 로그 모니터링](https://docs.cloud.google.com/logging/docs/alerting/monitoring-logs)
- [로그 기반 알림 정책](https://docs.cloud.google.com/logging/docs/alerting/log-based-alerts)
