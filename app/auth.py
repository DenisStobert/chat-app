from passlib.context import CryptContext
from datetime import datetime, timedelta
from jose import JWTError, jwt
import json

SECRET_KEY = "your_secret_key"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    
    # 🔥 Убеждаемся, что sub хранит строку (email)
    if "sub" in to_encode and isinstance(to_encode["sub"], dict):
        to_encode["sub"] = json.dumps(to_encode["sub"])  # Превращаем в строку
    
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
