# verifier.py
# ---------------------------------------------------------
# Verifies that agent output includes expected keywords
# ---------------------------------------------------------

def verify_keywords_in_response(response: str, keywords: list[str]) -> list[str]:
    """
    Verifies that all expected keywords appear in the response.
    Returns a list of any that are missing.
    """
    if not response:
        return keywords

    missing = []
    response_lower = response.lower()
    
    # loop for keywords
    for keyword in keywords:
        if keyword.lower() not in response_lower:
            missing.append(keyword)

    return missing