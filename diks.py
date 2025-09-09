import subprocess
import sys

# Eksik kütüphaneleri otomatik yükleme
def install(package):
    subprocess.check_call([sys.executable, "-m", "pip", "install", package])

try:
    import psutil
except ImportError:
    print("psutil kütüphanesi eksik, yükleniyor...")
    install("psutil")
    import psutil

try:
    import wmi
except ImportError:
    print("wmi kütüphanesi eksik, yükleniyor...")
    install("wmi")
    import wmi

def get_detailed_drive_info():
    c = wmi.WMI()

    # LogicalDisk -> Partition eşleştirmesi
    logical_to_partition = {}
    for mapping in c.Win32_LogicalDiskToPartition():
        logical = mapping.Dependent.DeviceID   # Örn: C:
        partition = mapping.Antecedent.DeviceID  # Örn: Disk #0, Partition #1
        logical_to_partition[logical] = partition

    # Partition -> PhysicalDisk eşleştirmesi
    partition_to_physical = {}
    for mapping in c.Win32_DiskDriveToDiskPartition():
        partition = mapping.Dependent.DeviceID   # Disk #0, Partition #1
        physical = mapping.Antecedent.DeviceID   # \\.\PHYSICALDRIVE0
        partition_to_physical[partition] = physical

    # Fiziksel disk bilgilerini önceden al
    physical_disk_info = {d.DeviceID: d for d in c.Win32_DiskDrive()}

    print("=== Disk Bilgileri ===")
    for part in psutil.disk_partitions(all=False):
        usage = psutil.disk_usage(part.mountpoint)
        print(f"\nMantıksal Sürücü: {part.device}")
        print(f"  Dosya Sistemi: {part.fstype}")
        print(f"  Toplam: {usage.total/(1024**3):.2f} GB")
        print(f"  Kullanılan: {usage.used/(1024**3):.2f} GB")
        print(f"  Boş: {usage.free/(1024**3):.2f} GB")

        # Mantıksal diskten partition’a geçiş
        logical_id = part.device.replace("\\", "")  # C:\
        if logical_id.endswith(":"):
            logical_id = logical_id  # Zaten doğru formatta
        else:
            logical_id = logical_id + ":"

        partition = logical_to_partition.get(logical_id)

        if partition:
            # Partition'dan fiziksel diske geçiş
            physical = partition_to_physical.get(partition)
            if physical:
                disk = physical_disk_info.get(physical)
                if disk:
                    print(f"  Fiziksel Disk: {disk.DeviceID} ({disk.Model})")
                    print(f"  Fiziksel Disk Boyutu: {int(disk.Size)/(1024**3):.2f} GB")
                    if disk.MediaType:
                        print(f"  Tür: {disk.MediaType}")
                else:
                    print("  Fiziksel disk bilgisi alınamadı!")
            else:
                print("  Partition fiziksel diske eşlenemedi!")
        else:
            print("  Mantıksal disk partition'a eşlenemedi!")

if __name__ == "__main__":
    get_detailed_drive_info()
