from unittest.mock import patch

import pytest

from signwriting.server import app
from signwriting.fingerspelling.fingerspelling import get_chars


def test_oversized_input_does_not_render():
    with patch("signwriting.visualizer.server.signwriting_to_image") as render:
        response = app.test_client().get("/visualizer", query_string={"fsw": "a" * 4097})
    assert response.status_code == 413
    render.assert_not_called()


@pytest.mark.parametrize("language", ["../secret", "/etc/passwd", "ase-bad"])
def test_language_rejects_paths(language):
    with pytest.raises(ValueError):
        get_chars(language)
