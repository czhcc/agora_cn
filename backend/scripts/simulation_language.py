"""Apply the configured output language to CAMEL's live and saved prompts."""

from typing import Any

from app.contracts.simulation_language_contract import simulation_language_instruction


def apply_simulation_language(agent_graph: Any, language: object) -> None:
    note = "\n## Simulation output language\n" + simulation_language_instruction(language)
    for _, agent in agent_graph.get_agents():
        changed = False
        for attribute in ("system_message", "_original_system_message"):
            message = getattr(agent, attribute, None)
            if message is not None and note not in message.content:
                # OASIS interviews keep only the part before '# RESPONSE FORMAT'.
                # Prefix the language instruction so that it survives that split.
                message.content = note + "\n" + message.content
                changed = True
        if changed and hasattr(agent, "init_messages"):
            agent.init_messages()
