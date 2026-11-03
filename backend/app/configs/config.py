import os

class Settings:
    #----------------------------------
    DATABASE_URL: str = os.getenv("DATABASE_URL", "")

    
    #---------------------------------
    JWT_SECRET_KEY: str = os.getenv(
        "JWT_SECRET_KEY",
        "development-secret-key",
    )

    JWT_ALGORITHM: str = os.getenv(
        "JWT_ALGORITHM",
        "HS256",
    )

    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(
        os.getenv(
            "ACCESS_TOKEN_EXPIRE_MINUTES",
            "60",
        )
    )

    #CHANGE IN PROD
    FRONTEND_ORIGIN: str = os.getenv(
    "FRONTEND_ORIGIN",
    "http://localhost:5173",
    )

    AUTH_COOKIE_SECURE: bool = (os.getenv("AUTH_COOKIE_SECURE", "false").lower() == "true")
    #----------------
    
    #---------------------------------
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    REDIS_PASSWORD: str = os.getenv("REDIS_PASSWORD", "")
    PMI_SESSION_IDLE_TTL_SECONDS: int = int(
        os.getenv("PMI_SESSION_IDLE_TTL_SECONDS", "1800")
    )
    PMI_SESSION_MAX_TTL_SECONDS: int = int(
        os.getenv("PMI_SESSION_MAX_TTL_SECONDS", "14400")
    )
    PMI_MAX_OPEN_SESSIONS_PER_USER: int = int(
        os.getenv("PMI_MAX_OPEN_SESSIONS_PER_USER", "5")
    )
    

settings = Settings()