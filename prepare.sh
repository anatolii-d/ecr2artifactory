# This script prepares the environment by installing necessary dependencies.
# It performs the following actions:
# 1. Updates the package list using `apt-get update`.
# 2. Checks if Python3 is installed; if not, installs it.
# 3. Checks if pip3 is installed; if not, installs it.
# 4. Checks if Docker is installed; if not, installs it.
# 5. Checks if AWS CLI is installed; if not, downloads and installs it.
# 6. Installs Python packages `boto3` and `python-dotenv` using pip.
# 7. Reminds the user to configure AWS credentials and set up Artifactory credentials.
#!/usr/bin/env bash

# Update the package list
sudo apt-get update -y -qq

# Function to check and install a package if not already installed
check_and_install() {
    local cmd=$1
    local pkg=$2
    local install_cmd=$3

    if ! command -v "$cmd" &> /dev/null
    then
        echo "$pkg not found, installing..."
        eval "$install_cmd"
    else
        echo "$pkg is already installed"
    fi
}

# Function to check and install a Python package if not already installed
check_and_install_python_package() {
    local pkg=$1

    if ! python3 -c "import $pkg" &> /dev/null
    then
        echo "$pkg not found, installing..."
        pip3 install -q "$pkg"
    else
        echo "$pkg is already installed"
    fi
}

# Check and install Python3
check_and_install python3 "Python3" "sudo apt-get install -y -qq python3"

# Check and install pip3
check_and_install pip3 "pip3" "sudo apt-get install -y -qq python3-pip"

# Check and install Docker
check_and_install docker "Docker" "sudo apt-get install -y -qq docker.io"

# Check and install AWS CLI
check_and_install aws "AWS CLI" "
    pushd /tmp > /dev/null
    curl 'https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip' -o 'awscliv2.zip'
    unzip awscliv2.zip
    sudo ./aws/install --bin-dir /usr/local/bin --install-dir /usr/local/aws-cli --update
    popd > /dev/null
"

# Check and install boto3
check_and_install_python_package boto3

# Check and install python-dotenv
check_and_install_python_package dotenv

if [ ! -f .env ]; then
    echo "Creating .env file"
    mv .env.example .env
fi

echo "All dependencies are installed"

echo "REMEMBER:"
echo "    You need run 'aws configure' to set up your AWS credentials"
echo "    You need to set up your Artifactory credentials in the .env file or set manuiually from input"