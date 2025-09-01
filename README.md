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
├── .gitignore          # Specifies files for git to ignore
├── .env.sample         # Sample environment file
└── README.md           # This setup guide
```

🚀 Deployment Options
---------------------

Choose one of the following methods to deploy the application.

### Option 1: Automated EC2 Setup with AWS CLI (Recommended)

This method uses the AWS CLI to create and configure an EC2 instance from your local machine, including all dependencies and application startup.

#### Prerequisites

1.  **AWS CLI Installed & Configured:** Ensure you have the [AWS CLI installed](https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html) and [configured](https://docs.aws.amazon.com/cli/latest/userguide/getting-started-quickstart.html) with your credentials.

2.  **EC2 Key Pair:** You must have an existing [EC2 Key Pair](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/ec2-key-pairs.html) in the AWS region you intend to use. This is required for SSH access.

3.  **Local Git Clone:** You should have this repository cloned to your local machine.

#### Steps

1.  **Create your Environment File:** Copy the sample environment file to a new `.env` file. This file will securely store your configuration and will not be checked into git.

    ```
    cp .env.sample .env
    ```

2.  **Edit the `.env` file:** Open the newly created `.env` file and fill in the values for `AWS_REGION`, `KEY_PAIR_NAME`, and your `REPO_URL`.

3.  **Make the script executable:**

    ```
    chmod +x aws_deploy.sh
    ```

4.  **Run the script from your local terminal.** The script will now read the configuration from your `.env` file and create all necessary AWS resources.

    ```
    ./aws_deploy.sh
    ```

5. **Connect using SSH:** After the script completes, it will output the Public IP address of the new instance, which you can use to access the host and deploy the app.
    ```
    # Replace the path to your .pem file and the public IP address
    ssh -i /path/to/your/key.pem ec2-user@<your-public-ip>
    ```

### Option 2: Manual Deployment on an Existing EC2 Instance

Use this method if you already have an EC2 instance running and prefer to set up the environment manually.

#### Step 1: Connect to Your EC2 Instance

1.  **Find your instance's Public IP:** In the AWS EC2 Console, select your instance and find the "Public IPv4 address" in the details panel.

2.  **Connect using SSH:** Use your terminal and the key pair you used to launch the instance to connect.

    ```
    # Replace the path to your .pem file and the public IP address
    ssh -i /path/to/your/key.pem ec2-user@<your-public-ip>
    ```

#### Step 2: Prepare the EC2 Instance

1.  **Clone the repository to your EC2 instance:**

    ```
    git clone <your-repo-url>
    cd ec2-db-quick
    ```

2.  **Make the dependency script executable:**

    ```
    chmod +x deploy.sh
    ```

3.  **Run the script to install Docker and Docker Compose:**

    ```
    ./deploy.sh
    ```

4.  **IMPORTANT:** After the script finishes, you **must log out and log back in** to your EC2 instance for the Docker group permissions to apply.

#### Step 3: Install and Configure the Observability Agent

Install your observability vendor's agent directly on the EC2 host. The agent will then monitor the host and the Docker containers running on it.

1.  **Install the Agent:** Follow your vendor's instructions to install the host agent.

2.  **Configure for Docker & Postgres:** Enable Docker monitoring in your agent's main configuration. Then, configure the PostgreSQL integration. Since the database port (`5432`) is mapped to the host, the agent can connect to it via `localhost`.

    Example agent configuration for Postgres (e.g., `/etc/vendor-agent/conf.d/postgres.d/conf.yaml`):

    ```yaml
    # This is a generic example. Refer to your vendor's documentation.
    instances:
      - host: localhost # The agent connects to the port mapped on the host
        port: 5432
        username: postgres
        password: postgres
        dbm: true
        dbname: ec2_db_quick_test
        tags:
          - "env:dev"
          - "service:ec2-db-quick-db"
    ```

3.  **Restart the Agent:**

    ```
    # The service name will depend on your vendor
    sudo systemctl restart <agent-service-name>
    ```

#### Step 4: Run the Application

With Docker, Docker Compose, and the agent installed, you can now start the application and database with a single command.

1.  **Navigate to the project directory:**

    ```
    cd ec2-db-quick
    ```

2.  **Start the services:** The `--build` flag tells Docker Compose to build the application image from the `Dockerfile`. The `-d` flag runs the containers in the background (detached mode).

    ```
    docker-compose up --build -d
    ```

3.  **Check the status:** You can see the running containers with `docker-compose ps`.

    ```
    docker-compose ps
    ```

#### Step 5: Stop the Application

To stop and remove the containers, network, and volumes defined in the compose file, run:

```
docker-compose down
```
