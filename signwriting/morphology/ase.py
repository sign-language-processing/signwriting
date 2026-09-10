"""Experimental ASL morphology placeholders, not implemented transformations.

An upstream grammar planner must decide whether a transformation is appropriate
for the lexical sign and sentence context. English inflection alone is not enough.
Pluralization currently passes FSW through unchanged; action-aspect hooks raise.
"""
# The FSW argument reserves the input contract for these explicitly unimplemented hooks.
# pylint: disable=unused-argument


def pluralize(fsw: str) -> str:
    """Return FSW unchanged until ASL plural realization is implemented.

    Not a generic sign duplication operation: quantifiers, spatial distribution,
    classifiers, or an unchanged sign may instead be appropriate in context.
    """
    # TODO: implement validated, sign-specific ASL plural realization rules.
    return fsw


def repeat_action(fsw: str) -> str:
    """Placeholder for repetitive action aspect, not nominal plurality or tense."""
    raise NotImplementedError("ASL repeat_action requires validated, sign-specific aspect rules")


def sustain_action(fsw: str) -> str:
    """Placeholder for sustained action aspect, not a generic English -ing mapping."""
    raise NotImplementedError("ASL sustain_action requires validated, sign-specific aspect rules")
