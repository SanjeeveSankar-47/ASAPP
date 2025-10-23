from pydantic.v1 import BaseSettings

class Settings(BaseSettings):
    NVIDIA_API_KEY: str = "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"
    GROQ_API_KEY: str = "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"
    SERPAPI_API_KEY: str = "5a900c620380c877837cc95ba954c9db5b7f6ee59a8cfb0a23400ee658be6c7c"
    LLM_MODEL : str = "nv-mistralai/mistral-nemo-12b-instruct"
    #DEFAULT_DATA_PATH: str = "C:\\Users\\arun5\\Desktop\\SAP\\src\\data\\Procurement KPI Analysis Dataset.csv"
    #DATABASE_URL: str = "sqlite+aiosqlite:///./SAP.db"

    class Config:
        env_file = ".env"
        case_sensitive = True   
    
settings = Settings()