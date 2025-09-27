import hashlib
import base64
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad


def encrypt_data(content: str, device_id: str, timestamp: str, aes_key: str) -> str:
    """AES CBC PKCS7 加密"""
    key = aes_key.encode("utf-8")

    # iv = SHA1(deviceId + timestamp).hexdigest()[:16]
    sha1_str = hashlib.sha1((device_id + timestamp).encode("utf-8")).hexdigest()
    iv = sha1_str[:16].encode("utf-8")

    cipher = AES.new(key, AES.MODE_CBC, iv)
    padded_data = pad(content.encode("utf-8"), AES.block_size)
    encrypted_bytes = cipher.encrypt(padded_data)

    return base64.b64encode(encrypted_bytes).decode("utf-8")


def decrypt_data(encrypted_base64: str, device_id: str, timestamp: str, aes_key: str) -> str:
    """AES CBC PKCS7 解密"""
    key = aes_key.encode("utf-8")

    sha1_str = hashlib.sha1((device_id + timestamp).encode("utf-8")).hexdigest()
    iv = sha1_str[:16].encode("utf-8")

    cipher = AES.new(key, AES.MODE_CBC, iv)
    encrypted_bytes = base64.b64decode(encrypted_base64)
    decrypted_bytes = unpad(cipher.decrypt(encrypted_bytes), AES.block_size)

    return decrypted_bytes.decode("utf-8")


# 示例
if __name__ == "__main__":
    key = "1234567890123456"   # 16字节密钥
    device_id = "device123"
    timestamp = "1690000000"

    text = "hello world"
    enc = encrypt_data(text, device_id, timestamp, key)
    print("加密结果:", enc)

    dec = decrypt_data(enc, device_id, timestamp, key)
    print("解密结果:", dec)
