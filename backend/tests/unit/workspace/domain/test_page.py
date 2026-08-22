from datetime import UTC, datetime, timedelta

import pytest

from md2blog.modules.workspace.domain.commands import CreatePageCommand
from md2blog.modules.workspace.domain.page import (
    BlankPageTitleError,
    InvalidPageContentError,
    InvalidPageParentError,
    Page,
    PageContent,
)
from md2blog.shared.domain.tsid import TSID

NOW = datetime(2026, 1, 1, tzinfo=UTC)


def test_page_normalizes_title_and_keeps_hierarchy() -> None:
    page = Page(
        id=TSID(2),
        owner_id=TSID(1),
        parent_id=TSID(3),
        title="  API 설계  ",
        content=PageContent(page_id=TSID(2), content="# API 설계"),
        sort_order=1,
        created_at=NOW,
        updated_at=NOW,
    )

    assert page.title == "API 설계"
    assert page.parent_id == TSID(3)


@pytest.mark.parametrize("title", ["", "   "])
def test_page_rejects_blank_title(title: str) -> None:
    with pytest.raises(BlankPageTitleError):
        Page(
            id=TSID(2),
            owner_id=TSID(1),
            parent_id=None,
            title=title,
            content=PageContent(page_id=TSID(2), content=""),
            sort_order=0,
            created_at=NOW,
            updated_at=NOW,
        )


def test_page_rejects_content_owned_by_another_page() -> None:
    with pytest.raises(InvalidPageContentError):
        Page(
            id=TSID(2),
            owner_id=TSID(1),
            parent_id=None,
            title="페이지",
            content=PageContent(page_id=TSID(3), content=""),
            sort_order=0,
            created_at=NOW,
            updated_at=NOW,
        )


def test_page_rejects_itself_as_parent() -> None:
    with pytest.raises(InvalidPageParentError):
        Page(
            id=TSID(2),
            owner_id=TSID(1),
            parent_id=TSID(2),
            title="페이지",
            content=PageContent(page_id=TSID(2), content=""),
            sort_order=0,
            created_at=NOW,
            updated_at=NOW,
        )


def test_page_create_assigns_the_same_creation_and_update_time() -> None:
    page = Page.create(
        CreatePageCommand(
            owner_id=TSID(1),
            title="새 페이지",
            content="# 새 페이지",
            parent_id=None,
            sort_order=0,
        ),
        created_at=NOW,
    )

    assert page.created_at == NOW
    assert page.updated_at == NOW


def test_page_change_preserves_creation_time_and_updates_modified_time() -> None:
    page = Page.create(
        CreatePageCommand(
            owner_id=TSID(1),
            title="기존 제목",
            content="",
            parent_id=None,
            sort_order=0,
        ),
        created_at=NOW,
    )
    changed_at = NOW + timedelta(minutes=1)

    renamed = page.rename("변경된 제목", changed_at=changed_at)

    assert renamed.created_at == NOW
    assert renamed.updated_at == changed_at
