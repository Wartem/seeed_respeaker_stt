# vosk_model_setup.py

from typing import Optional

from pathlib import Path
import wget
import zipfile
import shutil
import logging

def setup_vosk_model(model_path: str) -> Optional[str]:
    """
    Ensures the Vosk model exists at the specified path, downloading it if necessary.

    Args:
        model_path: Path to the model directory

    Returns:
        str: Path to the model directory if successful, None if failed
    """
    model_path = Path(model_path)
    zip_path = None
    logger = logging.getLogger(__name__)

    if model_path.exists():
        logger.info(f"Model already exists at {model_path}")
        return str(model_path)

    try:
        model_path.parent.mkdir(parents=True, exist_ok=True)
        model_name = model_path.name

        base_url = "https://alphacephei.com/vosk/models"
        zip_filename = f"{model_name}.zip"
        download_url = f"{base_url}/{zip_filename}"

        logger.info(f"Downloading Vosk model from {download_url}")
        zip_path = model_path.parent / zip_filename
        wget.download(download_url, str(zip_path))
        logger.info("Download completed")

        logger.info(f"Extracting model to {model_path.parent}")
        with zipfile.ZipFile(zip_path, "r") as zip_ref:
            zip_ref.extractall(str(model_path.parent))

        logger.info(f"Removing temporary zip file: {zip_path}")
        if zip_path.exists():
            zip_path.unlink()
            logger.info("Zip file removed successfully")

        logger.info("Model setup completed successfully")
        return str(model_path)

    except Exception as e:
        logger.error(f"Error setting up Vosk model: {str(e)}")
        if zip_path and zip_path.exists():
            logger.info(f"Cleaning up temporary zip file: {zip_path}")
            zip_path.unlink()
        if model_path.exists():
            logger.info(f"Cleaning up partial model directory: {model_path}")
            shutil.rmtree(model_path)
        raise
