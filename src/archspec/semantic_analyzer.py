from collections import Counter

from .ast import SystemDecl


class SemanticError(Exception):
    pass


class SemanticAnalyzer:
    def __init__(self, system: SystemDecl):
        self.system = system
        self.errors: list[tuple[int, int, str]] = []

    def analyze(self):
        self._check_storage()
        self._check_users()

        if self.errors:
            # We just raise the SemanticError; the CLI will handle the formatting
            raise SemanticError(self.errors)

    def _check_storage(self):
        mount_points = []
        for disk in self.system.storage:
            for part in disk.partitions:
                if part.mount:
                    mount_points.append(part.mount)

                # Check Subvolumes require BTRFS
                if part.subvolumes and part.fs != "BTRFS":
                    self.errors.append((part.line, part.column,
                        f"Partition '{part.name}' uses subvolumes but its filesystem is '{part.fs}', not 'BTRFS'."
                    ))

                # Basic Bootloader check
                if part.mount == "/boot" and self.system.bootloader:
                    if (
                        self.system.bootloader.type == "SYSTEMD_BOOT"
                        and part.fs != "FAT32"
                    ):
                        self.errors.append((part.line, part.column,
                            f"Partition mapped to /boot is '{part.fs}', but systemd-boot requires FAT32."
                        ))

        # Check duplicate mount points
        mount_counts = Counter(mount_points)
        for mount, count in mount_counts.items():
            if count > 1:
                # Add to first disk mapping
                self.errors.append((self.system.storage[0].line, self.system.storage[0].column,
                    f"Duplicate mount point defined: '{mount}' appears {count} times."
                ))

        # Check for root mount presence
        if "/" not in mount_points:
            line, col = (self.system.storage[0].line, self.system.storage[0].column) if self.system.storage else (self.system.line, self.system.column)
            self.errors.append((line, col,
                "No root partition mount point ('/') defined in storage."
            ))

    def _check_users(self):
        has_root = any(u.is_root for u in self.system.users)
        if not has_root:
            line, col = (self.system.users[0].line, self.system.users[0].column) if self.system.users else (self.system.line, self.system.column)
            self.errors.append((line, col,
                "No root user defined. You must declare a `root { ... }` block."
            ))

        usernames = [u.name for u in self.system.users if not u.is_root]
        users_counter = Counter(usernames)
        for uname, count in users_counter.items():
            if count > 1:
                # Find the user
                dup_user = next(u for u in self.system.users if u.name == uname)
                self.errors.append((dup_user.line, dup_user.column,
                    f"Duplicate normal user defined: '{uname}' appears {count} times."
                ))
