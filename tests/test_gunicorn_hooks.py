def test_assert_asserts():
    assert True


def test_pre_request_exists():
    from dynoscale.hooks.gunicorn import pre_request
    assert pre_request


def test_post_request_exists():
    from dynoscale.hooks.gunicorn import post_request
    assert post_request
