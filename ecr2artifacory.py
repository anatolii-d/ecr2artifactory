#!/usr/bin/env python3

# This script migrates Docker images from AWS ECR to Artifactory.

import subprocess
import boto3
import sys
import os
import argparse
import logging
import datetime
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    handlers=[
        logging.FileHandler(f"migration-{datetime.datetime.now().strftime('%Y-%m-%d-%H-%M')}.log", mode='w'),
        logging.StreamHandler()
    ]
)

# Load environment variables from .env file if present
load_dotenv()

# Configuration: Fetch from environment variables or input
AWS_REGION = os.getenv('AWS_REGION') or input("Enter AWS region (e.g., us-east-1): ")
AWS_PROFILE = os.getenv('AWS_PROFILE') or input("Enter AWS profile (e.g., default): ")
AWS_ID = os.getenv('AWS_ID') or input("Enter AWS account ID: (e.g, 1234567890): ")
ARTIFACTORY_REGISTRY_URL = os.getenv('ARTIFACTORY_REGISTRY_URL') or input("Enter Artifactory registry URL (e.g., your-artifactory-registry.com): ")
ARTIFACTORY_USERNAME = os.getenv('ARTIFACTORY_USERNAME') or input("Enter Artifactory username: ")
ARTIFACTORY_PASSWORD = os.getenv('ARTIFACTORY_PASSWORD') or input("Enter Artifactory password: ")
NEW_REPOSITORY_TAG_PREFIX = os.getenv('NEW_REPOSITORY_TAG_PREFIX') or input("Enter new tag repository prefix (e.g., new-repo-prefix): ")

def get_ecr_repositories(ecr_client):
    """
    Fetch all ECR repositories.
    """
    repositories = []
    paginator = ecr_client.get_paginator('describe_repositories')
    for page in paginator.paginate():
        repositories.extend(page['repositories'])
    return [repo['repositoryName'] for repo in repositories]

def get_image_tags(ecr_client, repository_name):
    """
    Get all image tags from an ECR repository.
    """
    image_tags = []
    paginator = ecr_client.get_paginator('list_images')
    for page in paginator.paginate(repositoryName=repository_name):
        image_tags.extend([image['imageTag'] for image in page['imageIds'] if 'imageTag' in image])
    return image_tags

def docker_login(registry, username=None, password=None):
    """
    Log in to a Docker registry.
    """
    if username and password:
        login_command = f"docker login {registry} -u {username} -p {password}"
    else:
        login_command = f"aws ecr get-login-password --region {AWS_REGION} | docker login --username AWS --password-stdin {registry}"
    subprocess.run(login_command, shell=True, check=True)

def pull_docker_image(image):
    """
    Pull Docker image.
    """
    subprocess.run(
        f"docker pull {image}",
        shell=True,
        check=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.STDOUT
    )

def tag_docker_image(source_image, target_image):
    """
    Re-tag a Docker image.
    """
    subprocess.run(f"docker tag {source_image} {target_image}", shell=True, check=True)

def push_docker_image(image):
    """
    Push Docker image to Artifactory.
    """
    subprocess.run(
        f"docker push {image}",
        shell=True,
        check=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.STDOUT
    )

def remove_docker_image(image):
    """
    Remove Docker image from local machine if it's not in use.
    """
    # Check if the image is in use
    result = subprocess.run(
        f"docker ps -a --filter ancestor={image} --format '{{{{.ID}}}}'",
        shell=True,
        check=True,
        stdout=subprocess.PIPE,
        text=True
    )
    container_ids = result.stdout.strip()
    if container_ids:
        logging.info(f"Image '{image}' is in use by containers: {container_ids}. Skipping removal.")
    else:
        subprocess.run(f"docker rmi {image}", shell=True, check=True)
        logging.info(f"Removed image: {image}")

def image_exists_in_artifactory(image):
    """
    Check if a Docker image exists in Artifactory.
    """
    try:
        subprocess.run(
            f"docker manifest inspect {image}",
            shell=True,
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        return True
    except subprocess.CalledProcessError:
        return False

def main():
    # Parse command-line arguments
    parser = argparse.ArgumentParser(description='Migrate Docker images from AWS ECR to Artifactory.')
    parser.add_argument('--force-update', action='store_true', help='Force update images even if they exist in Artifactory.')
    args = parser.parse_args()
    force_update = args.force_update

    # Initialize AWS ECR client
    session = boto3.Session(profile_name=AWS_PROFILE)
    ecr_client = session.client('ecr', region_name=AWS_REGION)

    # Step 1: Get ECR Repositories
    try:
        repositories = get_ecr_repositories(ecr_client)
    except Exception as e:
        logging.error(f"Error fetching ECR repositories: {e}")
        sys.exit(1)

    # Log in to AWS ECR once
    ecr_registry = f"{AWS_ID}.dkr.ecr.{AWS_REGION}.amazonaws.com"
    docker_login(ecr_registry)

    # Log in to Artifactory once
    docker_login(ARTIFACTORY_REGISTRY_URL, ARTIFACTORY_USERNAME, ARTIFACTORY_PASSWORD)

    # Step 2: Process each repository
    for repo_name in repositories:
        logging.info(f"Processing repository: {repo_name}")

        try:
            # Fetch image tags
            tags = get_image_tags(ecr_client, repo_name)
        except Exception as e:
            logging.error(f"Error fetching image tags for {repo_name}: {e}")
            continue

        # Step 3: Pull, Retag, Push, and Remove each image
        for tag in tags:
            ecr_image = f"{ecr_registry}/{repo_name}:{tag}"
            artifactory_image = f"{ARTIFACTORY_REGISTRY_URL}/{NEW_REPOSITORY_TAG_PREFIX}/{repo_name}:{tag}"

            # Check if image exists in Artifactory
            if not force_update and image_exists_in_artifactory(artifactory_image):
                logging.info(f"Image '{artifactory_image}' already exists in Artifactory. Skipping.")
                continue

            try:
                logging.info(f"Pulling image: {ecr_image}")
                pull_docker_image(ecr_image)

                logging.info(f"Re-tagging image: {ecr_image} -> {artifactory_image}")
                tag_docker_image(ecr_image, artifactory_image)

                logging.info(f"Pushing image: {artifactory_image}")
                push_docker_image(artifactory_image)

                # Remove images to free space
                logging.info(f"Removing local image: {ecr_image}")
                remove_docker_image(ecr_image)

                logging.info(f"Removing local image: {artifactory_image}")
                remove_docker_image(artifactory_image)

            except subprocess.CalledProcessError as e:
                logging.error(f"Error processing {ecr_image}: {e}")
                continue

if __name__ == "__main__":
    main()
