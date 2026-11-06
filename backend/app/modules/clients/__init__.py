"""
Clients: the shop's end customers — who books, at the desk or over WhatsApp.

A client belongs to the shop, not to a unit (spec P3), and is identified by
the phone number in E.164 (P2): the WhatsApp channel finds them by it.
Depends on `identity` through its `public.py`.
"""
