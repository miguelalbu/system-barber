"""
Control plane: creates, suspends, resumes and destroys shops (doc §6).

Called by the platform Core — never by a shop user — with its own credential
(`X-Core-Key`). Depends on `identity` through its `public.py`.
"""
