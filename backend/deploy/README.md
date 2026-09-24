# Cloud Run 배포 설정

`cloud-run.env`는 Cloud Run Service와 Outbox Job이 공유하는 비민감 운영 설정을
관리합니다. 비밀번호와 암호화 키는 이 파일에 넣지 않고 Secret Manager에서 관리합니다.
실제 파일에는 이메일 주소와 OAuth Client ID 같은 환경별 값이 있으므로 Git에서 제외하고,
placeholder만 있는 example 파일을 커밋합니다.

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

API Service와 Job의 실행 서비스 계정에는 자신이 참조하는 Secret에 대한
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
  --member serviceAccount:110854299603-compute@developer.gserviceaccount.com \
  --role roles/secretmanager.secretAccessor \
  --project md2blog-505805

gcloud secrets add-iam-policy-binding md2blog-outbox-token-encryption-key \
  --member serviceAccount:110854299603-compute@developer.gserviceaccount.com \
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
2. `md2blog-api`를 소스에서 배포합니다.
3. 배포된 Service의 이미지 digest를 조회합니다.
4. 같은 이미지로 `md2blog-purge-expired-pages` Job을 갱신합니다.
5. 같은 이미지로 `md2blog-process-outbox` Job을 갱신합니다.

스케줄러는 Job과 생명주기가 다르므로 최초 한 번 별도로 생성하며, 이후 애플리케이션
배포에서는 기존 Scheduler가 갱신된 Job을 계속 실행합니다.
