from dataclasses import dataclass


@dataclass
class RuntimeSecurityState:
    compromised: bool = False
    reason: str | None = None
    rule_id: str | None = None

class RuntimeCompromisedError(RuntimeError):
    pass


def ensure_runtime_safe() -> None:
    if runtime_security_state.compromised:
        raise RuntimeCompromisedError(
            f"Runtime is in compromised state: "
            f"{runtime_security_state.rule_id}"
        )

runtime_security_state = RuntimeSecurityState()
