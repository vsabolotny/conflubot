import subprocess
import sys
import os

from dotenv import load_dotenv

load_dotenv()
ECR_REPO = os.getenv("ECR_REPO")
REGION = os.getenv("REGION")

def run(cmd, shell=False):
    print(f"Running: {cmd if isinstance(cmd, str) else ' '.join(cmd)}")
    result = subprocess.run(cmd, shell=shell, check=True)
    return result

def main():
    try:
        run(["docker", "build", "--platform", "linux/amd64", "-t", "conflubot:latest", "."])
        login_cmd = f"aws ecr get-login-password --region {REGION} | docker login --username AWS --password-stdin {ECR_REPO.split('/')[0]}"
        run(login_cmd, shell=True)
        run(["docker", "tag", "conflubot:latest", ECR_REPO])
        run(["docker", "push", ECR_REPO])
        print("Deployment complete.")
    except subprocess.CalledProcessError as e:
        print(f"Command failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
