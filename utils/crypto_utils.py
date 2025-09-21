import base64
import json

from pathlib import Path
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

class CryptoUtils:
    """加密工具类，用于加密和解密敏感信息"""
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(CryptoUtils, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        self._initialized = True
        self._key = None
        self._fernet = None
        
    def _derive_key(self, password, salt=None):
        """从密码派生密钥"""
        if salt is None:
            # 使用固定的盐值，在生产环境中应该使用随机盐并存储
            salt = b'linlintrans_salt'
        
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        
        return base64.urlsafe_b64encode(kdf.derive(password.encode()))
    
    def initialize(self, password=None):
        """初始化加密工具"""
        if password is None:
            # 如果没有提供密码，尝试从环境变量获取
            password = 'linlin_pan4646606'
        
        self._key = self._derive_key(password)
        self._fernet = Fernet(self._key)
        return self
    
    def encrypt(self, data):
        """加密数据"""
        if self._fernet is None:
            self.initialize()
        
        if isinstance(data, dict):
            data = json.dumps(data)
        
        if isinstance(data, str):
            data = data.encode()
        
        return self._fernet.encrypt(data)
    
    def decrypt(self, encrypted_data):
        """解密数据"""
        if self._fernet is None:
            self.initialize()
        
        decrypted_data = self._fernet.decrypt(encrypted_data)
        
        try:
            # 尝试解析为JSON
            return json.loads(decrypted_data)
        except json.JSONDecodeError:
            # 如果不是JSON，返回解密后的字符串
            return decrypted_data.decode()
    
    def encrypt_to_file(self, data, file_path):
        """将加密数据保存到文件"""
        encrypted_data = self.encrypt(data)
        
        with open(file_path, 'wb') as f:
            f.write(encrypted_data)
    
    def decrypt_from_file(self, file_path):
        """从文件中读取并解密数据"""
        with open(file_path, 'rb') as f:
            encrypted_data = f.read()
        
        return self.decrypt(encrypted_data)
    
    def get_credentials_file_path(self,root_path):
        # 在项目根目录下创建一个隐藏的凭证文件
        credentials_dir = Path(root_path) / '.credentials'
        credentials_dir.mkdir(exist_ok=True)
        
        return credentials_dir / 'aliyun_credentials.enc'

# 创建单例实例
crypto_utils = CryptoUtils()
