"""
Motivational quotes for the Personal Software application
"""

MOTIVATIONAL_QUOTES = [
    {
        "text": "The only way to do great work is to love what you do.",
        "author": "Steve Jobs"
    },
    {
        "text": "Don't watch the clock; do what it does. Keep going.",
        "author": "Sam Levenson"
    },
    {
        "text": "Believe you can and you're halfway there.",
        "author": "Theodore Roosevelt"
    },
    {
        "text": "Everything you've ever wanted is on the other side of fear.",
        "author": "George Addair"
    },
    {
        "text": "It always seems impossible until it's done.",
        "author": "Nelson Mandela"
    },
    {
        "text": "Your time is limited, so don't waste it living someone else's life.",
        "author": "Steve Jobs"
    },
    {
        "text": "I can't change the direction of the wind, but I can adjust my sails to always reach my destination.",
        "author": "Jimmy Dean"
    },
    {
        "text": "The best way to predict the future is to create it.",
        "author": "Abraham Lincoln"
    },
    {
        "text": "Success is not final, failure is not fatal: it is the courage to continue that counts.",
        "author": "Winston Churchill"
    },
    {
        "text": "The future belongs to those who believe in the beauty of their dreams.",
        "author": "Eleanor Roosevelt"
    },
    {
        "text": "It does not matter how slowly you go as long as you do not stop.",
        "author": "Confucius"
    },
    {
        "text": "Everything you can imagine is real.",
        "author": "Pablo Picasso"
    },
    {
        "text": "Do what you can, with what you have, where you are.",
        "author": "Theodore Roosevelt"
    },
    {
        "text": "Act as if what you do makes a difference. It does.",
        "author": "William James"
    },
    {
        "text": "Success usually comes to those who are too busy to be looking for it.",
        "author": "Henry David Thoreau"
    },
    {
        "text": "Don't be afraid to give up the good to go for the great.",
        "author": "John D. Rockefeller"
    },
    {
        "text": "I find that the harder I work, the more luck I seem to have.",
        "author": "Thomas Jefferson"
    },
    {
        "text": "The way to get started is to quit talking and begin doing.",
        "author": "Walt Disney"
    },
    {
        "text": "The pessimist sees difficulty in every opportunity. The optimist sees opportunity in every difficulty.",
        "author": "Winston Churchill"
    },
    {
        "text": "Don't let yesterday take up too much of today.",
        "author": "Will Rogers"
    }
]

def get_random_quote():
    """Get a random quote from the collection"""
    import random
    quote = random.choice(MOTIVATIONAL_QUOTES)
    return f"{quote['text']} — {quote['author']}"

def get_all_quotes():
    """Get all quotes"""
    return MOTIVATIONAL_QUOTES

def get_formatted_quotes():
    """Get all quotes formatted as strings"""
    return [f"{q['text']} — {q['author']}" for q in MOTIVATIONAL_QUOTES]