"""
Neo4j domain models definition for graph-oriented relationships.
"""

from dataclasses import dataclass
from typing import Dict


@dataclass
class UserNode:
    id: int
    email: str
    name: str | None = None

    def get_credit_relation(self) -> str:
        # (User)-[:HAS_CREDIT]->(Credit) [cite: 2025-12-23]
        return "HAS_CREDIT"

    def get_schedule_relation(self) -> str:
        # (User)-[:SCHEDULED]->(Schedule) [cite: 2025-12-23]
        return "SCHEDULED"

    def to_graph_dict(self) -> Dict[str, object]:
        return {
            "user_id": self.id,
            "email": self.email,
            "name": self.name,
        }


@dataclass
class CreditNode:
    amount: int
    last_updated: str

    def to_graph_dict(self) -> Dict[str, object]:
        return {
            "amount": self.amount,
            "last_updated": self.last_updated,
        }


@dataclass
class ScheduleNode:
    frequency: str
    posts_per_day: int
    days: list[str]
    target_times: list[str]

    def to_graph_dict(self) -> Dict[str, object]:
        return {
            "frequency": self.frequency,
            "posts_per_day": self.posts_per_day,
            "days": self.days,
            "target_times": self.target_times,
        }

