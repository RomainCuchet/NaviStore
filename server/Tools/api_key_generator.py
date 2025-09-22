"""
Secure API Key Generator
Usage: python generate_api_key.py
"""

import secrets
import string
from typing import Optional


class APIKeyGenerator:
    """
    Cryptographically secure API key generator.
    TODO: probability of collision is almost zero but could be tested.
    """

    @staticmethod
    def generate_api_key(length: int = 32, prefix: Optional[str] = None) -> str:
        """
        Generate a secure alphanumeric API key

        Args:
            length: Length of the key (minimum 16 recommended)
            prefix: Optional prefix for the key (e.g., 'api_', 'sk_')

        Returns:
            Cryptographically secure API key

        Raises:
            ValueError: If length is less than 16
        """
        if length < 16:
            raise ValueError(
                "API key length must be at least 16 characters for security"
            )

        # Use letters and digits for readability and URL safety
        alphabet = string.ascii_letters + string.digits

        # Generate cryptographically secure random key
        key = "".join(secrets.choice(alphabet) for _ in range(length))

        # Add prefix if provided
        if prefix:
            return f"{prefix}{key}"

        return key

    @staticmethod
    def generate_multiple_keys(
        count: int, length: int = 32, prefix: Optional[str] = None
    ) -> list[str]:
        """
        Generate multiple API keys at once

        Args:
            count: Number of keys to generate
            length: Length of each key
            prefix: Optional prefix for keys

        Returns:
            List of unique API keys
        """
        keys = []
        for _ in range(count):
            key = APIKeyGenerator.generate_api_key(length, prefix)
            keys.append(key)

        return keys

    @staticmethod
    def run_interface():
        """Main function to generate API keys"""
        print("🔑 Secure API Key Generator\n")

        # Interactive generation
        try:
            num_keys = input(
                "How many API keys do you want to generate? (default: 1): "
            )
            num_keys = int(num_keys) if num_keys.strip() else 1

            length = input("Key length? (default: 32): ")
            length = int(length) if length.strip() else 32

            prefix = input("Key prefix (optional): ")
            prefix = prefix if prefix.strip() else None

            print(f"\n🔑 Generated {num_keys} API key(s):")
            print("-" * 50)

            if num_keys == 1:
                key = APIKeyGenerator.generate_api_key(length, prefix)
                print(key)
            else:
                keys = APIKeyGenerator.generate_multiple_keys(num_keys, length, prefix)
                for i, key in enumerate(keys, 1):
                    print(f"{i:2d}: {key}")

        except ValueError as e:
            print(f"❌ Error: {e}")
            return
        except KeyboardInterrupt:
            print("\n👋 Goodbye!")
            return


if __name__ == "__main__":
    APIKeyGenerator.run_interface()
