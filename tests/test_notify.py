import types
from fastapi import BackgroundTasks

import pytest


def test_notify_subscribers_queues_emails(monkeypatch):
    # Capture calls to the send_email used by newsletter_service
    sent = []

    def fake_send_email(background_tasks, to_email, subject, html):
        sent.append((to_email, subject))

    # Patch the send_email symbol inside the newsletter_service module
    monkeypatch.setattr('src.services.newsletter_service.send_email', fake_send_email)

    # Build fake subscribers
    class Sub:
        def __init__(self, email):
            self.email = email

    subscribers = [Sub('a@example.com'), Sub('b@example.com')]

    # Minimal fake DB with query(...).filter(...).all() chain
    class FakeQuery:
        def __init__(self, subs):
            self._subs = subs

        def filter(self, *args, **kwargs):
            return self

        def all(self):
            return self._subs

    class FakeDB:
        def __init__(self, subs):
            self._query = FakeQuery(subs)

        def query(self, model):
            return self._query

    fake_db = FakeDB(subscribers)

    # Create a simple coupon-like object
    coupon = types.SimpleNamespace(
        coupon_code='TEST10',
        coupon_name='Test Coupon',
        discount_value=10,
        discount_type='percent',
        expiry_date='2026-12-31',
        coupon_description='Test description'
    )

    # Call notify_subscribers
    from src.services.newsletter_service import notify_subscribers

    bg = BackgroundTasks()
    notify_subscribers(fake_db, coupon, bg, batch_size=50)

    # Our fake_send_email should have been called for each subscriber
    assert len(sent) == 2
    assert {s[0] for s in sent} == {'a@example.com', 'b@example.com'}
