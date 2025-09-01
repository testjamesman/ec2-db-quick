EC2 DB Quick Test Application
=============================

This application provides a set of endpoints designed to generate various types of telemetry data for testing an observability vendor integration. It runs entirely within Docker containers managed by Docker Compose.

📁 Project Structure
--------------------

```
ec2-db-quick/
├── aws_deploy.sh       # Automated AWS EC2 deployment script
├── docker-compose.yml  # Manages the app and db containers
├── Dockerfile          # Defines the Python application container
├── deploy.sh           # Manual dependency setup for an existing EC2
├── app.py              # The main FastAPI application
├── requirements.txt    # Python dependencies
└── README.md           # This setup guide

```

🚀 Deployment Options
---------------------

Choose one of the following methods to deploy the application.

### Option 1: Automated EC2 Setup with AWS CLI (Recommended)

This method uses the AWS CLI to create and configure an EC2 instance from your local machine, including all dependencies and application startup.

#### Prerequisites

1.  **AWS CLI Installed & Configured:** Ensure you have the [AWS CLI installed](https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html "null") and [configured](https://docs.aws.amazon.com/cli/latest/userguide/getting-started-quickstart.html "null") with your credentials.

2.  **EC2 Key Pair:** You must have an existing [EC2 Key Pair](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/ec2-key-pairs.html "null") in the AWS region you intend to use. This is required for SSH access.

3.  **Local Git Clone:** You should have this repository cloned to your local machine.

#### Steps

1.  **Set Environment Variables:** Before running the script, you must export three environment variables in your terminal. These variables are only set for your current terminal session.

    -   `AWS_REGION`: The AWS region to deploy to (e.g., `us-east-1`).

    -   `KEY_PAIR_NAME`: The name of your existing EC2 key pair.

    -   `REPO_URL`: The HTTPS URL of this git repository.

    **On macOS or Linux:**

    ```
    export AWS_REGION="us-east-1"
    export KEY_PAIR_NAME="your-key-pair-name"
    export REPO_URL="[https://github.com/your-username/ec2-db-quick.git](https://github.com/your-username/ec2-db-quick.git)"

    ```

    **On Windows (PowerShell):**

    ```
    $env:AWS_REGION="us-east-1"
    $env:KEY_PAIR_NAME="your-key-pair-name"
    $env:REPO_URL="[https://github.com/your-username/ec2-db-quick.git](https://github.com/your-username/ec2-db-quick.git)"

    ```

2.  **Make the script executable:**

    ```
    chmod +x aws_deploy.sh

    ```

3.  **Run the deployment script:**

    ```
    ./aws_deploy.sh

    ```

4.  **Connect and Access:** After the script completes, it will output the Public IP address of the new instance. Use this to access the application in your browser (`http://<public-ip>:8000`) or to connect via SSH.

### Option 2: Manual Deployment on an Existing EC2 Instance

Use this method if you already have an EC2 instance running and prefer to set up the environment manually.

#### Step 1: Connect to Your EC2 Instance

1.  **Find your instance's Public IP:** In the AWS EC2 Console, select your instance and find the "Public IPv4 address" in the details panel.

2.  **Connect using SSH:**

    ```
    # Replace the path to your .pem file and the public IP address
    ssh -i /path/to/your/key.pem ec2-user@<your-public-ip>

    ```

#### Step 2: Prepare the EC2 Instance

1.  **Clone the repository:**

    ```
    git clone <your-repo-url>
    cd ec2-db-quick

    ```

2.  **Install dependencies:**

    ```
    chmod +x deploy.sh
    ./deploy.sh

    ```

3.  **IMPORTANT:** Log out and log back in to your EC2 instance for the Docker group permissions to apply.

#### Step 3: Run the Application

1.  **Navigate to the project directory:**

    ```
    cd ec2-db-quick

    ```

2.  **Start the services:**

    ```
    docker-compose up --build -d

    ```

### Optional: Install Observability Agent

Once the EC2 instance is running, you can install your observability vendor's agent directly on the host to monitor the system and the Docker containers.

1.  **SSH into the instance.**

2.  **Follow your vendor's instructions** to install the host agent.

3.  **Configure the agent** for Docker and PostgreSQL monitoring. Since the database port (`5432`) is mapped to the host, the agent can connect to it via `localhost`.
