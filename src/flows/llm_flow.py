"""LLM processing flow for formatting reasoning."""

from typing import Dict, Any
from ..core.flow_engine import BaseFlow, FlowResult, register_flow
from ..core.llm_factory import llm_provider


@register_flow("llm_processing")
class LLMProcessingFlow(BaseFlow):
    """Flow for processing reasoning with LLM."""
    
    def execute(self, input_data: Dict[str, Any]) -> FlowResult:
        """Execute LLM processing."""
        self.log_start()
        
        try:
            # Validate input
            if not self.validate_input(input_data, ["question", "reasoning_text"]):
                return FlowResult(
                    success=False,
                    data=input_data,
                    error="Missing question or reasoning data"
                )
            
            
            question_data = input_data["question"]
            reasoning_text = input_data["reasoning_text"]
            
            # Generate formatted explanation
            formatted_explanation = self._generate_formatted_explanation(
                question_data, reasoning_text
            )
            
            result_data = input_data.copy()
            result_data["formatted_explanation"] = formatted_explanation
            
            self.logger.info("LLM processing completed")
            
            result = FlowResult(
                success=True,
                data=result_data,
                metadata={"flow": "llm_processing"}
            )
            
            
            self.log_end(result)
            return result
            
        except Exception as e:
            error_msg = f"LLM processing failed: {str(e)}"
            self.logger.error(error_msg)
            result = FlowResult(
                success=False,
                data=input_data,
                error=error_msg
            )
            self.log_end(result)
            return result
    
    def _generate_formatted_explanation(self, question_data: Dict[str, Any], 
                                      reasoning_text: str) -> str:
        """Generate formatted explanation using LLM."""
        prompt = self._build_explanation_prompt(question_data, reasoning_text)
        print(f"LLM processing prompt: {prompt}")
        
        explanation = llm_provider.generate_text(prompt, max_tokens=800)
        
        if not explanation:
            self.logger.warning("LLM generation failed, using fallback")
            explanation = self._generate_fallback_explanation(question_data, reasoning_text)
        
        print(f"LLM processing explanation: {explanation}")
        return explanation
        
    
    def _build_explanation_prompt(self, question_data: Dict[str, Any], 
                                reasoning_text: str) -> str:
        """Build prompt for LLM explanation generation."""
        
        question_text = question_data["question_text"]
        options = question_data["options"]
        correct_answer = question_data["correct_answer"]
        subject = question_data["subject"]
        
        # Format options
        options_text = "\n".join([f"{chr(65+i)}. {opt}" for i, opt in enumerate(options)])
        
        prompt = f"""Create a clear, educational explanation for this CAT {subject} question.

**Question:**
{question_text}

**Options:**
{options_text}

**Correct Answer:** {correct_answer}

**Additional Context:**
{reasoning_text if reasoning_text else "Use standard problem-solving approach for this type of question."}

**Instructions:**
1. Provide a step-by-step solution that's easy to follow
2. Explain the reasoning behind each step
3. Make it suitable for slideshow narration (clear, engaging)
4. Include why other options are incorrect if relevant
5. Keep the explanation concise but thorough
6. Use simple language that students can understand

Format your response with clear sections and bullet points where appropriate."""
        
        return prompt
    
    def _generate_fallback_explanation(self, question_data: Dict[str, Any], 
                                     reasoning_text: str) -> str:
        """Generate basic explanation when LLM fails."""
        question_text = question_data["question_text"]
        options = question_data["options"]
        correct_answer = question_data["correct_answer"]
        subject = question_data["subject"]
        
        options_text = "\n".join([f"{chr(65+i)}. {opt}" for i, opt in enumerate(options)])
        
        explanation = f"""# {subject} Question Explanation

## Question
{question_text}

## Answer Options
{options_text}

## Correct Answer: {correct_answer}

## Solution Approach
{reasoning_text if reasoning_text else "Follow systematic problem-solving steps for this question type."}

## Key Points
- Analyze the question carefully
- Apply relevant concepts
- Eliminate incorrect options
- Verify your answer

*Note: This is a basic explanation. For detailed step-by-step solutions, please configure an LLM API key.*
"""
        
        return explanation