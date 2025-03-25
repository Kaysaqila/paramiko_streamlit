import paramiko

def get_server_stats(host, username, password):
    try:
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(hostname=host, username=username, password=password)

        commands = {
            "CPU Usage": "top -bn1 | grep 'Cpu' | awk '{print $2}'",
            "Memory Usage": "free -m | awk 'NR==2{printf \"%.2f\", $3*100/$2 }'",
            "Disk Usage": "df -h / | awk 'NR==2{print $5}'",
            "Uptime": "uptime -p"
        }

        stats = {}
        for key, cmd in commands.items():
            stdin, stdout, stderr = client.exec_command(cmd)
            stats[key] = stdout.read().decode().strip()

        client.close()
        return stats

    except Exception as e:
        return {"Error": str(e)}
