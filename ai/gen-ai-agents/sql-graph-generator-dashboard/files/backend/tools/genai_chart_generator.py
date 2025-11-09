"""
GenAI-Powered Chart Generator
Uses OCI GenAI to generate custom visualization code based on data and user requirements
"""

import json
import oci
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
import numpy as np
import io
import base64
from typing import Dict, Any, List, Optional
from utils import config
import signal


class GenAIChartGenerator:
    """
    Generate custom charts using OCI GenAI to create Python visualization code
    """

    CHART_GENERATION_PROMPT = """You are an expert data visualization developer. Generate Python code to create beautiful, insightful charts.

User Request: "{user_request}"

Available Data (first 3 rows shown):
{data_preview}

Data Summary:
- Total rows: {total_rows}
- Columns: {columns}
- Numeric columns: {numeric_columns}

Requirements:
1. Create a matplotlib/seaborn visualization
2. Use the provided data variable called 'df' (pandas DataFrame)
3. Make the chart beautiful with proper titles, labels, colors
4. Return the chart as base64 image
5. Handle any data preprocessing needed
6. Choose the most appropriate chart type for the data and request

Generate ONLY Python code in this format:
```python
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
import numpy as np
import io
import base64

# Set style for beautiful charts
plt.style.use('seaborn-v0_8')
sns.set_palette("husl")

# Your visualization code here
# Use df as the DataFrame variable
# Example:
fig, ax = plt.subplots(figsize=(12, 8))

# Create your chart (customize based on user request and data)
# ... your chart code ...

# Finalize chart
plt.title("Your Chart Title", fontsize=16, fontweight='bold')
plt.tight_layout()

# Convert to base64
img_buffer = io.BytesIO()
plt.savefig(img_buffer, format='png', dpi=150, bbox_inches='tight',
           facecolor='white', edgecolor='none')
img_buffer.seek(0)
img_base64 = base64.b64encode(img_buffer.getvalue()).decode('utf-8')
plt.close()

# Return the base64 string
chart_base64 = img_base64
```

Generate the complete Python code that will create an appropriate visualization."""

    def __init__(self):
        # Initialize direct OCI GenAI client using chat API
        try:
            oci_config = oci.config.from_file()
            oci_config['region'] = 'eu-frankfurt-1'
            self.genai_client = oci.generative_ai_inference.GenerativeAiInferenceClient(oci_config)
            self.genai_client.base_client.endpoint = config.SERVICE_ENDPOINT

            self.model_id = config.MODEL_ID
            self.compartment_id = config.COMPARTMENT_ID
            self.oci_available = True
            print("LangChain OCI GenAI Chart Generator initialized successfully")
        except Exception as e:
            print(f"LangChain OCI GenAI Chart Generator not available: {e}")
            self.genai_client = None
            self.oci_available = False

    def generate_chart(self, user_request: str, data: List[Dict], chart_params: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Generate custom chart using GenAI-generated code
        """
        try:
            print(f"GenAI Chart Generator: Creating chart for: {user_request}")

            if not data:
                return {
                    "success": False,
                    "error": "No data provided for chart generation"
                }

            # Prepare data summary for GenAI
            df = pd.DataFrame(data)
            data_preview = df.head(3).to_dict('records')
            columns = list(df.columns)
            numeric_columns = list(df.select_dtypes(include=[np.number]).columns)

            # Create GenAI prompt
            prompt = self.CHART_GENERATION_PROMPT.format(
                user_request=user_request,
                data_preview=json.dumps(data_preview, indent=2, default=str),
                total_rows=len(df),
                columns=columns,
                numeric_columns=numeric_columns
            )

            # Call GenAI to generate code
            genai_response = self._call_genai(prompt)
            print(f"GenAI Response length: {len(genai_response)} chars")
            print(f"GenAI Response preview: {genai_response[:200]}...")

            # Extract Python code from response
            python_code = self._extract_code(genai_response)
            print(f" Extracted code length: {len(python_code) if python_code else 0} chars")

            if not python_code:
                print(" No Python code extracted, using fallback")
                return self._fallback_chart(df, user_request)

            print(f" Code preview: {python_code[:100]}...")

            # Execute the generated code
            print(" Executing generated Python code...")
            chart_result = self._execute_chart_code(python_code, df)
            print(f" Chart execution result: {chart_result.get('success', False)}")

            if chart_result["success"]:
                return {
                    "success": True,
                    "chart_base64": chart_result["chart_base64"],
                    "generated_code": python_code,
                    "method": "genai_generated",
                    "chart_config": {
                        "title": f"GenAI Chart: {user_request}",
                        "type": "custom",
                        "description": "Custom chart generated using GenAI"
                    }
                }
            else:
                print(f" Generated code failed, using fallback: {chart_result['error']}")
                return self._fallback_chart(df, user_request)

        except Exception as e:
            print(f" GenAI Chart Generation error: {e}")
            return self._fallback_chart(pd.DataFrame(data) if data else pd.DataFrame(), user_request)

    def _call_genai(self, prompt: str) -> str:
        """
        Call OCI GenAI model to generate chart code using direct Chat API
        """
        try:
            print(" Creating chat request...")
            # Create chat request using Oracle demo format for OpenAI GPT OSS 120B
            content = oci.generative_ai_inference.models.TextContent()
            content.text = prompt

            message = oci.generative_ai_inference.models.Message()
            message.role = "USER"
            message.content = [content]

            chat_request = oci.generative_ai_inference.models.GenericChatRequest()
            chat_request.api_format = oci.generative_ai_inference.models.BaseChatRequest.API_FORMAT_GENERIC
            chat_request.messages = [message]
            chat_request.max_tokens = 2000
            chat_request.temperature = 0.3
            chat_request.frequency_penalty = 0
            chat_request.presence_penalty = 0
            chat_request.top_p = 1
            chat_request.top_k = 0

            chat_detail = oci.generative_ai_inference.models.ChatDetails()
            chat_detail.serving_mode = oci.generative_ai_inference.models.OnDemandServingMode(model_id=self.model_id)
            chat_detail.chat_request = chat_request
            chat_detail.compartment_id = self.compartment_id

            # Call OCI GenAI
            print(" Calling OCI GenAI Chat API...")
            response = self.genai_client.chat(chat_detail)
            print(" Got response from OCI GenAI")

            # Extract response text
            response_text = ""
            if hasattr(response.data, 'chat_response') and response.data.chat_response:
                if hasattr(response.data.chat_response, 'choices') and response.data.chat_response.choices:
                    choice = response.data.chat_response.choices[0]
                    if hasattr(choice, 'message') and choice.message:
                        if hasattr(choice.message, 'content') and choice.message.content:
                            for content in choice.message.content:
                                if hasattr(content, 'text'):
                                    response_text += content.text

            return response_text.strip()

        except Exception as e:
            print(f" LangChain GenAI API call failed: {e}")
            return f"Error: {str(e)}"

    def _extract_code(self, genai_response: str) -> Optional[str]:
        """
        Extract Python code from GenAI response
        """
        try:
            # Look for code blocks
            if "```python" in genai_response:
                start = genai_response.find("```python") + 9
                end = genai_response.find("```", start)
                if end != -1:
                    return genai_response[start:end].strip()
            elif "```" in genai_response:
                start = genai_response.find("```") + 3
                end = genai_response.find("```", start)
                if end != -1:
                    return genai_response[start:end].strip()

            # If no code blocks, try to find code patterns
            lines = genai_response.split('\n')
            code_lines = []
            in_code = False

            for line in lines:
                if any(keyword in line for keyword in ['import ', 'plt.', 'sns.', 'fig,', 'ax =']):
                    in_code = True
                if in_code:
                    code_lines.append(line)

            return '\n'.join(code_lines) if code_lines else None

        except Exception as e:
            print(f" Code extraction error: {e}")
            return None

    def _execute_chart_code(self, python_code: str, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Safely execute the generated Python code
        """
        try:
            # Create a safe execution environment
            safe_globals = {
                'plt': plt,
                'sns': sns,
                'pd': pd,
                'np': np,
                'io': io,
                'base64': base64,
                'df': df,
                'chart_base64': None
            }

            # Execute the code
            exec(python_code, safe_globals)

            # Get the result
            chart_base64 = safe_globals.get('chart_base64')

            if chart_base64:
                return {
                    "success": True,
                    "chart_base64": chart_base64
                }
            else:
                return {
                    "success": False,
                    "error": "No chart_base64 variable found in generated code"
                }

        except Exception as e:
            return {
                "success": False,
                "error": f"Code execution error: {str(e)}"
            }

    def _fallback_chart(self, df: pd.DataFrame, user_request: str) -> Dict[str, Any]:
        """
        Generate a simple fallback chart when GenAI fails
        """
        try:
            fig, ax = plt.subplots(figsize=(10, 6))

            # Choose chart based on data
            if len(df.columns) >= 2:
                numeric_cols = df.select_dtypes(include=[np.number]).columns
                if len(numeric_cols) >= 2:
                    # Scatter plot for numeric data
                    ax.scatter(df[numeric_cols[0]], df[numeric_cols[1]], alpha=0.7)
                    ax.set_xlabel(numeric_cols[0])
                    ax.set_ylabel(numeric_cols[1])
                elif len(numeric_cols) == 1:
                    # Bar chart
                    if len(df) <= 20:
                        df[numeric_cols[0]].plot(kind='bar', ax=ax)
                    else:
                        df[numeric_cols[0]].plot(kind='line', ax=ax)
                    ax.set_ylabel(numeric_cols[0])

            plt.title(f"Chart for: {user_request}", fontsize=14)
            plt.tight_layout()

            # Convert to base64
            img_buffer = io.BytesIO()
            plt.savefig(img_buffer, format='png', dpi=150, bbox_inches='tight')
            img_buffer.seek(0)
            chart_base64 = base64.b64encode(img_buffer.getvalue()).decode('utf-8')
            plt.close()

            return {
                "success": True,
                "chart_base64": chart_base64,
                "method": "fallback",
                "chart_config": {
                    "title": f"Fallback Chart: {user_request}",
                    "type": "auto",
                    "description": "Simple fallback visualization"
                }
            }

        except Exception as e:
            return {
                "success": False,
                "error": f"Fallback chart error: {str(e)}"
            }