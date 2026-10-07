import asyncio

import aiohttp

from models import DbSession, SwapiPeople, close_db, create_db

BASE_URL = "https://swapi-node.vercel.app"
PEOPLE_LIST_URL = f"{BASE_URL}/api/people"


def person_id_from_url(url: str) -> str:
    return url.rstrip("/").split("/")[-1]


def str_field(fields: dict, key: str) -> str:
    value = fields.get(key)
    if value is None:
        return ""
    return str(value)


async def fetch_fields(
    session: aiohttp.ClientSession,
    cache: dict[str, dict],
    path: str,
) -> dict:
    if path in cache:
        return cache[path]
    async with session.get(f"{BASE_URL}{path}") as response:
        response.raise_for_status()
        data = await response.json()
    fields = data.get("fields", data)
    cache[path] = fields
    return fields


async def resolve_homeworld(
    session: aiohttp.ClientSession,
    cache: dict[str, dict],
    path: str | None,
) -> str:
    if not path:
        return ""
    fields = await fetch_fields(session, cache, path)
    return str(fields.get("name", ""))


async def resolve_paths(
    session: aiohttp.ClientSession,
    cache: dict[str, dict],
    paths: list[str] | None,
    field_name: str,
) -> str:
    if not paths:
        return ""
    coros = [fetch_fields(session, cache, path) for path in paths]
    results = await asyncio.gather(*coros)
    values = [str(item.get(field_name, "")) for item in results]
    return ", ".join(values)


async def enrich_person(
    session: aiohttp.ClientSession,
    cache: dict[str, dict],
    fields: dict,
) -> SwapiPeople:
    homeworld, films, starships, vehicles = await asyncio.gather(
        resolve_homeworld(session, cache, fields.get("homeworld")),
        resolve_paths(session, cache, fields.get("films"), "title"),
        resolve_paths(session, cache, fields.get("starships"), "starship_class"),
        resolve_paths(session, cache, fields.get("vehicles"), "name"),
    )
    return SwapiPeople(
        id=person_id_from_url(fields["url"]),
        birth_year=str_field(fields, "birth_year"),
        eye_color=str_field(fields, "eye_color"),
        films=films,
        gender=str_field(fields, "gender"),
        hair_color=str_field(fields, "hair_color"),
        height=str_field(fields, "height"),
        homeworld=homeworld,
        mass=str_field(fields, "mass"),
        name=str_field(fields, "name"),
        skin_color=str_field(fields, "skin_color"),
        starships=starships,
        vehicles=vehicles,
    )


async def fetch_all_people(session: aiohttp.ClientSession) -> list[dict]:
    people: list[dict] = []
    page = 1
    while True:
        async with session.get(
            PEOPLE_LIST_URL,
            params={"page": page, "limit": 10},
        ) as response:
            response.raise_for_status()
            data = await response.json()
        for item in data["results"]:
            people.append(item["fields"])
        if page >= data["pages"]:
            break
        page += 1
    return people


async def save_people(people: list[SwapiPeople]) -> None:
    async with DbSession() as db_session:
        db_session.add_all(people)
        await db_session.commit()


async def main():
    await create_db()
    cache: dict[str, dict] = {}

    async with aiohttp.ClientSession() as session:
        raw_people = await fetch_all_people(session)
        enrich_coros = [
            enrich_person(session, cache, fields) for fields in raw_people
        ]
        people_orm = await asyncio.gather(*enrich_coros)
        await save_people(list(people_orm))

    await close_db()
    print(f"Loaded {len(people_orm)} people into the database.")


if __name__ == "__main__":
    asyncio.run(main())
