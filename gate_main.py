import os
import time
from evdev import InputDevice, categorize, ecodes

from gate_logic import verify_consume_token

# ▼ 바코드 스캐너 이벤트 장치 (evtest에서 확인한 번호로 변경)
EVENT_DEVICE = "/dev/input/event0"

# ▼ HID KEYCODE → 문자 매핑 테이블 (필요한 항목만 우선 등록)
KEY_MAP = {
    ecodes.KEY_0: "0",
    ecodes.KEY_1: "1",
    ecodes.KEY_2: "2",
    ecodes.KEY_3: "3",
    ecodes.KEY_4: "4",
    ecodes.KEY_5: "5",
    ecodes.KEY_6: "6",
    ecodes.KEY_7: "7",
    ecodes.KEY_8: "8",
    ecodes.KEY_9: "9",

    ecodes.KEY_A: "a",
    ecodes.KEY_B: "b",
    ecodes.KEY_C: "c",
    ecodes.KEY_D: "d",
    ecodes.KEY_E: "e",
    ecodes.KEY_F: "f",
    ecodes.KEY_G: "g",
    ecodes.KEY_H: "h",
    ecodes.KEY_I: "i",
    ecodes.KEY_J: "j",
    ecodes.KEY_K: "k",
    ecodes.KEY_L: "l",
    ecodes.KEY_M: "m",
    ecodes.KEY_N: "n",
    ecodes.KEY_O: "o",
    ecodes.KEY_P: "p",
    ecodes.KEY_Q: "q",
    ecodes.KEY_R: "r",
    ecodes.KEY_S: "s",
    ecodes.KEY_T: "t",
    ecodes.KEY_U: "u",
    ecodes.KEY_V: "v",
    ecodes.KEY_W: "w",
    ecodes.KEY_X: "x",
    ecodes.KEY_Y: "y",
    ecodes.KEY_Z: "z",

    ecodes.KEY_MINUS: "-",
    ecodes.KEY_EQUAL: "=",
    ecodes.KEY_SLASH: "/",
    ecodes.KEY_DOT: ".",
    ecodes.KEY_COMMA: ",",
}

ENTER_KEYS = [ecodes.KEY_ENTER, ecodes.KEY_KPENTER]


def main_loop():
    print("------------------------------------------")
    print(f"🚀 Scan&Go Gate Controller ({os.uname().nodename}) Started")
    print("Listening via /dev/input/event0 (HID Events)...")
    print("------------------------------------------")

    dev = InputDevice(EVENT_DEVICE)

    buffer = ""

    for event in dev.read_loop():
        if event.type == ecodes.EV_KEY:
            key_event = categorize(event)

            # key press only (value == 1)
            if key_event.keystate == key_event.key_down:

                code = key_event.scancode

                # ENTER → QR 입력 완료
                if code in ENTER_KEYS:
                    token = buffer.strip()
                    if token:
                        print(f"\n[SCAN] Token Received: {token[:40]}...")
                        result = verify_consume_token(token)
                        print(f"[RESULT] Status: {result.get('status')}, Reason: {result.get('reason')}")
                    buffer = ""
                    continue

                # 일반 문자
                if code in KEY_MAP:
                    buffer += KEY_MAP[code]


if __name__ == "__main__":
    try:
        main_loop()
    except KeyboardInterrupt:
        print("\n🛑 Program terminated by user.")
    finally:
        print("🧩 Gate Controller Shutdown.")
