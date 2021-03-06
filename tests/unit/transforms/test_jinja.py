from kibitzr.transformer.jinja_transform import jinja_transform


def test_content_is_passed():
    ok, content = jinja_transform('hello {{ content }}!', 'world', {})
    assert ok is True
    assert content == "hello world!"


def test_lines_are_passed():
    ok, content = jinja_transform('{{ lines[1] }}', 'a\nb', {})
    assert ok is True
    assert content == "b"


def test_json_is_passed():
    ok, content = jinja_transform('{{ json["a"][1] }}', '{"a": [1, 2, 3]}', {})
    assert ok is True
    assert content == "2"


def test_css_selector_is_passed():
    ok, content = jinja_transform(
        '{{ css("div p") | text }}',
        '<div><a>A</a><p>P</p></div>',
        {},
    )
    assert ok is True
    assert content == "P"


def test_xpath_selector_is_passed():
    ok, content = jinja_transform(
        '{{ xpath("//div/p") | text }}',
        '<div><a>A</a><p>P</p></div>',
        {},
    )
    assert ok is True
    assert content == "P"
