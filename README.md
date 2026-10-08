# 센서 시간 정렬기

비동기 PLC·로봇 센서 데이터를 같은 시점의 트윈 스냅샷으로 정렬하고 오래된 값과 미래값 누출을 구분합니다.

## 핵심 기능

시간을 수신순서가 아닌 공통 기준의 event time으로 처리합니다. target 이하 최신값만 선택하고 허용 나이를 넘으면 value=null로 반환해 오래된 값을 정상값처럼 소비하지 않게 합니다. 동일 시각은 높은 sequence가 우선이며 동일 sequence의 충돌은 입력 오류입니다. 센서 ID는 장비 ID와 묶어 장비 간 혼합을 막습니다.

## 설치·실행

Python 3.10 이상. 외부 패키지·API 키·장비 연결이 필요 없습니다.

```bash
git clone https://github.com/MetaSonGi/telemetry-time-aligner.git
cd telemetry-time-aligner
python -m pip install -r requirements.txt
python main.py
python main.py --input sample-input.json --html result.html
python -m unittest -v
```

Windows에서 python 대신 py를 사용할 수 있습니다. 다른 디렉터리에서 실행해도 기본 샘플은 main.py 옆 파일에서 읽습니다. 모든 출력 파일 경로는 명시한 위치에 생성합니다.

## 웹에서 결과 확인

다운로드한 `example-report.html`을 브라우저에서 열면 검증한 샘플 결과가 보입니다. 입력을 수정하고 `python main.py --input sample-input.json --html result.html`을 실행하면 새 결과를 브라우저로 볼 수 있습니다. 보고서는 HTML에 결과를 포함하므로 네트워크·CDN·서버가 필요 없습니다. 입력 문자열은 escape해 HTML/스크립트로 실행하지 않습니다. 이는 입력 편집용 웹 앱이 아닌 실행 결과 뷰어입니다.

## 입력·출력 예제

합성 입력: [sample-input.json](sample-input.json). 필드와 형식은 이 파일이 최소 실행 예제입니다. 반환 규칙은 main.py의 `run(data)`에 정의됩니다. 손상된 JSON·필수 필드 누락·잘못된 수치 입력은 CLI가 종료 코드 2로 보고합니다.

```json
{
  "tolerance_s": 2,
  "snapshot_times_s": [
    0,
    2,
    5,
    8
  ],
  "readings": [
    {
      "asset_id": "robot-1",
      "sensor_id": "temperature",
      "time_s": 1,
      "sequence": 1,
      "value": 32
    },
    {
      "asset_id": "robot-1",
      "sensor_id": "temperature",
      "time_s": 4,
      "sequence": 2,
      "value": 34
    },
    {
      "asset_id": "robot-1",
      "sensor_id": "temperature",
      "time_s": 4,
      "sequence": 3,
      "value": 34.5
    },
    {
      "asset_id": "robot-1",
      "sensor_id": "current",
      "time_s": 2,
      "sequence": 1,
      "value": 1.2
    },
    {
      "asset_id": "robot-1",
      "sensor_id": "current",
      "time_s": 7,
      "sequence": 2,
      "value": 1.5
    }
  ]
}
```

출력 미리보기(생략 표시 부분은 설명이며 JSON 입력으로 사용하지 마세요):

```text
{
  "policy": "backward_asof_no_future",
  "duplicate_timestamps": 1,
  "snapshots": [
    {
      "time_s": 0,
      "values": [
        {
          "asset_id": "robot-1",
          "sensor_id": "current",
          "status": "missing",
          "value": null
        },
        {
          "asset_id": "robot-1",
          "sensor_id": "temperature",
          "status": "missing",
          "value": null
        }
      ]
    },
    {
      "time_s": 2,
      "values": [
        {
          "asset_id": "robot-1",
          "sensor_id": "current",
          "status": "fresh",
          "value": 1.2,
          "source_time_s": 2,
          "age_s": 0,
          "sequence": 1
        },
        {
          "asset_id": "robot-1",
          "sensor_id": "temperature",
          "status": "fresh",
          "value": 32,
          "source_time_s": 1,
          "age_s": 1,
          "sequence": 1
        }
      ]
    },
    {
      "time_s": 5,
      "values": [
        {
          "asset_id
… 전체 출력은 example-output.json 참조
```

전체 실행 결과: [example-output.json](example-output.json), [example-report.html](example-report.html).

## 설계 판단·통합

시간을 수신순서가 아닌 공통 기준의 event time으로 처리합니다. target 이하 최신값만 선택하고 허용 나이를 넘으면 value=null로 반환해 오래된 값을 정상값처럼 소비하지 않게 합니다. 동일 시각은 높은 sequence가 우선이며 동일 sequence의 충돌은 입력 오류입니다. 센서 ID는 장비 ID와 묶어 장비 간 혼합을 막습니다.

장비 데이터 수집 계층에서 합성 예제를 실제 데이터 스키마로 변환한 뒤 `run(data)`를 호출할 수 있습니다. Nest.js/Python 작업 큐 또는 테스트 자동화에서 JSON 입출력을 사용하고 XR/WebGL 화면에는 검증된 결과만 표시하는 방식으로 연결할 수 있습니다. 프로그램에는 실제 제어·유료 서비스·사용자 계정 접근 코드가 없습니다.

## 한계

배치 정렬용으로 watermark·실시간 지연버퍼·시계 동기화는 구현하지 않습니다. time_s는 수집기가 이미 같은 시계의 초 단위로 정규화했다고 가정합니다. 입력에 존재하지 않은 센서의 부재는 감지하지 않으며 단위 변환은 하지 않습니다.

가상의 경력, 논문 성능 수치, 모델 재현 또는 실물 제조 검증을 주장하지 않습니다. 데이터가 합성 예제인 만큼 현장 적용 전 데이터 품질·운영 조건을 다시 검증해야 합니다.

## 검증·근거

의미 있는 정상·경계·오류 테스트 4개를 실제 실행했습니다. 기록은 [VALIDATION.txt](VALIDATION.txt)에 있습니다. 논문 날짜·상태·확인 범위와 개발자 해석은 [TRENDS.md](TRENDS.md)를 참고하세요.

실행 기준일: 2026-10-09 (Asia/Seoul). 기존 저장소를 수정하지 않고 독립 프로그램으로 구성했습니다.
