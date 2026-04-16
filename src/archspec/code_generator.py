import textwrap
from .ast import SystemDecl

def dedent(text: str) -> str:
    return textwrap.dedent(text).strip()

class CodeGenerator:
    def __init__(self, system: SystemDecl):
        self.system = system
        self.script = []

    def generate(self) -> str:
        self.script.append("#!/bin/bash")
        self.script.append("set -e")
        self.script.append(f"# Generated Setup Script for ArchSpec: {self.system.name}\n")

        self.script.append(self._gen_clock())
        self.script.append(self._gen_storage())
        self.script.append(self._gen_pacstrap())
        self.script.append(self._gen_fstab())
        self.script.append(self._gen_chroot())

        return "\n\n".join(filter(None, self.script)) + "\n"

    def _gen_clock(self):
        return dedent("""
            # 1. Update system clock
            timedatectl set-ntp true
        """)

    def _gen_storage(self):
        lines = ["# 2. Partitioning Disk"]
        for st in self.system.storage:
            dev = st.device
            if dev == "LARGEST_DRIVE":
                lines.append(dedent("""
                    DRIVE=$(lsblk -b -d -o NAME,SIZE | tail -n+2 | sort -k2 -nr | head -n1 | awk '{print "/dev/"$1}')"""))
                dev = "$DRIVE"

            lines.append(f'echo "Formatting {dev}..."')
            lines.append(f"parted -s {dev} mklabel {st.scheme.lower()}")

            part_prefix = f"{dev}p" if "nvme" in dev else f"{dev}"
            for idx, part in enumerate(st.partitions, start=1):
                part_path = f"{part_prefix}{idx}"
                if part.fs == "FAT32":
                    lines.append(f"mkfs.vfat -F32 {part_path}")
                elif part.fs == "EXT4":
                    lines.append(f"mkfs.ext4 -F {part_path}")
                elif part.fs == "BTRFS":
                    lines.append(f"mkfs.btrfs -f {part_path}")
                elif part.fs == "SWAP":
                    lines.append(f"mkswap {part_path}")
                    lines.append(f"swapon {part_path}")

            lines.append("\n# 3. Mounting Partitions")
            for idx, part in enumerate(st.partitions, start=1):
                part_path = f"{part_prefix}{idx}"
                if part.mount == "/":
                    if part.subvolumes:
                        lines.append(dedent(f"""
                            mount {part_path} /mnt
                            """))
                        for subvol in part.subvolumes:
                            lines.append(f"btrfs subvolume create /mnt/{subvol}")
                        lines.append(dedent(f"""
                            umount /mnt
                            mount -o compress=zstd,subvol=@ {part_path} /mnt
                            """))
                    else:
                        lines.append(f"mount {part_path} /mnt")

            for idx, part in enumerate(st.partitions, start=1):
                part_path = f"{part_prefix}{idx}"
                if part.mount and part.mount != "/":
                    lines.append(f"mkdir -p /mnt{part.mount}")
                    lines.append(f"mount {part_path} /mnt{part.mount}")

        return "\n".join(lines)

    def _gen_pacstrap(self):
        pkgs = ["base", "linux", "linux-firmware"]
        if self.system.system_opts:
            pkgs[1] = self.system.system_opts.kernel_type.lower().replace("_", "-")
            if self.system.system_opts.headers:
                pkgs.append(f"{pkgs[1]}-headers")
            if self.system.system_opts.backup_kernel:
                bk = self.system.system_opts.backup_kernel.lower().replace("_", "-")
                pkgs.append(bk)
                if self.system.system_opts.headers:
                    pkgs.append(f"{bk}-headers")
            if self.system.system_opts.microcode:
                pkgs.append(f"{self.system.system_opts.microcode.lower()}-ucode")
            if self.system.system_opts.firewall == "UFW":
                pkgs.append("ufw")
            elif self.system.system_opts.firewall == "FIREWALLD":
                pkgs.append("firewalld")
            if self.system.system_opts.cpufreq:
                if self.system.system_opts.cpufreq == "POWER_PROFILES_DAEMON":
                    pkgs.append("power-profiles-daemon")
                else:
                    pkgs.append(self.system.system_opts.cpufreq.lower().replace("_", "-"))

        if self.system.software:
            if self.system.software.paccache_timer:
                pkgs.append("pacman-contrib")
            if self.system.software.reflector_timer:
                pkgs.append("reflector")
            if self.system.software.packages:
                pkgs.extend(self.system.software.packages)

        if self.system.desktop:
            if getattr(self.system.system_opts, 'gpu', None) == "NVIDIA":
                pkgs.extend(["nvidia", "nvidia-utils", "egl-wayland", "mesa"])
            elif getattr(self.system.system_opts, 'gpu', None)  == "AMD":
                pkgs.extend(["vulkan-radeon", "xf86-video-amdgpu", "mesa"])
            else:
                pkgs.extend(["vulkan-intel", "mesa"])

            if self.system.desktop.base_fonts:
                pkgs.extend(["noto-fonts", "noto-fonts-emoji", "noto-fonts-cjk", "ttf-dejavu"])
            if getattr(self.system.desktop, 'audio', None) == "PIPEWIRE":
                pkgs.extend(["pipewire", "pipewire-pulse", "pipewire-audio", "pipewire-alsa", "pipewire-jack", "wireplumber"])
            elif getattr(self.system.desktop, 'audio', None) == "PULSEAUDIO":
                pkgs.extend(["pulseaudio", "pulseaudio-alsa", "pulseaudio-bluetooth"])
            if getattr(self.system.desktop, 'bluetooth', False):
                pkgs.extend(["bluez", "bluez-utils"])

        return dedent(f"""
            # 4. Pacstrap Base Installation
            pacstrap -K /mnt {' '.join(pkgs)}
        """)

    def _gen_fstab(self):
        return dedent("""
            # 5. Generate Fstab
            genfstab -U /mnt >> /mnt/etc/fstab
        """)

    def _gen_chroot(self):
        lines = ["# 6. Chroot configurations", ""]
        chroot_cmd = "arch-chroot /mnt"

        lines.append(self._gen_chroot_opts(chroot_cmd))
        lines.append(self._gen_chroot_users(chroot_cmd))
        lines.append(self._gen_chroot_bootloader(chroot_cmd))
        lines.append(self._gen_chroot_desktop_hooks(chroot_cmd))
        lines.append(self._gen_chroot_execs(chroot_cmd))

        return "\n".join(filter(None, lines))

    def _gen_chroot_opts(self, chroot_cmd: str):
        lines = []
        if self.system.system_opts:
            opts = self.system.system_opts
            if getattr(opts, 'timezone', None):
                lines.append(f"{chroot_cmd} ln -sf /usr/share/zoneinfo/{opts.timezone} /etc/localtime")
                lines.append(f"{chroot_cmd} hwclock --systohc")
            if getattr(opts, 'locale', None):
                lines.append(f"{chroot_cmd} sed -i 's/^#{opts.locale}/{opts.locale}/' /etc/locale.gen")
                lines.append(f"{chroot_cmd} locale-gen")
                lines.append(f"echo 'LANG={opts.locale.split()[0]}' > /mnt/etc/locale.conf")
            if getattr(opts, 'hostname', None):
                lines.append(f"echo '{opts.hostname}' > /mnt/etc/hostname")
        return "\n".join(lines)

    def _gen_chroot_users(self, chroot_cmd: str):
        lines = []
        for user in self.system.users:
            if user.is_root:
                if getattr(user, 'password_hash', None):
                    lines.append(f"echo 'root:{user.password_hash}' | {chroot_cmd} chpasswd -e")
            else:
                groups_arg = f"-G {','.join(user.groups).lower()}" if getattr(user, 'groups', None) else ""
                shell_arg = f"-s /bin/{user.shell.lower()}" if getattr(user, 'shell', None) else ""
                lines.append(f"{chroot_cmd} useradd -m {groups_arg} {shell_arg} {user.name}")
                if getattr(user, 'password_hash', None):
                    lines.append(f"echo '{user.name}:{user.password_hash}' | {chroot_cmd} chpasswd -e")
        return "\n".join(lines)

    def _gen_chroot_bootloader(self, chroot_cmd: str):
        if not self.system.bootloader:
            return ""
        if self.system.bootloader.type == "SYSTEMD_BOOT":
            return f"{chroot_cmd} bootctl install"
        elif self.system.bootloader.type == "GRUB":
            return dedent(f"""
                {chroot_cmd} grub-install --target=x86_64-efi --efi-directory=/boot --bootloader-id=GRUB
                {chroot_cmd} grub-mkconfig -o /boot/grub/grub.cfg
            """)
        return ""

    def _gen_chroot_desktop_hooks(self, chroot_cmd: str):
        lines = []
        if self.system.desktop:
            if getattr(self.system.desktop, 'display_manager', None):
                lines.append(f"{chroot_cmd} systemctl enable {self.system.desktop.display_manager.lower()}")
            if getattr(self.system.desktop, 'bluetooth', False):
                lines.append(f"{chroot_cmd} systemctl enable bluetooth")

        if getattr(self.system, 'system_opts', None):
            opts = self.system.system_opts
            if getattr(opts, 'fstrim_timer', False):
                lines.append(f"{chroot_cmd} systemctl enable fstrim.timer")
            if getattr(opts, 'firewall', None):
                lines.append(f"{chroot_cmd} systemctl enable {opts.firewall.lower()}")
            if getattr(opts, 'cpufreq', None):
                cf = opts.cpufreq
                if cf == "POWER_PROFILES_DAEMON":
                    lines.append(f"{chroot_cmd} systemctl enable power-profiles-daemon")
                elif cf == "TLP":
                    lines.append(f"{chroot_cmd} systemctl enable tlp")
                elif cf == "AUTOCPU_FREQ":
                    lines.append(f"{chroot_cmd} systemctl enable auto-cpufreq")
            if getattr(opts, 'gpu', None) == "NVIDIA":
                lines.append(dedent(f"""
                    {chroot_cmd} mkdir -p /etc/pacman.d/hooks
                    cat << 'EOF' | {chroot_cmd} tee /etc/pacman.d/hooks/nvidia.hook > /dev/null
                    [Trigger]
                    Operation=Install
                    Operation=Upgrade
                    Operation=Remove
                    Type=Package
                    Target=nvidia
                    Target=linux
                    [Action]
                    Description=Update NVIDIA module in initcpio
                    Depends=mkinitcpio
                    When=PostTransaction
                    NeedsTargets
                    Exec=/bin/sh -c 'while read -r trg; do case $trg in linux*) exit 0; esac; done; /usr/bin/mkinitcpio -P'
                    EOF"""))

        if self.system.software:
            sw = self.system.software
            if getattr(sw, 'paccache_timer', False):
                lines.append(f"{chroot_cmd} systemctl enable paccache.timer")
            if getattr(sw, 'reflector_timer', False):
                lines.append(f"{chroot_cmd} systemctl enable reflector.timer")
            if getattr(sw, 'parallel_downloads', False):
                lines.append(f"{chroot_cmd} sed -i 's/^#ParallelDownloads/ParallelDownloads/' /etc/pacman.conf")
        return "\n".join(lines)

    def _gen_chroot_execs(self, chroot_cmd: str):
        lines = []
        if getattr(self.system, 'execs', None):
            lines.append("# Custom Exec hooks")
            for execute in self.system.execs:
                lines.append(dedent(f"""
                    cat << 'EOF' | {chroot_cmd} bash
                    {execute.command}
                    EOF"""))
        return "\n".join(lines)
