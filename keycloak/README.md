# Keycloak

This package contains the Keycloak configuration.

Keycloak is an open-source Identity and Access Management solution aimed at modern applications and services. It makes it easy to secure applications and services with little to no code.

## How To Add A New User

1. Go to: http://iai-ml4home028.iai.kit.edu/auth
2. Login with your admin account
3. Change the realm to `chatbot` (top left corner)
4. Go to `Users` and click on `Add user`
5. Set a username and an Email (check `Email verified` as we don't have an email server). Add the user to the developer if he should have access to the developer tools
6. After creating the user, go to the `Credentials` tab, set a password and enable `Temporary` to force the user to change the password on the first login.
7. Everything is set up! Give username and temporary password to the user.

## Docker Container

### [PostgreSQL Database](https://hub.docker.com/_/postgres)

- **Image**: `postgres:16`
- **Description**: The Postgres database stores the data for Keycloak

### [Keycloak](https://www.keycloak.org/)
The Keycloak Service in this repository authentificates Users via a "oauth" client. The Authentification process is however started inside the frontend, so do not set the "Client Authentification" flag in Keycloak.
The Example Enpoints used throughout this repositiory depend on a custom Keycloak Realm called "chatbot", keep it in when creating your own endpoints.

- **Image**: `quay.io/keycloak/keycloak:23.0`
- **Description**: Keycloak is an open-source Identity and Access Management solution aimed at modern applications and services. It makes it easy to secure applications and services with little to no code.
- **Url**: [http://iai-ml4home028.iai.kit.edu/auth](http://iai-ml4home028.iai.kit.edu/auth)
