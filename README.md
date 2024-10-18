
# ECR to Artifactory Migration Script

This script migrates Docker images from AWS Elastic Container Registry (ECR) to an Artifactory Docker registry.
This script is designed to work on Debian-like systems (e.g., Ubuntu). Ensure you have the necessary dependencies installed and configured.

## Overview

The script performs the following tasks:

- **Fetches Configuration**: Loads AWS and Artifactory credentials from environment variables or prompts the user for input.
- **Initializes AWS Client**: Creates a session with AWS using the provided profile and region.
- **Retrieves Repositories and Tags**: Lists all ECR repositories and their associated image tags.
- **Authenticates Registries**: Logs into AWS ECR and the Artifactory Docker registry.
- **Processes Images**: For each image tag in each repository:
  - Pulls the image from AWS ECR.
  - Re-tags the image with a new prefix for Artifactory.
  - Pushes the re-tagged image to the Artifactory registry.
  - Does not remove Docker images that are in use. Checks if the image is being used by any containers before attempting to remove it.
  - Removes local copies of the images if they're not in use.

## Prerequisites

- **Python 3**
- **AWS CLI** configured with appropriate permissions.
- **Docker** installed and running.
- Python packages:
  - `boto3`
  - `python-dotenv`

Install the Python packages using:

```bash
pip install boto3 python-dotenv
```

## Environment Variables

You can set the following environment variables in a  `.env`  file or export them directly:

- AWS_REGION: AWS region (e.g.,  `us-east-1`)
- AWS_PROFILE: AWS CLI profile name (e.g.,  default)
- AWS_ID: AWS account ID (e.g.,  123456789012)
- ARTIFACTORY_REGISTRY_URL: Artifactory registry URL (e.g.,  `artifactory.example.com`)
- ARTIFACTORY_USERNAME: Artifactory username
- ARTIFACTORY_PASSWORD: Artifactory password
- NEW_REPOSITORY_TAG_PREFIX: New tag prefix for re-tagging images (e.g.,  `new-repo-tag-prefix`)

## Usage

To install all dependencies, you can use the provided `prepare.sh` script. This script will ensure that all necessary tools and libraries are installed and configured correctly.

Run the script: `./prepare.sh`

This script will:

- Install Python 3 if it's not already installed.
- Install and configure the AWS CLI.
- Install Docker and ensure it's running.
- Install the required Python packages (`boto3` and `python-dotenv`).

Make sure to run this script with appropriate permissions (e.g., using `sudo` if necessary).

### Example

Run the script: `./ecr2artifactory.py`
If environment variables are not set, the script will prompt for the necessary information.
Sample prompts if environment variables are not set:

```env
Enter AWS region (e.g., us-east-1):
Enter AWS profile (e.g., default):
Enter AWS account ID (e.g., 123456789012):
Enter Artifactory registry URL (e.g., artifactory.example.com):
Enter Artifactory username: user
Enter Artifactory password: password
Enter new tag prefix (e.g., new-repo-tag-prefix):
```

The script will then process each repository and image, displaying progress and any encountered issues.

## Functions

- `get_ecr_repositories(ecr_client)`: Fetches all ECR repositories.
- `get_image_tags(ecr_client, repository_name)`: Retrieves all image tags from an ECR repository.
- `docker_login(registry, username=None, password=None)`: Logs into a Docker registry.
- `pull_docker_image(image)`: Pulls a Docker image.
- `tag_docker_image(source_image, target_image)`: Re-tags a Docker image.
- `push_docker_image(image)`: Pushes a Docker image to a registry.
- `remove_docker_image(image)`: Removes a Docker image if it's not in use.
- `main()`: Orchestrates the migration process.

## How It Works

1. **Initialization**:
    - Loads configuration from environment variables or user input.
    - Initializes an AWS session and ECR client.
2. **Fetching Repositories and Tags**:
    - Retrieves all repositories from ECR.
    - For each repository, retrieves all associated image tags.
3. **Authentication**:
    - Logs into AWS ECR.
    - Logs into the Artifactory registry using provided credentials.
4. **Migrating Images**:
    - For each image tag:
        - Pulls the image from ECR.
        - Re-tags the image for Artifactory.
        - Pushes the image to Artifactory.
        - **Image Removal**:
            - Checks if the image is in use by any containers.
            - If the image is in use, skips removal.
            - If not, removes the local image to conserve disk space.

## Notes

- **Image Safety**: The script ensures that Docker images currently in use by containers are not removed.
- **Error Handling**: Continues processing even if some images fail to migrate.
- **AWS Configuration**: Ensure your AWS CLI is configured correctly and has permissions to access ECR.
- **Security**: Handle sensitive information like passwords securely.
