
SUMMARIZATION = """\
Analyze the following batch of user messages. For each message, identify the main topic, provide a concise summary, and assess the sentiment on a scale from 1 (negative) to 10 (positive). Return your analysis as an array of JSON objects, with each object containing the message ID and the following fields: "topic", "summary", and "sentiment_score".

**Provide your analysis in this exact JSON format:**
[
  {
    "id": "msg_001",
    "topic": "The primary subject matter of the first message",
    "summary": "A concise 1-2 sentence summary of the key points",
    "sentiment_score": X
  },
  {
    "id": "msg_002",
    "topic": "The primary subject matter of the second message",
    "summary": "A concise 1-2 sentence summary of the key points",
    "sentiment_score": X
  },
  {
    "id": "msg_003",
    "topic": "The primary subject matter of the third message",
    "summary": "A concise 1-2 sentence summary of the key points",
    "sentiment_score": X
  }
]

**Before finalizing your response:**
1. Ensure you've accurately identified the central topic for each message
2. Verify your summaries capture the essential information in 1-2 sentences
3. Confirm your sentiment scores reflect the emotional tone (1=extremely negative, 10=extremely positive)
4. Check that your output is valid, parseable JSON
5. Make sure each message ID in your response matches the corresponding message ID from the input
\
"""

CATEGORIZATION_SYSTEM = """\
You are an expert content analyzer that categorizes user messages into a hierarchical taxonomy. You process batches of message summaries, each with a unique ID, and classify them into a 3-level nested category structure. Your categorization must follow a consistent taxonomy with increasing specificity at each level.

IMPORTANT CONSTRAINTS:
- Use no more than 5 primary categories
- Use no more than 5-6 secondary categories per primary category
- Use no more than 10 tertiary categories TOTAL across the entire taxonomy
- Maintain consistent naming and logical hierarchical relationships
- Reuse existing categories instead of creating new ones whenever possible

Analyze the following batch of message summaries and categorize each one into this constrained 3-level hierarchical taxonomy:

1. Primary category: Broadest level (e.g., "Human Resources", "Finance", "IT")
2. Secondary category: More specific domain within the primary category (e.g., "Policies", "Benefits", "Recruitment")
3. Tertiary category: Most specific classification (e.g., "Leaves", "Health Insurance", "Interview Process")

Ensure that each level builds upon the previous level with increasing specificity and follows logical parent-child relationships.

Return your analysis as a JSON array with each element containing "id", "primary_category", "secondary_category", and "tertiary_category".

**Example of expected categorization structure:**
- Primary: "Human Resources"
  - Secondary: "Policies"
    - Tertiary: "Leaves"
  - Secondary: "Benefits"
    - Tertiary: "Health Insurance"

\
"""

CATEGORIZATION_USER = """\

Message Batch:
{MESSAGE_BATCH}
\
"""

REPORT_GEN = """\
# **Generate a Categorized JSON Report of Messages**

## **Task**  
You are an expert data analyst. Your task is to generate a structured and insightful JSON report analyzing a batch of messages based on their category levels, summaries, and sentiment scores. Each message is classified into three hierarchical category levels (Category Level 2 and Category Level 3).  

## **Instructions**  
Follow these steps to generate the report:  
1. **Group messages by Category Level 2**, then further organize them into Category Level 3 subcategories.  
2. **Summarize each category level** by aggregating key themes and trends from message summaries.  
3. **Analyze sentiment scores** by calculating the average, highest, and lowest sentiment scores for each category level (1=extremely negative, 10=extremely positive). 
4. **Identify key insights** such as common concerns, prevailing sentiment trends, and outliers.  
5. **Format the output as a structured JSON object** with the following structure:  

## **Output Format (JSON)**  
{
  "categories": [
    {
      "category_level_1": "Category Name",
      "summary": "Concise summary of messages in this category",
      "average_sentiment_score": 7.2,
      "highest_sentiment_message": {
        "summary": "Message summary",
        "sentiment_score": 10
      },
      "lowest_sentiment_message": {
        "summary": "Message summary",
        "sentiment_score": 2
      },
      "key_insights": [
        "Notable pattern 1",
        "Notable pattern 2"
      ],
      "subcategories": [
        {
          "category_level_2": "Subcategory Name",
          "summary": "Common themes from messages",
          "average_sentiment_score": 6.5,
          "sentiment_range": {
            "lowest": 3,
            "highest": 9
          },
          "notable_sentiment_trends": [
            "Trend 1",
            "Trend 2"
          ],
        }
      ]
    }
  ]
}
\
"""



# (LLAMA format) COMPETITOR REPORT PROMPTS
SUMMARIZATION_LLAMA = """<system>
You are an AI assistant that analyzes text and provides structured analysis. Your task is to examine the user's message, identify the main topic, create a concise summary, and evaluate the sentiment on a scale from 1 (negative) to 10 (positive). You must return your analysis in valid JSON format.
</system>

<user>
Analyze the following message and provide your analysis in valid JSON format with these fields: "main_topic", "summary", and "sentiment_score" (where 1 is extremely negative and 10 is extremely positive).

Message: {USER_MESSAGE}
</user>

<assistant>
I'll analyze this message carefully.

{
  "main_topic": "The primary subject matter of the message",
  "summary": "A concise 1-2 sentence summary of the key points",
  "sentiment_score": X
}

Let me verify:
- The main topic accurately represents the central theme
- The summary captures the essential information in 1-2 sentences
- The sentiment score correctly reflects the emotional tone on a 1-10 scale
- The output is valid, parseable JSON
</assistant>
"""

CATEGORIZATION_LLAMA = """<system>
You are an expert content analyzer that categorizes user messages into a hierarchical taxonomy. You process batches of message summaries, each with a unique ID, and classify them into a 3-level nested category structure. Your categorization must follow a consistent taxonomy with increasing specificity at each level.
</system>

<user>
Analyze the following batch of message summaries and categorize each one into a 3-level hierarchical taxonomy:

1. Primary category: Broadest level (e.g., "Human Resources", "Finance", "IT")
2. Secondary category: More specific domain within the primary category (e.g., "Policies", "Benefits", "Recruitment")
3. Tertiary category: Most specific classification (e.g., "Leaves", "Health Insurance", "Interview Process")

Ensure that each level builds upon the previous level with increasing specificity and follows logical parent-child relationships.

Return your analysis as a JSON array with each element containing "id", "primary_category", "secondary_category", and "tertiary_category".

Example of expected categorization structure:
- Primary: "Human Resources"
  - Secondary: "Policies"
    - Tertiary: "Leaves"
  - Secondary: "Benefits"
    - Tertiary: "Health Insurance"

Message Batch:
{MESSAGE_BATCH}
</user>

<assistant>
I've analyzed each message summary and categorized them according to the 3-level hierarchical taxonomy:

```json
[
  {
    "id": "msg_001",
    "primary_category": "Primary level category",
    "secondary_category": "Secondary level category within primary",
    "tertiary_category": "Tertiary level category within secondary"
  },
  {
    "id": "msg_002",
    "primary_category": "Primary level category",
    "secondary_category": "Secondary level category within primary",
    "tertiary_category": "Tertiary level category within secondary"
  },
  {
    "id": "msg_003",
    "primary_category": "Primary level category",
    "secondary_category": "Secondary level category within primary",
    "tertiary_category": "Tertiary level category within secondary"
  }
]

"""

REPORT_GEN_LLAMA = """<|begin_of_text|>
<|start_header_id|>system<|end_header_id|>

You are an expert data analyst. Your task is to generate a structured and insightful JSON report analyzing a batch of messages based on their category levels, summaries, and sentiment scores. Each message is classified into three hierarchical category levels (Category Level 1, Category Level 2, and Category Level 3).

Follow these steps to generate the report:
1. **Group messages by Category Level 1**, then further organize them into Category Level 2 and Category Level 3 subcategories.
2. **Summarize each category level** by aggregating key themes and trends from message summaries.
3. **Analyze sentiment scores** by calculating the average, highest, and lowest sentiment scores for each category level.
4. **Identify key insights** such as common concerns, prevailing sentiment trends, and outliers.
5. **Format the output as a structured JSON object** with the following structure:

```json
{
  "categories": [
    {
      "category_level_1": "Category Name",
      "summary": "Concise summary of messages in this category",
      "average_sentiment_score": 7.2,
      "highest_sentiment_message": {
        "summary": "Message summary",
        "sentiment_score": 10
      },
      "lowest_sentiment_message": {
        "summary": "Message summary",
        "sentiment_score": 2
      },
      "key_insights": [
        "Notable pattern 1",
        "Notable pattern 2"
      ],
      "subcategories": [
        {
          "category_level_2": "Subcategory Name",
          "summary": "Common themes from messages",
          "average_sentiment_score": 6.5,
          "sentiment_range": {
            "lowest": 3,
            "highest": 9
          },
          "notable_sentiment_trends": [
            "Trend 1",
            "Trend 2"
          ],
          "subcategories": [
            {
              "category_level_3": "Sub-subcategory Name",
              "summary": "Detailed message patterns",
              "average_sentiment_score": 5.8,
              "sentiment_range": {
                "lowest": 1,
                "highest": 8
              },
              "notable_sentiment_trends": [
                "Specific insight based on sentiment analysis"
              ]
            }
          ]
        }
      ]
    }
  ]
}
"""
