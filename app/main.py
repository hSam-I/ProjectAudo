from app.logging.logger import logger
from app.config.settings import APP_NAME, APP_ENV


def main():
    logger.info(f"{APP_NAME} started")
    logger.info(f"Environment: {APP_ENV}")


if __name__ == "__main__":
    main()