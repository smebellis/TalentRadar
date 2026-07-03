from db.models.contact import Contact


class ContactScorer:
    PRIORITIES = {"hiring_manager": 1, "recruiter": 2, "veteran": 3, "peer": 4}

    def __init__(self, threshold: float, veteran_boost: float) -> None:
        self.threshold = threshold
        self.veteran_boost = veteran_boost

    def filter_and_sort(
        self,
        contact: list[Contact],
        searcher_is_veteran: bool,
    ) -> list[Contact]:
        lowest_priority = max(self.PRIORITIES.values())
        for item in contact:
            priority = self.PRIORITIES.get(item.category, lowest_priority)
            item.relevance_score = 5 - priority
            if searcher_is_veteran and item.is_veteran:
                item.relevance_score += self.veteran_boost

        filtered_contacts = [
            item for item in contact if item.relevance_score >= self.threshold
        ]

        sorted_contact = sorted(
            filtered_contacts,
            key=lambda item: self.PRIORITIES.get(item.category, lowest_priority),
        )

        return sorted_contact
