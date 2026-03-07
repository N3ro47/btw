from .ast import SystemDecl


class CodeGenerator:
    def __init__(self, system: SystemDecl):
        self.system = system
        self.script = []

    def generate(self) -> str:
        self.script.append("#!/bin/bash")
        self.script.append("set -e")
        self.script.append(f"# Generated Setup Script for ArchSpec: {self.system.name}")
        self.script.append("")

        self._gen_clock()
        self._gen_storage()
        self._gen_pacstrap()
        self._gen_fstab()
        self._gen_chroot()

        return "\n".join(self.script)

    def _gen_clock(self):
        self.script.append("# 1. Update system clock")
        self.script.append("timedatectl set-ntp true")
        self.script.append("")

    def _gen_storage(self):
        self.script.append("# 2. Partitioning Disk")
        for st in self.system.storage:
            dev = st.device
            if dev == "LARGEST_DRIVE":
                self.script.append(
                    "DRIVE=$(lsblk -b -d -o NAME,SIZE | tail -n+2 | sort -k2 -nr | head -n1 | awk '{print \"/dev/\"$1}')"
                )
                dev = "$DRIVE"

            self.script.append(f'echo "Formatting {dev}..."')

            # Simple wipedisk stub
            self.script.append(f"parted -s {dev} mklabel {st.scheme.lower()}")

            # Format and Mount
            part_prefix = f"{dev}p" if "nvme" in dev else f"{dev}"
            for idx, part in enumerate(st.partitions, start=1):
                part_path = f"{part_prefix}{idx}"
                if part.fs == "FAT32":
                    self.script.append(f"mkfs.vfat -F32 {part_path}")
                elif part.fs == "EXT4":
                    self.script.append(f"mkfs.ext4 -F {part_path}")
                elif part.fs == "BTRFS":
                    self.script.append(f"mkfs.btrfs -f {part_path}")
                elif part.fs == "SWAP":
                    self.script.append(f"mkswap {part_path}")
                    self.script.append(f"swapon {part_path}")

            self.script.append("")

            # Mounting phase
            self.script.append("# 3. Mounting Partitions")
            # Mount Root first
            for idx, part in enumerate(st.partitions, start=1):
                part_path = f"{part_prefix}{idx}"
                if part.mount == "/":
                    if part.subvolumes:
                        self.script.append(f"mount {part_path} /mnt")
                        for subvol in part.subvolumes:
                            self.script.append(f"btrfs subvolume create /mnt/{subvol}")
                        self.script.append("umount /mnt")
                        # Just an example simplified mount
                        self.script.append(
                            f"mount -o compress=zstd,subvol=@ {part_path} /mnt"
                        )
                    else:
                        self.script.append(f"mount {part_path} /mnt")

            # Mount others
            for idx, part in enumerate(st.partitions, start=1):
                part_path = f"{part_prefix}{idx}"
                if part.mount and part.mount != "/":
                    self.script.append(f"mkdir -p /mnt{part.mount}")
                    self.script.append(f"mount {part_path} /mnt{part.mount}")
            self.script.append("")

    def _gen_pacstrap(self):
        self.script.append("# 4. Pacstrap Base Installation")
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
            # Smart GPU/Display Drivers Default to generic/Intel if not specified
            if self.system.system_opts and self.system.system_opts.gpu == "NVIDIA":
                pkgs.extend(["nvidia", "nvidia-utils", "egl-wayland", "mesa"])
            elif self.system.system_opts and self.system.system_opts.gpu == "AMD":
                pkgs.extend(["vulkan-radeon", "xf86-video-amdgpu", "mesa"])
            else:
                pkgs.extend(["vulkan-intel", "mesa"])

            if self.system.desktop.base_fonts:
                pkgs.extend(["noto-fonts", "noto-fonts-emoji", "noto-fonts-cjk", "ttf-dejavu"])
            if self.system.desktop.audio == "PIPEWIRE":
                pkgs.extend(["pipewire", "pipewire-pulse", "pipewire-audio", "pipewire-alsa", "pipewire-jack", "wireplumber"])
            elif self.system.desktop.audio == "PULSEAUDIO":
                pkgs.extend(["pulseaudio", "pulseaudio-alsa", "pulseaudio-bluetooth"])
            if self.system.desktop.bluetooth:
                pkgs.extend(["bluez", "bluez-utils"])

        self.script.append(f"pacstrap -K /mnt {' '.join(pkgs)}")
        self.script.append("")

    def _gen_fstab(self):
        self.script.append("# 5. Generate Fstab")
        self.script.append("genfstab -U /mnt >> /mnt/etc/fstab")
        self.script.append("")

    def _gen_chroot(self):
        self.script.append("# 6. Chroot configurations")
        chroot_cmd = "arch-chroot /mnt"

        # System Opts
        if self.system.system_opts:
            if self.system.system_opts.timezone:
                tz = self.system.system_opts.timezone
                self.script.append(
                    f"{chroot_cmd} ln -sf /usr/share/zoneinfo/{tz} /etc/localtime"
                )
                self.script.append(f"{chroot_cmd} hwclock --systohc")
            if self.system.system_opts.locale:
                loc = self.system.system_opts.locale
                self.script.append(
                    f"{chroot_cmd} sed -i 's/^#{loc}/{loc}/' /etc/locale.gen"
                )
                self.script.append(f"{chroot_cmd} locale-gen")
                self.script.append(
                    f"echo 'LANG={loc.split()[0]}' > /mnt/etc/locale.conf"
                )
            if self.system.system_opts.hostname:
                host = self.system.system_opts.hostname
                self.script.append(f"echo '{host}' > /mnt/etc/hostname")

        # Users
        for user in self.system.users:
            if user.is_root:
                if user.password_hash:
                    self.script.append(
                        f"echo 'root:{user.password_hash}' | {chroot_cmd} chpasswd -e"
                    )
            else:
                groups_arg = ""
                if user.groups:
                    groups_arg = f"-G {','.join(user.groups).lower()}"
                shell_arg = f"-s /bin/{user.shell.lower()}" if user.shell else ""
                self.script.append(
                    f"{chroot_cmd} useradd -m {groups_arg} {shell_arg} {user.name}"
                )
                if user.password_hash:
                    self.script.append(
                        f"echo '{user.name}:{user.password_hash}' | {chroot_cmd} chpasswd -e"
                    )

        # Bootloader
        if self.system.bootloader:
            if self.system.bootloader.type == "SYSTEMD_BOOT":
                self.script.append(f"{chroot_cmd} bootctl install")
            elif self.system.bootloader.type == "GRUB":
                self.script.append(
                    f"{chroot_cmd} grub-install --target=x86_64-efi --efi-directory=/boot --bootloader-id=GRUB"
                )
                self.script.append(f"{chroot_cmd} grub-mkconfig -o /boot/grub/grub.cfg")

        # Desktop
        if self.system.desktop:
            if self.system.desktop.display_manager:
                self.script.append(
                    f"{chroot_cmd} systemctl enable {self.system.desktop.display_manager.lower()}"
                )
            if self.system.desktop.bluetooth:
                self.script.append(f"{chroot_cmd} systemctl enable bluetooth")

        # System Opts hooks
        if self.system.system_opts:
            if self.system.system_opts.fstrim_timer:
                self.script.append(f"{chroot_cmd} systemctl enable fstrim.timer")
            if self.system.system_opts.firewall:
                self.script.append(f"{chroot_cmd} systemctl enable {self.system.system_opts.firewall.lower()}")
            if self.system.system_opts.cpufreq:
                if self.system.system_opts.cpufreq == "POWER_PROFILES_DAEMON":
                    self.script.append(f"{chroot_cmd} systemctl enable power-profiles-daemon")
                elif self.system.system_opts.cpufreq == "TLP":
                    self.script.append(f"{chroot_cmd} systemctl enable tlp")
                elif self.system.system_opts.cpufreq == "AUTOCPU_FREQ":
                    self.script.append(f"{chroot_cmd} systemctl enable auto-cpufreq")
            if self.system.system_opts.gpu == "NVIDIA":
                self.script.append(f"{chroot_cmd} mkdir -p /etc/pacman.d/hooks")
                self.script.append(f"cat << 'EOF' | {chroot_cmd} tee /etc/pacman.d/hooks/nvidia.hook > /dev/null\n[Trigger]\nOperation=Install\nOperation=Upgrade\nOperation=Remove\nType=Package\nTarget=nvidia\nTarget=linux\n[Action]\nDescription=Update NVIDIA module in initcpio\nDepends=mkinitcpio\nWhen=PostTransaction\nNeedsTargets\nExec=/bin/sh -c 'while read -r trg; do case $trg in linux*) exit 0; esac; done; /usr/bin/mkinitcpio -P'\nEOF")

        # Software Hooks
        if self.system.software:
            if self.system.software.paccache_timer:
                self.script.append(f"{chroot_cmd} systemctl enable paccache.timer")
            if self.system.software.reflector_timer:
                self.script.append(f"{chroot_cmd} systemctl enable reflector.timer")
            if self.system.software.parallel_downloads:
                self.script.append(f"{chroot_cmd} sed -i 's/^#ParallelDownloads/ParallelDownloads/' /etc/pacman.conf")

        # Execs
        if self.system.execs:
            self.script.append("# Custom Exec hooks")
            for execute in self.system.execs:
                # Evaluate script block in chroot
                self.script.append(
                    f"cat << 'EOF' | {chroot_cmd} bash\n{execute.command}\nEOF"
                )
