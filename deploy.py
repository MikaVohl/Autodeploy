import os
import subprocess
import tempfile
import zipfile
import re
import paramiko
from io import StringIO
import time


def download_or_extract_code(repo_url: str = None, zip_file_path: str = None) -> str:
    temp_dir = tempfile.mkdtemp(prefix="app_code_")

    if repo_url:
        print(f"[INFO] Cloning repo from {repo_url} to {temp_dir}...")
        subprocess.run(["git", "clone", repo_url, temp_dir], check=True)
        return temp_dir

    if zip_file_path:
        print(f"[INFO] Extracting zip file from {zip_file_path} to {temp_dir}...")
        with zipfile.ZipFile(zip_file_path, 'r') as zip_ref:
            zip_ref.extractall(temp_dir)
        return temp_dir

    return temp_dir


def analyze_repo(repo_path: str, known_framework: str = None) -> dict:
    results = {
        "framework": known_framework or "unknown",
        "ports": [5000],  # default assumption
        "needs_localhost_replacement": False
    }

    # Check for Flask or Django in requirements.txt
    req_txt = os.path.join(repo_path, "requirements.txt")
    if os.path.isfile(req_txt):
        with open(req_txt, "r") as f:
            content = f.read().lower()
            if "django" in content:
                results["framework"] = "django"
                results["ports"] = [8000]
            elif "flask" in content:
                results["framework"] = "flask"
                results["ports"] = [5000]

    # Check for Node.js frameworks in package.json
    pkg_json = os.path.join(repo_path, "package.json")
    if os.path.isfile(pkg_json):
        with open(pkg_json, "r") as f:
            content = f.read().lower()
            if '"express"' in content or '"koa"' in content:
                results["framework"] = "nodejs"
                results["ports"] = [3000]

    # Very naive check for 'localhost' references
    for root, dirs, files in os.walk(repo_path):
        for file in files:
            if file.endswith((".py", ".js", ".ts", ".html")):
                filepath = os.path.join(root, file)
                with open(filepath, "r", encoding="utf-8", errors="ignore") as code_file:
                    code_text = code_file.read()
                    if "localhost" in code_text:
                        results["needs_localhost_replacement"] = True
                        break

    return results


def generate_terraform_config(provider: str, repo_analysis: dict, instance_type: str = "t2.micro") -> str:
    import random
    import string

    region = "us-east-1"
    ami = "ami-08c40ec9ead489470"

    if provider.lower() != "aws":
        return "# Future: Add Terraform config for other providers"

    # build ingress rules from ports discovered
    ports = repo_analysis.get("ports", [5000])
    ingress_blocks = []
    for p in ports:
        ingress_blocks.append(f"""
      ingress {{
        description = "Allow inbound on port {p}"
        from_port   = {p}
        to_port     = {p}
        protocol    = "tcp"
        cidr_blocks = ["0.0.0.0/0"]
      }}
    """)

    ingress_blocks.append(f"""
      ingress {{
        description = "Allow inbound SSH on port 22"
        from_port   = 22
        to_port     = 22
        protocol    = "tcp"
        cidr_blocks = ["0.0.0.0/0"]
      }}
    """)

    ingress_str = "".join(ingress_blocks)

    framework = repo_analysis.get("framework", "unknown")
    user_data_script = generate_user_data_script(framework)

    # Random suffix for unique resource names
    random_suffix = ''.join(random.choices(string.ascii_lowercase + string.digits, k=6))

    tf_config = f"""
terraform {{
  required_providers {{
    aws = {{
      source  = "hashicorp/aws"
      version = ">= 4.0"
    }}
  }}
  required_version = ">= 1.0"
}}

provider "aws" {{
  region = "{region}"
}}

data "aws_vpc" "default" {{
  default = true
}}

data "aws_subnets" "default" {{
  filter {{
    name   = "vpc-id"
    values = [data.aws_vpc.default.id]
  }}
}}

data "aws_security_groups" "existing_sg" {{
  filter {{
    name   = "group-name"
    values = ["auto_deployed_sg"]
  }}

  filter {{
    name   = "vpc-id"
    values = [data.aws_vpc.default.id]
  }}
}}

resource "aws_security_group" "app_sg_new" {{
  count = length(data.aws_security_groups.existing_sg.ids) == 0 ? 1 : 0

  name        = "auto_deployed_sg_{random_suffix}"
  description = "Security group for auto-deployed app"
  vpc_id      = data.aws_vpc.default.id

{ingress_str}
  egress {{
    description = "Allow all outbound"
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }}
}}

locals {{
  final_sg_id = length(data.aws_security_groups.existing_sg.ids) > 0 ? data.aws_security_groups.existing_sg.ids[0] : aws_security_group.app_sg_new[0].id
}}

resource "tls_private_key" "ssh_key" {{
  algorithm = "RSA"
  rsa_bits  = 2048
}}

resource "aws_key_pair" "generated_key" {{
  key_name   = "auto_deployed_key_{random_suffix}"
  public_key = tls_private_key.ssh_key.public_key_openssh
}}

resource "aws_instance" "app_server" {{
  ami                    = "{ami}"
  instance_type          = "{instance_type}"
  key_name               = aws_key_pair.generated_key.key_name
  subnet_id              = element(data.aws_subnets.default.ids, 0)
  vpc_security_group_ids = [local.final_sg_id]

  user_data = <<-EOT
{user_data_script}
  EOT

  tags = {{
    Name = "AutoDeployedVM"
  }}
}}

output "public_ip" {{
  description = "Public IP of the instance"
  value       = aws_instance.app_server.public_ip
}}

output "private_key_pem" {{
  description = "Private key in PEM format (Sensitive! Do not commit to public repos)"
  value       = tls_private_key.ssh_key.private_key_pem
  sensitive   = true
}}
"""
    return tf_config

def generate_user_data_script(framework: str) -> str:
    """
    Minimal user_data script that only installs system packages needed for
    Python or Node apps. We no longer place a sample app here.
    """
    if framework in ["flask", "django"]:
        return """#!/bin/bash
set -e
sudo apt-get update -y
sudo apt-get install -y python3 python3-pip git
"""
    else:
        # Default: Just install Python for now
        return """#!/bin/bash
set -e
sudo apt-get update -y
sudo apt-get install -y python3 python3-pip git
"""

########################################
# 4. RUN TERRAFORM APPLY
########################################

def run_terraform_apply(tf_config: str):
    tf_temp_dir = tempfile.mkdtemp(prefix="tf_")
    main_tf_path = os.path.join(tf_temp_dir, "main.tf")

    # Write out the Terraform config
    with open(main_tf_path, "w") as f:
        f.write(tf_config)

    # terraform init
    subprocess.run(["terraform", "init"], cwd=tf_temp_dir, check=True)

    # terraform apply
    subprocess.run(["terraform", "apply", "-auto-approve"], cwd=tf_temp_dir, check=True)

    # terraform output -json
    result = subprocess.run(
        ["terraform", "output", "-json"],
        cwd=tf_temp_dir,
        capture_output=True,
        text=True
    )

    import json
    outputs = json.loads(result.stdout)

    public_ip = outputs.get("public_ip", {}).get("value")
    private_key = outputs.get("private_key_pem", {}).get("value")
    print("Private key (PEM format):", private_key)

    return public_ip, private_key


def deploy_application(public_ip: str, repo_path: str, needs_localhost_fix: bool, framework: str, ssh_key: str = None):
    print(f"[INFO] Deploying application from {repo_path} to VM at IP {public_ip}...")

    if not ssh_key:
        print("[WARNING] No SSH key provided. Cannot deploy code via SSH.")
        return

    # If code references 'localhost', do a naive replacement
    if needs_localhost_fix:
        replace_localhost(repo_path, public_ip)

    # Use paramiko to SSH into the instance, copy code, install deps, and run the app
    username = "ubuntu"
    
    try:
        time.sleep(30)
        print("ssh key:",ssh_key)
        key_stream = StringIO(ssh_key)
        pkey = paramiko.RSAKey.from_private_key(key_stream)

        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        
        # Convert IP address format for AWS hostname
        formatted_ip = public_ip.replace('.', '-')
        hostname = f"ec2-{formatted_ip}.compute-1.amazonaws.com"
        
        print(f"attempting to connect to {hostname} with username {username}")
        print(f"using private key {pkey}")
        ssh.connect(hostname, username=username, pkey=pkey)

        sftp = ssh.open_sftp()

        # make the app directory
        try:
            sftp.mkdir(f"/home/{username}/app")
        except IOError:
            pass
    
        # upload files from repo_path to /home/{username}/
        for root, dirs, files in os.walk(repo_path):
            rel_path = os.path.relpath(root, repo_path)
            if rel_path == ".":
                rel_path = ""
            remote_dir = f"/home/{username}/app/{rel_path}"
            try:
                sftp.stat(remote_dir)
            except IOError:
                sftp.mkdir(remote_dir)

            for file in files:
                local_file = os.path.join(root, file)
                remote_file = f"{remote_dir}/{file}"
                print(f"[INFO] Uploading {local_file} to {remote_file}...")
                sftp.put(local_file, remote_file)

        sftp.close()

        # Now install dependencies and start the app, depending on the framework
        print("[INFO] Checking for requirements.txt...")
        stdin, stdout, stderr = ssh.exec_command(f"test -f /home/{username}/app/app/requirements.txt && echo 'YES' || echo 'NO'")
        has_requirements = stdout.read().decode().strip()
        print(f"[INFO] requirements.txt present: {has_requirements}")

        # Check if pip is installed with retries
        max_retries = 3
        retry_delay = 5
        
        for attempt in range(max_retries):
            stdin, stdout, stderr = ssh.exec_command("which pip3")
            if stdout.channel.recv_exit_status() == 0:
                break
            
            print(f"[INFO] Installing pip (attempt {attempt + 1}/{max_retries})...")
            stdin, stdout, stderr = ssh.exec_command("sudo apt-get install -y python3-pip")
            if stdout.channel.recv_exit_status() == 0:
                break
            
            if attempt < max_retries - 1:
                print(f"[INFO] Waiting {retry_delay} seconds before retrying...")
                time.sleep(retry_delay)
            else:
                print("[ERROR] Failed to install pip after all attempts:")
                print(stderr.read().decode())
                return
            
        
        if has_requirements == "YES":
            print("[INFO] Installing Python dependencies...")
            stdin, stdout, stderr = ssh.exec_command(f"sudo python3 -m pip install -r /home/{username}/app/app/requirements.txt")
            # Wait for command to complete and check output
            exit_status = stdout.channel.recv_exit_status()
            if exit_status != 0:
                print("[ERROR] Failed to install requirements:")
                print(stderr.read().decode())
            else:
                print("[INFO] Successfully installed requirements")

        print("[INFO] Checking installed packages...")
        stdin, stdout, stderr = ssh.exec_command("sudo python3 -m pip freeze")
        print("[INFO] Installed packages:")
        print("pip:",stdout.read().decode())

        print("[INFO] Starting the application...")
        stdin, stdout, stderr = ssh.exec_command(f"cd /home/{username}/app/app && nohup python3 app.py > app.log 2>&1 &")
        exit_status = stdout.channel.recv_exit_status()
        if exit_status != 0:
            print("[ERROR] Failed to start application:")
            print(stderr.read().decode())
        else:
            print("[INFO] Application started successfully")

        # Check if the application is running
        stdin, stdout, stderr = ssh.exec_command("ps aux | grep python3")
        print("[INFO] Process status:")
        print(stdout.read().decode())

        ssh.close()
        print("[INFO] SSH connection closed")

    except Exception as e:
        print(f"[ERROR] Deployment failed: {e}")


def replace_localhost(repo_path: str, public_ip: str):
    print(f"[INFO] Replacing 'localhost' references with {public_ip} in repo files...")
    for root, dirs, files in os.walk(repo_path):
        for file in files:
            if file.endswith((".py", ".js", ".ts", ".html")):
                filepath = os.path.join(root, file)
                with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
                    content = f.read()
                new_content = re.sub(r"localhost", public_ip, content)
                new_content = re.sub(r"127.0.0.1", '0.0.0.0', new_content)
                with open(filepath, "w", encoding="utf-8") as f:
                    f.write(new_content)