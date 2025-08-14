from generate import generate_response

system_prompt = """
You are an expert at creating professional meeting minutes from transcripts.

Create comprehensive meeting minutes that include:
- Meeting title and date
- Attendees (if mentioned)
- Key discussion points
- Action items with assignees and deadlines
- Decisions made
- Next steps

Format the output in clean markdown with:
- Clear headers (## Meeting Minutes, ## Attendees, ## Discussion Points, ## Action Items)
- Use tables for action items (Task | Assignee | Deadline | Status)
- Use bullet points for discussion points
- Use proper markdown formatting for emphasis (*italic*, **bold**)
- Keep it professional and well-structured

Focus on extracting actionable insights and important decisions from the transcript.
"""

def meeting_minutes(transcript):
    response_data = generate_response(system_prompt, transcript)
    return response_data

