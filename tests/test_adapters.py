from __future__ import annotations

import pytest

from vouchline.adapters import spans_to_events
from vouchline.errors import InputError


def test_otlp_tool_span_becomes_request_and_response() -> None:
    payload = {
        "resourceSpans": [
            {
                "scopeSpans": [
                    {
                        "spans": [
                            {
                                "spanId": "abc",
                                "name": "execute_tool",
                                "startTimeUnixNano": "1767225600000000000",
                                "attributes": [
                                    {
                                        "key": "gen_ai.operation.name",
                                        "value": {"stringValue": "execute_tool"},
                                    },
                                    {"key": "gen_ai.tool.name", "value": {"stringValue": "search"}},
                                ],
                                "status": {"code": "STATUS_CODE_OK"},
                            }
                        ]
                    }
                ]
            }
        ]
    }
    events = spans_to_events(payload)
    assert [event["kind"] for event in events] == ["tool.requested", "tool.responded"]
    assert events[0]["payload"]["tool"] == "search"
    assert events[1]["payload"]["status"] == "ok"


def test_otlp_unknown_span_is_preserved_as_extension() -> None:
    events = spans_to_events(
        {
            "resourceSpans": [
                {
                    "scopeSpans": [
                        {
                            "spans": [
                                {
                                    "spanId": "x",
                                    "name": "chat",
                                    "startTimeUnixNano": "1767225600000000000",
                                    "attributes": [],
                                }
                            ]
                        }
                    ]
                }
            ]
        }
    )
    assert events[0]["kind"] == "extension.otlp.span"


def test_otlp_invalid_timestamp_uses_compatibility_fallback() -> None:
    payload = {"resourceSpans": [{"scopeSpans": [{"spans": [{"spanId": "x", "name": "chat"}]}]}]}
    events = spans_to_events(payload)
    assert events[0]["timestamp"]


def test_otlp_rejects_out_of_range_numeric_timestamp() -> None:
    payload = {
        "resourceSpans": [
            {
                "scopeSpans": [
                    {
                        "spans": [
                            {
                                "spanId": "x",
                                "name": "chat",
                                "startTimeUnixNano": "999999999999999999999999999999999999",
                            }
                        ]
                    }
                ]
            }
        ]
    }
    with pytest.raises(InputError, match="out-of-range"):
        spans_to_events(payload)


def test_otlp_requires_bounded_array() -> None:
    with pytest.raises(InputError):
        spans_to_events({"resourceSpans": "bad"})
    with pytest.raises(InputError):
        spans_to_events({"resourceSpans": []}, max_spans=0)
