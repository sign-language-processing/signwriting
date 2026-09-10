"""Unimplemented morphology must never silently emit synthetic training labels."""
import pytest

from signwriting.morphology.ase import pluralize, repeat_action, sustain_action


@pytest.mark.parametrize("transform", [pluralize, repeat_action, sustain_action])
def test_placeholders_fail_explicitly(transform):
    with pytest.raises(NotImplementedError, match=transform.__name__):
        transform("M507x507S1f720487x492")
