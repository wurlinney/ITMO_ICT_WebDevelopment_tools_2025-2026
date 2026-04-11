from enum import Enum
from typing import List, Optional

from sqlmodel import Field, Relationship, SQLModel


class RaceType(str, Enum):
    director = "director"
    worker = "worker"
    junior = "junior"


class SkillWarriorLink(SQLModel, table=True):
    skill_id: Optional[int] = Field(
    default=None, foreign_key="skill.id", primary_key=True
    )
    warrior_id: Optional[int] = Field(
    default=None, foreign_key="warrior.id", primary_key=True
    )
    level: int | None


class SkillDefault(SQLModel):
    name: str
    description: Optional[str] = ""


class SkillView(SkillDefault):
    id: Optional[int] = None


class Skill(SkillDefault, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    warriors: Optional[List["Warrior"]] = Relationship(
        back_populates="skills", link_model=SkillWarriorLink
    )


class ProfessionDefault(SQLModel):
    title: str
    description: str


class Profession(ProfessionDefault, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    warriors_prof: List["Warrior"] = Relationship(back_populates="profession")


class WarriorDefault(SQLModel):
    race: RaceType
    name: str
    level: int
    profession_id: Optional[int] = Field(default=None, foreign_key="profession.id")


class Warrior(WarriorDefault, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    profession: Optional[Profession] = Relationship(back_populates="warriors_prof")
    skills: Optional[List[Skill]] = Relationship(
        back_populates="warriors", link_model=SkillWarriorLink
    )


class WarriorProfessions(WarriorDefault):
    id: Optional[int] = None
    profession: Optional[Profession] = None
    skills: List[SkillView] = Field(default_factory=list)
