#!/usr/bin/env python3
"""
System Monitor - Überwacht System-Ressourcen
Zeigt CPU, RAM, Disk-Usage für Raspberry Pi
"""

import psutil
import time
import os
from datetime import datetime
import yaml


def get_system_info():
    """Sammelt System-Informationen"""
    info = {}
    
    # CPU
    info['cpu_percent'] = psutil.cpu_percent(interval=1)
    info['cpu_count'] = psutil.cpu_count()
    info['cpu_freq'] = psutil.cpu_freq().current if psutil.cpu_freq() else 0
    
    # RAM
    mem = psutil.virtual_memory()
    info['ram_total_gb'] = mem.total / (1024**3)
    info['ram_used_gb'] = mem.used / (1024**3)
    info['ram_percent'] = mem.percent
    
    # Disk
    disk = psutil.disk_usage('/')
    info['disk_total_gb'] = disk.total / (1024**3)
    info['disk_used_gb'] = disk.used / (1024**3)
    info['disk_percent'] = disk.percent
    
    # Temperatur (Raspberry Pi spezifisch)
    try:
        with open('/sys/class/thermal/thermal_zone0/temp', 'r') as f:
            temp = float(f.read().strip()) / 1000
            info['cpu_temp'] = temp
    except:
        info['cpu_temp'] = None
    
    # Uptime
    info['uptime_seconds'] = time.time() - psutil.boot_time()
    
    return info


def format_uptime(seconds):
    """Formatiert Uptime schön"""
    days = int(seconds // 86400)
    hours = int((seconds % 86400) // 3600)
    minutes = int((seconds % 3600) // 60)
    
    parts = []
    if days > 0:
        parts.append(f"{days}d")
    if hours > 0:
        parts.append(f"{hours}h")
    if minutes > 0:
        parts.append(f"{minutes}m")
    
    return " ".join(parts) if parts else "< 1m"


def print_system_status():
    """Gibt System-Status aus"""
    info = get_system_info()
    
    print("\n" + "="*50)
    print("  System Monitor - " + datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    print("="*50)
    
    # CPU
    print(f"\n📊 CPU")
    print(f"  Usage:  {info['cpu_percent']:.1f}%")
    print(f"  Cores:  {info['cpu_count']}")
    if info['cpu_freq'] > 0:
        print(f"  Freq:   {info['cpu_freq']:.0f} MHz")
    if info['cpu_temp']:
        temp_icon = "🔥" if info['cpu_temp'] > 70 else "🌡️"
        print(f"  Temp:   {temp_icon} {info['cpu_temp']:.1f}°C")
    
    # RAM
    print(f"\n💾 RAM")
    print(f"  Total:  {info['ram_total_gb']:.2f} GB")
    print(f"  Used:   {info['ram_used_gb']:.2f} GB ({info['ram_percent']:.1f}%)")
    print(f"  Free:   {info['ram_total_gb'] - info['ram_used_gb']:.2f} GB")
    
    # Warnungen
    if info['ram_percent'] > 80:
        print(f"  ⚠️  RAM-Usage hoch!")
    
    # Disk
    print(f"\n💿 Disk")
    print(f"  Total:  {info['disk_total_gb']:.2f} GB")
    print(f"  Used:   {info['disk_used_gb']:.2f} GB ({info['disk_percent']:.1f}%)")
    print(f"  Free:   {info['disk_total_gb'] - info['disk_used_gb']:.2f} GB")
    
    if info['disk_percent'] > 90:
        print(f"  ⚠️  Disk fast voll!")
    
    # Uptime
    print(f"\n⏱️  Uptime: {format_uptime(info['uptime_seconds'])}")
    
    print("\n" + "="*50 + "\n")


def monitor_continuous(interval=5):
    """Monitort kontinuierlich"""
    print("Kontinuierlicher Monitor (Strg+C zum Beenden)")
    print(f"Update-Intervall: {interval} Sekunden")
    
    try:
        while True:
            os.system('clear' if os.name == 'posix' else 'cls')
            print_system_status()
            
            # Prozesse
            print("🔝 Top Prozesse nach RAM:")
            processes = []
            for proc in psutil.process_iter(['pid', 'name', 'memory_percent']):
                try:
                    processes.append(proc.info)
                except:
                    pass
            
            processes.sort(key=lambda x: x['memory_percent'], reverse=True)
            
            for i, proc in enumerate(processes[:5]):
                print(f"  {i+1}. {proc['name'][:30]:30} {proc['memory_percent']:.1f}%")
            
            time.sleep(interval)
            
    except KeyboardInterrupt:
        print("\n\nMonitor beendet")


def check_health():
    """Prüft System-Gesundheit"""
    info = get_system_info()
    
    issues = []
    
    # CPU zu hoch
    if info['cpu_percent'] > 90:
        issues.append(f"⚠️  CPU-Usage sehr hoch: {info['cpu_percent']}%")
    
    # RAM zu hoch
    if info['ram_percent'] > 85:
        issues.append(f"⚠️  RAM-Usage sehr hoch: {info['ram_percent']}%")
    
    # Disk zu voll
    if info['disk_percent'] > 90:
        issues.append(f"⚠️  Disk fast voll: {info['disk_percent']}%")
    
    # Temperatur zu hoch
    if info['cpu_temp'] and info['cpu_temp'] > 75:
        issues.append(f"⚠️  CPU-Temperatur hoch: {info['cpu_temp']}°C")
    
    if issues:
        print("❌ System-Probleme erkannt:")
        for issue in issues:
            print(f"  {issue}")
        return False
    else:
        print("✅ System läuft gut")
        return True


def main():
    """CLI Interface"""
    import argparse
    
    parser = argparse.ArgumentParser(description="System Monitor für Raspberry Pi")
    parser.add_argument('command', nargs='?', default='status',
                       choices=['status', 'monitor', 'health'],
                       help='Aktion: status (einmalig), monitor (kontinuierlich), health (check)')
    parser.add_argument('--interval', type=int, default=5,
                       help='Update-Intervall für monitor (Sekunden)')
    
    args = parser.parse_args()
    
    if args.command == 'status':
        print_system_status()
    elif args.command == 'monitor':
        monitor_continuous(args.interval)
    elif args.command == 'health':
        check_health()


if __name__ == "__main__":
    main()
