import smtplib
from email.mime.text import MIMEText
import psutil
from datetime import datetime
import socket
import sys
import os
import subprocess
import requests
import netifaces


#credentials
USER = "<gmail>"
PASS = "<app psswd of google>"
TO_EMAIL = "<receiver mail>"
LOG_FILE = "./server_email.log"
MAX_LOG_ENTRIES = 1000


messages = []  #log buffer

def format_datetime(ts=None):
    if not ts:
        ts = datetime.now()
    date_str = ts.strftime("%d/%m/%Y")
    time_str = ts.strftime("%H-%M-%S")
    return f"Date : {date_str}\nTime : {time_str}"

def get_internal_ips():
    ip_info = {}
    for iface in netifaces.interfaces():
        addrs = netifaces.ifaddresses(iface)
        ipv4 = addrs.get(netifaces.AF_INET, [{'addr': 'N/A'}])[0]['addr']
        ipv6 = addrs.get(netifaces.AF_INET6, [{'addr': 'N/A'}])[0]['addr']
        ip_info[iface] = {'IPv4': ipv4, 'IPv6': ipv6}
    return ip_info

def get_external_ips():
    try:
        ipv4 = requests.get("https://api.ipify.org", timeout=5).text
    except:
        ipv4 = "N/A"
    try:
        ipv6 = requests.get("https://api64.ipify.org", timeout=5).text
    except:
        ipv6 = "N/A"
    return {'IPv4': ipv4, 'IPv6': ipv6}

def format_ip_report():
    internal = get_internal_ips()
    internal_str = "Internal IPs:\n"
    for iface, ips in internal.items():
        internal_str += f"Interface {iface}: IPv4: {ips['IPv4']}, IPv6: {ips['IPv6']}\n"
    external = get_external_ips()
    external_str = f"\nExternal IPs:\nIPv4: {external['IPv4']}\nIPv6: {external['IPv6']}\n"
    return internal_str + external_str

def get_startup_report():
    hostname = socket.gethostname()
    boot_time = datetime.fromtimestamp(psutil.boot_time())
    
    #Disk usage
    disk_info = ""
    for part in psutil.disk_partitions(all=False):
        usage = psutil.disk_usage(part.mountpoint)
        disk_info += f"{part.device} ({part.mountpoint}): {usage.percent}% used\n"
    
    #RAM
    ram = psutil.virtual_memory()
    
    #CPU
    cpu_info = f"Cores: {psutil.cpu_count(logical=True)}\n"
    
    #syslog
    try:
        sys_logs = subprocess.check_output("tail -n 50 /var/log/syslog", shell=True).decode()
    except:
        sys_logs = "N/A"
    
    timestamp = format_datetime()
    ip_report = format_ip_report()
    
    body = f"""
Server Startup Report - {hostname}
{timestamp}

Boot Time: {boot_time.strftime('%d/%m/%Y %H-%M-%S')}

{ip_report}

Disk Usage:
{disk_info}

RAM: Total={ram.total//(1024**2)}MB, Used={ram.used//(1024**2)}MB, Free={ram.available//(1024**2)}MB

CPU Info:
{cpu_info}

Startup Logs:
{sys_logs}
"""
    return body

def get_health_report():
    hostname = socket.gethostname()
    
    #CPU
    cpu_usage = psutil.cpu_percent(interval=1)
    try:
        cpu_temp = subprocess.check_output("sensors | grep 'Package id 0:'", shell=True).decode().strip()
    except:
        cpu_temp = "N/A"
    
    #RAM
    ram = psutil.virtual_memory()
    
    #Disk
    disk_info = ""
    for part in psutil.disk_partitions(all=False):
        usage = psutil.disk_usage(part.mountpoint)
        disk_info += f"{part.device} ({part.mountpoint}): {usage.percent}% used\n"
    
    #Network stats
    net = psutil.net_io_counters()
    
    timestamp = format_datetime()
    ip_report = format_ip_report()
    
    body = f"""
Server Health Report - {hostname}
{timestamp}

{ip_report}

CPU Usage: {cpu_usage}%
CPU Temperature: {cpu_temp}

RAM: Total={ram.total//(1024**2)}MB, Used={ram.used//(1024**2)}MB, Free={ram.available//(1024**2)}MB

Disk Usage:
{disk_info}

Network: Sent={net.bytes_sent//1024}KB, Received={net.bytes_recv//1024}KB

"""
    return body

def send_email(subject, body):
    msg = MIMEText(body)
    msg['Subject'] = subject
    msg['From'] = USER
    msg['To'] = TO_EMAIL

    try:
        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.starttls()
            server.login(USER, PASS)
            server.send_message(msg)
        messages.append(f"{format_datetime()} - SUCCESS: {subject}")
    except Exception as e:
        messages.append(f"{format_datetime()} - FAILED: {subject} - {e}")

def write_log():
    if os.path.exists(LOG_FILE):
        with open(LOG_FILE, "r") as f:
            lines = f.readlines()
    else:
        lines = []

    lines.extend([msg + "\n" for msg in messages])
    if len(lines) > MAX_LOG_ENTRIES:
        lines = lines[-MAX_LOG_ENTRIES:]
    with open(LOG_FILE, "w") as f:
        f.writelines(lines)



if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "startup":
        send_email("Server Startup Report", get_startup_report())
    else:
        send_email("Server Health Update", get_health_report())

    write_log()
