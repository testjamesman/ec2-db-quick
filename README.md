EC2 DB Quick Test Application
=============================

This application provides a set of endpoints designed to generate various types of telemetry data for testing an observability vendor integration. It runs entirely within Docker containers managed by Docker Compose.

📁 Project Structure
--------------------

```
ec2-db-quick/
├── aws_deploy.sh            # Automated AWS EC2 instance creation script
├── local_docker_install.sh  # Installs Docker & Compose on the EC2 host
├── docker-compose.yml       # Manages the app and db containers
├── Dockerfile               # Defines the Python application container
├── app.py                   # The main FastAPI application
├── requirements.txt         # Python dependencies
└── README.md                # This setup guide

```

🚀 Deployment Guide
-------------------

The deployment is a two-step process:

1.  **Provision:** Use the `aws_deploy.sh` script from your local machine to create the EC2 instance and its networking.

2.  **Configure & Run:** SSH into the new instance to install dependencies and start the application.

### Step 1: Provision the EC2 Instance (Local Machine)

This method uses the AWS CLI to create the EC2 instance from your local machine.

#### Prerequisites

1.  **AWS CLI Installed & Configured:** Ensure you have the [AWS CLI installed](https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html "null") and [configured](https://docs.aws.amazon.com/cli/latest/userguide/getting-started-quickstart.html "null") with your credentials.

2.  **EC2 Key Pair:** You must have an existing [EC2 Key Pair](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/ec2-key-pairs.html "null") in the AWS region you intend to use. This is required for SSH access.

3.  **Git Clone:** You should have this repository cloned to your local machine.

#### Instructions

1.  **Set Environment Variables:** Before running the script, you must export the required configuration as environment variables in your terminal.

    -   **On macOS or Linux:**

        ```
        export AWS_REGION="us-west-1"
        export KEY_PAIR_NAME="your-key-pair-name"
        export REPO_URL="[https://github.com/your-username/ec2-db-quick.git](https://github.com/your-username/ec2-db-quick.git)"

        ```

    -   **Note:** Replace the values with your specific AWS region, key pair name, and the Git repository URL.

2.  **Make the script executable:**

    ```
    chmod +x aws_deploy.sh

    ```

3.  **Run the script:**

    ```
    ./aws_deploy.sh

    ```

    The script will create the EC2 instance and security group. When it finishes, it will output the **Public IP address** of the new instance. You will need this for the next step.

### Step 2: Configure and Run the Application (EC2 Instance)

Now, you will connect to the newly created instance to set up Docker and run the application.

1.  **Connect to Your EC2 Instance via SSH:**

    ```
    # Replace the path to your .pem file and the public IP from the previous step
    ssh -i /path/to/your/key.pem ec2-user@<your-public-ip>

    ```

2.  **Clone the Repository:**

    ```
    git clone $REPO_URL
    cd ec2-db-quick

    ```

    *(Note: You can get the `$REPO_URL` by running `echo $REPO_URL` on your local machine if you forget it)*

3.  **Install Docker and Docker Compose:** Run the installation script.

    ```
    chmod +x local_docker_install.sh
    ./local_docker_install.sh

    ```

4.  **IMPORTANT: Re-login to Apply Permissions:** After the script finishes, you **must log out and log back in** to your EC2 instance for the Docker group permissions to apply.

    ```
    exit
    # Now, re-run the ssh command from step 1
    ssh -i /path/to/your/key.pem ec2-user@<your-public-ip>

    ```

5.  **Start the Application:** Once you are logged back in, navigate to the project directory and start the services using Docker Compose.

    ```
    cd ec2-db-quick
    docker compose up --build -d

    ```

6.  **Verify:** Your application should now be accessible at `http://<your-public-ip>:8000`. You can check the status of the running containers with `docker compose ps`.

### Stopping the Application

To stop and remove the containers, network, and volumes, run the following command from the project directory on the EC2 instance:

```
docker compose down

```
