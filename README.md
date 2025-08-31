# RAHashComparer - RetroAchievements ROM Hash Comparer

## 설명

`RAHashComparer`는 게임 ROM 파일들을 [RetroAchievements.org](https://retroachievements.org)의 데이터베이스와 비교하여, 공식적으로 지원되는 게임인지 확인하고 결과를 CSV 파일로 정리해주는 프로그램 입니다.

## 주요 기능

- **자동 시스템 감지**: 폴더 이름을 기반으로 처리할 게임 시스템(콘솔)을 자동으로 인식합니다.
- **해시 비교**: `RAHasher.exe`를 사용하여 로컬 ROM의 해시를 계산하고 RA 서버의 공식 해시와 비교합니다.
- **CSV 리포트 생성**: 일치/불일치 결과를 `hashreports` 폴더에 시스템별 CSV 파일로 저장합니다.
- **다양한 옵션**: 하위 폴더 검색(`-r`), ROM 경로 지정(`--dir`), 실행 전 미리보기(`--dry-run`) 등 다양한 실행 옵션을 지원합니다.
- **보조 스크립트**: 지원되는 콘솔 목록을 쉽게 확인할 수 있는 `RAHC_print_consoles.py`를 함께 제공합니다.

## 요구 사항

- Python 3.x : 파이썬
- `requests` : 파이썬 라이브러리
- `RAHasher.exe`: [RetroAchievements Tools Releases](https://github.com/RetroAchievements/RALibretro/releases) 페이지에서 다운로드할 수 있습니다. 받은 zip 파일의 압축을 풀어 나온 `RAHasher.exe`를 스크립트와 동일한 폴더에 두거나 `settings.cfg`에 경로를 지정해야 합니다.

## 설치 및 설정

1.  **필요 라이브러리 설치:**
    ```shell
    pip install requests
    ```

2.  **최초 실행 및 설정 파일 생성:**
    스크립트를 처음 실행하면 `settings.cfg` (설정 파일)와 `RAHC_print_consoles.py` (콘솔 목록 출력 스크립트)가 자동으로 생성됩니다.
    ```shell
    py RAHashComparer.py
    ```

3.  **계정 정보 입력:**
    처음 실행하면 파일이 2개 생성됩니다.
    settings.cfg
    RAHC_print_consoles.py 
    
    이 둘 중 `settings.cfg` 파일을 열어 `[RA_ACCOUNT]` 섹션에 본인의 RetroAchievements 사용자 이름(`username`)과 웹 API 키(`api_key`)를 입력하고 저장합니다. API 키는 [RA 제어판](https://retroachievements.org/controlpanel.php)에서 발급받을 수 있습니다.

    ```ini
    [RA_ACCOUNT]
    username = your_username_here
    api_key = your_api_key_here
    ```

## 사용법

기본적인 사용법은 다음과 같습니다.

```shell
py RAHashComparer.py [시스템_폴더명_1] [시스템_폴더명_2] [옵션]
```

### 사용 예시

- **SNES ROM 처리 (현재 폴더 기준):**
  ```shell
  py RAHashComparer.py snes
  ```

- **SNES와 GBA ROM 처리 (하위 폴더 포함):**
  ```shell
  py RAHashComparer.py snes gba -r
  ```

- **특정 경로에 있는 PSX ROM 처리:**
  ```shell
  py RAHashComparer.py psx --dir D:/RetroROMs
  ```

- **자동 감지된 모든 시스템 처리 (하위 폴더 포함):**
  (시스템 이름을 생략하면 `settings.cfg`에 정의된 폴더가 존재할 경우 자동으로 처리합니다.)
  ```shell
  py RAHashComparer.py -r
  ```

### 옵션

- `-h`, `--help`: 도움말을 표시합니다.
- `-r`, `--recursive`: 하위 폴더까지 모두 검색합니다.
- `--dir [경로]`: ROM이 있는 기본 폴더 경로를 지정합니다. (기본값: 현재 폴더)
- `--list`: RA에서 지원하는 전체 콘솔 목록과 설정된 폴더 매핑을 출력합니다.
- `--dry-run`: 실제 해시 계산 없이 처리될 파일 목록만 출력합니다.
- `--verbose`: 각 파일의 해시 계산 과정 등 상세 정보를 실시간으로 출력합니다.

## 출력

결과는 `hashreports` 폴더 안에 `시스템명_ID.csv` 형태의 파일로 저장됩니다. CSV 파일에는 다음과 같은 정보가 포함됩니다.

- `Status`: `Matched` (일치) 또는 `Unmatched` (불일치)
- `Game Title`: RA에 등록된 게임 제목 (일치하는 경우)
- `ROM Path`: 로컬 ROM 파일의 전체 경로
- `Game ID`: RA 게임 ID (일치하는 경우)
- `Achievements`: 등록된 업적 수 (일치하는 경우)
- `MD5 Hash`: 파일의 MD5 해시 값
