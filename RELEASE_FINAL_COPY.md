# 릴리즈 최종 복붙용

## Tag

`v0.1.0`

## Title

`v0.1.0 - 첫 공개 버전`

## About Description

`Windows utility that fixes broken Korean filenames by normalizing decomposed Hangul into readable names.`

## Topics

`windows`, `python`, `unicode`, `normalization`, `korean`, `hangul`, `filename`, `utility`, `productivity`

## Release Body

```md
첫 공개 버전입니다.

## 무엇을 해결하나요

Windows에서 한글 파일명이 자모 분리 형태로 깨져 보일 때, 정상 한글 이름으로 복구합니다.

예:
- `코로나19로.pdf` -> `코로나19로.pdf`
- `가상자산 시계열.pdf` -> `가상자산 시계열.pdf`

## 포함된 기능

- 깨진 한글 파일명 탐지
- 변경될 이름 미리보기
- 파일 여러 개 드래그앤드롭
- 폴더 드래그앤드롭
- 하위 폴더까지 스캔
- 파일/폴더 이름 일괄 변경
- 이름 충돌 자동 감지
- 실행 로그 JSON 저장

## 실제 데모 자산

릴리즈에 함께 첨부하면 좋은 파일:

- `output/actual_demo/actual_demo_hero.png`
- `output/actual_demo/actual_demo.gif`
- `output/actual_demo/actual_demo.mp4`

## 사용 방법

1. `run_hangul_filename_fixer.bat` 실행
2. 폴더를 선택하거나 파일 여러 개를 드래그해서 놓기
3. 미리보기 확인
4. `이름 변경 실행` 클릭

## 주의

- 이 도구는 파일 내용이 아니라 파일 이름만 변경합니다.
- 이름 충돌이 있는 항목은 자동으로 건너뜁니다.
- 실행 로그가 스크립트 폴더에 JSON으로 저장됩니다.
```
