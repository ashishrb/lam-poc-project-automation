#!/usr/bin/env python3
"""
Communication Engine for Task Extraction
Extracts tasks from emails, meetings, chat transcripts, and other communications
"""

import json
import logging
import re
from datetime import datetime, date, timedelta
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.project import Project, Task
from app.models.user import User
from app.models.project import TaskStatus, TaskPriority
from app.services.ai_guardrails import AIGuardrails
from app.core.config import settings

logger = logging.getLogger(__name__)


class CommunicationType(str, Enum):
    """Types of communication sources"""
    EMAIL = "email"
    MEETING = "meeting"
    CHAT = "chat"
    DOCUMENT = "document"
    VOICE_MEMO = "voice_memo"


class TaskExtractionConfidence(str, Enum):
    """Confidence levels for extracted tasks"""
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


@dataclass
class ExtractedTask:
    """Extracted task information"""
    title: str
    description: str
    assignee: Optional[str]
    due_date: Optional[date]
    priority: TaskPriority
    estimated_hours: Optional[float]
    project_id: Optional[int]
    confidence: TaskExtractionConfidence
    source: str
    source_id: str
    context: Dict[str, Any]


@dataclass
class CommunicationContext:
    """Context information for communication"""
    communication_type: CommunicationType
    source_id: str
    timestamp: datetime
    participants: List[str]
    project_context: Optional[str]
    summary: str


class CommunicationEngine:
    """Engine for extracting tasks from communications"""
    
    def __init__(self):
        self.guardrails = AIGuardrails()
        self.task_patterns = {
            "action_items": [
                r"(?:need to|must|should|will|going to)\s+(.+?)(?:\.|$)",
                r"(?:action item|todo|task):\s*(.+?)(?:\.|$)",
                r"(?:follow up|follow-up|followup):\s*(.+?)(?:\.|$)",
                r"(?:next steps?|next action):\s*(.+?)(?:\.|$)"
            ],
            "assignments": [
                r"(?:assign|delegate|give)\s+(.+?)\s+to\s+(.+?)(?:\.|$)",
                r"(.+?)\s+will\s+(.+?)(?:\.|$)",
                r"(.+?)\s+is\s+responsible\s+for\s+(.+?)(?:\.|$)"
            ],
            "deadlines": [
                r"(?:by|due|deadline|end of)\s+(.+?)(?:\.|$)",
                r"(?:next|this)\s+(?:week|month|day)(?:\.|$)",
                r"(\d{1,2}/\d{1,2}/\d{4})",
                r"(\d{4}-\d{2}-\d{2})"
            ],
            "priorities": [
                r"(?:urgent|critical|high priority|asap|immediately)",
                r"(?:medium priority|moderate|normal)",
                r"(?:low priority|when possible|sometime)"
            ]
        }
    
    async def extract_tasks_from_communication(
        self, 
        content: str,
        communication_type: CommunicationType,
        source_id: str,
        project_id: Optional[int] = None,
        db: AsyncSession = None
    ) -> Dict[str, Any]:
        """Extract tasks from communication content"""
        try:
            # Create communication context
            context = await self._create_communication_context(
                content, communication_type, source_id, project_id
            )
            
            # Extract tasks using pattern matching
            pattern_tasks = await self._extract_tasks_by_patterns(content, context)
            
            # Extract tasks using AI
            ai_tasks = await self._extract_tasks_by_ai(content, context)
            
            # Combine and deduplicate tasks
            all_tasks = await self._combine_and_deduplicate_tasks(
                pattern_tasks, ai_tasks, context
            )
            
            # Validate and enhance tasks
            validated_tasks = await self._validate_and_enhance_tasks(
                all_tasks, project_id, db
            )
            
            return {
                "success": True,
                "source_id": source_id,
                "communication_type": communication_type.value,
                "total_tasks_extracted": len(validated_tasks),
                "tasks": [
                    {
                        "title": task.title,
                        "description": task.description,
                        "assignee": task.assignee,
                        "due_date": task.due_date.isoformat() if task.due_date else None,
                        "priority": task.priority.value,
                        "estimated_hours": task.estimated_hours,
                        "project_id": task.project_id,
                        "confidence": task.confidence.value,
                        "source": task.source,
                        "source_id": task.source_id,
                        "context": task.context
                    }
                    for task in validated_tasks
                ],
                "summary": {
                    "high_confidence": len([t for t in validated_tasks if t.confidence == TaskExtractionConfidence.HIGH]),
                    "medium_confidence": len([t for t in validated_tasks if t.confidence == TaskExtractionConfidence.MEDIUM]),
                    "low_confidence": len([t for t in validated_tasks if t.confidence == TaskExtractionConfidence.LOW])
                }
            }
            
        except Exception as e:
            logger.error(f"Error extracting tasks from communication: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def create_tasks_from_extraction(
        self, 
        extracted_tasks: List[Dict[str, Any]],
        project_id: int,
        db: AsyncSession
    ) -> Dict[str, Any]:
        """Create actual tasks from extracted task data"""
        try:
            created_tasks = []
            failed_tasks = []
            
            for task_data in extracted_tasks:
                try:
                    # Validate task data
                    validation_result = await self._validate_task_data(task_data)
                    if not validation_result["valid"]:
                        failed_tasks.append({
                            "task_data": task_data,
                            "error": validation_result["error"]
                        })
                        continue
                    
                    # Create task
                    task = await self._create_task_from_data(task_data, project_id, db)
                    created_tasks.append(task)
                    
                except Exception as e:
                    failed_tasks.append({
                        "task_data": task_data,
                        "error": str(e)
                    })
            
            return {
                "success": True,
                "created_tasks": len(created_tasks),
                "failed_tasks": len(failed_tasks),
                "task_ids": [task.id for task in created_tasks],
                "failures": failed_tasks
            }
            
        except Exception as e:
            logger.error(f"Error creating tasks from extraction: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def process_email_for_tasks(
        self, 
        email_content: str,
        email_id: str,
        sender: str,
        recipients: List[str],
        subject: str,
        project_id: Optional[int] = None,
        db: AsyncSession = None
    ) -> Dict[str, Any]:
        """Process email specifically for task extraction"""
        try:
            # Enhance email content with metadata
            enhanced_content = f"""
Subject: {subject}
From: {sender}
To: {', '.join(recipients)}

Content:
{email_content}
"""
            
            # Extract tasks
            extraction_result = await self.extract_tasks_from_communication(
                enhanced_content, CommunicationType.EMAIL, email_id, project_id, db
            )
            
            if not extraction_result["success"]:
                return extraction_result
            
            # Add email-specific context
            for task in extraction_result["tasks"]:
                task["context"]["email_subject"] = subject
                task["context"]["email_sender"] = sender
                task["context"]["email_recipients"] = recipients
            
            return extraction_result
            
        except Exception as e:
            logger.error(f"Error processing email for tasks: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def process_meeting_transcript(
        self, 
        transcript: str,
        meeting_id: str,
        participants: List[str],
        meeting_date: datetime,
        project_id: Optional[int] = None,
        db: AsyncSession = None
    ) -> Dict[str, Any]:
        """Process meeting transcript for task extraction"""
        try:
            # Enhance transcript with meeting context
            enhanced_content = f"""
Meeting Date: {meeting_date.isoformat()}
Participants: {', '.join(participants)}

Transcript:
{transcript}
"""
            
            # Extract tasks
            extraction_result = await self.extract_tasks_from_communication(
                enhanced_content, CommunicationType.MEETING, meeting_id, project_id, db
            )
            
            if not extraction_result["success"]:
                return extraction_result
            
            # Add meeting-specific context
            for task in extraction_result["tasks"]:
                task["context"]["meeting_date"] = meeting_date.isoformat()
                task["context"]["meeting_participants"] = participants
            
            return extraction_result
            
        except Exception as e:
            logger.error(f"Error processing meeting transcript: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def process_chat_transcript(
        self, 
        chat_content: str,
        chat_id: str,
        participants: List[str],
        chat_date: datetime,
        project_id: Optional[int] = None,
        db: AsyncSession = None
    ) -> Dict[str, Any]:
        """Process chat transcript for task extraction"""
        try:
            # Enhance chat content with context
            enhanced_content = f"""
Chat Date: {chat_date.isoformat()}
Participants: {', '.join(participants)}

Chat:
{chat_content}
"""
            
            # Extract tasks
            extraction_result = await self.extract_tasks_from_communication(
                enhanced_content, CommunicationType.CHAT, chat_id, project_id, db
            )
            
            if not extraction_result["success"]:
                return extraction_result
            
            # Add chat-specific context
            for task in extraction_result["tasks"]:
                task["context"]["chat_date"] = chat_date.isoformat()
                task["context"]["chat_participants"] = participants
            
            return extraction_result
            
        except Exception as e:
            logger.error(f"Error processing chat transcript: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    # Private helper methods
    
    async def _create_communication_context(
        self, 
        content: str, 
        communication_type: CommunicationType,
        source_id: str,
        project_id: Optional[int]
    ) -> CommunicationContext:
        """Create communication context"""
        # Extract participants (simplified)
        participants = self._extract_participants(content)
        
        # Generate summary
        summary = await self._generate_summary(content)
        
        return CommunicationContext(
            communication_type=communication_type,
            source_id=source_id,
            timestamp=datetime.now(),
            participants=participants,
            project_context=str(project_id) if project_id else None,
            summary=summary
        )
    
    async def _extract_tasks_by_patterns(
        self, 
        content: str, 
        context: CommunicationContext
    ) -> List[ExtractedTask]:
        """Extract tasks using pattern matching"""
        tasks = []
        
        # Extract action items
        for pattern in self.task_patterns["action_items"]:
            matches = re.finditer(pattern, content, re.IGNORECASE)
            for match in matches:
                task_title = match.group(1).strip()
                if len(task_title) > 5:  # Minimum meaningful length
                    tasks.append(ExtractedTask(
                        title=task_title,
                        description=f"Extracted from {context.communication_type.value}",
                        assignee=None,
                        due_date=None,
                        priority=TaskPriority.MEDIUM,
                        estimated_hours=None,
                        project_id=int(context.project_context) if context.project_context else None,
                        confidence=TaskExtractionConfidence.MEDIUM,
                        source=context.communication_type.value,
                        source_id=context.source_id,
                        context={"extraction_method": "pattern", "pattern": pattern}
                    ))
        
        # Extract assignments
        for pattern in self.task_patterns["assignments"]:
            matches = re.finditer(pattern, content, re.IGNORECASE)
            for match in matches:
                assignee = match.group(1).strip()
                task_title = match.group(2).strip()
                if len(task_title) > 5:
                    tasks.append(ExtractedTask(
                        title=task_title,
                        description=f"Assigned to {assignee}",
                        assignee=assignee,
                        due_date=None,
                        priority=TaskPriority.MEDIUM,
                        estimated_hours=None,
                        project_id=int(context.project_context) if context.project_context else None,
                        confidence=TaskExtractionConfidence.HIGH,
                        source=context.communication_type.value,
                        source_id=context.source_id,
                        context={"extraction_method": "pattern", "pattern": pattern}
                    ))
        
        return tasks
    
    async def _extract_tasks_by_ai(
        self, 
        content: str, 
        context: CommunicationContext
    ) -> List[ExtractedTask]:
        """Extract tasks using AI"""
        try:
            # Create prompt for AI
            prompt = self._create_task_extraction_prompt(content, context)
            
            # Call AI service
            ai_response = await self.guardrails.call_ai_model(prompt)
            
            # Parse AI response
            tasks = await self._parse_ai_task_response(ai_response, context)
            
            return tasks
            
        except Exception as e:
            logger.error(f"Error extracting tasks by AI: {e}")
            return []
    
    def _create_task_extraction_prompt(self, content: str, context: CommunicationContext) -> str:
        """Create prompt for AI task extraction"""
        return f"""
Extract tasks from the following {context.communication_type.value} communication.

Communication Type: {context.communication_type.value}
Participants: {', '.join(context.participants)}
Project Context: {context.project_context or 'Not specified'}

Content:
{content}

Please extract all tasks, action items, and assignments mentioned in this communication. For each task, provide:
1. Task title (clear and actionable)
2. Description (what needs to be done)
3. Assignee (who is responsible, if mentioned)
4. Due date (if mentioned)
5. Priority (high/medium/low based on urgency indicators)
6. Estimated hours (if mentioned or can be inferred)

Return the results as a JSON array with the following structure:
[
  {{
    "title": "Task title",
    "description": "Task description",
    "assignee": "Assignee name or null",
    "due_date": "YYYY-MM-DD or null",
    "priority": "high|medium|low",
    "estimated_hours": "number or null"
  }}
]

Focus on actionable items and avoid duplicates.
"""
    
    async def _parse_ai_task_response(
        self, 
        ai_response: str, 
        context: CommunicationContext
    ) -> List[ExtractedTask]:
        """Parse AI response into ExtractedTask objects"""
        tasks = []
        
        try:
            # Extract JSON from AI response
            json_match = re.search(r'\[.*\]', ai_response, re.DOTALL)
            if not json_match:
                return tasks
            
            task_data = json.loads(json_match.group())
            
            for item in task_data:
                # Parse priority
                priority = TaskPriority.MEDIUM
                if item.get("priority") == "high":
                    priority = TaskPriority.HIGH
                elif item.get("priority") == "low":
                    priority = TaskPriority.LOW
                
                # Parse due date
                due_date = None
                if item.get("due_date"):
                    try:
                        due_date = datetime.fromisoformat(item["due_date"]).date()
                    except (ValueError, TypeError):
                        pass
                
                # Parse estimated hours
                estimated_hours = None
                if item.get("estimated_hours"):
                    try:
                        estimated_hours = float(item["estimated_hours"])
                    except (ValueError, TypeError):
                        pass
                
                tasks.append(ExtractedTask(
                    title=item["title"],
                    description=item["description"],
                    assignee=item.get("assignee"),
                    due_date=due_date,
                    priority=priority,
                    estimated_hours=estimated_hours,
                    project_id=int(context.project_context) if context.project_context else None,
                    confidence=TaskExtractionConfidence.HIGH,
                    source=context.communication_type.value,
                    source_id=context.source_id,
                    context={"extraction_method": "ai"}
                ))
            
        except Exception as e:
            logger.error(f"Error parsing AI task response: {e}")
        
        return tasks
    
    async def _combine_and_deduplicate_tasks(
        self, 
        pattern_tasks: List[ExtractedTask],
        ai_tasks: List[ExtractedTask],
        context: CommunicationContext
    ) -> List[ExtractedTask]:
        """Combine and deduplicate tasks from different extraction methods"""
        all_tasks = pattern_tasks + ai_tasks
        
        # Simple deduplication based on title similarity
        unique_tasks = []
        seen_titles = set()
        
        for task in all_tasks:
            # Normalize title for comparison
            normalized_title = task.title.lower().strip()
            
            if normalized_title not in seen_titles:
                seen_titles.add(normalized_title)
                unique_tasks.append(task)
        
        return unique_tasks
    
    async def _validate_and_enhance_tasks(
        self, 
        tasks: List[ExtractedTask],
        project_id: Optional[int],
        db: AsyncSession
    ) -> List[ExtractedTask]:
        """Validate and enhance extracted tasks"""
        enhanced_tasks = []
        
        for task in tasks:
            try:
                # Validate task title
                if len(task.title.strip()) < 3:
                    continue
                
                # Enhance assignee if possible
                if task.assignee and not await self._validate_assignee(task.assignee, db):
                    task.assignee = None
                    task.confidence = TaskExtractionConfidence.LOW
                
                # Set project ID if not specified
                if not task.project_id and project_id:
                    task.project_id = project_id
                
                # Enhance description if needed
                if not task.description or task.description == task.title:
                    task.description = f"Task extracted from {task.source}"
                
                enhanced_tasks.append(task)
                
            except Exception as e:
                logger.error(f"Error enhancing task {task.title}: {e}")
                continue
        
        return enhanced_tasks
    
    def _extract_participants(self, content: str) -> List[str]:
        """Extract participants from communication content"""
        # Simple extraction - in a real system, this would be more sophisticated
        participants = []
        
        # Look for email addresses
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        emails = re.findall(email_pattern, content)
        participants.extend(emails)
        
        # Look for names (simplified)
        name_pattern = r'\b[A-Z][a-z]+\s+[A-Z][a-z]+\b'
        names = re.findall(name_pattern, content)
        participants.extend(names[:5])  # Limit to first 5 names
        
        return list(set(participants))
    
    async def _generate_summary(self, content: str) -> str:
        """Generate summary of communication content"""
        # Simplified summary - in a real system, this would use AI
        words = content.split()
        if len(words) > 50:
            return f"Communication with {len(words)} words, {len(content)} characters"
        else:
            return content[:100] + "..." if len(content) > 100 else content
    
    async def _validate_assignee(self, assignee: str, db: AsyncSession) -> bool:
        """Validate if assignee exists in the system"""
        try:
            # Check if assignee is a valid user
            result = await db.execute(
                select(User).where(User.name.ilike(f"%{assignee}%"))
            )
            return result.scalar_one_or_none() is not None
        except Exception:
            return False
    
    async def _validate_task_data(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate task data before creation"""
        try:
            # Check required fields
            if not task_data.get("title") or len(task_data["title"].strip()) < 3:
                return {"valid": False, "error": "Task title is too short"}
            
            # Validate priority
            priority = task_data.get("priority", "medium")
            if priority not in ["high", "medium", "low"]:
                return {"valid": False, "error": "Invalid priority value"}
            
            # Validate due date format
            if task_data.get("due_date"):
                try:
                    datetime.fromisoformat(task_data["due_date"])
                except (ValueError, TypeError):
                    return {"valid": False, "error": "Invalid due date format"}
            
            return {"valid": True}
            
        except Exception as e:
            return {"valid": False, "error": str(e)}
    
    async def _create_task_from_data(
        self, 
        task_data: Dict[str, Any], 
        project_id: int, 
        db: AsyncSession
    ) -> Task:
        """Create a Task object from extracted data"""
        # Parse due date
        due_date = None
        if task_data.get("due_date"):
            try:
                due_date = datetime.fromisoformat(task_data["due_date"]).date()
            except (ValueError, TypeError):
                pass
        
        # Parse priority
        priority = TaskPriority.MEDIUM
        if task_data.get("priority") == "high":
            priority = TaskPriority.HIGH
        elif task_data.get("priority") == "low":
            priority = TaskPriority.LOW
        
        # Create task
        task = Task(
            title=task_data["title"],
            description=task_data.get("description", ""),
            project_id=project_id,
            assigned_to_id=None,  # Would need to resolve assignee name to ID
            priority=priority,
            status=TaskStatus.TODO,
            start_date=date.today(),
            due_date=due_date,
            estimated_hours=task_data.get("estimated_hours"),
            actual_hours=None,
            dependencies=None
        )
        
        db.add(task)
        await db.commit()
        await db.refresh(task)
        
        return task

