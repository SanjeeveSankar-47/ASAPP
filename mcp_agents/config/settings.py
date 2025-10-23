from pydantic.v1 import BaseSettings

class Settings(BaseSettings):
    NVIDIA_API_KEY: str = ""
    GROQ_API_KEY: str = ""
    SERPAPI_API_KEY: str = ""
    #DEFAULT_DATA_PATH: str = "C:\\Users\\arun5\\Desktop\\SAP\\src\\data\\Procurement KPI Analysis Dataset.csv"
    #DATABASE_URL: str = "sqlite+aiosqlite:///./SAP.db"

    class Config:
        env_file = ".env"
        case_sensitive = True   
    

settings = Settings()
