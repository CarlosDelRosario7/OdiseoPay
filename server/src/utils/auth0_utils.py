import jwt
from flask import current_app
from jwt import PyJWKClient


def validate_auth0_token(token: str) -> dict:
    domain = current_app.config["AUTH0_DOMAIN"]
    audience = current_app.config["AUTH0_AUDIENCE"]
    algorithms = current_app.config["AUTH0_ALGORITHMS"]

    if not domain or not audience:
        raise RuntimeError("Auth0 no está configurado correctamente.")

    issuer = f"https://{domain}/"
    jwks_url = f"{issuer}.well-known/jwks.json"

    jwks_client = PyJWKClient(jwks_url)
    signing_key = jwks_client.get_signing_key_from_jwt(token)

    payload = jwt.decode(
        token,
        signing_key.key,
        algorithms=algorithms,
        audience=audience,
        issuer=issuer,
    )

    return payload