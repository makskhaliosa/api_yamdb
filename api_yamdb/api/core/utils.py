import random


def generate_code(start=0, end=9, size=6):
    confirmation_code = ''.join(
        [str(random.randint(start, end)) for x in range(size)])
    return confirmation_code
