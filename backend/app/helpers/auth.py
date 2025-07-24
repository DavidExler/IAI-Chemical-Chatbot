import functools
import logging
import os
from collections.abc import Callable
from dataclasses import dataclass

import requests
from fastapi import Depends, HTTPException, Request
from fastapi.security import OAuth2PasswordBearer
from jose import jwt

LOGGER = logging.getLogger(__name__)


@dataclass
class KeycloakUser:
    sub: str
    azp: str | None = None
    roles: list[str] = None
    preferred_username: str | None = None
    username: str | None = None

    @property
    def user_id(self) -> str:
        return self.sub

    @property
    def name(self) -> str | None:
        return self.preferred_username or self.username


class FastAPIKeycloak:
    realm_uri: str = os.environ.get(
        "KEYCLOAK_REALM_URI", "http://iai-ml4home028.iai.kit.edu/auth/realms/chatbot"
    )
    timeout: int = 10

    @functools.cached_property
    def open_id_configuration(self) -> dict:
        LOGGER.debug(f"Fetching OpenID configuration from {self.realm_uri}")
        return requests.get(
            url=f"{self.realm_uri}/.well-known/openid-configuration",
            timeout=self.timeout,
        ).json()

    @functools.cached_property
    def token_uri(self) -> str:
        return self.open_id_configuration.get("token_endpoint")

    @functools.cached_property
    def user_auth_scheme(self) -> OAuth2PasswordBearer:
        return OAuth2PasswordBearer(tokenUrl=self.token_uri)

    async def user_auth_scheme_by_request(self, request: Request) -> str | None:
        return await OAuth2PasswordBearer(tokenUrl=self.token_uri)(request=request)

    @functools.cached_property
    def public_key(self) -> str:
        LOGGER.debug(f"Fetching public key from {self.realm_uri}")
        response = requests.get(url=self.realm_uri, timeout=self.timeout)
        public_key = response.json()["public_key"]
        return f"-----BEGIN PUBLIC KEY-----\n{public_key}\n-----END PUBLIC KEY-----"

    def get_current_user(
        self, required_roles: list[str] = None
    ) -> Callable[[OAuth2PasswordBearer], KeycloakUser]:
        def current_user(
            token: OAuth2PasswordBearer = Depends(self.user_auth_scheme),
        ) -> KeycloakUser:
            LOGGER.debug(f"Checking user authentication")
            decoded_token = jwt.decode(token, self.public_key, audience="account")
            user = KeycloakUser(
                sub=decoded_token["sub"],
                azp=decoded_token["azp"],
                roles=decoded_token.get("roles", []),
                preferred_username=decoded_token.get("preferred_username"),
                username=decoded_token.get("username"),
            )

            if any(r not in user.roles for r in required_roles or []):
                raise HTTPException(
                    status_code=403,
                    detail=f"Role '{required_roles}' is required to access this resource",
                )

            return user

        return current_user

    async def current_user_by_request(self, request: Request) -> KeycloakUser | None:
        try:
            LOGGER.debug(f"Checking user authentication by request")
            token = await self.user_auth_scheme_by_request(request)
            decoded_token = jwt.decode(token, self.public_key, audience="account")
            return KeycloakUser(
                sub=decoded_token["sub"],
                azp=decoded_token["azp"],
                roles=decoded_token.get("roles", []),
                preferred_username=decoded_token.get("preferred_username"),
                username=decoded_token.get("username"),
            )
        except Exception:
            return None
