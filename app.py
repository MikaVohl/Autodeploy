from chatbot import process_deployment_request
from deploy import (
    download_or_extract_code,
    analyze_repo,
    generate_terraform_config,
    run_terraform_apply,
    deploy_application
)

def main():
    print("Welcome to the Deployment Assistant!")

    # user_input = input("\nWhat would you like to deploy today? (type 'exit' to quit): ")
    # if user_input.lower() == 'exit':
    #     print("Thank you for using the Deployment Assistant. Goodbye!")
    #     return

    # deployment_instructions = process_deployment_request(user_input)
    # print("[DEBUG] Deployment Instructions:", deployment_instructions)

    # provider = deployment_instructions.get('cloud_provider') or "aws"
    # app_type = deployment_instructions.get('application_type') or "unknown"
    # resource_size = deployment_instructions.get('resource_size') or "t2.micro"
    provider = "aws"
    app_type = "flask"
    resource_size = "t2.micro"

    # repo_url = input("Enter the GitHub repo URL (leave blank if using a zip file): ").strip()
    repo_url = "https://github.com/Arvo-AI/hello_world"
    zip_file_path = None
    if not repo_url:
        zip_file_path = input("Enter the path to your zip file: ").strip()

    try:
        code_path = download_or_extract_code(repo_url=repo_url, zip_file_path=zip_file_path)
        print(f"Code downloaded/extracted to: {code_path}")
    except Exception as e:
        print(f"[ERROR] Failed to retrieve code: {e}")
        return

    repo_analysis = analyze_repo(code_path, known_framework=app_type)
    print("[DEBUG] Repo Analysis:", repo_analysis)

    # Generate Terraform config for the selected provider
    tf_config = generate_terraform_config(provider, repo_analysis, instance_type=resource_size)
    
    # Run Terraform to provision the VM
    try:
        public_ip, private_key = run_terraform_apply(tf_config)
        print(f"Terraform provisioning complete. Public IP: {public_ip}")
    except Exception as e:
        print(f"[ERROR] Terraform apply failed: {e}")
        return

    if public_ip:
        deploy_application(
            public_ip=public_ip,
            repo_path=code_path,
            needs_localhost_fix=repo_analysis["needs_localhost_replacement"],
            framework=repo_analysis["framework"],
            ssh_key=private_key
        )
        print(f"deployment completed. App is at http://{public_ip}:{repo_analysis['ports'][0]}/")


if __name__ == "__main__":
    main()