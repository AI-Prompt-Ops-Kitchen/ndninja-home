import bcrypt

class UserService:
    @staticmethod
    def hash_password(password: str) -> str:
        """Hash a password using bcrypt"""
        # bcrypt automatically handles the 72-byte limit
        salt = bcrypt.gensalt(rounds=12)
        hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
        return hashed.decode('utf-8')

    @staticmethod
    def verify_password(password: str, hashed: str) -> bool:
        """Verify a password against a bcrypt hash"""
        return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))
