parser grammar ArchParser;

options { tokenVocab=ArchLexer; }

program: importStmt* systemDecl EOF;

importStmt: IMPORT STRING SEMI;

systemDecl: SYSTEM ID (EXTENDS ID)? LBRACE block* RBRACE;

block: bootloaderBlock
     | systemOptsBlock
     | storageBlock
     | usersBlock
     | softwareBlock
     | desktopBlock
     | linkBlock
     | execBlock
     ;

bootloaderBlock: BOOTLOADER LBRACE bootloaderParam* RBRACE;
bootloaderParam: TYPE ASSIGN (SYSTEMD_BOOT | GRUB) SEMI
               | ID ASSIGN expr SEMI
               ;

systemOptsBlock: SYSTEM_OPTS LBRACE systemOptsParam* RBRACE;
systemOptsParam: HOSTNAME ASSIGN STRING SEMI
               | TIMEZONE ASSIGN STRING SEMI
               | LOCALE ASSIGN STRING SEMI
               | TYPE ASSIGN (LINUX | LINUX_LTS | LINUX_ZEN | LINUX_HARDENED) SEMI
               | HEADERS ASSIGN TYPE_BOOL SEMI
               | FSTRIM_TIMER ASSIGN TYPE_BOOL SEMI
               | MICROCODE ASSIGN (INTEL | AMD) SEMI
               | CPUFREQ ASSIGN (TLP | AUTOCPU_FREQ | POWERTOP | POWER_PROFILES_DAEMON) SEMI
               | FIREWALL ASSIGN (UFW | FIREWALLD) SEMI
               | BACKUP_KERNEL ASSIGN (LINUX | LINUX_LTS | LINUX_ZEN | LINUX_HARDENED) SEMI
               | GPU ASSIGN (NVIDIA | AMD | INTEL) SEMI
               ;

storageBlock: STORAGE ID ON (STRING | LARGEST_DRIVE | SMALLEST_DRIVE) LBRACE storageParam* partition* RBRACE;
storageParam: SCHEME ASSIGN (GPT | MBR) SEMI;

partition: PARTITION (ID | ROOT) LBRACE partitionParam* RBRACE;
partitionParam: SIZE ASSIGN sizeExpr SEMI
              | FS ASSIGN fsType SEMI
              | MOUNT ASSIGN STRING SEMI
              | FLAGS ASSIGN arrayExpr SEMI
              | SUBVOLUMES ASSIGN stringArrayExpr SEMI
              ;

fsType: EXT4 | BTRFS | FAT32 | XFS | F2FS | NILFS2 | JFS | REISERFS | SWAP;

usersBlock: USERS LBRACE userDecl* RBRACE;
userDecl: rootDecl | normalUserDecl;

rootDecl: ROOT LBRACE userParam* RBRACE;
normalUserDecl: USER STRING LBRACE userParam* RBRACE;

userParam: PASSWORD_HASH ASSIGN HASH LPAREN STRING RPAREN SEMI
         | GROUPS ASSIGN arrayExpr SEMI
         | SHELL ASSIGN (BASH | ZSH | FISH) SEMI
         | UID ASSIGN TYPE_INT SEMI
         ;

softwareBlock: SOFTWARE LBRACE softwareParam* RBRACE;
softwareParam: MANAGER ASSIGN (PACMAN) SEMI
             | AUR_HELPER ASSIGN (YAY | PARU) SEMI
             | PACKAGES ASSIGN stringArrayExpr SEMI
             | AUR_PACKAGES ASSIGN stringArrayExpr SEMI
             | PACCACHE_TIMER ASSIGN TYPE_BOOL SEMI
             | PARALLEL_DOWNLOADS ASSIGN TYPE_BOOL SEMI
             | REFLECTOR_TIMER ASSIGN TYPE_BOOL SEMI
             ;

desktopBlock: DESKTOP LBRACE desktopParam* RBRACE;
desktopParam: ENV ASSIGN ID SEMI
            | DISPLAY_MANAGER ASSIGN ID SEMI
            | BASE_FONTS ASSIGN TYPE_BOOL SEMI
            | AUDIO ASSIGN (PIPEWIRE | PULSEAUDIO) SEMI
            | BLUETOOTH ASSIGN TYPE_BOOL SEMI
            ;

linkBlock: LINK STRING ARROW STRING SEMI;

execBlock: EXEC LBRACE STRING RBRACE;

/* Expressions */
expr: TYPE_INT
    | TYPE_BOOL
    | STRING
    | anyId
    | arrayExpr
    | stringArrayExpr
    ;

sizeExpr: TYPE_INT SIZE_UNIT
        | REMAINING
        ;

arrayExpr: LBRACKET (anyId (COMMA anyId)*)? RBRACKET;
stringArrayExpr: LBRACKET (STRING (COMMA STRING)*)? RBRACKET;

anyId: ID | EFI | BOOT | SWAP_FLAG 
     | LINUX | LINUX_LTS | LINUX_ZEN | LINUX_HARDENED
     | PACMAN | YAY | PARU
     | INTEL | AMD | NVIDIA | UFW | FIREWALLD | TLP | AUTOCPU_FREQ | POWERTOP | POWER_PROFILES_DAEMON | PIPEWIRE | PULSEAUDIO
     ;
