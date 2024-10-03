import random
import string
import os
import json

def generate_api_key(length=32):
    """Generate a random API key."""
    characters = string.ascii_letters + string.digits
    api_key = ''.join(random.choice(characters) for _ in range(length))
    return api_key

def save_api_key(api_key, filename='api_key.json'):
    """Save the API key to a file in JSON format."""
    # expire_time = datetime.now(timezone.utc) + timedelta(days=30)  # Example expiration time
    data = {
        "api_id": 1,
        "api": api_key
        # "token_expire": expire_time.isoformat()
    }
    with open(filename, 'w') as file:
        json.dump(data, file)
    print(f"API key saved to {filename}")

def load_api_key(filename='api_key.json'):
    """Load the API key from a file."""
    if not os.path.exists(filename):
        print(f"{filename} does not exist. Generating a new API key.")
        api_key = generate_api_key()
        save_api_key(api_key, filename)
    else:
        with open(filename, 'r') as file:
            data = json.load(file)
            api_key = data["api"]
    return api_key

if __name__ == "__main__":
    # Generate and save a new API key
    new_api_key = generate_api_key()
    save_api_key(new_api_key)

    # Load the API key (this will load the existing key or generate a new one if the file doesn't exist)
    api_key = load_api_key()
    print(f"Loaded API key: {api_key}")
