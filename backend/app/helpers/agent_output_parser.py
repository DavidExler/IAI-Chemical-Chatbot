from __future__ import annotations

import json
import logging
import re
from collections.abc import Callable
from typing import Any

from langchain.agents.agent import AgentOutputParser
from langchain_core.agents import AgentAction, AgentFinish
from langchain_core.exceptions import OutputParserException

LOGGER = logging.getLogger(__name__)


class JSONAgentOutputParser(AgentOutputParser):
    def parse(self, text: str) -> AgentAction | AgentFinish:
        try:
            LOGGER.info("text: %s", text)
            response = parse_json_markdown(text)
            LOGGER.info("response: %s", response)
            if isinstance(response, list):
                # gpt turbo frequently ignores the directive to emit a single action
                LOGGER.warning("Got multiple action responses: %s", response)
                response = response[0]
            if response["action"] == "Final Answer":
                return AgentFinish({"output": response["action_input"]}, text)
            else:
                return AgentAction(
                    response["action"], response.get("action_input", {}), text
                )
        except Exception as e:
            raise OutputParserException(f"Could not parse LLM output: {text}") from e

    @property
    def _type(self) -> str:
        return "json-agent"


def parse_partial_json(s: str, *, strict: bool = False) -> Any:
    try:
        return json.loads(s, strict=strict)
    except json.JSONDecodeError:
        pass

    new_s = ""
    stack = []
    is_inside_string = False
    escaped = False

    for char in s:
        if is_inside_string:
            if char == '"' and not escaped:
                is_inside_string = False
            elif char == "\n" and not escaped:
                char = "\\n"  # Replace the newline character with the escape sequence.
            elif char == "\\":
                escaped = not escaped
            else:
                escaped = False
        else:
            if char == '"':
                is_inside_string = True
                escaped = False
            elif char == "{":
                stack.append("}")
            elif char == "[":
                stack.append("]")
            elif char == "}" or char == "]":
                if stack and stack[-1] == char:
                    stack.pop()
                else:
                    return None

        new_s += char

    if is_inside_string:
        new_s += '"'

    while new_s:
        final_s = new_s

        for closing_char in reversed(stack):
            final_s += closing_char

        try:
            return json.loads(final_s, strict=strict)
        except json.JSONDecodeError:
            new_s = new_s[:-1]
    return json.loads(s, strict=strict)


def _parse_json(
    json_str: str, *, parser: Callable[[str], Any] = parse_partial_json
) -> dict:
    # replace '"' in string to !?! for regex parsing and revert it back after parsing
    action = re.search(r'"action":\s*"([^"]+)', json_str)
    json_str = json_str.replace('\\"', "!?!")
    action_input = re.search(r'"action_input":\s*"([^"]+)', json_str)
    return {
        "action": action.group(1).strip() if action else "",
        "action_input": (
            action_input.group(1).strip().replace("!?!", '\\"') if action_input else ""
        ),
    }
    # try:
    #     json_str = json_str.strip().strip("`")
    #     json_str = _custom_parser(json_str)
    #     return parser(json_str)
    # except json.JSONDecodeError:
    #     action = re.search(r'"action":\s*"([^"]+)', json_str)
    #     json_str = json_str.replace('\\"', "!?!")
    #     action_input = re.search(r'"action_input":\s*"([^"]+)', json_str)
    #     return {
    #         "action": action.group(1).strip() if action else "",
    #         "action_input": (
    #             action_input.group(1).strip().replace("!?!", '\\"')
    #             if action_input
    #             else ""
    #         ),
    #     }


def parse_json_markdown(
    json_string: str, *, parser: Callable[[str], Any] = parse_partial_json
) -> dict:
    try:
        return _parse_json(json_string, parser=parser)
    except json.JSONDecodeError:
        match = re.search(r"```(json)?(.*)", json_string, re.DOTALL)
        if match is None:
            json_str = json_string
        else:
            json_str = match.group(2)
    return _parse_json(json_str, parser=parser)
