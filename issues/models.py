from django.db import models

# Create your models here.
from abc import ABC, abstractmethod

VALID_STATUSES = ('open', 'in_progress', 'resolved', 'closed')
VALID_PRIORITIES = ('low', 'medium', 'high', 'critical')


class BaseEntity(ABC):
    FIELDS = ()

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        if not cls.FIELDS:
            raise TypeError(f"{cls.__name__} must define FIELDS")

    @abstractmethod
    def validate(self):
        pass

    def to_dict(self):
        return {key: getattr(self, key) for key in self.FIELDS}


class Reporter(BaseEntity):
    FIELDS = ('id', 'name', 'email', 'team')

    def __init__(self, id, name, email, team):
        self.id = id
        self.name = name
        self.email = email
        self.team = team

    def validate(self):
        if not self.name or not self.name.strip():
            raise ValueError('Name cannot be empty')
        if '@' not in self.email:
            raise ValueError('Invalid email')
        if not self.team or not self.team.strip():
            raise ValueError('Team cannot be empty')


class Issue(BaseEntity):
    FIELDS = ('id', 'title', 'description', 'status', 'priority', 'reporter_id')

    def __init__(self, id, title, description, status, priority, reporter_id):
        self.id = id
        self.title = title
        self.description = description
        self.status = status
        self.priority = priority
        self.reporter_id = reporter_id

    def validate(self):
        if not self.title or not self.title.strip():
            raise ValueError('Title cannot be empty')
        if self.status not in VALID_STATUSES:
            raise ValueError(f"Invalid status. Allowed: {', '.join(VALID_STATUSES)}")
        if self.priority not in VALID_PRIORITIES:
            raise ValueError(f"Invalid priority. Allowed: {', '.join(VALID_PRIORITIES)}")

    def describe(self):
        return f"{self.title} [{self.priority}]"


class CriticalIssue(Issue):
    def describe(self):
        return f"[URGENT] {self.title} — needs immediate attention"


class LowPriorityIssue(Issue):
    def describe(self):
        return f"{self.title} — low priority, handle when free"