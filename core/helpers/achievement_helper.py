"""
Achievement Memory Helper

Interactive tool to help users recall and document their professional achievements
through guided questioning and LLM-powered prompts.
"""

import logging
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from enum import Enum

from core.llm.base import LLMProvider
from core.models import Achievement

logger = logging.getLogger(__name__)


class QuestionType(Enum):
    """Types of questions to ask."""
    OPEN_ENDED = "open_ended"
    SPECIFIC = "specific"
    QUANTITATIVE = "quantitative"
    IMPACT = "impact"
    CHALLENGE = "challenge"
    RESULT = "result"


@dataclass
class Question:
    """A question to help recall achievements."""
    text: str
    type: QuestionType
    context: Optional[str] = None
    examples: Optional[List[str]] = None


@dataclass
class AchievementDraft:
    """A draft achievement being built through conversation."""
    role: str
    company: str
    raw_responses: Dict[str, str]
    text: Optional[str] = None
    skills: Optional[List[str]] = None
    metrics: Optional[List[str]] = None
    impact: Optional[str] = None
    keywords: Optional[List[str]] = None
    
    def __post_init__(self):
        if self.skills is None:
            self.skills = []
        if self.metrics is None:
            self.metrics = []
        if self.keywords is None:
            self.keywords = []


class AchievementMemoryHelper:
    """
    Interactive helper to recall and document achievements.
    
    Uses a conversational approach with guided questions to help users
    remember and articulate their professional accomplishments.
    """
    
    # Standard question templates
    QUESTION_TEMPLATES = {
        "initial": [
            "What was your main responsibility in this role?",
            "What was the biggest challenge you faced?",
            "What project or initiative are you most proud of?",
        ],
        "challenge": [
            "What problem were you trying to solve?",
            "Why was this challenging or important?",
            "What obstacles did you overcome?",
        ],
        "action": [
            "What specific actions did you take?",
            "What technologies or methods did you use?",
            "Who did you work with or lead?",
        ],
        "result": [
            "What was the outcome?",
            "How did you measure success?",
            "What impact did this have on the business/team/users?",
        ],
        "quantify": [
            "Can you put a number on that? (percentage, amount, time saved, etc.)",
            "How many people/systems/users were affected?",
            "What was the before and after comparison?",
        ]
    }
    
    def __init__(self, llm_provider: Optional[LLMProvider] = None):
        """
        Initialize achievement helper.
        
        Args:
            llm_provider: Optional LLM for generating follow-up questions
        """
        self.llm = llm_provider
    
    def start_session(self, role: str, company: str) -> AchievementDraft:
        """
        Start a new achievement documentation session.
        
        Args:
            role: Job title/position
            company: Company name
        
        Returns:
            New AchievementDraft
        """
        return AchievementDraft(
            role=role,
            company=company,
            raw_responses={}
        )
    
    def get_initial_questions(self) -> List[Question]:
        """Get initial questions to start the conversation."""
        return [
            Question(
                text=q,
                type=QuestionType.OPEN_ENDED,
                examples=["Led migration to microservices", "Reduced deployment time by 50%"]
            )
            for q in self.QUESTION_TEMPLATES["initial"]
        ]
    
    def get_follow_up_questions(
        self,
        draft: AchievementDraft,
        previous_answer: str,
        question_category: str = "action"
    ) -> List[Question]:
        """
        Get follow-up questions based on previous answers.
        
        Args:
            draft: Current achievement draft
            previous_answer: User's previous response
            question_category: Category of questions to ask
        
        Returns:
            List of follow-up questions
        """
        if self.llm and len(previous_answer) > 20:
            # Use LLM to generate contextual follow-ups
            return self._generate_llm_questions(draft, previous_answer)
        
        # Fall back to template questions
        templates = self.QUESTION_TEMPLATES.get(question_category, self.QUESTION_TEMPLATES["action"])
        return [
            Question(
                text=q,
                type=QuestionType.SPECIFIC,
                context=f"Based on: {previous_answer[:100]}..."
            )
            for q in templates
        ]
    
    def _generate_llm_questions(
        self,
        draft: AchievementDraft,
        previous_answer: str
    ) -> List[Question]:
        """Generate contextual follow-up questions using LLM."""
        prompt = f"""Based on this achievement description, generate 2-3 specific follow-up questions to help the person provide more details:

Role: {draft.role} at {draft.company}
Their response: {previous_answer}

Generate questions that will help them:
1. Quantify the impact (numbers, percentages, time saved)
2. Specify the technologies or methods used
3. Clarify the business value or outcome

Format each question on a new line starting with "Q:"
"""
        
        try:
            response = self.llm.generate(prompt, max_tokens=200)
            questions_text = response.content
            
            questions = []
            for line in questions_text.split('\n'):
                if line.strip().startswith('Q:'):
                    q_text = line.strip()[2:].strip()
                    if q_text:
                        questions.append(Question(
                            text=q_text,
                            type=QuestionType.SPECIFIC,
                            context=previous_answer[:100]
                        ))
            
            return questions[:3]  # Return max 3 questions
        
        except Exception as e:
            logger.error(f"Error generating LLM questions: {e}")
            return self.get_follow_up_questions(draft, previous_answer, "action")
    
    def process_answer(
        self,
        draft: AchievementDraft,
        question_type: str,
        answer: str
    ) -> AchievementDraft:
        """
        Process user's answer and update draft.
        
        Args:
            draft: Current achievement draft
            question_type: Type of question answered
            answer: User's response
        
        Returns:
            Updated draft
        """
        # Store raw response
        draft.raw_responses[question_type] = answer
        
        # Extract metrics if present
        metrics = self._extract_metrics(answer)
        if metrics and draft.metrics is not None:
            draft.metrics.extend(metrics)
        
        # Extract skills/technologies
        skills = self._extract_skills(answer)
        if skills and draft.skills is not None:
            draft.skills.extend(skills)
        
        return draft
    
    def _extract_metrics(self, text: str) -> List[str]:
        """Extract quantifiable metrics from text."""
        import re
        
        metrics = []
        
        # Look for percentages
        percentages = re.findall(r'\d+%', text)
        metrics.extend(percentages)
        
        # Look for numbers with units
        numbers = re.findall(r'\d+[KMB]?\+?\s*(?:users|customers|systems|hours|days|months)', text, re.IGNORECASE)
        metrics.extend(numbers)
        
        # Look for time savings
        time_saved = re.findall(r'(?:reduced|decreased|saved|improved).*?(?:\d+%|\d+\s*(?:hours|days|months))', text, re.IGNORECASE)
        metrics.extend(time_saved)
        
        return list(set(metrics))  # Remove duplicates
    
    def _extract_skills(self, text: str) -> List[str]:
        """Extract technical skills and technologies from text."""
        # Common tech keywords
        tech_keywords = [
            'Python', 'Java', 'JavaScript', 'TypeScript', 'React', 'Angular', 'Vue',
            'Docker', 'Kubernetes', 'AWS', 'Azure', 'GCP', 'PostgreSQL', 'MongoDB',
            'Redis', 'Kafka', 'RabbitMQ', 'Jenkins', 'GitLab', 'GitHub', 'CI/CD',
            'microservices', 'REST', 'GraphQL', 'API', 'SQL', 'NoSQL', 'Git',
            'Terraform', 'Ansible', 'Linux', 'Nginx', 'Apache', 'Node.js', 'Django',
            'Flask', 'FastAPI', 'Spring', 'Express', 'TensorFlow', 'PyTorch',
            'Machine Learning', 'AI', 'Data Science', 'Analytics'
        ]
        
        found_skills = []
        text_lower = text.lower()
        
        for skill in tech_keywords:
            if skill.lower() in text_lower:
                found_skills.append(skill)
        
        return found_skills
    
    def finalize_achievement(
        self,
        draft: AchievementDraft,
        use_llm: bool = True
    ) -> Achievement:
        """
        Finalize achievement from draft responses.
        
        Args:
            draft: Completed achievement draft
            use_llm: Whether to use LLM to craft final text
        
        Returns:
            Completed Achievement object
        """
        if use_llm and self.llm:
            achievement_text = self._generate_achievement_text(draft)
        else:
            achievement_text = self._compose_achievement_text(draft)
        
        # Determine impact level
        impact = self._determine_impact(draft)
        
        return Achievement(
            text=achievement_text,
            skills=list(set(draft.skills)) if draft.skills else [],
            metrics=list(set(draft.metrics)) if draft.metrics else [],
            impact=impact,
            keywords=list(set(draft.keywords)) if draft.keywords else []
        )
    
    def _generate_achievement_text(self, draft: AchievementDraft) -> str:
        """Use LLM to generate polished achievement text."""
        # Combine all responses
        context = "\n".join([
            f"{k}: {v}"
            for k, v in draft.raw_responses.items()
        ])
        
        prompt = f"""Create a concise, impactful achievement statement from these details:

Role: {draft.role} at {draft.company}

Details:
{context}

Metrics found: {', '.join(draft.metrics) if draft.metrics else 'None'}
Skills used: {', '.join(draft.skills) if draft.skills else 'None'}

Write ONE achievement statement that:
1. Starts with a strong action verb
2. Includes specific metrics/numbers
3. Emphasizes business impact
4. Is 1-2 sentences (max 150 characters)
5. Uses past tense

Achievement:"""
        
        try:
            response = self.llm.generate(prompt, max_tokens=150)
            text = response.content.strip()
            
            # Clean up the response
            if text.startswith("Achievement:"):
                text = text[12:].strip()
            
            return text
        
        except Exception as e:
            logger.error(f"Error generating achievement text: {e}")
            return self._compose_achievement_text(draft)
    
    def _compose_achievement_text(self, draft: AchievementDraft) -> str:
        """Compose achievement text from responses without LLM."""
        # Get the most substantial responses
        responses = list(draft.raw_responses.values())
        
        if not responses:
            return "Contributed to team success"
        
        # Use the longest response as base
        base_text = max(responses, key=len)
        
        # Add metrics if available
        if draft.metrics:
            metrics_str = ", ".join(draft.metrics[:2])
            if metrics_str.lower() not in base_text.lower():
                base_text = f"{base_text} ({metrics_str})"
        
        return base_text[:200]  # Limit length
    
    def _determine_impact(self, draft: AchievementDraft) -> str:
        """Determine impact level based on metrics and responses."""
        # High impact indicators
        high_indicators = ['led', 'architected', 'designed', 'launched', 'transformed']
        
        # Check for significant metrics
        has_large_numbers = False
        if draft.metrics:
            for metric in draft.metrics:
                digits = ''.join(filter(str.isdigit, metric))
                if digits and int(digits) > 50:
                    has_large_numbers = True
                    break
        
        # Check responses for high-impact words
        all_text = ' '.join(draft.raw_responses.values()).lower()
        has_high_impact_words = any(word in all_text for word in high_indicators)
        
        if has_large_numbers or has_high_impact_words:
            return "high"
        elif draft.metrics:
            return "medium"
        else:
            return "low"
    
    def get_completion_suggestions(self, draft: AchievementDraft) -> List[str]:
        """
        Get suggestions for what information is still missing.
        
        Args:
            draft: Current achievement draft
        
        Returns:
            List of suggestions
        """
        suggestions = []
        
        if not draft.metrics:
            suggestions.append("Add quantifiable metrics (percentages, numbers, time saved)")
        
        if not draft.skills:
            suggestions.append("Mention specific technologies or methods used")
        
        if 'result' not in draft.raw_responses:
            suggestions.append("Describe the outcome or business impact")
        
        if 'challenge' not in draft.raw_responses:
            suggestions.append("Explain what problem you solved or challenge you overcame")
        
        return suggestions


def interactive_achievement_session(
    role: str,
    company: str,
    llm_provider: Optional[LLMProvider] = None
) -> Achievement:
    """
    Run an interactive achievement documentation session.
    
    This is a convenience function for CLI/script usage.
    
    Args:
        role: Job title
        company: Company name
        llm_provider: Optional LLM provider
    
    Returns:
        Completed Achievement
    """
    helper = AchievementMemoryHelper(llm_provider)
    draft = helper.start_session(role, company)
    
    print(f"\nDocumenting achievement for: {role} at {company}")
    print("=" * 60)
    
    # Ask initial questions
    questions = helper.get_initial_questions()
    
    for i, question in enumerate(questions, 1):
        print(f"\nQuestion {i}: {question.text}")
        if question.examples:
            print(f"Examples: {', '.join(question.examples[:2])}")
        
        answer = input("Your answer: ").strip()
        
        if answer:
            helper.process_answer(draft, f"q{i}", answer)
            
            # Ask one follow-up
            if i == 1:  # After first question
                follow_ups = helper.get_follow_up_questions(draft, answer, "result")
                if follow_ups:
                    print(f"\nFollow-up: {follow_ups[0].text}")
                    follow_answer = input("Your answer: ").strip()
                    if follow_answer:
                        helper.process_answer(draft, "follow_up", follow_answer)
    
    # Show what's missing
    suggestions = helper.get_completion_suggestions(draft)
    if suggestions:
        print("\nSuggestions to improve this achievement:")
        for sugg in suggestions:
            print(f"  - {sugg}")
    
    # Finalize
    achievement = helper.finalize_achievement(draft, use_llm=bool(llm_provider))
    
    print("\n" + "=" * 60)
    print("Final Achievement:")
    print(achievement.text)
    if achievement.metrics:
        print(f"Metrics: {', '.join(achievement.metrics)}")
    if achievement.skills:
        print(f"Skills: {', '.join(achievement.skills)}")
    print(f"Impact: {achievement.impact}")
    
    return achievement

# Made with Bob
