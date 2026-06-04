import os

import uvicorn

from niuke_mianjing_backend.config import settings


def main() -> None:
    host = os.getenv("API_HOST", "127.0.0.1")
    port = int(os.getenv("API_PORT", str(settings.API_PORT or 8000)))

    uvicorn.run(
        "niuke_mianjing_backend.api.app:app",
        host=host,
        port=port,
        reload=True,
    )


if __name__ == "__main__":
    main()
