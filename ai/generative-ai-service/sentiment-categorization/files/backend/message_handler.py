import csv
from typing import List


def read_messages(
    filepath: str, columns: List[str] = ["ID", "Message"]
) -> List[List[str]]:
    with open(filepath, newline="", encoding="utf-8") as file:
        reader = csv.DictReader(file)
        extracted_data = []

        for row in reader:
            extracted_row = [row[col] for col in columns if col in row]
            extracted_data.append(extracted_row)

    return extracted_data


def batchify(lst, batch_size):
    return [lst[i : i + batch_size] for i in range(0, len(lst), batch_size)]


def match_categories(summaries, categories):
    result = []
    for i, elem in enumerate(summaries[0]):
        if elem["id"] == categories[0][i]["id"]:
            elem["primary_category"] = categories[0][i]["primary_category"]
            elem["secondary_category"] = categories[0][i]["secondary_category"]
            elem["tertiary_category"] = categories[0][i]["tertiary_category"]
            result.append(elem)
    return result


def group_by_category_level(categories_list):
    result = {}

    for category in categories_list:
        primary = category["primary_category"]
        secondary = category["secondary_category"]
        tertiary = category["tertiary_category"]

        if primary not in result:
            result[primary] = {}

        if secondary not in result[primary]:
            result[primary][secondary] = {}

        if tertiary not in result[primary][secondary]:
            result[primary][secondary][tertiary] = []

        result[primary][secondary][tertiary].append(category["id"])

    return result
