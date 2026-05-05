def parse_jobs(data: dict) -> list[dict]:
    return data.get("job_table", {}).get("rows", [])


def parse_contacts(data: dict) -> list[dict]:
    return data.get("contact_table", {}).get("rows", [])
