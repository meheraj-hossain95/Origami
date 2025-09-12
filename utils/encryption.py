"""
Encryption utilities for journal entries - simplified version without cryptography dependency
"""
import os
import base64
import config

class EncryptionManager:
    """Handle encryption and decryption of sensitive data - simplified version"""
    
    def __init__(self):
        self.key_file = config.ENCRYPTION_KEY_FILE if hasattr(config, 'ENCRYPTION_KEY_FILE') else 'encryption.key'
    
    def simple_encrypt(self, text: str, password: str) -> tuple:
        """Simple encryption using password (placeholder implementation)"""
        try:
            # Simple XOR-based encryption (not secure, just for demonstration)
            password_bytes = password.encode('utf-8')
            text_bytes = text.encode('utf-8')
            
            encrypted = bytearray()
            for i, byte in enumerate(text_bytes):
                encrypted.append(byte ^ password_bytes[i % len(password_bytes)])
            
            return bytes(encrypted), b'simple_salt'
        except Exception as e:
            raise Exception(f"Encryption failed: {str(e)}")
    
    def simple_decrypt(self, encrypted_data: bytes, password: str, salt: bytes = None) -> str:
        """Simple decryption using password (placeholder implementation)"""
        try:
            # Simple XOR-based decryption
            password_bytes = password.encode('utf-8')
            
            decrypted = bytearray()
            for i, byte in enumerate(encrypted_data):
                decrypted.append(byte ^ password_bytes[i % len(password_bytes)])
            
            return bytes(decrypted).decode('utf-8')
        except Exception as e:
            raise Exception(f"Decryption failed: {str(e)}")
    
    def encrypt_text(self, text: str, password: str) -> tuple:
        """Encrypt text with password"""
        return self.simple_encrypt(text, password)
    
    def decrypt_text(self, encrypted_data: bytes, password: str, salt: bytes) -> str:
        """Decrypt text with password"""
        return self.simple_decrypt(encrypted_data, password, salt)
    
    def encrypt_with_master_key(self, text: str) -> bytes:
        """Encrypt text using a simple master key"""
        try:
            # Use a simple default password for master key
            master_password = "default_master_key_2024"
            encrypted, _ = self.simple_encrypt(text, master_password)
            return encrypted
        except Exception as e:
            raise Exception(f"Master key encryption failed: {str(e)}")
    
    def decrypt_with_master_key(self, encrypted_data: bytes) -> str:
        """Decrypt text using a simple master key"""
        try:
            master_password = "default_master_key_2024"
            return self.simple_decrypt(encrypted_data, master_password)
        except Exception as e:
            raise Exception(f"Master key decryption failed: {str(e)}")

# Global encryption manager instance
encryption_manager = EncryptionManager()

def encrypt_journal_entry(content: str, use_password: bool = False, password: str = None) -> tuple:
    """
    Encrypt journal entry content
    Returns (encrypted_data, salt) if password is used, otherwise (encrypted_data, None)
    """
    if use_password and password:
        return encryption_manager.encrypt_text(content, password)
    else:
        # Use master key encryption
        encrypted_data = encryption_manager.encrypt_with_master_key(content)
        return encrypted_data, None

def decrypt_journal_entry(encrypted_data: bytes, salt: bytes = None, password: str = None) -> str:
    """
    Decrypt journal entry content
    """
    if salt and password:
        return encryption_manager.decrypt_text(encrypted_data, password, salt)
    else:
        # Use master key decryption
        return encryption_manager.decrypt_with_master_key(encrypted_data)

def is_encryption_available() -> bool:
    """Check if encryption is available and properly configured"""
    try:
        # Test encryption/decryption
        test_text = "test"
        encrypted = encryption_manager.encrypt_with_master_key(test_text)
        decrypted = encryption_manager.decrypt_with_master_key(encrypted)
        return decrypted == test_text
    except Exception:
        return False
