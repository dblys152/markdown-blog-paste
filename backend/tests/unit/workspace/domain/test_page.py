import pytest

from md2blog.modules.workspace.domain.page import Page
from md2blog.shared.domain.tsid import TSID


def test_page_normalizes_title_and_keeps_hierarchy() -> None:
    page = Page(
        id=TSID(2),
        owner_id=TSID(1),
        parent_id=TSID(3),
        title="  API 설계  ",
        content="# API 설계",
        position=1,
    )

    assert page.title == "API 설계"
    assert page.parent_id == TSID(3)


@pytest.mark.parametrize("title", ["", "   "])
def test_page_rejects_blank_title(title: str) -> None:
    with pytest.raises(ValueError, match="must not be blank"):
        Page(id=TSID(2), owner_id=TSID(1), title=title, content="")
