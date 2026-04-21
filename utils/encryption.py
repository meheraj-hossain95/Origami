import config

class EncryptionManager:
    def __init__(self):
        self.master_password = "default_master_key_2024"

    def _xor(self, data: bytes, password: str) -> bytes:
        if not password:
            raise ValueError("Password required")

        key = password.encode()
        return bytes(b ^ key[i % len(key)] for i, b in enumerate(data))

    def encrypt(self, text: str, password: str):
        encrypted = self._xor(text.encode(), password)
        return encrypted, b'simple_salt'

    def decrypt(self, encrypted: bytes, password: str) -> str:
        return self._xor(encrypted, password).decode()

    def encrypt_master(self, text: str) -> bytes:
        return self._xor(text.encode(), self.master_password)

    def decrypt_master(self, encrypted: bytes) -> str:
        return self._xor(encrypted, self.master_password).decode()


encryption_manager = EncryptionManager()


def encrypt_journal_entry(content: str, use_password=False, password=None):
    if use_password:
        return encryption_manager.encrypt(content, password)
    return encryption_manager.encrypt_master(content), None


def decrypt_journal_entry(encrypted: bytes, salt=None, password=None):
    if password:
        return encryption_manager.decrypt(encrypted, password)
    return encryption_manager.decrypt_master(encrypted)


def is_encryption_available() -> bool:
    try:
        t = "test"
        return encryption_manager.decrypt_master(
            encryption_manager.encrypt_master(t)
        ) == t
    except Exception:
        return False