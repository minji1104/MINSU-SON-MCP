from mcp.server.fastmcp import FastMCP, Context
import openai
import os
import re
from typing import List, Dict, Optional, Any
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Create an MCP server
mcp = FastMCP("Language Style Mirroring")

# Configure OpenAI API key from environment variable
openai.api_key = os.getenv("OPENAI_API_KEY", "")

# Default language
DEFAULT_LANGUAGE = os.getenv("DEFAULT_LANGUAGE", "en")

# Dictionary to store analyzed styles
analyzed_styles = {}

# Helper function to use the YouTube transcript MCP server
async def get_transcripts(url: str, lang: str = None, enableParagraphs: bool = False) -> Dict[str, Any]:
    """
    Get video transcripts using YouTube Transcript MCP server
    
    Args:
        url (str): YouTube video URL or ID
        lang (str): Language code for transcript (default: DEFAULT_LANGUAGE)
        enableParagraphs (bool): Enable automatic paragraph breaks (default: False)
        
    Returns:
        Dict[str, Any]: Transcript data including text and metadata
    """
    # Use the default language if none is provided
    if lang is None:
        lang = DEFAULT_LANGUAGE
        
    try:
        # Create server parameters for youtube-transcript MCP server
        server_params = StdioServerParameters(
            command="npx",
            args=["-y", "@kimtaeyoon83/mcp-server-youtube-transcript"],
            env=None
        )
        
        async with stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as session:
                # Initialize the connection
                await session.initialize()
                
                # Call the get_transcripts tool
                result = await session.call_tool(
                    "get_transcript", 
                    arguments={
                        "url": url,
                        "lang": lang,
                        "enableParagraphs": enableParagraphs
                    }
                )
                
                # Process the result
                if isinstance(result, dict) and "text" in result:
                    return result
                elif isinstance(result, str):
                    return {"text": result}
                else:
                    return {"text": str(result)}
                    
    except Exception as e:
        raise Exception(f"Error getting transcript: {str(e)}")

@mcp.tool()
async def analyze_youtube_style(url: str, lang: str = None, ctx: Context = None) -> str:
    """
    Analyze the speaking/writing style of a person in a YouTube video.
    
    Args:
        url (str): YouTube video URL or ID
        lang (str): Language code for transcript (default: DEFAULT_LANGUAGE)
    
    Returns:
        str: Analysis of the person's language style
    """
    # Use the default language if none is provided
    if lang is None:
        lang = DEFAULT_LANGUAGE
        
    if ctx:
        await ctx.report_progress(0, 3)
        ctx.info(f"Fetching transcript for {url}")
    
    # Get transcript using MCP YouTube Transcript server
    try:
        transcript_data = await get_transcripts(url=url, lang=lang, enableParagraphs=True)
        transcript_text = transcript_data.get('text', '')
        
        if not transcript_text:
            return "Error: Could not extract transcript text from the video."
        
        if ctx:
            await ctx.report_progress(1, 3)
            ctx.info("Analyzing language style")
        
        # Use OpenAI to analyze the style
        analysis = await analyze_style_with_openai(transcript_text)
        
        # Store the analysis
        video_id = extract_video_id(url)
        analyzed_styles[video_id] = analysis
        
        if ctx:
            await ctx.report_progress(3, 3)
            ctx.info("Analysis complete")
        
        return analysis
    
    except Exception as e:
        return f"Error analyzing YouTube style: {str(e)}"

@mcp.tool()
async def mirror_style(text: str, style_id: str) -> str:
    """
    Transform the given text to match the analyzed language style.
    
    Args:
        text (str): The text to transform
        style_id (str): ID of the previously analyzed style (YouTube video ID or custom name)
    
    Returns:
        str: Transformed text in the target style
    """
    if style_id not in analyzed_styles:
        return f"Error: Style with ID '{style_id}' not found. Please analyze a style first."
    
    style_analysis = analyzed_styles[style_id]
    
    # Use OpenAI to transform the text
    try:
        transformed_text = await transform_text_with_openai(text, style_analysis)
        return transformed_text
    except Exception as e:
        return f"Error mirroring style: {str(e)}"

@mcp.tool()
async def save_style(style_id: str, description: str) -> str:
    """
    Save a custom style with a specific ID.
    
    Args:
        style_id (str): Custom ID to save the style as
        description (str): Detailed description of the language style
    
    Returns:
        str: Confirmation message
    """
    try:
        analyzed_styles[style_id] = description
        return f"Successfully saved style with ID: {style_id}"
    except Exception as e:
        return f"Error saving style: {str(e)}"

@mcp.tool()
async def list_saved_styles() -> str:
    """
    List all saved language styles.
    
    Returns:
        str: List of saved styles with their IDs
    """
    if not analyzed_styles:
        return "No styles have been saved yet."
    
    result = "Saved styles:\n\n"
    for style_id in analyzed_styles:
        result += f"- {style_id}\n"
    
    return result

@mcp.resource("style://{style_id}")
async def get_style(style_id: str) -> str:
    """
    Get the analysis for a specific style.
    
    Args:
        style_id (str): ID of the style to retrieve
    
    Returns:
        str: Style analysis
    """
    if style_id not in analyzed_styles:
        return f"Style with ID '{style_id}' not found."
    
    return analyzed_styles[style_id]

# Helper functions
async def analyze_style_with_openai(text: str) -> str:
    """Analyze language style using OpenAI API"""
    system_prompt = """
    You are a linguistic analyst specialized in identifying unique speech and writing patterns.
    Analyze the provided text and identify the key characteristics of the speaker's language style including:
    
    1. Vocabulary choices (formality level, specialized terms, favorite words/phrases)
    2. Sentence structure (length, complexity, active/passive voice preference)
    3. Rhetorical devices (metaphors, similes, analogies, etc.)
    4. Tone and sentiment (professional, casual, optimistic, critical, etc.)
    5. Speech patterns (filler words, pauses, repetition)
    6. Unique expressions or catchphrases
    7. Grammar and syntax patterns
    8. Cultural or regional language markers
    
    Provide a comprehensive style guide that could be used to mimic this person's language style convincingly.
    """
    
    # Limit text length to avoid token limits
    max_length = 8000
    if len(text) > max_length:
        # Take the beginning, middle and end sections
        section_length = max_length // 3
        text_sample = text[:section_length] + "\n...\n" + text[len(text)//2-section_length//2:len(text)//2+section_length//2] + "\n...\n" + text[-section_length:]
    else:
        text_sample = text
    
    response = await openai.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Analyze the following text:\n\n{text_sample}"}
        ],
        temperature=0.2,
        max_tokens=1500
    )
    
    return response.choices[0].message.content

async def transform_text_with_openai(text: str, style_analysis: str) -> str:
    """Transform text to match a specific language style"""
    system_prompt = f"""
    You are an expert in linguistic style transfer. Your task is to rewrite the provided text 
    to match a specific language style that will be described to you.
    
    Here is the style guide to follow:
    
    {style_analysis}
    
    Rewrite the text to match this style perfectly while preserving the original meaning completely.
    Don't add any comments or explanations - just provide the rewritten text.
    """
    
    response = await openai.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Rewrite this text in the described style:\n\n{text}"}
        ],
        temperature=0.7,
        max_tokens=2000
    )
    
    return response.choices[0].message.content

def extract_video_id(url: str) -> str:
    """Extract YouTube video ID from URL or return the ID if already provided"""
    if len(url) == 11 and re.match(r'^[A-Za-z0-9_-]{11}$', url):
        return url
    
    # Extract from various YouTube URL formats
    patterns = [
        r'(?:youtube\.com\/watch\?v=|youtu\.be\/|youtube\.com\/embed\/|youtube\.com\/v\/|youtube\.com\/e\/|youtube\.com\/user\/[^\/]+\/[^\/]+\/|youtube\.com\/[^\/]+\/[^\/]+\/|youtube\.com\/verify_age\?next_url=\/watch%3Fv%3D|youtube\.com\/get_video_info\?video_id=|youtube\.com\/shorts\/)([A-Za-z0-9_-]{11})',
        r'youtube\.com\/watch\?.*?v=([A-Za-z0-9_-]{11})',
        r'youtube\.com\/.*?\?.*?v=([A-Za-z0-9_-]{11})'
    ]
    
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    
    # If no match found, return the original URL
    return url

if __name__ == "__main__":
    mcp.run() 