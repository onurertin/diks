import subprocess
import sys

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

try:
    import matplotlib.pyplot as plt
except ImportError:
    print("matplotlib kütüphanesi eksik, yükleniyor...")
    install("matplotlib")
    import matplotlib.pyplot as plt

def get_detailed_drive_info_and_plot_subplots():
    c = wmi.WMI()

    logical_to_partition = {}
    for mapping in c.Win32_LogicalDiskToPartition():
        logical = mapping.Dependent.DeviceID
        partition = mapping.Antecedent.DeviceID
        logical_to_partition[logical] = partition

    partition_to_physical = {}
    for mapping in c.Win32_DiskDriveToDiskPartition():
        partition = mapping.Dependent.DeviceID
        physical = mapping.Antecedent.DeviceID
        partition_to_physical[partition] = physical

    physical_disk_info = {d.DeviceID: d for d in c.Win32_DiskDrive()}

    print("=== Disk Bilgileri ===")

    devices = []
    used_sizes_gb = []
    free_sizes_gb = []
    total_sizes_gb = []
    disk_models = []

    for part in psutil.disk_partitions(all=False):
        try:
            usage = psutil.disk_usage(part.mountpoint)
        except PermissionError:
            continue

        print(f"\nMantıksal Sürücü: {part.device}")
        print(f"  Dosya Sistemi: {part.fstype}")
        print(f"  Toplam: {usage.total/(1024**3):.2f} GB")
        print(f"  Kullanılan: {usage.used/(1024**3):.2f} GB")
        print(f"  Boş: {usage.free/(1024**3):.2f} GB")

        logical_id = part.device.replace("\\", "")
        if not logical_id.endswith(":"):
            logical_id = logical_id + ":"

        partition = logical_to_partition.get(logical_id)

        model = "Bilinmiyor"

        if partition:
            physical = partition_to_physical.get(partition)
            if physical:
                disk = physical_disk_info.get(physical)
                if disk:
                    model = disk.Model.strip()
                    print(f"  Fiziksel Disk: {disk.DeviceID} ({model})")
                    print(f"  Fiziksel Disk Boyutu: {int(disk.Size)/(1024**3):.2f} GB")
                    if disk.MediaType:
                        print(f"  Tür: {disk.MediaType}")
                else:
                    print("  Fiziksel disk bilgisi alınamadı!")
            else:
                print("  Partition fiziksel diske eşlenemedi!")
        else:
            print("  Mantıksal disk partition'a eşlenemedi!")

        devices.append(part.device)
        used_sizes_gb.append(usage.used / (1024**3))
        free_sizes_gb.append(usage.free / (1024**3))
        total_sizes_gb.append(usage.total / (1024**3))
        disk_models.append(model)

    count = len(devices)
    cols = 3
    rows = (count + cols - 1) // cols

    fig, axs = plt.subplots(rows, cols, figsize=(5 * cols, 5 * rows))
    axs = axs.flatten()

    for i in range(count):
        sizes = [used_sizes_gb[i], free_sizes_gb[i]]
        labels = [
            f"Dolu: {used_sizes_gb[i]:.1f} GB",
            f"Boş: {free_sizes_gb[i]:.1f} GB"
        ]

        title = f"{devices[i]} - {disk_models[i]}"

        axs[i].pie(
            sizes,
            labels=labels,
            autopct="%1.1f%%",
            colors=["#ff9999", "#99ff99"],
            startangle=140,
            wedgeprops={"edgecolor": "w"},
            textprops={"fontsize": 10},
        )
        axs[i].set_title(title, fontsize=11)
        axs[i].axis("equal")

    for j in range(count, len(axs)):
        axs[j].axis("off")

    plt.tight_layout()
    plt.show()

if __name__ == "__main__":
    get_detailed_drive_info_and_plot_subplots()
