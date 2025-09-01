EC2 DB Quick Test Application
=============================

This application provides a set of endpoints designed to generate various types of telemetry data for testing an observability vendor integration. It runs entirely within Docker containers managed by Docker Compose, utilizing PostgreSQL and MySQL databases.

> **⚠️ Cost Warning:** This demo uses a `t3.medium` EC2 instance by default, which is **outside the AWS Free Tier**. To avoid unexpected charges, please ensure you terminate the EC2 instance using the AWS Console or by running `docker compose down` and then shutting down the instance when you are finished with your testing.

📁 Project Structure
--------------------

```
ec2-db-quick/
├── aws_deploy.sh           # Automated AWS EC2 deployment script
├── aws_cleanup.sh          # Automated AWS resource cleanup script
├── local_docker_install.sh # Script to install Docker and DB clients on the EC2 host
├── docker-compose.yml      # Manages the app, postgres, and mysql containers
├── Dockerfile              # Defines the Python application container
├── app.py                  # The main FastAPI application
├── requirements.txt        # Python dependencies
└── README.md               # This setup guide

```

🚀 Deployment
-------------

This guide will walk you through creating the EC2 instance and deploying the application.

### Step 1: Create the EC2 Instance (Local Machine)

This method uses the AWS CLI to create an EC2 instance from your local machine.

#### Prerequisites

1.  **AWS CLI Installed & Configured:** Ensure you have the [AWS CLI installed](https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html "null") and [configured](https://docs.aws.amazon.com/cli/latest/userguide/getting-started-quickstart.html "null") with your credentials.

2.  **EC2 Key Pair:** You must have an existing [EC2 Key Pair](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/ec2-key-pairs.html "null") in the AWS region you intend to use. This is required for SSH access.

3.  **Local Git Clone:** You should have this repository cloned to your local machine.

#### Actions

1.  **Set Environment Variables:** Before running the script, you must export the following environment variables in your local terminal.

    **On macOS/Linux:**

    ```
    export AWS_REGION="us-west-1"
    export KEY_PAIR_NAME="your-key-pair-name"
    export REPO_URL="[https://github.com/your-username/ec2-db-quick.git](https://github.com/your-username/ec2-db-quick.git)"

    ```

    **On Windows (Command Prompt):**

    ```
    set AWS_REGION="us-west-1"
    set KEY_PAIR_NAME="your-key-pair-name"
    set REPO_URL="[https://github.com/your-username/ec2-db-quick.git](https://github.com/your-username/ec2-db-quick.git)"

    ```

    *Replace the values with your specific AWS region, the name of your `.pem` file (without the extension), and the URL to your forked repository.*

2.  **Make the script executable:**  `chmod +x aws_deploy.sh`

3.  **Run the script from your local terminal.** This will create the EC2 instance, security groups, and clone the repository in the `ec2-user`'s home directory.

    ```
    ./aws_deploy.sh

    ```

### Step 2: Install Dependencies & Run App (EC2 Instance)

1.  **Connect to the new instance via SSH.** The `aws_deploy.sh` script will output the public IP address. Use it to connect.

    ```
    # Replace the path to your .pem file and the public IP address
    ssh -i /path/to/your/key.pem ec2-user@<your-public-ip>

    ```

2.  **Run the installation script on the EC2 instance.** Once connected, navigate to the cloned repository and run the setup script. This installs Docker, Docker Compose, and the database CLI clients.

    ```
    cd ec2-db-quick
    chmod +x local_docker_install.sh
    ./local_docker_install.sh

    ```

3.  **Start the application.** After the script completes, run the application using Docker Compose. The first build will take several minutes.

    ```
    docker compose up --build -d

    ```

### Step 3: Querying Databases from the Host (Optional)

After the containers are running, you can connect to each database directly from the EC2 host's terminal using the newly installed CLI clients. This is useful for manual checks or debugging.

**Connect to PostgreSQL:**

```
export PGPASSWORD="postgres" & psql --host=localhost --username=postgres --dbname=ec2_db_quick_test

```

**Connect to MySQL:**

```
mysql --host=127.0.0.1 --user=mysql_user -pmysql_password --database=ec2_db_quick_test

```

### Step 4: Cleanup (Local Machine)

When you are finished testing, run the cleanup script from your local machine to terminate the EC2 instance and delete the security group to avoid ongoing AWS charges.

1.  **Set your AWS_REGION:** Make sure you have exported the same `AWS_REGION` variable you used for deployment.

    ```
    export AWS_REGION="us-west-1"

    ```

2.  **Make the script executable:**

    ```
    chmod +x aws_cleanup.sh

    ```

3.  **Run the cleanup script:**

    ```
    ./aws_cleanup.sh
    ```