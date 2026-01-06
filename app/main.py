import uvicorn
from fastapi import FastAPI
from app.api import auth, users


app = FastAPI()

app.include_router(auth.router, prefix="/users", tags=["Пользователи"])
app.include_router(users.router, prefix="/users", tags=["Пользователи"])

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
    )