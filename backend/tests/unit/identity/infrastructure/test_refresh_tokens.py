from md2blog.modules.identity.infrastructure.tokens import SecureRefreshTokenManager


def test_refresh_token_is_random_and_only_hash_is_persistable() -> None:
    manager = SecureRefreshTokenManager()

    first = manager.generate()
    second = manager.generate()

    assert first.raw != second.raw
    assert len(first.token_hash) == 64
    assert manager.hash(first.raw) == first.token_hash
    assert first.raw not in first.token_hash
