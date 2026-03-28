# 링크드인 최종 게시글

파일 이름이 `코로나19로.pdf`처럼 자모가 분리되어 보인 적이 있었습니다.

처음에는 단순한 인코딩 문제처럼 보이지만, 실제로는 파일명이 분해형 유니코드(NFD)로 저장된 경우가 많습니다. 특히 맥, OneDrive, 메신저, 압축 파일을 거치면서 이런 문제가 자주 생깁니다.

그래서 이 문제만 빠르게 해결하는 작은 Windows 도구를 만들었습니다. 이름은 `파일명구조대`입니다.

이 도구는:
- 깨진 한글 파일명을 자동으로 찾고
- 바뀔 이름을 미리 보여주고
- 충돌은 건너뛰고
- 파일 여러 개를 한 번에 정리할 수 있습니다

이번에는 실제 앱 기준 데모 이미지와 짧은 시연 영상도 같이 정리해두었습니다.

관심 있으시면 저장소에서 바로 보실 수 있습니다.

GitHub:
https://github.com/SakJaeLim/filename-rescue

#Windows #Python #Productivity #Unicode #Hangul #Utility #OpenSource

## 첨부 추천 순서

1. `output/actual_demo/actual_demo_hero.png`
2. `output/actual_demo/actual_demo.gif`
