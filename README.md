# OAuth2 Authorization Code Grant Authorization Server

## Authorization Code Grant
  - 클라이언트가 사용자를 인증 서버 로그인 페이지로 리다이렉트
  - 사용자가 로그인하고 동의
  - 인증 서버가 클라이언트에게 authorization code 전달
  - 클라이언트가 그 code를 토큰 엔드포인트에 보내서 access token 획득

## PKCE(Proof Key for Code Exchange)
  - Authorization Code 탈취당해도 토큰으로 교환 못 하게 막는 장치
  - code_verifier
    - 랜덤 문자열(비밀값)
    - 클라이언트만 알고 있음
  - code_challenge
    - code_verifier를 변환한 값
    - 서버에 미리 전달됨
  - Authorization 요청
    - code_challenge = BASE64URL(SHA256(code_verifier)) 같이 보냄.
  - Authorization Code 발급
    - 서버는 code_challenge를 저장하고 Authorization Code 발급
  - Token 요청
    - 클라이언트가 Code로 토큰 요청할 때 code_verifier 보냄.
  - 서버 검증
    - code_verifier -> SHA256 -> code_challenge와 비교 후 같으면 통과 다르면 거절

## 테스트

### 브라우저에 아래 URL 입력

```sh
http://localhost:9000/oauth2/authorize?response_type=code&client_id=public-client&scope=read&redirect_uri=http://localhost:9000/callback&code_challenge=E9Melhoa2OwvFrEMTJguCHaoeK1t8URWbuGJSstw-cM&code_challenge_method=S256
```

### callback URL에서 code 가져와서 curl로 access token 획득

```sh
curl -v \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "grant_type=authorization_code" \
  -d "client_id=public-client" \
  -d "code=<callback URL로 받은 authorization code>" \
  -d "redirect_uri=http://localhost:9000/callback" \
  -d "code_verifier=dBjftJeZ4CVP-mB92K27uhbUJU1p1r_wW1gFWFOEjXk" \
  http://localhost:9000/oauth2/token
```
