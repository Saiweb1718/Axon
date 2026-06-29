"""External integrations the Execution agent can deliver into (Gmail, CRM, …).

Each is optional and degrades gracefully: if it isn't configured, the platform
still drafts the artifact — it just doesn't push it anywhere.
"""
