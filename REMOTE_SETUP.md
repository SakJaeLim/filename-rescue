# GitHub 원격 연결 안내

현재 로컬 저장소는 `SakJaeLim` 계정 기준으로 올릴 준비를 마친 상태를 목표로 합니다.

## 추천 저장소 이름

- `filename-rescue`

## GitHub 웹에서 할 일

1. `SakJaeLim` 계정으로 새 저장소 생성
2. 저장소 이름을 `filename-rescue`로 입력
3. Public 선택
4. `Add a README`, `.gitignore`, `License` 체크는 끄기

## 그 다음 로컬에서 할 명령

```powershell
git remote add origin https://github.com/SakJaeLim/filename-rescue.git
git push -u origin main
```

## 저장소 설명 추천

`파일명구조대 | 깨진 한글 파일명 복구기`

## GitHub About 문구 추천

`Windows utility that fixes broken Korean filenames by normalizing decomposed Hangul into readable names.`
