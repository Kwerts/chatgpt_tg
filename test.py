import secrets
import string


def generate():
    alphabet = string.ascii_letters + string.digits
    password = ''
    for _ in range(12):
        password += secrets.choice(alphabet)
    return password

print(generate())