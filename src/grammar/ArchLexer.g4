lexer grammar ArchLexer;

/* Keywords - System */
SYSTEM: 'system';
EXTENDS: 'extends';
IMPORT: 'import';

/* Keywords - Blocks */
BOOTLOADER: 'bootloader';
SYSTEM_OPTS: 'system_opts';
STORAGE: 'storage';
PARTITION: 'partition';
SOFTWARE: 'software';
USERS: 'users';
USER: 'user';
ROOT: 'root';
DESKTOP: 'desktop';
LINK: 'link';
EXEC: 'exec';

/* Keywords - Properties */
HOSTNAME: 'hostname';
TIMEZONE: 'timezone';
LOCALE: 'locale';
TYPE: 'type';
HEADERS: 'headers';
FSTRIM_TIMER: 'fstrim_timer';
MICROCODE: 'microcode';
CPUFREQ: 'cpufreq';
FIREWALL: 'firewall';
BACKUP_KERNEL: 'backup_kernel';
GPU: 'gpu';
/*disk on*/
ON: 'on'; 
SCHEME: 'scheme';
SIZE: 'size';
FS: 'fs';
MOUNT: 'mount';
FLAGS: 'flags';
SUBVOLUMES: 'subvolumes';
PASSWORD_HASH: 'password_hash';
GROUPS: 'groups';
SHELL: 'shell';
UID: 'uid';
MANAGER: 'manager';
AUR_HELPER: 'aur_helper';
PACKAGES: 'packages';
AUR_PACKAGES: 'aur_packages';
PACCACHE_TIMER: 'paccache_timer';
PARALLEL_DOWNLOADS: 'parallel_downloads';
REFLECTOR_TIMER: 'reflector_timer';
ENV: 'env';
DISPLAY_MANAGER: 'display_manager';
BASE_FONTS: 'base_fonts';
AUDIO: 'audio';
BLUETOOTH: 'bluetooth';

/* Built-in Functions */
HASH: 'hash';

/* Storage Keywords & Units */
REMAINING: 'REMAINING';
SIZE_UNIT: 'MB' | 'GB' | 'TB';

/* Enums - Storage schemes */
GPT: 'GPT';
MBR: 'MBR';

/* Enums - Filesystems */
EXT4: 'EXT4';
BTRFS: 'BTRFS';
FAT32: 'FAT32';
XFS: 'XFS';
F2FS: 'F2FS';
NILFS2: 'NILFS2';
JFS: 'JFS';
REISERFS: 'REISERFS';
SWAP: 'SWAP';

/* Enums - Flags */
EFI: 'EFI';
BOOT: 'BOOT';
SWAP_FLAG: 'SWAP_FLAG';

/* Enums - Kernels */
LINUX: 'LINUX';
LINUX_LTS: 'LINUX_LTS';
LINUX_ZEN: 'LINUX_ZEN';
LINUX_HARDENED: 'LINUX_HARDENED';

/* Enums - Package Managers */
PACMAN: 'PACMAN';
YAY: 'YAY';
PARU: 'PARU';

/* Enums - Hardware & System */
INTEL: 'INTEL';
AMD: 'AMD';
NVIDIA: 'NVIDIA';
UFW: 'UFW';
FIREWALLD: 'FIREWALLD';
TLP: 'TLP';
AUTOCPU_FREQ: 'AUTOCPU_FREQ';
POWERTOP: 'POWERTOP';
POWER_PROFILES_DAEMON: 'POWER_PROFILES_DAEMON';
PIPEWIRE: 'PIPEWIRE';
PULSEAUDIO: 'PULSEAUDIO';

/* Enums - Shells */
ZSH: 'ZSH';
BASH: 'BASH';
FISH: 'FISH';

/* Enums - Bootloaders */
SYSTEMD_BOOT: 'SYSTEMD_BOOT';
GRUB: 'GRUB';

/* Drive Selectors */
LARGEST_DRIVE: 'LARGEST_DRIVE';
SMALLEST_DRIVE: 'SMALLEST_DRIVE';

/* Basic Types */
TYPE_BOOL: 'true' | 'false';
TYPE_INT: [0-9]+;
STRING: '"' (~["\r\n\\] | '\\' .)* '"';

/* Structure Symbols */
LBRACE: '{';
RBRACE: '}';
LBRACKET: '[';
RBRACKET: ']';
LPAREN: '(';
RPAREN: ')';
ASSIGN: '=';
SEMI: ';';
COMMA: ',';
ARROW: '->';

/* Generic IDs for Groups, Custom properties, Usernames if not strings */
ID: [a-zA-Z_][a-zA-Z0-9_-]*;

/* Whitespace and Comments */
WS: [ \t\r\n]+ -> skip;
LINE_COMMENT: '//' ~[\r\n]* -> skip;
BLOCK_COMMENT: '/*' .*? '*/' -> skip;
