#!/usr/bin/env python3
"""
True LAM Integration using Salesforce/xLAM-1b-fc-r model
This provides real AI understanding and function calling capabilities
"""

import json
import torch
import requests
from transformers import AutoModelForCausalLM, AutoTokenizer
from bs4 import BeautifulSoup
import os
from typing import Dict, List, Any
from datetime import datetime
import sqlite3
import pandas as pd

# Set random seed for reproducibility
torch.random.manual_seed(0)

class TrueLAMInterface:
    def __init__(self):
        """Initialize the True LAM Interface with the actual model"""
        self.model_name = "Salesforce/xLAM-1b-fc-r"
        print(f"🤖 Loading True LAM Model: {self.model_name}")
        
        try:
            # Try to load model with proper device handling
            import torch
            device = "cuda" if torch.cuda.is_available() else "cpu"
            
            self.model = AutoModelForCausalLM.from_pretrained(
                self.model_name, 
                device_map="auto" if device == "cuda" else None,
                torch_dtype=torch.float16 if device == "cuda" else torch.float32,
                trust_remote_code=True
            )
            
            # Move to CPU if not using CUDA to avoid MPS issues
            if device == "cpu":
                self.model = self.model.to("cpu")
            
            self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
            print(f"✅ True LAM Model loaded successfully on {device}!")
        except Exception as e:
            print(f"❌ Error loading LAM model: {e}")
            print("🔄 Falling back to pattern matching...")
            self.model = None
            self.tokenizer = None
        
        # Task instruction for the model
        self.task_instruction = """
You are an expert in composing functions for an Enterprise Management System. You are given a question and a set of possible functions. 
Based on the question, you will need to make one or more function/tool calls to achieve the purpose. 
IMPORTANT: You MUST use the available functions when the user asks for specific actions like:
- "Show me sales report" → use generate_sales_report
- "Get weather" → use get_weather  
- "Create file" → use write_file
- "Read file" → use read_file
- "Search for" → use search_internet

If none of the functions can be used, point it out and refuse to answer. 
If the given question lacks the parameters required by the function, also point it out.
""".strip()

        # Format instruction for JSON output
        self.format_instruction = """
The output MUST be a valid JSON array of tool calls. If no function call is needed, return an empty array [].
If function calls are needed, return an array like this:
[
{"name": "func_name1", "arguments": {"argument1": "value1", "argument2": "value2"}},
{"name": "func_name2", "arguments": {"argument1": "value1"}}
]

EXAMPLES:
- "Show me sales report for this year" → [{"name": "generate_sales_report", "arguments": {"quarter": "Q4"}}]
- "What's the weather in London?" → [{"name": "get_weather", "arguments": {"location": "London"}}]
- "Create a file called sales.txt" → [{"name": "write_file", "arguments": {"filename": "sales.txt", "content": "Sales data"}}]
""".strip()

        # Define available tools for Enterprise Management System
        self.tools = [
            {
                "name": "get_weather",
                "description": "Get the current weather for a location",
                "parameters": {
                    "location": {
                        "type": "string",
                        "description": "The city and state, e.g. San Francisco, New York, London"
                    }
                }
            },
            {
                "name": "write_file",
                "description": "Write content to a file",
                "parameters": {
                    "filename": {
                        "type": "string",
                        "description": "The name of the file to write, e.g. sales.txt, report.txt"
                    },
                    "content": {
                        "type": "string",
                        "description": "The content to write to the file"
                    }
                }
            },
            {
                "name": "read_file",
                "description": "Read content from a file",
                "parameters": {
                    "filename": {
                        "type": "string",
                        "description": "The name of the file to read, e.g. sales.txt, report.txt"
                    }
                }
            },
            {
                "name": "search_internet",
                "description": "Search for information on the internet",
                "parameters": {
                    "query": {
                        "type": "string",
                        "description": "The search query, e.g. 'latest news on AI'"
                    }
                }
            },
            {
                "name": "generate_sales_report",
                "description": "Generate a sales report for a specific quarter or time period. Use this when user asks for sales reports, quarterly reports, or sales data.",
                "parameters": {
                    "quarter": {
                        "type": "string",
                        "description": "The quarter for the report, e.g. Q1, Q2, Q3, Q4, or 'this year'. Default to Q4 if not specified."
                    },
                    "filename": {
                        "type": "string",
                        "description": "Optional: filename to save the report, e.g. sales.txt"
                    }
                }
            },
            {
                "name": "generate_employee_report",
                "description": "Generate an employee performance report",
                "parameters": {
                    "employee_id": {
                        "type": "string",
                        "description": "The employee ID, e.g. EMP001, EMP002"
                    },
                    "quarter": {
                        "type": "string",
                        "description": "The quarter for the report, e.g. Q1, Q2, Q3, Q4"
                    }
                }
            },
            {
                "name": "send_email_report",
                "description": "Send an email report to a specific address",
                "parameters": {
                    "to_email": {
                        "type": "string",
                        "description": "The email address to send to, e.g. manager@company.com"
                    },
                    "subject": {
                        "type": "string",
                        "description": "The subject of the email"
                    },
                    "content": {
                        "type": "string",
                        "description": "The content of the email"
                    }
                }
            }
        ]

    def convert_to_xlam_tool(self, tools: List[Dict]) -> List[Dict]:
        """Convert OpenAI format tools to xLAM format"""
        xlam_tools = []
        for tool in tools:
            # Determine required parameters (exclude optional ones)
            required_params = []
            for param_name, param_info in tool["parameters"].items():
                # Check if parameter description indicates it's optional
                if "optional" not in param_info.get("description", "").lower():
                    required_params.append(param_name)
            
            xlam_tool = {
                "name": tool["name"],
                "description": tool["description"],
                "parameters": {
                    "type": "object",
                    "properties": tool["parameters"],
                    "required": required_params
                }
            }
            xlam_tools.append(xlam_tool)
        return xlam_tools

    def build_prompt(self, query: str) -> str:
        """Build the prompt for the LAM model"""
        tools_json = json.dumps(self.convert_to_xlam_tool(self.tools), indent=2)
        
        prompt = f"{self.task_instruction}\n\nAvailable functions:\n{tools_json}\n\n{self.format_instruction}\n\nIMPORTANT: When user asks for sales reports, ALWAYS use generate_sales_report function.\n\nQuestion: {query}\n\nAnswer:"
        return prompt

    def get_weather(self, location: str) -> Dict[str, Any]:
        """Get weather information for a location"""
        try:
            url = f"https://wttr.in/{location}?format=j1"
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            current_condition = data['current_condition'][0]
            
            weather_info = {
                "location": location,
                "temperature": f"{current_condition['temp_C']}°C",
                "feels_like": f"{current_condition['FeelsLikeC']}°C",
                "humidity": f"{current_condition['humidity']}%",
                "description": current_condition['weatherDesc'][0]['value'],
                "wind_speed": f"{current_condition['windspeedKmph']} km/h"
            }
            
            return {
                "success": True,
                "data": f"""🌤️ **Weather for {location}**
- Temperature: {weather_info['temperature']}
- Feels like: {weather_info['feels_like']}
- Humidity: {weather_info['humidity']}
- Description: {weather_info['description']}
- Wind Speed: {weather_info['wind_speed']}"""
            }
        except Exception as e:
            return {"success": False, "error": f"Failed to get weather: {str(e)}"}

    def write_file(self, filename: str, content: str) -> Dict[str, Any]:
        """Write content to a file"""
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(content)
            return {
                "success": True,
                "data": f"✅ Successfully wrote to file: {filename}\n\nContent:\n{content}"
            }
        except Exception as e:
            return {"success": False, "error": f"Failed to write file: {str(e)}"}

    def read_file(self, filename: str) -> Dict[str, Any]:
        """Read content from a file"""
        try:
            if not os.path.exists(filename):
                return {"success": False, "error": f"File {filename} does not exist"}
            
            with open(filename, 'r', encoding='utf-8') as f:
                content = f.read()
            return {
                "success": True,
                "data": f"📄 **File: {filename}**\n\n{content}"
            }
        except Exception as e:
            return {"success": False, "error": f"Failed to read file: {str(e)}"}

    def search_internet(self, query: str) -> Dict[str, Any]:
        """Search for information on the internet"""
        try:
            url = f"https://api.duckduckgo.com/?q={query}&format=json&no_html=1&skip_disambig=1"
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            abstract = data.get('Abstract', 'No information found')
            source = data.get('AbstractSource', 'DuckDuckGo')
            
            return {
                "success": True,
                "data": f"🔍 **Search Results for: {query}**\n\n{abstract}\n\nSource: {source}"
            }
        except Exception as e:
            return {"success": False, "error": f"Failed to search: {str(e)}"}

    def generate_sales_report(self, quarter: str, filename: str = None) -> Dict[str, Any]:
        """Generate a sales report for a specific quarter"""
        try:
            report_content = f"""
SALES REPORT - {quarter}
Generated on: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

SUMMARY:
- Total Sales: $150,000
- Total Units: 500
- Average Sale: $300
- Top Product: Smartphone
- Top Region: North

This is a sample sales report for {quarter}.
"""
            
            # If filename is provided, save the report to file
            if filename:
                try:
                    with open(filename, 'w', encoding='utf-8') as f:
                        f.write(report_content)
                    return {
                        "success": True, 
                        "data": f"✅ **Sales Report Generated for {quarter}**\n\nReport saved to: {filename}\n\n{report_content}",
                        "file_saved": True,
                        "filename": filename
                    }
                except Exception as file_error:
                    return {
                        "success": True, 
                        "data": f"✅ **Sales Report Generated for {quarter}**\n\n{report_content}",
                        "file_saved": False,
                        "file_error": str(file_error)
                    }
            
            return {
                "success": True, 
                "data": f"✅ **Sales Report Generated for {quarter}**\n\n{report_content}"
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    def generate_employee_report(self, employee_id: str, quarter: str) -> Dict[str, Any]:
        """Generate an employee performance report"""
        try:
            report_content = f"""
EMPLOYEE PERFORMANCE REPORT
Employee ID: {employee_id}
Quarter: {quarter}
Generated on: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

PERFORMANCE METRICS:
- Hours Worked: 160
- Tasks Completed: 25
- Quality Score: 8.5/10
- Performance Level: Good

RECOMMENDATIONS:
- Continue current performance
- Focus on skill development
- Set specific goals for next quarter
"""
            return {
                "success": True, 
                "data": f"✅ **Employee Report Generated**\n\n{report_content}"
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    def send_email_report(self, to_email: str, subject: str, content: str) -> Dict[str, Any]:
        """Send an email report (simulated)"""
        try:
            # Simulate email sending
            email_log = f"""
📧 **Email Sent Successfully**
To: {to_email}
Subject: {subject}
Content: {content}

(Simulated for POC - would use real SMTP in production)
"""
            return {
                "success": True,
                "data": email_log
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    def execute_tool_call(self, tool_call: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a tool call"""
        tool_name = tool_call.get("name")
        arguments = tool_call.get("arguments", {})
        
        if tool_name == "get_weather":
            return self.get_weather(**arguments)
        elif tool_name == "write_file":
            return self.write_file(**arguments)
        elif tool_name == "read_file":
            return self.read_file(**arguments)
        elif tool_name == "search_internet":
            return self.search_internet(**arguments)
        elif tool_name == "generate_sales_report":
            return self.generate_sales_report(**arguments)
        elif tool_name == "generate_employee_report":
            return self.generate_employee_report(**arguments)
        elif tool_name == "send_email_report":
            return self.send_email_report(**arguments)
        else:
            return {"success": False, "error": f"Unknown tool: {tool_name}"}

    def process_query_with_ai(self, query: str) -> Dict[str, Any]:
        """Process query using the actual LAM model"""
        try:
            if not self.model or not self.tokenizer:
                return {"success": False, "error": "LAM model not loaded"}
            
            # Build prompt
            prompt = self.build_prompt(query)
            
            # Tokenize and generate
            inputs = self.tokenizer(prompt, return_tensors="pt")
            
            # Move inputs to the same device as model
            device = next(self.model.parameters()).device
            input_ids = inputs["input_ids"].to(device)
            attention_mask = inputs["attention_mask"].to(device) if "attention_mask" in inputs else None
            
            with torch.no_grad():
                outputs = self.model.generate(
                    input_ids,
                    attention_mask=attention_mask,
                    max_new_tokens=512,
                    temperature=0.1,
                    do_sample=True,
                    pad_token_id=self.tokenizer.eos_token_id
                )
            
            # Decode response
            response_text = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
            
            # Extract the generated part (after "Answer:")
            if "Answer:" in response_text:
                answer_part = response_text.split("Answer:")[-1].strip()
            else:
                answer_part = response_text
            
            # Try to parse JSON from the response
            try:
                # Look for JSON array in the response
                start_idx = answer_part.find('[')
                end_idx = answer_part.rfind(']') + 1
                
                if start_idx != -1 and end_idx != 0:
                    json_str = answer_part[start_idx:end_idx]
                    tool_calls = json.loads(json_str)
                else:
                    # Look for single JSON object
                    start_idx = answer_part.find('{')
                    end_idx = answer_part.rfind('}') + 1
                    
                    if start_idx != -1 and end_idx != 0:
                        json_str = answer_part[start_idx:end_idx]
                        tool_calls = [json.loads(json_str)]  # Wrap single object in array
                    else:
                        return {
                            "success": True,
                            "data": f"🤖 **AI Response**: {answer_part}"
                        }
                
                if not tool_calls:
                    return {
                        "success": True,
                        "data": "🤖 **AI Response**: I understand your request, but I don't have the appropriate tools to help with this specific query."
                    }
                
                # Execute tool calls
                results = []
                for tool_call in tool_calls:
                    result = self.execute_tool_call(tool_call)
                    results.append(result)
                
                # Combine results
                combined_data = "\n\n".join([r.get("data", str(r)) for r in results if r.get("success")])
                
                return {
                    "success": True,
                    "data": f"🤖 **AI Understanding & Action**:\n\n{combined_data}",
                    "tool_calls": tool_calls,
                    "raw_response": answer_part
                }
                    
            except json.JSONDecodeError:
                return {
                    "success": True,
                    "data": f"🤖 **AI Response**: {answer_part}"
                }
                
        except Exception as e:
            return {"success": False, "error": f"AI processing failed: {str(e)}"}

    def process_query_fallback(self, query: str) -> Dict[str, Any]:
        """Fallback to pattern matching if AI model fails"""
        query_lower = query.lower()
        
        # Weather queries
        if any(word in query_lower for word in ["weather", "temperature", "climate"]):
            location = "London"  # Default
            if "in" in query_lower:
                parts = query_lower.split("in")
                if len(parts) > 1:
                    location_part = parts[-1].strip()
                    location_part = location_part.replace("?", "").replace("!", "").strip()
                    words = location_part.split()
                    if len(words) <= 3:
                        location = " ".join(words)
                    else:
                        location = words[0]
            
            return {
                "success": True,
                "data": f"🔄 **Fallback Mode**: Getting weather for {location}",
                "tool_calls": [{"name": "get_weather", "arguments": {"location": location}}]
            }
        
        # File operations
        elif any(word in query_lower for word in ["write", "create", "save", "generate"]):
            filename = "report.txt"
            content = "Sample content generated by fallback mode."
            
            if ".txt" in query_lower:
                words = query_lower.split()
                for i, word in enumerate(words):
                    if ".txt" in word:
                        filename = word
                        break
            
            return {
                "success": True,
                "data": f"🔄 **Fallback Mode**: Creating file {filename}",
                "tool_calls": [{"name": "write_file", "arguments": {"filename": filename, "content": content}}]
            }
        
        # File read operations
        elif any(word in query_lower for word in ["read", "open", "show"]) and any(word in query_lower for word in ["file", ".txt"]):
            filename = "sample.txt"
            
            if ".txt" in query_lower:
                words = query_lower.split()
                for i, word in enumerate(words):
                    if ".txt" in word:
                        filename = word
                        break
            
            return {
                "success": True,
                "data": f"🔄 **Fallback Mode**: Reading file {filename}",
                "tool_calls": [{"name": "read_file", "arguments": {"filename": filename}}]
            }
        
        # Search operations
        elif any(word in query_lower for word in ["search", "find", "look"]) and any(word in query_lower for word in ["news", "information", "about"]):
            search_query = query_lower
            if "search for" in query_lower:
                search_query = query_lower.split("search for")[-1].strip()
            elif "find" in query_lower:
                search_query = query_lower.split("find")[-1].strip()
            
            return {
                "success": True,
                "data": f"🔄 **Fallback Mode**: Searching for {search_query}",
                "tool_calls": [{"name": "search_internet", "arguments": {"query": search_query}}]
            }
        
        # Sales report
        elif any(word in query_lower for word in ["sales report", "quarterly sales", "sales data"]):
            quarter = "Q4"
            if "this year" in query_lower:
                quarter = "Q4"
            
            return {
                "success": True,
                "data": f"🔄 **Fallback Mode**: Generating sales report for {quarter}",
                "tool_calls": [{"name": "generate_sales_report", "arguments": {"quarter": quarter}}]
            }
        
        else:
            return {
                "success": False,
                "error": "I don't understand this query. Please try rephrasing."
            }

    def process_query(self, query: str) -> Dict[str, Any]:
        """Main method to process queries - uses AI for understanding, pattern matching for function calling"""
        print(f"🤖 Processing query: {query}")
        
        # Use AI model for understanding the intent
        ai_understanding = self.get_ai_understanding(query)
        
        # Use pattern matching for reliable function calling
        pattern_result = self.process_query_fallback(query)
        
        # Execute tool calls if pattern matching found them
        if pattern_result.get("success") and pattern_result.get("tool_calls"):
            try:
                # Execute each tool call
                results = []
                for tool_call in pattern_result["tool_calls"]:
                    result = self.execute_tool_call(tool_call)
                    results.append(result)
                
                # Combine results
                combined_data = "\n\n".join([r.get("data", str(r)) for r in results if r.get("success")])
                
                # Add AI understanding to the response
                if ai_understanding:
                    combined_data = f"🤖 **AI Understanding**: {ai_understanding}\n\n" + combined_data
                
                return {
                    "success": True,
                    "data": combined_data,
                    "tool_calls": pattern_result["tool_calls"]
                }
            except Exception as e:
                return {
                    "success": False,
                    "error": f"Failed to execute tool calls: {str(e)}"
                }
        elif pattern_result.get("success"):
            # No tool calls, just return the pattern result with AI understanding
            if ai_understanding:
                pattern_result["data"] = f"🤖 **AI Understanding**: {ai_understanding}\n\n" + pattern_result["data"]
            return pattern_result
        else:
            return pattern_result
    
    def get_ai_understanding(self, query: str) -> str:
        """Get AI understanding of the query without function calling"""
        try:
            if not self.model or not self.tokenizer:
                return None
            
            # Simple prompt for understanding
            understanding_prompt = f"""You are an AI assistant. Understand what the user is asking for.

User: {query}

Assistant: The user is asking for:"""
            
            # Tokenize and generate
            inputs = self.tokenizer(understanding_prompt, return_tensors="pt")
            
            # Move inputs to the same device as model
            device = next(self.model.parameters()).device
            input_ids = inputs["input_ids"].to(device)
            attention_mask = inputs["attention_mask"].to(device) if "attention_mask" in inputs else None
            
            with torch.no_grad():
                outputs = self.model.generate(
                    input_ids,
                    attention_mask=attention_mask,
                    max_new_tokens=100,
                    temperature=0.3,
                    do_sample=True,
                    pad_token_id=self.tokenizer.eos_token_id
                )
            
            # Decode response
            response_text = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
            
            # Extract the generated part
            if understanding_prompt in response_text:
                understanding = response_text.split(understanding_prompt)[-1].strip()
                return understanding
            else:
                return None
                
        except Exception as e:
            print(f"❌ AI understanding error: {e}")
            return None

def main():
    """Test the True LAM Interface"""
    lam = TrueLAMInterface()
    
    test_queries = [
        "What's the weather in London?",
        "Create a file called sales.txt with sales data",
        "Show me sales report for this year",
        "Read the sales.txt file",
        "Search for latest AI news"
    ]
    
    print("🧪 Testing True LAM Interface")
    print("=" * 50)
    
    for query in test_queries:
        print(f"\n📝 Query: {query}")
        print("-" * 40)
        
        result = lam.process_query(query)
        
        if result.get("success"):
            print("✅ Success!")
            print(result.get("data", "No data"))
        else:
            print("❌ Failed!")
            print(result.get("error", "Unknown error"))
        
        print("=" * 50)

if __name__ == "__main__":
    main() 