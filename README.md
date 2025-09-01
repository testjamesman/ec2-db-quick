EC2 DB Quick Test Application
=============================

This application provides a set of endpoints designed to generate various types of telemetry data for testing an observability vendor integration. It runs entirely within Docker containers managed by Docker Compose, providing test endpoints for PostgreSQL, MySQL, and Microsoft SQL Server.

> **⚠️ Cost Warning:** This demo uses a `t3.medium` EC2 instance by default, which is **outside the AWS Free Tier**. To avoid unexpected charges, please ensure you terminate the EC2 instance using the AWS Console or by running `docker compose down` and then shutting down the instance when you are finished with your testing.

📁 Project Structure
--------------------

```
ec2-db-quick/
├── aws_deploy.sh             # Automated AWS EC2 deployment script
├── local_docker_install.sh   # Script to install Docker on a host
├── docker-compose.yml        # Manages the app and all db containers
├── Dockerfile                # Defines the Python application container
├── app.py                    # The main FastAPI application
├── requirements.txt          # Python dependencies
└── README.md                 # This setup guide

```

🚀 Deployment Options
---------------------

Choose one of the following methods to deploy the application.

### Option 1: Automated EC2 Setup with AWS CLI (Recommended)

This method uses the AWS CLI to create and configure an EC2 instance from your local machine.

#### Prerequisites

1.  **AWS CLI Installed & Configured:** Ensure you have the [AWS CLI installed](https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html "null") and [configured](https://docs.aws.amazon.com/cli/latest/userguide/getting-started-quickstart.html "null") with your credentials.

2.  **EC2 Key Pair:** You must have an existing [EC2 Key Pair](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/ec2-key-pairs.html "null") in the AWS region you intend to use.

#### Steps

1.  **Set Environment Variables:** Before running the script, you must export the following environment variables in your terminal.

    **For macOS/Linux:**

    ```
    export AWS_REGION="us-west-1"
    export KEY_PAIR_NAME="your-key-pair-name"
    export REPO_URL="[https://github.com/your-username/ec2-db-quick.git](https://github.com/your-username/ec2-db-quick.git)"

    ```

    **For Windows (Command Prompt):**

    ```
    set AWS_REGION="us-west-1"
    set KEY_PAIR_NAME="your-key-pair-name"
    set REPO_URL="[https://github.com/your-username/ec2-db-quick.git](https://github.com/your-username/ec2-db-quick.git)"

    ```

2.  **Make the script executable:**

    ```
    chmod +x aws_deploy.sh

    ```

3.  **Run the script from your local terminal.**

    ```
    ./aws_deploy.sh

    ```

    The script will create the EC2 instance, output its public IP, and clone the repository.

4.  **Connect and Deploy:** Follow the "Manual Deployment" steps below, starting from **Step 2**, to install Docker and run the application on the newly created instance.

### Option 2: Manual Deployment on an Existing EC2 Instance

Use this method if you already have an EC2 instance running and prefer to set up the environment manually.

#### Step 1: Connect to Your EC2 Instance & Clone Repo

1.  **Connect using SSH:**

    ```
    # Replace the path to your .pem file and the public IP address
    ssh -i /path/to/your/key.pem ec2-user@<your-public-ip>

    ```

2.  **Clone the repository (if not done by `aws_deploy.sh`):**

    ```
    git clone [https://github.com/your-username/ec2-db-quick.git](https://github.com/your-username/ec2-db-quick.git)
    cd ec2-db-quick

    ```

#### Step 2: Install Docker and Docker Compose

1.  **Run the installation script:** This script will install all necessary dependencies on the EC2 host.

    ```
    chmod +x local_docker_install.sh
    ./local_docker_install.sh

    ```

2.  **IMPORTANT:** After the script finishes, you **must log out and log back in** to your EC2 instance for the Docker group permissions to apply.

#### Step 3: Run the Application

With Docker and Docker Compose installed, you can now start the application and all three databases with a single command.

1.  **Navigate to the project directory and start the services:** The `--build` flag tells Docker Compose to build the application image. The `-d` flag runs the containers in the background.

    ```
    cd ec2-db-quick
    docker compose up --build -d

    ```

2.  **Check the status:** You can see the running containers with `docker compose ps`.

#### Step 4: Stop the Application

To stop and remove all containers, networks, and volumes, run:

```
docker compose down

```

### Optional: Install and Configure an Observability Agent

Install your observability vendor's agent directly on the EC2 host.

1.  **Install the Agent:** Follow your vendor's instructions to install the host agent.

2.  **Configure for Databases:** Enable integrations for PostgreSQL, MySQL, and MSSQL. Since the database ports are mapped to the host, the agent can connect to them via `localhost`.

3.  **Restart the Agent:**  `sudo systemctl restart <agent-service-name>`