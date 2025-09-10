"""Question selection flow."""

from typing import Dict, Any
from ..core.unified_flow_engine import BaseFlow, FlowResult, register_flow
from ..core.database import db


@register_flow("question_selection")
class QuestionSelectionFlow(BaseFlow):
    """Flow for selecting random CAT questions."""

    def execute(self, input_data: Dict[str, Any]) -> FlowResult:
        """Execute question selection."""
        self.log_start()

        try:
            # Get optional subject filter
            subject = input_data.get("subject")

            # Get random question
            question = db.get_random_question(subject)

            if not question:
                error_msg = "No questions found in database"
                self.logger.error(error_msg)
                return FlowResult(success=False, data=input_data, error=error_msg)

            # Prepare result data
            result_data = {
                "question": {
                    "id": question.id,
                    "subject": question.subject,
                    "year": question.year,
                    "question_text": question.question_text,
                    "options": question.options,
                    "correct_answer": question.correct_answer,
                    "topic": question.topic,
                    "difficulty": question.difficulty,
                }
            }

            self.logger.info(
                f"Selected question {question.id} from {question.subject} ({question.year})"
            )

            result = FlowResult(
                success=True, data=result_data, metadata={"flow": "question_selection"}
            )
            print(f"Question selection result: {result}")
            self.log_end(result)
            return result

        except Exception as e:
            error_msg = f"Question selection failed: {str(e)}"
            self.logger.error(error_msg)
            result = FlowResult(success=False, data=input_data, error=error_msg)
            self.log_end(result)
            return result
