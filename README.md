# Diplom-Fingerprinting Demo

A self-contained demo that launches **two Docker stacks**:

- **UOIS** – the University Open Information System (backend & database)
- **FastAPI-Fingerprinting** – service that extracts TLS/HTTP fingerprints and serves an OpenAPI UI

Both stacks share a custom Docker network so they can communicate securely over HTTPS.

## 1 · Clone the repository

    git clone https://github.com/Hieulangtu/Diplom-Fingerprinting.git
    cd Diplom-Fingerprinting

---

## 2 · Create the shared Docker network

    docker network create shared-net-uois

_(Skip if it already exists.)_

---

## 3 · Start the **UOIS** stack

    cd _uois
    docker compose -f docker-compose.hk2025.yml up -d

---

## 4 · Start the **FastAPI-Fingerprinting** stack

    cd ../fastAPI-fingerprinting
    docker compose up -d    # uses docker-compose.yml

---

## 5 · Verify the services

### FastAPI service

Open your browser:

    https://localhost/docs#

You’ll get Swagger / OpenAPI where you can test the fingerprinting endpoints.

### UOIS service (curl only)

**Sign up**

curl -k -X POST https://localhost/auth/signup -H "Content-Type: application/json" -d "{\"username\":\"newuser\",\"email\":\"newuser@example.com\",\"password\":\"pass\",\"is_staff\":false,\"is_active\":true}"

**Log in**

curl -k -i -c jar.txt -X POST https://localhost/auth/login -H "Content-Type: application/json" -d "{\"username\":\"newuser\",\"password\":\"pass\"}"

**access server** (Take the access token from Log in phase)

curl -L -k -i -b jar.txt -H "Authorization: Bearer <Token>" https://localhost/

If successful, a `Set-Cookie` header is returned; reuse it with `-b jar.txt` for subsequent calls.

---
