# 언어 스타일 미러링 MCP 서버 (Language Style Mirroring MCP Server)

MCP 프로토콜을 사용해 특정 인물(유명인, 직장 동료 등)의 말투/글투를 분석하고 미러링하는 서비스입니다.

## 주요 기능

- **YouTube 영상 분석**: 유튜브 영상에서 특정 인물의 말투를 분석합니다.
- **스타일 미러링**: 분석된 말투/글투 스타일로 입력 텍스트를 변환합니다.
- **스타일 저장 및 관리**: 분석된 스타일을 저장하고 나중에 재사용할 수 있습니다.

## 설치 방법

1. 저장소를 클론합니다:
```bash
git clone <repository-url>
cd language-style-mirroring
```

2. 필요한 패키지를 설치합니다:
```bash
pip install -r requirements.txt
```

3. YouTube 트랜스크립트 MCP 서버를 설치합니다 (Claude Desktop용):
```bash
# Claude Desktop 설정 (claude_desktop_config.json)
{
  "mcpServers": {
    "youtube-transcript": {
      "command": "npx",
      "args": ["-y", "@kimtaeyoon83/mcp-server-youtube-transcript"]
    }
  }
}
```

## 사용 방법

### 서버 실행하기

```bash
python language_mirroring_server.py
```

### Claude Desktop 설정

Claude Desktop 설정 파일에 이 서버를 추가합니다:

```json
{
  "mcpServers": {
    "youtube-transcript": {
      "command": "npx",
      "args": ["-y", "@kimtaeyoon83/mcp-server-youtube-transcript"]
    },
    "language-mirroring": {
      "command": "python",
      "args": ["language_mirroring_server.py"],
      "env": {
        "OPENAI_API_KEY": "your-openai-api-key-here"
      }
    }
  }
}
```

## 사용 예시

### 1. YouTube 영상의 말투 분석하기

```
YouTube 영상 URL: https://www.youtube.com/watch?v=VIDEO_ID에서 말투를 분석해주세요.
```

### 2. 분석된 스타일로 텍스트 변환하기

```
"안녕하세요, 오늘은 좋은 날씨네요."라는 문장을 VIDEO_ID 스타일로 바꿔주세요.
```

### 3. 커스텀 스타일 저장하기

```
"steve-jobs"라는 ID로 다음 스타일을 저장해주세요: "간결한 문장과 강한 어조를 사용하며, 'amazing', 'incredible'과 같은 형용사를 자주 사용합니다..."
```

## 추가 기능 개발 계획

1. 텍스트 기반 스타일 분석 (문서, 트위터 등)
2. 스타일 합성 (여러 스타일 결합)
3. 실시간 스타일 미러링 채팅 인터페이스

## 라이선스

MIT

## 문의

궁금하신 점이나 제안사항이 있으시면 이슈를 등록해주세요. 