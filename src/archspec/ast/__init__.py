from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class ASTNode:
    pass


# ---- Storage Nodes ----


@dataclass
class Partition(ASTNode):
    name: str
    size: str
    fs: Optional[str] = None
    mount: Optional[str] = None
    flags: List[str] = field(default_factory=list)
    subvolumes: List[str] = field(default_factory=list)


@dataclass
class Storage(ASTNode):
    name: str
    device: str
    scheme: str = "GPT"
    partitions: List[Partition] = field(default_factory=list)


# ---- User Nodes ----


@dataclass
class User(ASTNode):
    name: str
    is_root: bool = False
    password_hash: Optional[str] = None
    groups: List[str] = field(default_factory=list)
    shell: Optional[str] = None
    uid: Optional[int] = None


# ---- System & Config Nodes ----


@dataclass
class Bootloader(ASTNode):
    type: str


@dataclass
class SystemOpts(ASTNode):
    hostname: Optional[str] = None
    timezone: Optional[str] = None
    locale: Optional[str] = None
    kernel_type: str = "LINUX"
    headers: bool = False
    fstrim_timer: bool = False
    microcode: Optional[str] = None
    cpufreq: Optional[str] = None
    firewall: Optional[str] = None
    backup_kernel: Optional[str] = None
    gpu: Optional[str] = None


@dataclass
class Software(ASTNode):
    manager: str = "PACMAN"
    aur_helper: Optional[str] = None
    packages: List[str] = field(default_factory=list)
    aur_packages: List[str] = field(default_factory=list)
    paccache_timer: bool = False
    parallel_downloads: bool = False
    reflector_timer: bool = False


@dataclass
class Desktop(ASTNode):
    env: Optional[str] = None
    display_manager: Optional[str] = None
    base_fonts: bool = False
    audio: Optional[str] = None
    bluetooth: bool = False


@dataclass
class Link(ASTNode):
    source: str
    target: str


@dataclass
class Exec(ASTNode):
    command: str


# ---- Root Node ----


@dataclass
class SystemDecl(ASTNode):
    name: str
    extends: Optional[str] = None
    bootloader: Optional[Bootloader] = None
    system_opts: Optional[SystemOpts] = None
    storage: List[Storage] = field(default_factory=list)
    users: List[User] = field(default_factory=list)
    software: Optional[Software] = None
    desktop: Optional[Desktop] = None
    links: List[Link] = field(default_factory=list)
    execs: List[Exec] = field(default_factory=list)
