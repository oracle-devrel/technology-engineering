from core.glossary import get_glossary_for_pair


def build_system_prompt(source_language: str, target_language: str) -> str:
    glossary = get_glossary_for_pair(source_language, target_language)

    glossary_block = ""
    if glossary:
        lines = [f"  {k} -> {v}" for k, v in glossary.items()]
        glossary_block = (
            "\n\nMandatory terminology. If any source term appears in the text, "
            "use exactly the mapped target term:\n"
            + "\n".join(lines)
        )

    return (
        f"You are a professional translator specialising in online lottery, "
        f"gambling, and finance.\n\n"
        f"Translate the following text from {source_language} to {target_language}.\n"
        f"Only output the translated text. Do not include any explanation, "
        f"preamble, or extra information."
        f"{glossary_block}"
    )


def build_user_prompt(text: str) -> str:
    return text
