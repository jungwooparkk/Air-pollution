# 공식 Rasa 이미지 확장
FROM rasa/rasa:latest

# 작업 디렉토리를 /app으로 설정
WORKDIR /app

# Rasa 프로젝트 파일 복사 (domain.yml, data/, config.yml 등)
COPY . /app

# 필요한 경우, custom actions 및 관련된 requirements-actions.txt 파일 복사 및 설치
# 만약 액션 서버를 별도로 배포한다면 여기서는 복사하지 않아도 됨
# COPY actions /app/actions
# COPY actions/requirements-actions.txt ./
# RUN pip install -r requirements-actions.txt

# 모델 학습 (만약 이미 학습된 모델이 없다면)
# CMD ["rasa", "train", "--force"] # 이 줄은 배포 시 학습이 필요할 때만 사용. 이미 학습된 모델이 있다면 주석 처리하거나 제거.

# Rasa 코어 서버 시작
# --enable-api: REST API 활성화
# --port 5005: Rasa 코어 서버 기본 포트
# --cors "*": 모든 CORS 허용 (개발 단계에서만 사용 권장)
# --debug: 디버그 모드 (로그 상세화)
# --endpoints endpoints.yml: 액션 서버 등 외부 서비스 연결 설정
