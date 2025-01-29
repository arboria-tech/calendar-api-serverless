import os
import shutil
import subprocess
import tempfile
from typing import List, Tuple
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Define constants
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
SRC_DIR = os.path.join(BASE_DIR, 'src')
TERRAFORM_DIR = os.path.join(SRC_DIR, 'terraform')
DEPLOYMENTS_DIR = os.path.join(TERRAFORM_DIR, 'deployments')
LAMBDA_SOURCE_DIR = os.path.join(SRC_DIR, 'lambdas')
LAYER_SOURCE_DIR = os.path.join(SRC_DIR, 'layers')

# List of Lambda functions to zip
LAMBDA_FUNCTIONS = [
    'google_calendar_credentials_callback',
    'redirect_google_credentials',
    'get_calendar_events',
    'create_calendar_event'
]

def ensure_directory_exists(directory: str) -> None:
    """Create directory if it doesn't exist."""
    if not os.path.exists(directory):
        os.makedirs(directory)
        logger.info(f"Created directory: {directory}")

def install_layer_dependencies(temp_dir: str, requirements_file: str) -> None:
    """Install layer dependencies in the specified directory."""
    try:
        python_dir = os.path.join(temp_dir, 'python')
        os.makedirs(python_dir, exist_ok=True)
        
        subprocess.run([
            'pip', 'install',
            '-r', requirements_file,
            '--target', python_dir,
            '--platform', 'manylinux2014_x86_64',
            '--only-binary=:all:',
            '--upgrade'
        ], check=True)
        logger.info("Layer dependencies installed successfully")
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to install layer dependencies: {e}")
        raise

def create_layer_zip() -> None:
    """Create ZIP file for the Google Calendar layer."""
    layer_name = 'google_calendar_layer'
    requirements_file = os.path.join(LAYER_SOURCE_DIR, layer_name, 'requirements.txt')
    zip_path = os.path.join(DEPLOYMENTS_DIR, f"{layer_name}.zip")

    if not os.path.exists(requirements_file):
        logger.error(f"Requirements file not found: {requirements_file}")
        return

    with tempfile.TemporaryDirectory() as temp_dir:
        logger.info(f"Creating layer ZIP: {layer_name}")
        install_layer_dependencies(temp_dir, requirements_file)
        shutil.make_archive(
            base_name=zip_path.replace('.zip', ''),
            format='zip',
            root_dir=temp_dir
        )
        logger.info(f"Layer ZIP created successfully: {zip_path}")

def create_lambda_zip(function_name: str) -> None:
    """Create ZIP file for a Lambda function."""
    source_path = os.path.join(LAMBDA_SOURCE_DIR, f"{function_name}.py")
    zip_path = os.path.join(DEPLOYMENTS_DIR, f"{function_name}.zip")

    if not os.path.exists(source_path):
        logger.error(f"Lambda source file not found: {source_path}")
        return

    with tempfile.TemporaryDirectory() as temp_dir:
        logger.info(f"Creating Lambda ZIP: {function_name}")
        # Copy the Lambda function file
        shutil.copy2(source_path, os.path.join(temp_dir, 'lambda_function.py'))
        # Copy the client_secret.json if it exists
        client_secret = os.path.join(LAMBDA_SOURCE_DIR, 'client_secret.json')
        if os.path.exists(client_secret):
            shutil.copy2(client_secret, os.path.join(temp_dir, 'client_secret.json'))
        
        shutil.make_archive(
            base_name=zip_path.replace('.zip', ''),
            format='zip',
            root_dir=temp_dir
        )
        logger.info(f"Lambda ZIP created successfully: {zip_path}")

def main() -> None:
    """Main function to execute the zipping process."""
    try:
        # Ensure deployments directory exists
        ensure_directory_exists(DEPLOYMENTS_DIR)

        # Create layer ZIP
        create_layer_zip()

        # Create Lambda ZIPs
        for function_name in LAMBDA_FUNCTIONS:
            create_lambda_zip(function_name)

        logger.info("All ZIPs created successfully!")

    except Exception as e:
        logger.error(f"An error occurred: {e}")
        raise

if __name__ == "__main__":
    main()
