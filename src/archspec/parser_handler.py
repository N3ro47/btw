from src.grammar.build.ArchParser import ArchParser
from src.grammar.build.ArchParserVisitor import ArchParserVisitor

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


class ASTVisitor(ArchParserVisitor):
    def __init__(self):
        super().__init__()
        self.system = None

    def visitProgram(self, ctx: ArchParser.ProgramContext):
        print("[*] OUTLINE: Visiting visitProgram...")
        # We assume one system declaration per file for now
        return self.visit(ctx.systemDecl())

    def visitSystemDecl(self, ctx: ArchParser.SystemDeclContext):
        print("[*] OUTLINE: Visiting visitSystemDecl...")
        sys_name = ctx.ID(0).getText()
        extends_id = None
        if ctx.EXTENDS():
            extends_id = ctx.ID(1).getText()

        self.system = SystemDecl(name=sys_name, extends=extends_id)

        # Visit all sub-blocks
        for block in ctx.block():
            self.visit(block)

        return self.system

    def visitBootloaderBlock(self, ctx: ArchParser.BootloaderBlockContext):
        print("[*] OUTLINE: Visiting visitBootloaderBlock...")
        bt = Bootloader(type="dummy")
        self.system.bootloader = bt
        return bt

    def visitSystemOptsBlock(self, ctx: ArchParser.SystemOptsBlockContext):
        print("[*] OUTLINE: Visiting visitSystemOptsBlock...")
        opts = SystemOpts()
        self.system.system_opts = opts
        return opts

    def visitStorageBlock(self, ctx: ArchParser.StorageBlockContext):
        print("[*] OUTLINE: Visiting visitStorageBlock...")
        st = Storage(name="dummy", device="dummy")
        self.system.storage.append(st)
        return st

    def visitPartition(self, ctx: ArchParser.PartitionContext):
        print("[*] OUTLINE: Visiting visitPartition...")
        part = Partition(name="dummy", size="dummy")
        return part

    def visitUsersBlock(self, ctx: ArchParser.UsersBlockContext):
        print("[*] OUTLINE: Visiting visitUsersBlock...")
        for user_decl in ctx.userDecl():
            if user_decl.rootDecl():
                self.visitRootDecl(user_decl.rootDecl())
            elif user_decl.normalUserDecl():
                self.visitNormalUserDecl(user_decl.normalUserDecl())

    def visitRootDecl(self, ctx: ArchParser.RootDeclContext):
        print("[*] OUTLINE: Visiting visitRootDecl...")
        user = User(name="root", is_root=True)
        self.system.users.append(user)
        return user

    def visitNormalUserDecl(self, ctx: ArchParser.NormalUserDeclContext):
        print("[*] OUTLINE: Visiting visitNormalUserDecl...")
        user = User(name="dummy", is_root=False)
        self.system.users.append(user)
        return user

    def visitSoftwareBlock(self, ctx: ArchParser.SoftwareBlockContext):
        print("[*] OUTLINE: Visiting visitSoftwareBlock...")
        sw = Software()
        self.system.software = sw
        return sw

    def visitDesktopBlock(self, ctx: ArchParser.DesktopBlockContext):
        print("[*] OUTLINE: Visiting visitDesktopBlock...")
        desk = Desktop()
        self.system.desktop = desk
        return desk

    def visitLinkBlock(self, ctx: ArchParser.LinkBlockContext):
        print("[*] OUTLINE: Visiting visitLinkBlock...")
        link = Link(source="dummy", target="dummy")
        self.system.links.append(link)
        return link

    def visitExecBlock(self, ctx: ArchParser.ExecBlockContext):
        print("[*] OUTLINE: Visiting visitExecBlock...")
        execute = Exec(command="dummy")
        self.system.execs.append(execute)
        return execute
