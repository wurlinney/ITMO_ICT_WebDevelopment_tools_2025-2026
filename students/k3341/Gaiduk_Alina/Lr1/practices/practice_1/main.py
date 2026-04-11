from typing_extensions import TypedDict

from fastapi import FastAPI, HTTPException
from models import *

app = FastAPI()


temp_bd = [
{
    "id": 1,
    "race": "director",
    "name": "Мартынов Дмитрий",
    "level": 12,
    "profession": {
        "id": 1,
        "title": "Влиятельный человек",
        "description": "Эксперт по всем вопросам"
    },
    "skills":
        [{
            "id": 1,
            "name": "Купле-продажа компрессоров",
            "description": ""

        },
        {
            "id": 2,
            "name": "Оценка имущества",
            "description": ""

        }]
},
{
    "id": 2,
    "race": "worker",
    "name": "Андрей Косякин",
    "level": 12,
    "profession": {
        "id": 1,
        "title": "Дельфист-гребец",
        "description": "Уважаемый сотрудник"
    },
    "skills": []
},
]


def _collect_professions() -> List[dict]:
    professions: List[dict] = []
    seen_ids = set()
    for warrior in temp_bd:
        profession = warrior.get("profession")
        if not profession:
            continue
        profession_id = profession.get("id")
        if profession_id in seen_ids:
            continue
        seen_ids.add(profession_id)
        professions.append(profession)
    return professions


def _find_warrior_by_id(warrior_id: int):
    for warrior in temp_bd:
        if warrior.get("id") == warrior_id:
            return warrior
    return None


@app.get("/warriors_list")
def warriors_list() -> List[Warrior]:
    return temp_bd


@app.get("/warrior/{warrior_id}")
def warriors_get(warrior_id: int) -> List[Warrior]:
    return [warrior for warrior in temp_bd if warrior.get("id") == warrior_id]


@app.post("/warrior")
def warriors_create(warrior: Warrior) -> TypedDict('Response', {"status": int, "data": Warrior}):
    warrior_to_append = warrior.model_dump()
    temp_bd.append(warrior_to_append)
    return {"status": 200, "data": warrior}


@app.delete("/warrior/delete{warrior_id}")
def warrior_delete(warrior_id: int):
    for i, warrior in enumerate(temp_bd):
        if warrior.get("id") == warrior_id:
            temp_bd.pop(i)
            break
    return {"status": 201, "message": "deleted"}


@app.put("/warrior{warrior_id}")
def warrior_update(warrior_id: int, warrior: Warrior) -> List[Warrior]:
    for war in temp_bd:
        if war.get("id") == warrior_id:
            warrior_to_append = warrior.model_dump()
            temp_bd.remove(war)
            temp_bd.append(warrior_to_append)
    return temp_bd


@app.get("/professions_list")
def professions_list() -> List[Profession]:
    return _collect_professions()


@app.get("/profession/{profession_id}")
def profession_get(profession_id: int) -> Profession:
    for profession in _collect_professions():
        if profession.get("id") == profession_id:
            return profession
    raise HTTPException(status_code=404, detail="Profession not found")


@app.post("/profession/{warrior_id}")
def profession_create(warrior_id: int, profession: Profession):
    if any(item.get("id") == profession.id for item in _collect_professions()):
        raise HTTPException(status_code=400, detail="Profession with this id already exists")

    warrior = _find_warrior_by_id(warrior_id)
    if warrior is None:
        raise HTTPException(status_code=404, detail="Warrior not found")

    warrior["profession"] = profession.model_dump()
    return {"status": 201, "data": warrior["profession"]}


@app.put("/profession/{profession_id}")
def profession_update(profession_id: int, profession: Profession):
    updated_count = 0
    new_profession = profession.model_dump()
    new_profession["id"] = profession_id

    for warrior in temp_bd:
        warrior_profession = warrior.get("profession")
        if warrior_profession and warrior_profession.get("id") == profession_id:
            warrior["profession"] = new_profession
            updated_count += 1

    if updated_count == 0:
        raise HTTPException(status_code=404, detail="Profession not found")

    return {"status": 200, "updated": updated_count, "data": new_profession}


@app.delete("/profession/{profession_id}")
def profession_delete(profession_id: int):
    deleted_count = 0
    no_profession = {
        "id": 0,
        "title": "no_profession",
        "description": "",
    }

    for warrior in temp_bd:
        warrior_profession = warrior.get("profession")
        if warrior_profession and warrior_profession.get("id") == profession_id:
            warrior["profession"] = no_profession
            deleted_count += 1

    if deleted_count == 0:
        raise HTTPException(status_code=404, detail="Profession not found")

    return {"status": 200, "deleted": deleted_count}
