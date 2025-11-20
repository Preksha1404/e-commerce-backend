# 🛒 Multi-Role E-Commerce Platform — Backend

[![Python](https://img.shields.io/badge/Python-3.10-blue)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.95-green)](https://fastapi.tiangolo.com/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15-blue)](https://www.postgresql.org/)
[![License](https://img.shields.io/badge/License-MIT-green)](LICENSE)

A production-oriented backend for a multi-role e-commerce platform supporting Admins, Sellers, and Customers. Features include authentication, product management, cart & checkout, coupons, payments (Stripe), order management, dashboards, notifications, and AI-powered review summaries.

---

## Table of contents
- [Key features](#key-features)
- [Tech stack](#tech-stack)
- [Getting started](#getting-started)
    - [Requirements](#requirements)
    - [Local setup](#local-setup)
    - [Run the server](#run-the-server)
- [Testing](#testing)
- [Development notes](#development-notes)
- [License](#license)

---

## Key features
- Role-based authentication (Admin, Seller, Customer) with JWT
- Product CRUD, CSV bulk upload, approvals
- Cart, checkout, order creation, invoices
- Coupons: percentage/flat, min cart value, expiry, usage limits
- Stripe integration (test mode), payment webhooks
- Seller & Admin dashboards and analytics
- Email notifications and seller alerts
- Wishlist & reviews, review moderation
- LLM-powered review summaries and product Q/A
- File uploads via Cloudinary

---

## Tech stack
- Backend: FastAPI, Pydantic
- ORM: SQLAlchemy
- Auth: JWT
- DB: PostgreSQL
- Payments: Stripe (test)
- File storage: Cloudinary
- Deployment: Render

---

## Getting started

### Requirements
- Python 3.10+
- PostgreSQL 12+

Adjust keys to your setup.

### Local setup (example)
1. Clone repo
     - git clone <repo-url> && cd e-commerce-backend
2. Create and activate virtualenv
     - python -m venv .venv
     - source .venv/bin/activate  (Windows: .venv\Scripts\activate)
3. Install dependencies
     - pip install -r requirements.txt
4. Create `.env` using the `.env.example` file.

### Run the server
- Development:
    - uvicorn src.main:app --reload
- API docs:
    - Open http://localhost:8000/docs (Swagger)


---

## Development notes
- Project structure follows modular FastAPI apps (routers, services, models).
- Use dependency injection for DB sessions and external services (Stripe, Cloudinary).
- Important endpoints: auth, products, cart, orders, coupons, webhooks (/webhooks/stripe).
- Implement proper rate limiting and input validation in production.


---

## License
This project is licensed under the MIT License. See LICENSE for details.

---

