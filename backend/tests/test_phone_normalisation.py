from backend.app.services.phone_normalisation import normalise_uk_phone

EXPECTED = "+447700900101"


def test_local_format_with_space():
    result = normalise_uk_phone("07700 900101")
    assert result.status == "valid"
    assert result.normalised_number == EXPECTED


def test_local_format_no_space():
    result = normalise_uk_phone("07700900101")
    assert result.status == "valid"
    assert result.normalised_number == EXPECTED


def test_local_format_hyphen():
    result = normalise_uk_phone("07700-900101")
    assert result.status == "valid"
    assert result.normalised_number == EXPECTED


def test_local_format_parentheses():
    result = normalise_uk_phone("(07700) 900101")
    assert result.status == "valid"
    assert result.normalised_number == EXPECTED


def test_e164_format():
    result = normalise_uk_phone("+447700900101")
    assert result.status == "valid"
    assert result.normalised_number == EXPECTED


def test_e164_format_with_spaces():
    result = normalise_uk_phone("+44 7700 900101")
    assert result.status == "valid"
    assert result.normalised_number == EXPECTED


def test_international_0044_format():
    result = normalise_uk_phone("0044 7700 900101")
    assert result.status == "valid"
    assert result.normalised_number == EXPECTED


def test_international_0044_no_spaces():
    result = normalise_uk_phone("00447700900101")
    assert result.status == "valid"
    assert result.normalised_number == EXPECTED


def test_none_is_unavailable():
    result = normalise_uk_phone(None)
    assert result.status == "unavailable"
    assert result.normalised_number is None


def test_blank_is_unavailable():
    result = normalise_uk_phone("   ")
    assert result.status == "unavailable"
    assert result.normalised_number is None


def test_empty_string_is_unavailable():
    result = normalise_uk_phone("")
    assert result.status == "unavailable"
    assert result.normalised_number is None


def test_withheld_is_unavailable():
    result = normalise_uk_phone("withheld")
    assert result.status == "unavailable"


def test_private_is_unavailable():
    result = normalise_uk_phone("private")
    assert result.status == "unavailable"


def test_unknown_is_unavailable():
    result = normalise_uk_phone("unknown")
    assert result.status == "unavailable"


def test_alphabetic_value_is_invalid():
    result = normalise_uk_phone("abc123")
    assert result.status == "invalid"
    assert result.normalised_number is None


def test_wrong_length_is_invalid():
    result = normalise_uk_phone("+4477009001")
    assert result.status == "invalid"


def test_non_uk_country_code_is_invalid():
    result = normalise_uk_phone("+1234567890")
    assert result.status == "invalid"
