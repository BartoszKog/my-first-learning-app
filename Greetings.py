import random
from datetime import datetime

class Greetings:
    morning_greetings = ["Good morning!", "Morning!", "Top of the morning!"]
    afternoon_greetings = ["Good afternoon!", "Hello!", "Good day!", "Hi!"]
    evening_greetings = ["Good evening!", "Evening!", "Hi there!"]

    @classmethod
    def get_greeting(cls):
        current_hour = datetime.now().hour
        if 5 <= current_hour < 12:
            return random.choice(cls.morning_greetings)
        elif 12 <= current_hour < 18:
            return random.choice(cls.afternoon_greetings)
        else:
            return random.choice(cls.evening_greetings)