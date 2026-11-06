"""
Catalog: what a shop sells — services today; combos, clubs and plans later.

Also owns which services each barber performs (`barber_services`), pointing at
identity's `barbers` table by foreign key only. Depends on `identity` through
its `public.py`; identity never imports this module.
"""
