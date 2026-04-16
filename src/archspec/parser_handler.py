from src.grammar.build.ArchParser import ArchParser
from src.grammar.build.ArchParserVisitor import ArchParserVisitor
from antlr4.error.ErrorListener import ErrorListener

from .ast import (
    Bootloader,
    Desktop,
    Exec,
    Link,
    Partition,
    Software,
    Storage,
    SystemDecl,
    SystemOpts,
    User,
)


class CompilerErrorListener(ErrorListener):
    def __init__(self):
        super().__init__()
        self.errors = []

    def syntaxError(self, recognizer, offendingSymbol, line, column, msg, e):
        self.errors.append((line, column, msg))



class ASTVisitor(ArchParserVisitor):
    def __init__(self):
        super().__init__()
        self.system = None

    def visitProgram(self, ctx: ArchParser.ProgramContext):
        # We assume one system declaration per file for now
        return self.visit(ctx.systemDecl())

    def visitSystemDecl(self, ctx: ArchParser.SystemDeclContext):
        sys_name = ctx.ID(0).getText()
        extends_id = None
        if ctx.EXTENDS():
            extends_id = ctx.ID(1).getText()

        self.system = SystemDecl(name=sys_name, extends=extends_id).set_location(ctx.start.line, ctx.start.column)

        # Visit all sub-blocks
        for block in ctx.block():
            self.visit(block)

        return self.system

    def visitBootloaderBlock(self, ctx: ArchParser.BootloaderBlockContext):
        bt_type = "SYSTEMD_BOOT"  # Default
        for param in ctx.bootloaderParam():
            if param.TYPE():
                bt_type = param.getChild(2).getText()

        self.system.bootloader = Bootloader(type=bt_type).set_location(ctx.start.line, ctx.start.column)
        return self.system.bootloader

    def visitSystemOptsBlock(self, ctx: ArchParser.SystemOptsBlockContext):
        opts = SystemOpts().set_location(ctx.start.line, ctx.start.column)
        for param in ctx.systemOptsParam():
            if param.HOSTNAME():
                opts.hostname = param.STRING().getText().strip('"')
            elif param.TIMEZONE():
                opts.timezone = param.STRING().getText().strip('"')
            elif param.LOCALE():
                opts.locale = param.STRING().getText().strip('"')
            elif param.TYPE():
                opts.kernel_type = param.getChild(2).getText()
            elif param.HEADERS():
                opts.headers = param.TYPE_BOOL().getText() == "true"
            elif param.FSTRIM_TIMER():
                opts.fstrim_timer = param.TYPE_BOOL().getText() == "true"
            elif param.MICROCODE():
                opts.microcode = param.getChild(2).getText()
            elif param.CPUFREQ():
                opts.cpufreq = param.getChild(2).getText()
            elif param.FIREWALL():
                opts.firewall = param.getChild(2).getText()
            elif param.BACKUP_KERNEL():
                opts.backup_kernel = param.getChild(2).getText()
            elif param.GPU():
                opts.gpu = param.getChild(2).getText()

        self.system.system_opts = opts
        return opts

    def visitStorageBlock(self, ctx: ArchParser.StorageBlockContext):
        st_name = ctx.ID().getText()

        if ctx.STRING():
            device_str = ctx.STRING().getText().strip('"')
        elif ctx.LARGEST_DRIVE():
            device_str = "LARGEST_DRIVE"
        elif ctx.SMALLEST_DRIVE():
            device_str = "SMALLEST_DRIVE"

        st = Storage(name=st_name, device=device_str).set_location(ctx.start.line, ctx.start.column)

        for param in ctx.storageParam():
            if param.SCHEME():
                st.scheme = param.getChild(2).getText()

        for part_ctx in ctx.partition():
            st.partitions.append(self.visitPartition(part_ctx))

        self.system.storage.append(st)
        return st

    def visitPartition(self, ctx: ArchParser.PartitionContext):
        if ctx.ROOT():
            p_name = "root"
        else:
            p_name = ctx.ID().getText()

        part = Partition(name=p_name, size="0").set_location(ctx.start.line, ctx.start.column)

        for param in ctx.partitionParam():
            if param.SIZE():
                part.size = param.sizeExpr().getText()
            elif param.FS():
                part.fs = param.fsType().getText()
            elif param.MOUNT():
                part.mount = param.STRING().getText().strip('"')
            elif param.FLAGS():
                flags_ctx = param.arrayExpr()
                if flags_ctx.anyId():
                    part.flags = [id_node.getText() for id_node in flags_ctx.anyId()]
            elif param.SUBVOLUMES():
                subvols_ctx = param.stringArrayExpr()
                if subvols_ctx.STRING():
                    part.subvolumes = [
                        s.getText().strip('"') for s in subvols_ctx.STRING()
                    ]

        return part

    def visitUsersBlock(self, ctx: ArchParser.UsersBlockContext):
        for user_decl in ctx.userDecl():
            if user_decl.rootDecl():
                self.visitRootDecl(user_decl.rootDecl())
            elif user_decl.normalUserDecl():
                self.visitNormalUserDecl(user_decl.normalUserDecl())

    def visitRootDecl(self, ctx: ArchParser.RootDeclContext):
        user = User(name="root", is_root=True).set_location(ctx.start.line, ctx.start.column)
        self._populate_user_params(user, ctx.userParam())
        self.system.users.append(user)

    def visitNormalUserDecl(self, ctx: ArchParser.NormalUserDeclContext):
        username = ctx.STRING().getText().strip('"')
        user = User(name=username, is_root=False).set_location(ctx.start.line, ctx.start.column)
        self._populate_user_params(user, ctx.userParam())
        self.system.users.append(user)

    def _populate_user_params(self, user: User, params: list):
        for param in params:
            if param.PASSWORD_HASH():
                user.password_hash = param.STRING().getText().strip('"')
            elif param.GROUPS():
                grp_ctx = param.arrayExpr()
                if grp_ctx.anyId():
                    user.groups = [id_node.getText() for id_node in grp_ctx.anyId()]
            elif param.SHELL():
                user.shell = param.getChild(2).getText()
            elif param.UID():
                user.uid = int(param.TYPE_INT().getText())

    def visitSoftwareBlock(self, ctx: ArchParser.SoftwareBlockContext):
        sw = Software().set_location(ctx.start.line, ctx.start.column)
        for param in ctx.softwareParam():
            if param.MANAGER():
                sw.manager = param.getChild(2).getText()
            elif param.AUR_HELPER():
                sw.aur_helper = param.getChild(2).getText()
            elif param.PACKAGES():
                pkg_ctx = param.stringArrayExpr()
                if pkg_ctx.STRING():
                    sw.packages = [s.getText().strip('"') for s in pkg_ctx.STRING()]
            elif param.AUR_PACKAGES():
                aur_ctx = param.stringArrayExpr()
                if aur_ctx.STRING():
                    sw.aur_packages = [s.getText().strip('"') for s in aur_ctx.STRING()]
            elif param.PACCACHE_TIMER():
                sw.paccache_timer = param.TYPE_BOOL().getText() == "true"
            elif param.PARALLEL_DOWNLOADS():
                sw.parallel_downloads = param.TYPE_BOOL().getText() == "true"
            elif param.REFLECTOR_TIMER():
                sw.reflector_timer = param.TYPE_BOOL().getText() == "true"

        self.system.software = sw
        return sw

    def visitDesktopBlock(self, ctx: ArchParser.DesktopBlockContext):
        desk = Desktop().set_location(ctx.start.line, ctx.start.column)
        for param in ctx.desktopParam():
            if param.ENV():
                desk.env = param.ID().getText()
            elif param.DISPLAY_MANAGER():
                desk.display_manager = param.ID().getText()
            elif param.BASE_FONTS():
                desk.base_fonts = param.TYPE_BOOL().getText() == "true"
            elif param.AUDIO():
                desk.audio = param.getChild(2).getText()
            elif param.BLUETOOTH():
                desk.bluetooth = param.TYPE_BOOL().getText() == "true"

        self.system.desktop = desk
        return desk

    def visitLinkBlock(self, ctx: ArchParser.LinkBlockContext):
        src = ctx.STRING(0).getText().strip('"')
        tgt = ctx.STRING(1).getText().strip('"')
        self.system.links.append(Link(source=src, target=tgt).set_location(ctx.start.line, ctx.start.column))

    def visitExecBlock(self, ctx: ArchParser.ExecBlockContext):
        bash_cmd = ctx.STRING().getText().strip('"')
        self.system.execs.append(Exec(command=bash_cmd).set_location(ctx.start.line, ctx.start.column))
