from pathlib import Path

from app.config import settings
from app.db import SessionLocal
from app.seed.run import seed_all


def main() -> None:
    with SessionLocal() as session:
        for line in seed_all(session, Path(settings.seed_dir)):
            print(f"Seed: {line}")


if __name__ == "__main__":
    main()
