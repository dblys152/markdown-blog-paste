# Cloud Run 배포 설정

`cloud-run.env`는 Cloud Run Service의 비민감 운영 설정을 관리합니다. 비밀번호와
암호화 키는 이 파일에 넣지 않고 Secret Manager에서 관리합니다.
실제 파일에는 이메일 주소와 OAuth Client ID 같은 환경별 값이 있으므로 Git에서 제외하고,
placeholder만 있는 example 파일을 커밋합니다.

운영 로그 레벨은 `LOG_LEVEL=INFO`를 기본값으로 사용합니다. 장애 분석을 위해 일시적으로
`DEBUG`로 낮출 수 있지만 요청 본문, 인증 토큰, 비밀번호와 이메일 원문은 어떤 레벨에서도
기록하지 않습니다.

최초 한 번 example을 복사하고 실제 운영값을 입력합니다.

```bash
cp deploy/cloud-run.env.example deploy/cloud-run.env
```

## 필요한 Secret

배포 전에 다음 Secret이 존재해야 합니다.

```text
md2blog-database-url
md2blog-jwt-secret-key
md2blog-smtp-password
md2blog-outbox-token-encryption-key
```

API Service 실행 서비스 계정에는 참조하는 Secret에 대한
`roles/secretmanager.secretAccessor` 권한이 필요합니다.

SMTP Secret이 없다면 최초 한 번 생성하고 Gmail 앱 비밀번호를 새 버전으로 추가합니다.

```bash
gcloud secrets create md2blog-smtp-password \
  --replication-policy automatic \
  --project md2blog-505805

gcloud secrets versions add md2blog-smtp-password \
  --data-file=- \
  --project md2blog-505805
```

실행 서비스 계정에는 필요한 Secret만 허용합니다.

```bash
gcloud secrets add-iam-policy-binding md2blog-outbox-token-encryption-key \
  --member serviceAccount:md2blog-api@md2blog-505805.iam.gserviceaccount.com \
  --role roles/secretmanager.secretAccessor \
  --project md2blog-505805

gcloud secrets add-iam-policy-binding md2blog-smtp-password \
  --member serviceAccount:md2blog-api@md2blog-505805.iam.gserviceaccount.com \
  --role roles/secretmanager.secretAccessor \
  --project md2blog-505805
```

## 배포

백엔드 디렉터리에서 실행합니다.

```bash
./deploy/deploy-cloud-run.sh
```

스크립트는 다음 순서로 동작합니다.

1. 필요한 Secret의 존재 여부를 확인합니다.
2. DB, JWT, SMTP, Outbox 암호화 Secret을 Service에 연결합니다.
3. `md2blog-api`를 소스에서 배포합니다.

Outbox 재처리와 만료된 휴지통 정리는 FastAPI 프로세스의 내부 Scheduler가 수행합니다.
인스턴스 시작 시 누락 작업을 즉시 확인하므로 비활성 기간에 정해진 실행 시각을 놓쳐도
다음 활성화 시 처리합니다.

내부 Scheduler 배포와 동작을 확인한 뒤 기존 Cloud Scheduler와 Cloud Run Job은 제거할
수 있습니다.

```bash
gcloud scheduler jobs delete md2blog-purge-expired-pages-daily \
  --project md2blog-505805 \
  --location asia-southeast1

gcloud run jobs delete md2blog-purge-expired-pages \
  --project md2blog-505805 \
  --region asia-southeast1

gcloud run jobs delete md2blog-process-outbox \
  --project md2blog-505805 \
  --region asia-southeast1
```
