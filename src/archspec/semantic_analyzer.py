from .ast import SystemDecl


class SemanticError(Exception):
    pass


class SemanticAnalyzer:
    def __init__(self, system: SystemDecl):
        self.system = system
        self.errors: list[str] = []

    def analyze(self):
        print("[*] OUTLINE: Executing Semantic Analysis phase...")
        self._check_storage()
        self._check_users()

        if self.errors:
            msg = "\n".join(self.errors)
            raise SemanticError(
                f"Semantic Validation Failed with {len(self.errors)} errors:\n{msg}"
            )

    def _check_storage(self):
        # TODO: Check for duplicate mount points.
        # TODO: Check that partition filesystems match their mount requirements.
        # TODO: Ensure root '/' mount presence.
        pass

    def _check_users(self):
        # TODO: Ensure root user exists.
        # TODO: Check for duplicate user names.
        pass
