import uvicorn

from src.application import app
from src.settings import SETTINGS


if __name__ == "__main__":
    uvicorn.run(
        "src.main:app",
        host=SETTINGS.APP.HOST,
        port=SETTINGS.APP.PORT,
        reload=SETTINGS.APP.RELOAD,
    )

