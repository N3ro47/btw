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
        self.script.append("# [COMPILER OUTLINE]: clock sync commands (timedatectl) will be generated here.")

    def _gen_storage(self):
        self.script.append("# [COMPILER OUTLINE]: parted, mkfs, and mount commands will be generated here based on AST.")

    def _gen_pacstrap(self):
        self.script.append("# [COMPILER OUTLINE]: pacstrap commands will be generated here based on AST packages.")

    def _gen_fstab(self):
        self.script.append("# [COMPILER OUTLINE]: genfstab commands will be generated here.")

    def _gen_chroot(self):
        self.script.append("# [COMPILER OUTLINE]: arch-chroot commands for users, bootloader, desktop, etc. will be generated here.")
