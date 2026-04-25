def combine_jobs(google_jobs: list, linkedin_jobs: list) -> list:
    combined_jobs = {}
    for job in google_jobs:
        combined_jobs[(job.title, job.company)] = job

    for job in linkedin_jobs:
        combined_jobs.setdefault((job.title, job.company), job)

    return list(combined_jobs.values())
