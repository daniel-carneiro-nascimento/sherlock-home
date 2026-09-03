from __future__ import annotations

from dataclasses import dataclass

import scripts.financial_chat as cli


class FakeSession:
    def __init__(self):
        self.executed = []

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, traceback):
        return False

    def execute(self, statement):
        self.executed.append(str(statement))


@dataclass(frozen=True)
class FakeResult:
    answer: str
    tools_used: tuple[str, ...]


class FakeService:
    def __init__(self):
        self.calls = []

    def ask(self, session, *, user_message):
        self.calls.append((session, user_message))
        return FakeResult(
            answer="Resposta baseada nos dados locais.",
            tools_used=(
                "get_monthly_spending",
                "get_category_spending",
            ),
        )


def test_real_chat_cli_runs_service_with_database_session(monkeypatch, capsys):
    session = FakeSession()
    service = FakeService()

    monkeypatch.setattr(cli, "SessionLocal", lambda: session)
    monkeypatch.setattr(cli, "build_financial_chat_service", lambda: service)

    exit_code = cli.run_chat("Analise meus gastos de junho de 2026.")
    captured = capsys.readouterr()

    assert exit_code == 0
    assert session.executed == ["SELECT 1"]
    assert service.calls == [
        (session, "Analise meus gastos de junho de 2026.")
    ]
    assert "get_monthly_spending" in captured.out
    assert "Resposta baseada nos dados locais." in captured.out


def test_real_chat_cli_can_hide_tools(monkeypatch, capsys):
    monkeypatch.setattr(cli, "SessionLocal", lambda: FakeSession())
    monkeypatch.setattr(cli, "build_financial_chat_service", lambda: FakeService())

    exit_code = cli.run_chat("Quanto gastei?", show_tools=False)
    captured = capsys.readouterr()

    assert exit_code == 0
    assert "Tools used:" not in captured.out
    assert "Resposta baseada nos dados locais." in captured.out


def test_real_chat_cli_rejects_empty_question(capsys):
    exit_code = cli.run_chat("   ")
    captured = capsys.readouterr()

    assert exit_code == 2
    assert "must not be empty" in captured.err


def test_real_chat_cli_reports_agent_failure(monkeypatch, capsys):
    class FailingService:
        def ask(self, session, *, user_message):
            raise cli.ToolPlanError("invalid tool plan")

    monkeypatch.setattr(cli, "SessionLocal", lambda: FakeSession())
    monkeypatch.setattr(cli, "build_financial_chat_service", lambda: FailingService())

    exit_code = cli.run_chat("Pergunta válida")
    captured = capsys.readouterr()

    assert exit_code == 1
    assert "agent execution failed" in captured.err
