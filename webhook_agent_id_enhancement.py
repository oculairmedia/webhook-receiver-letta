#!/usr/bin/env python3
"""
Enhancement suggestion for agent ID extraction to handle more flexible formats.
This could be added to your webhook receiver if needed.
"""

def enhanced_agent_id_extraction(request_path):
    """
    Enhanced agent ID extraction that handles multiple formats:
    - /v1/agents/agent-[uuid]/messages (current)
    - /v1/agents/[any-agent-id]/messages (enhanced)
    """
    if "agents" not in request_path:
        return None
        
    parts = request_path.split("/")
    try:
        agents_index = parts.index("agents")
        if len(parts) > agents_index + 1:
            potential_agent_id = parts[agents_index + 1]
            
            # Current strict validation
            if potential_agent_id.startswith("agent-"):
                return potential_agent_id
                
            # Enhanced: Accept any non-empty agent ID that looks reasonable
            if potential_agent_id and len(potential_agent_id) > 3 and "-" in potential_agent_id:
                print(f"[AGENT_ID] Accepting flexible agent ID format: {potential_agent_id}")
                return potential_agent_id
                
    except ValueError:
        pass
        
    return None

# Test cases
test_paths = [
    "/v1/agents/agent-9c48bb82-46e3-4be6-80eb-8ca43e3a68b6/messages",  # Current format
    "/v1/agents/some-agent-id/messages",  # Your sample format
    "/v1/agents/custom-agent-123/messages",  # Custom format
    "/v1/agents/abc/messages",  # Too short
    "/v1/agents//messages",  # Empty
]

print("Testing Enhanced Agent ID Extraction:")
print("=" * 50)

for path in test_paths:
    result = enhanced_agent_id_extraction(path)
    print(f"Path: {path}")
    print(f"Result: {result}")
    print()