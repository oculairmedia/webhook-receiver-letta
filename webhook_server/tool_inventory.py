"""
Tool Inventory Module

Manages tool inventory tracking and memory block generation for agents.
Provides visibility into currently attached tools with categorization and context.
"""

import os
import requests
from typing import Dict, List, Optional, Tuple
from datetime import datetime, UTC
from collections import defaultdict

from .config import get_api_url, LETTA_API_HEADERS

# Category mapping based on MCP server names
CATEGORY_MAPPING = {
    "Searxng": "Web Search",
    "bookstack": "Knowledge & Docs",
    "ghost": "Content Publishing",
    "postiz": "Social Media",
    "huly": "Project Management",
    "vibekanban": "Project Management",
    "vibekanban_system": "Project Management",
    "filesystem": "Filesystem",
    "penpot": "Design",
    "photoprism": "Media",
    "graphiti": "Knowledge Graph",
    "lettachat": "Communication",
    "matrix": "Communication",
    "agent_registry": "Agent Discovery",
    "fin": "Finance",
    "komodo": "DevOps",
    "claude-code-mcp": "Code Execution",
    "opencode": "Code Execution",
    "Letta_code": "Code Execution",
    "payloadcms": "CMS",
    "resume": "Personal Data",
    "context7": "Documentation",
    "letta": "Agent Management",
    "lettatoolsselector": "Tool Management",
}

# Core tools that are always available (not from MCP)
CORE_TOOL_NAMES = {
    "send_message",
    "conversation_search",
    "conversation_search_date",
    "archival_memory_insert",
    "archival_memory_search",
    "core_memory_append",
    "core_memory_replace",
}

# In-memory tracking of recent tool attachments per agent
# Structure: {agent_id: [{tool_name, tool_id, reason, score, timestamp}, ...]}
RECENT_ATTACHMENTS: Dict[str, List[Dict]] = {}


def get_agent_tools_with_details(agent_id: str) -> List[Dict]:
    """
    Fetch all tools attached to an agent with full metadata.
    
    Args:
        agent_id: The agent ID
        
    Returns:
        List of tool dicts with: id, name, description, mcp_server_name, tags, etc.
    """
    if not agent_id:
        print("[TOOL_INVENTORY] No agent_id provided")
        return []
    
    try:
        url = get_api_url(f"agents/{agent_id}/tools")
        headers = {**LETTA_API_HEADERS, "user_id": agent_id}
        
        print(f"[TOOL_INVENTORY] Fetching tools for agent {agent_id}")
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        tools = response.json()
        print(f"[TOOL_INVENTORY] Retrieved {len(tools)} tools")
        
        return tools if isinstance(tools, list) else []
        
    except Exception as e:
        print(f"[TOOL_INVENTORY] Error fetching tools: {e}")
        return []


def categorize_tool(tool: Dict) -> str:
    """
    Determine the category for a tool based on its metadata.
    
    Args:
        tool: Tool dict with metadata
        
    Returns:
        Category name
    """
    tool_name = tool.get("name", "").lower()
    
    # Check if it's a core tool
    if tool_name in CORE_TOOL_NAMES:
        return "Core"
    
    # Check MCP server name
    mcp_metadata = tool.get("metadata_", {}).get("mcp", {})
    server_name = mcp_metadata.get("server_name") or tool.get("mcp_server_name")
    
    if server_name and server_name in CATEGORY_MAPPING:
        return CATEGORY_MAPPING[server_name]
    
    # Check tags for hints
    tags = tool.get("tags", [])
    for tag in tags:
        if isinstance(tag, str):
            tag_lower = tag.lower()
            if "mcp:" in tag_lower:
                mcp_name = tag_lower.split("mcp:")[-1]
                if mcp_name in CATEGORY_MAPPING:
                    return CATEGORY_MAPPING[mcp_name]
    
    return "Other"


def categorize_tools(tools: List[Dict]) -> Dict[str, List[Dict]]:
    """
    Categorize tools into domains.
    
    Args:
        tools: List of tool dicts
        
    Returns:
        Dict mapping category name to list of tools
    """
    categorized = defaultdict(list)
    
    for tool in tools:
        category = categorize_tool(tool)
        categorized[category].append(tool)
    
    return dict(categorized)


def record_tool_attachment(agent_id: str, tool_name: str, tool_id: str, 
                          reason: str, score: float):
    """
    Record when a tool was attached and why.
    
    Args:
        agent_id: The agent ID
        tool_name: Name of the tool
        tool_id: ID of the tool
        reason: Why it was attached (e.g., "auto: keyword 'search'")
        score: Match score (0-100)
    """
    if agent_id not in RECENT_ATTACHMENTS:
        RECENT_ATTACHMENTS[agent_id] = []
    
    attachment_record = {
        "tool_name": tool_name,
        "tool_id": tool_id,
        "reason": reason,
        "score": score,
        "timestamp": datetime.now(UTC).isoformat()
    }
    
    # Add to front of list (most recent first)
    RECENT_ATTACHMENTS[agent_id].insert(0, attachment_record)
    
    # Keep only last 10 attachments
    RECENT_ATTACHMENTS[agent_id] = RECENT_ATTACHMENTS[agent_id][:10]
    
    print(f"[TOOL_INVENTORY] Recorded attachment: {tool_name} for agent {agent_id}")


def get_recent_attachments(agent_id: str, limit: int = 5) -> List[Dict]:
    """
    Get recent tool attachments for an agent.
    
    Args:
        agent_id: The agent ID
        limit: Maximum number to return
        
    Returns:
        List of recent attachment records
    """
    return RECENT_ATTACHMENTS.get(agent_id, [])[:limit]


def format_tool_entry(tool: Dict, include_description: bool = True) -> str:
    """
    Format a single tool for display.
    
    Args:
        tool: Tool dict
        include_description: Whether to include description
        
    Returns:
        Formatted string
    """
    name = tool.get("name", "unknown")
    description = tool.get("description", "")
    
    # Truncate long descriptions
    if description and len(description) > 80:
        description = description[:77] + "..."
    
    if include_description and description:
        return f"• {name} - {description}"
    else:
        return f"• {name}"


def format_tool_inventory(agent_id: str, tools: List[Dict], 
                          prompt: Optional[str] = None) -> str:
    """
    Format tools into concise memory block content.
    
    Args:
        agent_id: The agent ID
        tools: List of all tools attached to agent
        prompt: Optional prompt that triggered this update (for context)
        
    Returns:
        Formatted inventory string
    """
    if not tools:
        return "🛠️ Available Tools: None currently attached."
    
    # Categorize tools
    categorized = categorize_tools(tools)
    
    # Get recent attachments
    recent = get_recent_attachments(agent_id, limit=3)
    recent_tool_ids = {r["tool_id"] for r in recent}
    
    # Build the inventory
    lines = [f"🛠️ Available Tools ({len(tools)} total)\n"]
    
    # Show recently attached tools first (if any)
    if recent:
        lines.append("═══ Recently Attached ═══")
        for attachment in recent:
            tool_name = attachment["tool_name"]
            score = attachment["score"]
            timestamp = attachment["timestamp"]
            reason = attachment["reason"]
            
            # Parse timestamp
            try:
                dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                time_str = dt.strftime("%Y-%m-%d %H:%M")
            except:
                time_str = "recent"
            
            lines.append(f"• {tool_name}")
            lines.append(f"  └─ [{reason} • score: {score:.0f}% • {time_str}]")
        lines.append("")
    
    # Category order priority
    priority_categories = ["Core", "Web Search", "Communication", "Knowledge Graph", 
                          "Project Management", "Code Execution"]
    
    # Show priority categories first
    shown_categories = set()
    for category in priority_categories:
        if category in categorized:
            category_tools = categorized[category]
            lines.append(f"═══ {category} ═══")
            
            for tool in category_tools[:5]:  # Limit to 5 per category
                # Skip if already shown in recent
                if tool.get("id") not in recent_tool_ids:
                    lines.append(format_tool_entry(tool, include_description=True))
            
            shown_categories.add(category)
            lines.append("")
    
    # Show remaining categories
    for category in sorted(categorized.keys()):
        if category not in shown_categories:
            category_tools = categorized[category]
            lines.append(f"═══ {category} ═══")
            
            for tool in category_tools[:5]:  # Limit to 5 per category
                if tool.get("id") not in recent_tool_ids:
                    lines.append(format_tool_entry(tool, include_description=True))
            
            lines.append("")
    
    # Add footer
    timestamp = datetime.now(UTC).strftime("%Y-%m-%d %H:%M:%S UTC")
    lines.append(f"[Last updated: {timestamp}]")
    
    inventory_text = "\n".join(lines)
    
    # Ensure we don't exceed block size limit (keep under 4500 chars)
    if len(inventory_text) > 4500:
        print(f"[TOOL_INVENTORY] Inventory too long ({len(inventory_text)} chars), truncating...")
        inventory_text = inventory_text[:4450] + "\n...\n[Content truncated]"
    
    return inventory_text


def build_tool_inventory_block(agent_id: str, prompt: Optional[str] = None,
                               attachment_result: Optional[Dict] = None) -> Dict:
    """
    Build the complete tool inventory memory block for an agent.
    
    Args:
        agent_id: The agent ID
        prompt: Optional prompt that triggered this
        attachment_result: Optional structured result from find_attach_tools
        
    Returns:
        Dict with 'success' (bool), 'content' (str), and optional 'error' (str) keys
    """
    try:
        # Record any new attachments if provided
        if attachment_result and isinstance(attachment_result, dict):
            successful_attachments = attachment_result.get("details", {}).get("successful_attachments", [])
            
            for attachment in successful_attachments:
                tool_name = attachment.get("name", "unknown")
                tool_id = attachment.get("tool_id", "")
                score = attachment.get("match_score", 0)
                
                # Build reason from prompt
                reason = "auto"
                if prompt:
                    # Extract keywords from prompt
                    keywords = prompt.lower().split()[:3]
                    keyword_str = " ".join(keywords)
                    reason = f"auto: '{keyword_str}'"
                
                record_tool_attachment(agent_id, tool_name, tool_id, reason, score)
        
        # Fetch all current tools
        tools = get_agent_tools_with_details(agent_id)
        
        if not tools:
            print(f"[TOOL_INVENTORY] No tools found for agent {agent_id}")
            return {
                "success": False,
                "error": "No tools found for agent"
            }
        
        # Format inventory
        content = format_tool_inventory(agent_id, tools, prompt)
        
        print(f"[TOOL_INVENTORY] Generated inventory ({len(content)} chars)")
        
        return {
            "success": True,
            "content": content
        }
        
    except Exception as e:
        print(f"[TOOL_INVENTORY] Error building inventory: {e}")
        return {
            "success": False,
            "error": str(e)
        }
