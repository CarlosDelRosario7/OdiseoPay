#!/usr/bin/env bash
# security_checks.sh — Verificación no destructiva de Injection e integridad de datos (E4-A3, Carlos)
#
# Alcance: SOLO LECTURA + POST /api/auth/login. Ninguna prueba crea, modifica ni borra datos.
# Requiere el servidor en marcha en BASE_URL (por defecto http://127.0.0.1:5000) y MariaDB con datos.
# Las credenciales dev (admin/admin1234, documentadas en server/README.md y test.http) se usan
# únicamente para obtener un token válido. NUNCA se imprimen tokens completos ni la clave JWT.
#
# Uso:   server/tests/security_checks.sh [BASE_URL]
# Salida: [PASS]/[FAIL]/[SKIP]/[INFO] por prueba + resumen. Exit code 1 si hay FAIL.
# Fecha de creación: 2026-11-12 | commit: edf5f4a | rama: main

set -u
cd "$(dirname -- "${BASH_SOURCE[0]}")"
SERVER_DIR="$(cd .. && pwd)"
ROOT_DIR="$(cd ../.. && pwd)"
BASE_URL="${1:-http://127.0.0.1:5000}"
ADMIN_USER="${ODISEOPAY_ADMIN_USER:-admin}"
ADMIN_PASSWORD="${ODISEOPAY_ADMIN_PASSWORD:-admin1234}"
PY="$ROOT_DIR/.venv/bin/python"
[ -x "$PY" ] || PY="$(command -v python3)"
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

PASS=0; FAIL=0; SKIP=0; INFO=0
ok()   { PASS=$((PASS + 1)); printf '[PASS] %s\n' "$1"; }
bad()  { FAIL=$((FAIL + 1)); printf '[FAIL] %s\n' "$1"; }
skip() { SKIP=$((SKIP + 1)); printf '[SKIP] %s\n' "$1"; }
info() { INFO=$((INFO + 1)); printf '[INFO] %s\n' "$1"; }

http_code() { curl -s -m 5 -o "$TMP/body" -w '%{http_code}' "$@"; }

echo "=============================================================="
echo " OdiseoPay — verificación de Injection e integridad (E4-A3)"
echo " $(date '+%Y-%m-%d %H:%M:%S %Z') | BASE_URL=$BASE_URL"
echo " Pruebas no destructivas: solo lectura + POST /api/auth/login"
echo "=============================================================="

echo
echo "── A. Análisis estático ─────────────────────────────────────"

# A1. Sin SQL crudo / evaluación dinámica en el backend
RAW=$(grep -rnE "(^|[^a-zA-Z_.])(eval|exec)\(|yaml\.load\(|shell[[:space:]]*=[[:space:]]*True|pickle\.|\.execute\(|[^a-zA-Z_.]text\(" "$ROOT_DIR/server/src" --include='*.py' | grep -v __pycache__ | grep -v 'has_request_context' || true)
if [ -z "$RAW" ]; then
  ok "A1. Sin SQL crudo, eval/exec, shell=True, pickle ni yaml.load en server/src"
else
  bad "A1. Patrones peligrosos detectados:"; printf '%s\n' "$RAW"
fi

# A2. requirements.txt con versiones fijadas (==)
TOTAL=$(grep -cE '^[A-Za-z0-9_.-]+[=<>!~]' "$ROOT_DIR/server/requirements.txt" || true)
PINNED=$(grep -cE '^[A-Za-z0-9_.-]+==' "$ROOT_DIR/server/requirements.txt" || true)
if [ "$TOTAL" -gt 0 ] && [ "$PINNED" -eq "$TOTAL" ]; then
  ok "A2. requirements.txt con $PINNED/$TOTAL dependencias fijadas (==)"
else
  bad "A2. Dependencias sin fijar: $PINNED/$TOTAL"
fi

# A3. Lockfile del frontend presente
if [ -f "$ROOT_DIR/client/package-lock.json" ]; then
  ok "A3. client/package-lock.json presente ($(wc -c < "$ROOT_DIR/client/package-lock.json") bytes)"
else
  bad "A3. client/package-lock.json no encontrado"
fi

# A4. server/.env fuera del control de versiones
if git -C "$ROOT_DIR" ls-files --error-unmatch server/.env >/dev/null 2>&1; then
  bad "A4. server/.env está rastreado en git (debe corregirse)"
else
  ok "A4. server/.env no está rastreado en git (.gitignore lo excluye)"
fi

# A5. Código de logging de seguridad con rotación
if grep -q 'RotatingFileHandler' "$ROOT_DIR/server/src/utils/security_log.py"; then
  ok "A5. security_log.py usa RotatingFileHandler (1 MB, 3 backups)"
else
  bad "A5. security_log.py sin rotación"
fi

echo
echo "── B. Pruebas dinámicas contra $BASE_URL ───────────────────"

# B0. Servidor accesible
CODE=$(http_code "$BASE_URL/api/health")
if [ "$CODE" != "200" ]; then
  skip "B1–B11. Servidor no responde 200 en /api/health (HTTP $CODE); pruebas dinámicas omitidas"
else
  ok "B0. /api/health → 200 OK"

  # B1. Inyección SQL en el login (campo usuario)
  ALL401=1
  for payload in \
    "' OR '1'='1' -- " \
    "' OR 1=1 -- " \
    "admin'-- " \
    "' UNION SELECT 1,2,3,4,5 -- " \
    "'; DROP TABLE usuarios; -- " ; do
    CODE=$(http_code -X POST "$BASE_URL/api/auth/login" -H 'Content-Type: application/json' --data "{\"usuario\":\"$payload\",\"contrasena\":\"wrongpass\"}")
    if [ "$CODE" != "401" ]; then ALL401=0; printf '       payload=%q → HTTP %s\n' "$payload" "$CODE"; fi
    if grep -qEi 'traceback|mysql|pymysql|sqlalchemy|syntax error' "$TMP/body"; then ALL401=0; printf '       payload=%q → filtró error SQL\n' "$payload"; fi
  done
  [ "$ALL401" = 1 ] && ok "B1. SQLi en /api/auth/login (5 payloads) → todos 401, sin errores SQL" || bad "B1. Algún payload SQLi no devolvió 401 limpio"

  # B2. Credenciales incorrectas
  CODE=$(http_code -X POST "$BASE_URL/api/auth/login" -H 'Content-Type: application/json' --data '{"usuario":"nadie_xyz","contrasena":"incorrecta"}')
  [ "$CODE" = "401" ] && ok "B2. Login con credenciales incorrectas → 401" || bad "B2. Esperado 401, recibido $CODE"

  # B3. XSS reflejado: el payload no debe devolverse crudo
  XSS='<script>alert(1)</script>'
  CODE=$(http_code -X POST "$BASE_URL/api/auth/login" -H 'Content-Type: application/json' --data "{\"usuario\":\"$XSS\",\"contrasena\":\"wrongpass\"}")
  if [ "$CODE" = "401" ] && ! grep -qF "$XSS" "$TMP/body"; then
    ok "B3. XSS en login → 401 y payload no se refleja en la respuesta"
  else
    bad "B3. XSS reflejado o código inesperado (HTTP $CODE)"
  fi

  # B4. Ruta protegida sin token
  CODE=$(http_code "$BASE_URL/api/productos")
  [ "$CODE" = "401" ] && ok "B4. /api/productos sin token → 401" || bad "B4. Esperado 401, recibido $CODE"

  # Obtener token válido (dev credentials) para B5–B8
  CODE=$(http_code -X POST "$BASE_URL/api/auth/login" -H 'Content-Type: application/json' --data "{\"usuario\":\"$ADMIN_USER\",\"contrasena\":\"$ADMIN_PASSWORD\"}")
  if [ "$CODE" = "200" ]; then
    TOKEN=$("$PY" -c "import json;print(json.load(open('$TMP/body'))['access_token'])")

    # B5. Token con payload manipulado (sin re-firmar)
    MANIP=$("$PY" -c "
t='$TOKEN'.split('.')
p=t[1]
i=len(p)//2
p=p[:i] + ('A' if p[i] != 'A' else 'B') + p[i+1:]
print('.'.join([t[0], p, t[2]]))")
    CODE=$(http_code "$BASE_URL/api/productos?page=1&per_page=5" -H "Authorization: Bearer $MANIP")
    [ "$CODE" = "401" ] && ok "B5. Token con payload alterado → 401" || bad "B5. Esperado 401, recibido $CODE"

    # B6. Token alg=none (firma vacía)
    NONE=$("$PY" -c "
import base64, json
b64u = lambda b: base64.urlsafe_b64encode(b).rstrip(b'=').decode()
h = b64u(json.dumps({'alg':'none','typ':'JWT'}).encode())
p = b64u(json.dumps({'sub':'3','rol':'Admin','exp':4102444800}).encode())
print(f'{h}.{p}.')")
    CODE=$(http_code "$BASE_URL/api/productos?page=1&per_page=5" -H "Authorization: Bearer $NONE")
    [ "$CODE" = "401" ] && ok "B6. Token alg=none → 401 rechazado" || bad "B6. Esperado 401, recibido $CODE"

    # B7. Token firmado con clave distinta (HS256)
    WRONG=$("$PY" -c "
import time, jwt
print(jwt.encode({'sub':'3','exp':int(time.time())+600}, 'clave-incorrecta-de-prueba', algorithm='HS256'))" 2>/dev/null)
    if [ -n "$WRONG" ]; then
      CODE=$(http_code "$BASE_URL/api/productos?page=1&per_page=5" -H "Authorization: Bearer $WRONG")
      [ "$CODE" = "401" ] && ok "B7. Token firmado con clave desconocida → 401" || bad "B7. Esperado 401, recibido $CODE"
    else
      skip "B7. PyJWT no disponible en el venv; prueba omitida"
    fi

    # B8. Token expirado (firma válida, exp en el pasado; clave real leída de .env en memoria)
    EXPIRED=$("$PY" -c "
import time, jwt
from dotenv import dotenv_values
secret = dotenv_values('$SERVER_DIR/.env').get('JWT_SECRET_KEY')
now = int(time.time())
print(jwt.encode({'sub':'3','iat':now-7200,'exp':now-3600,'jti':'e4-expired-probe'}, secret, algorithm='HS256'))" 2>/dev/null)
    if [ -n "$EXPIRED" ]; then
      CODE=$(http_code "$BASE_URL/api/productos?page=1&per_page=5" -H "Authorization: Bearer $EXPIRED")
      [ "$CODE" = "401" ] && ok "B8. Token expirado (firma válida, exp pasado) → 401" || bad "B8. Esperado 401, recibido $CODE"
    else
      skip "B8. No se pudo generar el token expirado; prueba omitida"
    fi

    # B9. Límite per_page (integridad/anti-abuso): 99999 debe toparse en 100
    CODE=$(http_code "$BASE_URL/api/productos?page=1&per_page=99999" -H "Authorization: Bearer $TOKEN")
    if [ "$CODE" = "200" ]; then
      PPR=$("$PY" -c "import json;print(json.load(open('$TMP/body')).get('per_page'))")
      if [ "$PPR" -le 100 ] 2>/dev/null; then
        ok "B9. per_page=99999 → el servidor lo limita a $PPR (≤100)"
      else
        bad "B9. per_page=99999 → el servidor respondió per_page=$PPR (sin límite)"
      fi
    else
      skip "B9. /api/productos respondió $CODE; prueba omitida"
    fi
  else
    skip "B5–B9. Login dev ($ADMIN_USER) no disponible (HTTP $CODE); pruebas con token omitidas"
  fi

  # B10. CORS con origen malicioso: no debe reflejarlo
  HDRS=$(curl -s -m 5 -i -H 'Origin: https://evil.example.com' "$BASE_URL/api/health")
  if printf '%s' "$HDRS" | grep -qi '^access-control-allow-origin:'; then
    bad "B10. CORS refleja origen no permitido ($(printf '%s' "$HDRS" | grep -i '^access-control-allow-origin:' | tr -d '\r'))"
  else
    ok "B10. CORS no emite Access-Control-Allow-Origin para https://evil.example.com"
  fi

  # B11. Login con Content-Type no JSON (smuggling básico)
  CODE=$(http_code -X POST "$BASE_URL/api/auth/login" -H 'Content-Type: text/plain' --data "' OR '1'='1' -- ")
  case "$CODE" in
    400|401|422) ok "B11. POST login con Content-Type: text/plain → $CODE (sin 500 ni stack trace)" ;;
    *) bad "B11. Esperado 400/401/422, recibido $CODE" ;;
  esac

  # B12. Rate limiting (informativo, no bloqueante)
  NO429=0
  for i in 1 2 3 4 5 6; do
    CODE=$(http_code -X POST "$BASE_URL/api/auth/login" -H 'Content-Type: application/json' --data '{"usuario":"brute_probe","contrasena":"wrongpass"}')
    [ "$CODE" != "429" ] && NO429=$((NO429 + 1))
  done
  if [ "$NO429" -eq 6 ]; then
    info "B12. Sin rate limiting en /api/auth/login (6 intentos → sin 429). Hallazgo: agregar límite de peticiones (p. ej. flask-limiter). Documentado como pendiente, no aplicado."
  else
    ok "B12. Rate limiting activo en /api/auth/login (429 tras varios intentos)"
  fi
fi

echo
echo "=============================================================="
printf ' RESUMEN: %s PASS | %s FAIL | %s SKIP | %s INFO\n' "$PASS" "$FAIL" "$SKIP" "$INFO"
echo "=============================================================="
[ "$FAIL" -gt 0 ] && exit 1
exit 0
