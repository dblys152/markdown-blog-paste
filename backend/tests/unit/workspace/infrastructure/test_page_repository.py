from md2blog.modules.workspace.domain.commands import CreatePageCommand
from md2blog.modules.workspace.domain.page import Page
from md2blog.modules.workspace.infrastructure.repositories import SqlAlchemyPageRepository
from md2blog.shared.domain.tsid import TSID


class RecordingSession:
    def __init__(self) -> None:
        self.events: list[tuple[str, object | None]] = []

    async def execute(self, statement: object) -> None:
        self.events.append(("execute", statement))


async def test_add_inserts_page_and_content_with_one_statement() -> None:
    session = RecordingSession()
    repository = SqlAlchemyPageRepository(session)  # type: ignore[arg-type]
    page = Page.create(
        CreatePageCommand(
            owner_id=TSID(1),
            title="새 페이지",
            content="# 새 페이지",
            parent_id=None,
            sort_order=0,
        )
    )

    await repository.add(page)

    assert [event for event, _ in session.events] == ["execute"]
    sql = str(session.events[0][1])
    assert "WITH inserted_page AS" in sql
    assert "INSERT INTO pages" in sql
    assert "INSERT INTO page_contents" in sql
