from dotenv import load_dotenv
import os

load_dotenv()

class Settings:
    DATABASE_URL: str = os.getenv("DATABASE_URL")
    SECRET_KEY: str = os.getenv("SECRET_KEY")
    ORS_API_KEY: str = os.getenv("ORS_API_KEY")
    ALGORITHM: str = os.getenv("ALGORITHM", "HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 60))
    
    NAVITIA_TOKEN: str = os.getenv("NAVITIA_TOKEN")
    NAVITIA_COVERAGE: str = os.getenv("NAVITIA_COVERAGE", "fr-idf")

settings = Settings()





