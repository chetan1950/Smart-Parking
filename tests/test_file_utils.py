from utils.file_utils import allowed_file


def test_file_validation_uses_extensions():
    allowed = {"jpg", "jpeg", "png"}
    assert allowed_file("parking.JPG", allowed)
    assert not allowed_file("virus.exe", allowed)
    assert not allowed_file("no_extension", allowed)
