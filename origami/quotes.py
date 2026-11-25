from __future__ import annotations

import random

QUOTES: tuple[tuple[str, str], ...] = (
    ("We are what we repeatedly do. Excellence, then, is not an act, but a habit.", "Will Durant"),
    ("Well begun is half done.", "Aristotle"),
    ("It is not that we have a short time to live, but that we waste a lot of it.", "Seneca"),
    ("Nothing will work unless you do.", "Maya Angelou"),
    ("You can't use up creativity. The more you use, the more you have.", "Maya Angelou"),
    ("The impediment to action advances action. What stands in the way becomes the way.", "Marcus Aurelius"),
    (
        "Perfection is achieved, not when there is nothing more to add, but when there is nothing left "
        "to take away.",
        "Antoine de Saint-Exupéry",
    ),
    ("Do what you can, with what you have, where you are.", "Theodore Roosevelt"),
    ("The best way out is always through.", "Robert Frost"),
    ("Little by little, one travels far.", "J. R. R. Tolkien"),
    ("A journey of a thousand miles begins with a single step.", "Lao Tzu"),
    ("Nature does not hurry, yet everything is accomplished.", "Lao Tzu"),
    ("Attention is the rarest and purest form of generosity.", "Simone Weil"),
    ("How we spend our days is, of course, how we spend our lives.", "Annie Dillard"),
    ("Begin anywhere.", "John Cage"),
    ("Make it work, make it right, make it fast.", "Kent Beck"),
    ("Fall seven times, stand up eight.", "Japanese proverb"),
    ("What you do every day matters more than what you do once in a while.", "Gretchen Rubin"),
    ("You do not rise to the level of your goals. You fall to the level of your systems.", "James Clear"),
    ("Plans are worthless, but planning is everything.", "Dwight D. Eisenhower"),
)


def random_quote(seed: int | None = None) -> tuple[str, str]:
    return random.Random(seed).choice(QUOTES)
