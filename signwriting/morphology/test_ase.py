"""Document the current no-op pluralization and unimplemented aspect hooks."""
import pytest

from signwriting.morphology.ase import pluralize, repeat_action, sustain_action


def test_pluralize_returns_fsw_unchanged():
    fsw = "M507x507S1f720487x492"
    assert pluralize(fsw) == fsw


@pytest.mark.parametrize("transform", [repeat_action, sustain_action])
def test_placeholders_fail_explicitly(transform):
    with pytest.raises(NotImplementedError, match=transform.__name__):
        transform("M507x507S1f720487x492")
