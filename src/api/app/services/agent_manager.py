# from typing import List, Iterator, Any
# from semantic_kernel.agents import Agent

# class AgentManager(List[Agent]):
#     def __init__(self, *args, **kwargs):
#         super().__init__()
#         self._agents: List[Agent] = list(*args, **kwargs)

#     def __getitem__(self, index: int) -> Agent:
#         return self._agents[index]

#     def __setitem__(self, index: int, value: Agent) -> None:
#         self._agents[index] = value

#     def __delitem__(self, index: int) -> None:
#         del self._agents[index]

#     def __len__(self) -> int:
#         return len(self._agents)

#     def insert(self, index: int, value: Agent) -> None:
#         self._agents.insert(index, value)

#     def append(self, agent: Agent) -> None:
#         self._agents.append(agent)

#     def remove(self, agent: Agent) -> None:
#         self._agents.remove(agent)

#     def __iter__(self) -> Iterator[Agent]:
#         return iter(self._agents)

#     def get_agent(self, agent_name: str) -> Agent | None:
#         for agent in self._agents:
#             if agent.name == agent_name:
#                 return agent
#         return None

# __all__ = ["AgentManager"]
