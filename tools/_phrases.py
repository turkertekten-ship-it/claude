#!/usr/bin/env python3
"""Phrase lists shared by the guards.

One definition, imported by both `verify_provenance.py` and `prompt_forge.py`.
A rule that exists in two files is two rules: they drift, and the drift is
silent. If you add a phrase, add it here.
"""

from __future__ import annotations

# Phrases that assert a conversation history nothing in this repository can
# show. In a *document* they are fabricated memory. In a *prompt* they are
# worse: they instruct the model to act on a shared past it does not have,
# which is an invitation to invent one.
FALSE_MEMORY = [
    "as we discussed",
    "as discussed earlier",
    "in our previous chat",
    "in our last conversation",
    "per our last conversation",
    "you previously said",
    "you told me earlier",
    "as you mentioned earlier",
    "as you said before",
    "we agreed that",
    "recall that you",
    "from our earlier chats",
    "based on our past conversations",
]
