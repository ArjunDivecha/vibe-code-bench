import random
import string

def generate_password(length=12, uppercase=False, numbers=False, symbols=False):
    characters = string.ascii_lowercase
    if uppercase:
        characters += string.ascii_uppercase
    if numbers:
        characters += string.digits
    if symbols:
        characters += string.punctuation
    
    return ''.join(random.choice(characters) for _ in range(length))

def calculate_password_strength(password):
    strength = len(password)
    print(f"Password strength: {strength} characters")

def main():
    password = generate_password(12, True, True, True)
    print(f"Generated password: {password}")
    calculate_password_strength(password)

if __name__ == "__main__":
    main()