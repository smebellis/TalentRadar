import pytest

from pipeline.state import PipelineContext, PipelineState


def test_pipeline_state_has_expected_values():
    assert PipelineState.IDLE.value == "idle"
    assert PipelineState.SEARCHING.value == "searching"
    assert PipelineState.COMPLETE.value == "complete"
    assert PipelineState.ERROR.value == "error"


def test_pipeline_context_initializes_with_empty_collections():
    ctx = PipelineContext()
    assert ctx.jobs == []
    assert ctx.contacts == []
    assert ctx.messages == []
    assert ctx.errors == []


def test_pipeline_context_default_state_is_idle():
    ctx = PipelineContext()
    assert ctx.state == PipelineState.IDLE


def test_pipeline_context_state_can_be_updated():
    ctx = PipelineContext()
    ctx.state = PipelineState.SEARCHING
    assert ctx.state == PipelineState.SEARCHING


def test_pipeline_context_errors_accumulate():
    ctx = PipelineContext()
    ctx.errors.append("something went wrong")
    assert len(ctx.errors) == 1
