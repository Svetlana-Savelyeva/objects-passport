#!/usr/bin/env python3
"""Паспорта объектов — шифрование секретных полей.

Секретные поля каждого объекта (доступ в парадную, пароль Wi-Fi, лицевой счёт
и свои строки с пометкой secret) хранятся в data/objects.json только в
зашифрованном виде (AES-256-GCM, ключ из пароля через PBKDF2-SHA256).

Рабочий цикл правки:
    export PASSPORT_KEY='пароль'
    python3 tools/passport.py open    # -> .secrets/objects.plain.json (в git не попадает)
    ... правим .secrets/objects.plain.json ...
    python3 tools/passport.py seal    # -> data/objects.json (секреты снова зашифрованы)

Другие команды:
    python3 tools/passport.py init         # новая соль и проверочная строка (смена пароля: open, init, seal)
    python3 tools/passport.py check        # проверить пароль
"""
import base64, json, os, sys
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data", "objects.json")
CRYPTO = os.path.join(ROOT, "data", "crypto.json")
PLAIN = os.path.join(ROOT, ".secrets", "objects.plain.json")
CHECK_TEXT = "passport-ok"
SECRET_FIELDS = ["access", "wifiPass", "account"]
ITERATIONS = 600_000


def b64(b): return base64.b64encode(b).decode()
def unb64(s): return base64.b64decode(s)


def key_from(password, cfg):
    kdf = PBKDF2HMAC(algorithm=hashes.SHA256(), length=32, salt=unb64(cfg["salt"]), iterations=cfg["iterations"])
    return AESGCM(kdf.derive(password.encode()))


def enc(aes, obj):
    iv = os.urandom(12)
    return b64(iv + aes.encrypt(iv, json.dumps(obj, ensure_ascii=False, sort_keys=True).encode(), None))


def dec(aes, s):
    raw = unb64(s)
    return json.loads(aes.decrypt(raw[:12], raw[12:], None))


def password():
    p = os.environ.get("PASSPORT_KEY")
    if not p:
        sys.exit("Задайте пароль: export PASSPORT_KEY='...'")
    return p


def load_cfg_key():
    cfg = json.load(open(CRYPTO, encoding="utf-8"))
    aes = key_from(password(), cfg)
    try:
        assert dec(aes, cfg["check"]) == CHECK_TEXT
    except Exception:
        sys.exit("Неверный пароль")
    return cfg, aes


def cmd_init():
    cfg = {"kdf": "PBKDF2-SHA256", "cipher": "AES-256-GCM", "iterations": ITERATIONS, "salt": b64(os.urandom(16))}
    aes = key_from(password(), cfg)
    cfg["check"] = enc(aes, CHECK_TEXT)
    os.makedirs(os.path.dirname(CRYPTO), exist_ok=True)
    json.dump(cfg, open(CRYPTO, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    print("data/crypto.json обновлён. Теперь выполните seal.")


def cmd_open():
    _, aes = load_cfg_key()
    objs = json.load(open(DATA, encoding="utf-8"))
    for o in objs:
        s = dec(aes, o["enc"]) if o.get("enc") else {}
        for f in SECRET_FIELDS:
            o[f] = s.get(f, "")
        cv = s.get("custom", {})
        for row in o.get("custom", []):
            if row.get("secret"):
                row["value"] = cv.get(row["label"], "")
                row.pop("filled", None)
        o.pop("enc", None); o.pop("secretFilled", None)
    os.makedirs(os.path.dirname(PLAIN), exist_ok=True)
    json.dump(objs, open(PLAIN, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    print(f"Открыто {len(objs)} объектов -> {os.path.relpath(PLAIN, ROOT)}")


def seal_objects(objs, aes, old_by_id):
    out = []
    for o in objs:
        o = dict(o)
        payload = {f: o.pop(f, "") or "" for f in SECRET_FIELDS}
        custom, cv = [], {}
        for row in o.get("custom", []):
            row = dict(row)
            if row.get("secret"):
                v = row.pop("value", "") or ""
                cv[row["label"]] = v
                row["filled"] = bool(v.strip())
            custom.append(row)
        o["custom"] = custom
        payload["custom"] = cv
        payload = {k: v for k, v in payload.items() if v}
        o["secretFilled"] = [f for f in SECRET_FIELDS if payload.get(f, "").strip()]
        old = old_by_id.get(o["id"])
        reuse = None
        if old and old.get("enc"):
            try:
                if dec(aes, old["enc"]) == payload:
                    reuse = old["enc"]
            except Exception:
                pass
        o["enc"] = reuse or (enc(aes, payload) if payload else "")
        out.append(o)
    return out


def cmd_seal():
    _, aes = load_cfg_key()
    objs = json.load(open(PLAIN, encoding="utf-8"))
    old = {}
    if os.path.exists(DATA):
        old = {o["id"]: o for o in json.load(open(DATA, encoding="utf-8"))}
    objs.sort(key=lambda o: (o.get("order", 9999), o["id"]))
    out = seal_objects(objs, aes, old)
    json.dump(out, open(DATA, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(f"Зашифровано и записано {len(out)} объектов -> data/objects.json")


def cmd_check():
    load_cfg_key(); print("Пароль верный")


if __name__ == "__main__":
    cmds = {"init": cmd_init, "open": cmd_open, "seal": cmd_seal, "check": cmd_check}
    if len(sys.argv) < 2 or sys.argv[1] not in cmds:
        print(__doc__); sys.exit(1)
    cmds[sys.argv[1]]()
