import requests
from api_rag import create_query_engine, get_query_response

def call_api(query):
    url = 'http://localhost:8000/'
    response = requests.get(url, params={'query': query})
    if response.status_code == 200:
        return response.json()
    else:
        raise Exception(f"Failed to get response from API, status code: {response.status_code}")


# Example usage
if __name__ == "__main__":
    queries = [
        "What are the document formats supported by the Vision service?",
        "How can I reset my password?",
        "What is the maximum file size for uploads?",
        "Can you provide the API endpoint for retrieving user profiles?",
        "What are the security measures in place for API transactions?",
        "How do I update my billing information?",
        "What types of notifications will users receive?",
        "Is there a way to retrieve historical data?",
        "Can the system integrate with third-party services?",
        "What are the system requirements for installing the client application?"
    ]
    engine = create_query_engine()
    for i in queries:
        try:
            result = get_query_response(i, engine)
            print("API Response:", result)
        except Exception as e:
            print(str(e))
