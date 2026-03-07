from collections import Counter

from .ast import SystemDecl


class SemanticError(Exception):
    pass


class SemanticAnalyzer:
    def __init__(self, system: SystemDecl):
        self.system = system
        self.errors: list[str] = []

    def analyze(self):
        self._check_storage()
        self._check_users()

        if self.errors:
            msg = "\n".join(self.errors)
            raise SemanticError(
                f"Semantic Validation Failed with {len(self.errors)} errors:\n{msg}"
            )

    def _check_storage(self):
        mount_points = []
        for disk in self.system.storage:
            for part in disk.partitions:
                if part.mount:
                    mount_points.append(part.mount)

                # Check Subvolumes require BTRFS
                if part.subvolumes and part.fs != "BTRFS":
                    self.errors.append(
                        f"Partition '{part.name}' uses subvolumes but its filesystem is '{part.fs}', not 'BTRFS'."
                    )

                # Basic Bootloader check
                if part.mount == "/boot" and self.system.bootloader:
                    if (
                        self.system.bootloader.type == "SYSTEMD_BOOT"
                        and part.fs != "FAT32"
                    ):
                        self.errors.append(
                            f"Partition mapped to /boot is '{part.fs}', but systemd-boot requires FAT32."
                        )

        # Check duplicate mount points
        mount_counts = Counter(mount_points)
        for mount, count in mount_counts.items():
            if count > 1:
                self.errors.append(
                    f"Duplicate mount point defined: '{mount}' appears {count} times."
                )

        # Check for root mount presence
        if "/" not in mount_points:
            self.errors.append(
                "No root partition mount point ('/') defined in storage."
            )

    def _check_users(self):
        has_root = any(u.is_root for u in self.system.users)
        if not has_root:
            self.errors.append(
                "No root user defined. You must declare a `root { ... }` block."
            )

        usernames = [u.name for u in self.system.users if not u.is_root]
        users_counter = Counter(usernames)
        for uname, count in users_counter.items():
            if count > 1:
                self.errors.append(
                    f"Duplicate normal user defined: '{uname}' appears {count} times."
                )
