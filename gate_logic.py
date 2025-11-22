# gate_logic.py

import requests
import jwt
import time
from datetime import datetime, timedelta
# 설정 파일에서 필요한 상수들을 가져옵니다.
from config import GATE_VERIFY_API_URL, SERVER_PUBLIC_KEY, GATE_ID, JWT_ALGORITHMS, GATE_API_KEY


# --- A. 더미 GPIO 및 UX 함수 (하드웨어 도착 시 이 부분을 실제 코드로 대체) ---

def open_gate():
    """게이트를 열고 닫는 동작을 시뮬레이션합니다. (실제 릴레이 제어)"""
    print("🚦 릴레이 신호 ON: 게이트 OPEN")
    # TODO: 하드웨어 연결 시 이 위치에 실제 RPi.GPIO 코드를 작성합니다.
    # 예: GPIO.output(RELAY_PIN, GPIO.HIGH)
    time.sleep(3) # 문 열림 시간 가정
    print("🚪 릴레이 신호 OFF: 게이트 CLOSE")
    # 예: GPIO.output(RELAY_PIN, GPIO.LOW)

def display_status(is_success, reason=""):
    """게이트 신뢰 UX(LED, 소리)를 시뮬레이션합니다. (서버 응답 OK 시에만 초록불)"""
    if is_success:
        print("✅ 초록불 ON: 결제 완료. 통과하세요!")
    else:
        print(f"❌ 빨간불 ON: 차단됨. 사유: {reason}")
        
# --- B. 핵심 로직 함수 ---

def verify_consume_token(token_string: str, gate_id: str = GATE_ID) -> dict:
    """
    1. JWT 로컬 1차 검증 (서명/TTL/Scope)
    2. 백엔드 API 호출 및 최종 검증 (verify-consume)
    3. 결과에 따른 게이트 제어
    """
    print(f"\n--- 토큰 검증 시작 (Gate ID: {gate_id}) ---")

    # 1. 로컬 JWT 검증 (Defense-in-Depth)
    try:
        # 🔑 서버 공개키로 서명 유효성, 만료 시간(TTL) 등을 한 번에 검증합니다.
        payload = jwt.decode(
            token_string, 
            SERVER_PUBLIC_KEY, 
            algorithms=JWT_ALGORITHMS, 
            options={"verify_signature": True, "require": ['exp', 'jti']}
        )
        
        # 게이트 범위(Scope) 검증
        if payload.get('gate') != gate_id:
             reason = "GATE_SCOPE_MISMATCH"
             print(f"🚨 로컬 검증 실패: 게이트 범위 불일치. 차단됨. 사유: {reason}")
             display_status(False, reason)
             return {"status": "BLOCK", "reason": reason}
        
        print(f"✨ 로컬 검증 통과 (서명/TTL/Scope OK). 트랜잭션 ID: {payload.get('tid')}")

    except jwt.exceptions.InvalidSignatureError:
        reason = "INVALID_SIGNATURE"
        print(f"🚨 로컬 검증 실패: JWT 서명이 유효하지 않습니다. 차단됨. 사유: {reason}")
        display_status(False, reason)
        return {"status": "BLOCK", "reason": reason}
    except jwt.exceptions.ExpiredSignatureError:
        reason = "TOKEN_EXPIRED"
        print(f"🚨 로컬 검증 실패: 토큰이 만료되었습니다. 차단됨. 사유: {reason}")
        display_status(False, reason)
        return {"status": "BLOCK", "reason": reason}
    except Exception as e:
        reason = f"TOKEN_PARSING_ERROR: {e.__class__.__name__}"
        print(f"🚨 로컬 검증 실패: 토큰 파싱 오류. 차단됨. 사유: {reason}")
        display_status(False, reason)
        return {"status": "BLOCK", "reason": reason}

    # 2. 서버에 verify-consume API 호출 (Zero-Trust 핵심)
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {GATE_API_KEY}" # 게이트 인증
    }
    api_payload = {
        "token": token_string,
        "gate_id": gate_id,
        "device_hash": payload.get('device_hash', 'UNKNOWN'), # 디바이스 바인딩 정보 포함
    }

    try:
        print(f"🌐 서버에 최종 검증/소비 요청 중: {GATE_VERIFY_API_URL}")
        # 왕복 p95 < 300ms 목표를 위해 타임아웃을 짧게 설정
        response = requests.post(GATE_VERIFY_API_URL, json=api_payload, headers=headers, timeout=0.4) 

        # 3. 서버 응답 확인 (서버의 'OK'가 와야만 문 개방)
        if response.status_code == 200:
            server_result = response.json()
            if server_result.get("status") == "OK":
                display_status(True)
                open_gate() # 서버 OK 시에만 게이트 개방
                return {"status": "OPEN", "reason": "Server OK"}
            else:
                reason = server_result.get("reason", "Server Denied")
                display_status(False, reason) # 실패 시 노란불/안내 멘트
                # 고위험 시 샘플 검증 라인 유도
                return {"status": "BLOCK", "reason": reason}

        else:
            print(f"🌐 서버 통신 오류: HTTP {response.status_code}")
            display_status(False, "SERVER_COMMUNICATION_ERROR")
            return {"status": "BLOCK", "reason": "SERVER_COMMUNICATION_ERROR"}
    
    except requests.exceptions.Timeout:
        reason = "TIMEOUT"
        print("🌐 서버 통신 오류: 타임아웃 발생 (신뢰 최우선, 기본 차단)")
        display_status(False, reason)
        return {"status": "BLOCK", "reason": reason}
    except requests.exceptions.RequestException as e:
        reason = f"NETWORK_FAIL: {e.__class__.__name__}"
        print(f"🌐 서버 통신 오류: 네트워크 접속 실패. 차단됨. 사유: {reason}")
        display_status(False, reason)
        return {"status": "BLOCK", "reason": reason}


# --- C. 테스트 실행 예시 ---
if __name__ == "__main__":
    
    # 🚨 NOTE: 이 테스트는 서버 통신이 필요하며, config.py의 값이 실제와 다르면 실패합니다.
    # JWT를 생성하는 Dummy 코드는 실제 서버 키가 없어 생략하며, Postman 등으로 확보한 
    # 실제 토큰 문자열을 여기에 넣어 테스트해야 합니다.

    # 1. 유효한 토큰 문자열 (백엔드에서 발급받아야 함)
    TEST_TOKEN_VALID = "eyJhbGciOiJFUzI1NiIsInR5cCI6IkpXVCJ9.ey..." # 유효 토큰
    # 2. 만료된 토큰 문자열 (백엔드에서 발급받아야 함)
    TEST_TOKEN_EXPIRED = "eyJhbGciOiJFUzI1NiIsInR5cCI6IkpXVCJ9.ey..." # 만료 토큰

    print("=== TEST A: 유효 토큰으로 서버 최종 검증 시도 ===")
    verify_consume_token(TEST_TOKEN_VALID)
    
    print("\n" + "="*50)
    
    # 만약 로컬 검증을 테스트하고 싶다면, config.py의 공개키를 잘못된 값으로 설정하고 진행
    print("=== TEST B: 만료된 토큰으로 로컬 검증 실패 시도 ===")
    # (이 토큰이 이미 만료되었다면 서버 통신 전 로컬에서 차단되어야 합니다.)
    verify_consume_token(TEST_TOKEN_EXPIRED)