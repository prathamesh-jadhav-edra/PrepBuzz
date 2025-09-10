"""Unified Flow Engine - Simple, clean implementation combining standard and agentic execution."""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, Type
from dataclasses import dataclass
from loguru import logger
import uuid
import time


@dataclass
class FlowResult:
    """Result of a flow execution."""
    success: bool
    data: Dict[str, Any]
    error: Optional[str] = None
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


class BaseFlow(ABC):
    """Abstract base class for all flows."""

    def __init__(self, name: str, config: Dict[str, Any] = None):
        self.name = name
        self.config = config or {}
        self.logger = logger.bind(flow=name)

    @abstractmethod
    def execute(self, input_data: Dict[str, Any]) -> FlowResult:
        """Execute the flow with input data."""
        pass

    def validate_input(self, input_data: Dict[str, Any], required_keys: List[str]) -> bool:
        """Validate that required keys are present in input data."""
        missing_keys = [key for key in required_keys if key not in input_data]
        if missing_keys:
            self.logger.error(f"Missing required keys: {missing_keys}")
            return False
        return True

    def log_start(self):
        """Log flow start."""
        self.logger.info(f"Starting flow: {self.name}")

    def log_end(self, result: FlowResult):
        """Log flow completion."""
        status = "SUCCESS" if result.success else "FAILED"
        self.logger.info(f"Flow {self.name} completed with status: {status}")
        if result.error:
            self.logger.error(f"Flow error: {result.error}")


class SimpleAgent:
    """Simplified agent for intelligent processing."""
    
    def __init__(self, name: str, capabilities: List[str]):
        self.name = name
        self.capabilities = capabilities
        self.logger = logger.bind(agent=name)
    
    def analyze_content(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze content and provide insights."""
        question = data.get("question", {})
        subject = question.get("subject", "Unknown")
        
        # Simple analysis
        complexity = self._assess_complexity(question)
        strategy = self._recommend_strategy(complexity, subject)
        
        self.logger.info(f"Content analysis: complexity={complexity:.2f}, strategy={strategy}")
        
        return {
            "complexity_score": complexity,
            "recommended_strategy": strategy,
            "confidence": 0.85,
            "insights": f"Analyzed {subject} question with {complexity:.0%} complexity"
        }
    
    def plan_strategy(self, analysis: Dict[str, Any], data: Dict[str, Any]) -> Dict[str, Any]:
        """Plan optimal processing strategy."""
        strategy = analysis.get("recommended_strategy", "balanced")
        complexity = analysis.get("complexity_score", 0.5)
        
        # Strategy planning
        pipeline_config = self._optimize_pipeline(strategy, complexity)
        
        self.logger.info(f"Strategy planning: {strategy} approach with optimization")
        
        return {
            "strategy": strategy,
            "pipeline_config": pipeline_config,
            "confidence": 0.90,
            "estimated_time": 45 + (complexity * 30)  # Basic time estimation
        }
    
    def execute_pipeline(self, strategy: Dict[str, Any], flows: List[str], data: Dict[str, Any], engine) -> Dict[str, Any]:
        """Execute pipeline with intelligent monitoring."""
        start_time = time.time()
        strategy_name = strategy.get("strategy", "standard")
        pipeline_config = strategy.get("pipeline_config", {})
        
        self.logger.info(f"Executing pipeline with {strategy_name} strategy")
        
        # Execute flows with config optimization
        try:
            result = engine._execute_standard_pipeline(flows, data, pipeline_config)
            execution_time = time.time() - start_time
            
            return {
                "execution_result": result,
                "execution_time": execution_time,
                "strategy_used": strategy_name,
                "success": result.success,
                "confidence": 0.88 if result.success else 0.3
            }
        except Exception as e:
            return {
                "execution_result": FlowResult(False, data, str(e)),
                "execution_time": time.time() - start_time,
                "strategy_used": strategy_name,
                "success": False,
                "confidence": 0.0,
                "error": str(e)
            }
    
    def _assess_complexity(self, question: Dict[str, Any]) -> float:
        """Assess question complexity (0.0 to 1.0)."""
        text = question.get("question_text", "")
        subject = question.get("subject", "")
        
        # Simple heuristics
        complexity = 0.3  # base complexity
        
        # Text length factor
        if len(text) > 200:
            complexity += 0.2
        
        # Subject complexity
        if subject in ["Quant", "Logic"]:
            complexity += 0.3
        elif subject == "DI":
            complexity += 0.2
        
        # Keywords indicating complexity
        complex_keywords = ["calculate", "analyze", "determine", "derive", "prove"]
        if any(keyword in text.lower() for keyword in complex_keywords):
            complexity += 0.2
        
        return min(complexity, 1.0)
    
    def _recommend_strategy(self, complexity: float, subject: str) -> str:
        """Recommend processing strategy based on complexity."""
        if complexity > 0.7:
            return "quality"  # High quality for complex questions
        elif complexity < 0.4:
            return "performance"  # Fast processing for simple questions
        else:
            return "balanced"  # Balanced approach for medium complexity
    
    def _optimize_pipeline(self, strategy: str, complexity: float) -> Dict[str, Any]:
        """Optimize pipeline configuration based on strategy."""
        config = {}
        
        if strategy == "quality":
            config = {
                "reasoning_extraction": {"depth": "enhanced", "search_timeout": 15},
                "llm_processing": {"temperature": 0.2, "max_tokens": 1000}
            }
        elif strategy == "performance":
            config = {
                "reasoning_extraction": {"depth": "basic", "search_timeout": 5},
                "llm_processing": {"temperature": 0.7, "max_tokens": 500}
            }
        else:  # balanced
            config = {
                "reasoning_extraction": {"depth": "standard", "search_timeout": 10},
                "llm_processing": {"temperature": 0.5, "max_tokens": 750}
            }
        
        return config


class UnifiedFlowEngine:
    """Unified flow engine supporting both standard and agentic execution."""

    def __init__(self):
        self._flows: Dict[str, Type[BaseFlow]] = {}
        self._instances: Dict[str, BaseFlow] = {}
        self.agent = SimpleAgent("intelligent_coordinator", ["analysis", "strategy", "execution"])
        logger.info("UnifiedFlowEngine initialized")

    def register_flow(self, name: str, flow_class: Type[BaseFlow]):
        """Register a flow class."""
        self._flows[name] = flow_class
        logger.info(f"Registered flow: {name}")

    def create_flow(self, name: str, config: Dict[str, Any] = None) -> Optional[BaseFlow]:
        """Create flow instance."""
        if name not in self._flows:
            logger.error(f"Flow not found: {name}")
            return None

        # Use cached instance if available and no specific config provided
        if name in self._instances and config is None:
            return self._instances[name]

        # Create new instance
        try:
            flow_instance = self._flows[name](name, config)
            if config is None:  # Cache only default instances
                self._instances[name] = flow_instance
            return flow_instance
        except Exception as e:
            logger.error(f"Failed to create flow {name}: {e}")
            return None

    def get_available_flows(self) -> List[str]:
        """Get list of registered flow names."""
        return list(self._flows.keys())

    def execute_pipeline(
        self,
        flow_names: List[str],
        initial_data: Dict[str, Any] = None,
        flow_configs: Dict[str, Dict[str, Any]] = None,
        agentic: bool = False
    ) -> FlowResult:
        """Execute pipeline with optional agentic intelligence."""
        
        if agentic:
            return self._execute_agentic_pipeline(flow_names, initial_data, flow_configs)
        else:
            return self._execute_standard_pipeline(flow_names, initial_data, flow_configs)

    def _execute_standard_pipeline(
        self,
        flow_names: List[str],
        initial_data: Dict[str, Any] = None,
        flow_configs: Dict[str, Dict[str, Any]] = None,
    ) -> FlowResult:
        """Execute standard pipeline (original behavior)."""
        
        if not flow_names:
            return FlowResult(success=False, data={}, error="No flows specified")

        current_data = initial_data or {}
        flow_configs = flow_configs or {}
        pipeline_results = []

        logger.info(f"Starting standard pipeline with {len(flow_names)} flows")

        for flow_name in flow_names:
            # Get flow configuration
            config = flow_configs.get(flow_name)

            # Create flow instance
            flow = self.create_flow(flow_name, config)
            if not flow:
                error_msg = f"Failed to create flow: {flow_name}"
                logger.error(error_msg)
                return FlowResult(
                    success=False,
                    data=current_data,
                    error=error_msg,
                    metadata={"completed_flows": pipeline_results},
                )

            # Execute flow
            try:
                result = flow.execute(current_data)
                pipeline_results.append({
                    "flow": flow_name,
                    "success": result.success,
                    "error": result.error,
                })

                if not result.success:
                    logger.error(f"Pipeline stopped at flow {flow_name}: {result.error}")
                    return FlowResult(
                        success=False,
                        data=current_data,
                        error=f"Flow {flow_name} failed: {result.error}",
                        metadata={"completed_flows": pipeline_results},
                    )

                # Merge result data into current data for next flow
                current_data.update(result.data)

            except Exception as e:
                error_msg = f"Exception in flow {flow_name}: {str(e)}"
                logger.error(error_msg)
                pipeline_results.append({
                    "flow": flow_name, 
                    "success": False, 
                    "error": error_msg
                })
                return FlowResult(
                    success=False,
                    data=current_data,
                    error=error_msg,
                    metadata={"completed_flows": pipeline_results},
                )

        logger.info("Standard pipeline completed successfully")
        return FlowResult(
            success=True,
            data=current_data,
            metadata={"completed_flows": pipeline_results},
        )

    def _execute_agentic_pipeline(
        self,
        flow_names: List[str],
        initial_data: Dict[str, Any] = None,
        flow_configs: Dict[str, Dict[str, Any]] = None,
    ) -> FlowResult:
        """Execute pipeline with intelligent agentic coordination."""
        
        session_id = str(uuid.uuid4())
        current_data = initial_data or {}
        
        logger.info(f"Starting agentic pipeline execution {session_id}")
        
        try:
            # Phase 1: Content Analysis
            analysis = self.agent.analyze_content(current_data)
            
            # Phase 2: Strategy Planning
            strategy = self.agent.plan_strategy(analysis, current_data)
            
            # Phase 3: Intelligent Pipeline Execution
            execution_result = self.agent.execute_pipeline(
                strategy, flow_names, current_data, self
            )
            
            # Prepare enhanced result
            final_result = execution_result["execution_result"]
            
            # Add agentic insights to metadata
            if final_result.metadata is None:
                final_result.metadata = {}
                
            final_result.metadata.update({
                "session_id": session_id,
                "agent_analysis": analysis,
                "strategy_used": strategy,
                "execution_time": execution_result["execution_time"],
                "confidence": execution_result["confidence"],
                "agentic_mode": True
            })
            
            logger.info(f"Agentic pipeline completed with {execution_result['confidence']:.0%} confidence")
            return final_result
            
        except Exception as e:
            logger.error(f"Agentic pipeline execution failed: {e}")
            return FlowResult(
                success=False,
                data=current_data,
                error=f"Agentic pipeline error: {str(e)}",
                metadata={"session_id": session_id, "agentic_mode": True},
            )

    def get_status(self) -> Dict[str, Any]:
        """Get engine status."""
        return {
            "available_flows": self.get_available_flows(),
            "cached_instances": len(self._instances),
            "agent_capabilities": self.agent.capabilities,
        }


# Create decorator for flow registration
def register_flow(name: str):
    """Decorator for registering flows."""
    def decorator(flow_class: Type[BaseFlow]):
        unified_engine.register_flow(name, flow_class)
        return flow_class
    return decorator


# Global engine instance
unified_engine = UnifiedFlowEngine()