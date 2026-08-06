"""ASGI middleware for the retail voice application.

Kept as a package so transport-level concerns (request size limits, and
anything similar added later) stay out of backend/app/main.py, which is
deliberately a thin wiring module.
"""
