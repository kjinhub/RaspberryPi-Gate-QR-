# config.py

# --- 1. 서버 API 엔드포인트 및 게이트 ID 설정 ---
# 실제 백엔드 서버의 verify-consume API 주소 (HTTPS 권장)
GATE_VERIFY_API_URL = "https://api.scango.com/gate/verify-consume"

# 이 게이트 컨트롤러의 고유 식별자 (토큰의 'gate' 클레임과 일치해야 함)
GATE_ID = "ZONE-A" 

# --- 2. 서버 JWT 공개키 (Zero-Trust 1차 검증용) ---
# 백엔드 서버의 ECDSA/RSA 서명에 사용된 공개키를 여기에 정확히 붙여넣어야 합니다.
SERVER_PUBLIC_KEY = """
-----BEGIN PUBLIC KEY-----
YOUR_ACTUAL_SERVER_PUBLIC_KEY_HERE_OBTAINED_FROM_BACKEND
-----END PUBLIC KEY-----
"""
# 서버가 사용하는 JWT 알고리즘 (예: ES256, RS256)
JWT_ALGORITHMS = ["ES256"] 

# --- 3. API 통신용 인증 정보 ---
# 게이트가 서버에 자신을 인증하기 위한 보안 키
GATE_API_KEY = "YOUR_SECURE_API_KEY_FOR_GATE_AUTH"