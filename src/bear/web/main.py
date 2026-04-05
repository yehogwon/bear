from __future__ import annotations

import uvicorn

from bear.config.settings import Settings


def main() -> None:
    settings = Settings()
    uvicorn.run('bear.web.app:create_app', host=settings.host, port=settings.port, factory=True)


if __name__ == '__main__':
    main()
