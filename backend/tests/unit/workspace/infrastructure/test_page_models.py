from sqlalchemy import BigInteger, Text

from md2blog.modules.workspace.infrastructure.models import PageContentModel, PageModel


def test_page_metadata_and_content_use_separate_tables() -> None:
    assert "content" not in PageModel.__table__.c
    assert isinstance(PageContentModel.__table__.c.page_id.type, BigInteger)
    assert PageContentModel.__table__.c.page_id.primary_key
    assert isinstance(PageContentModel.__table__.c.content.type, Text)


def test_page_content_is_deleted_with_its_page() -> None:
    foreign_key = next(iter(PageContentModel.__table__.c.page_id.foreign_keys))

    assert foreign_key.target_fullname == "pages.id"
    assert foreign_key.ondelete == "CASCADE"
