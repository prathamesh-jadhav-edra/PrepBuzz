"""Extensible flow engine for processing pipelines."""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, Type
from dataclasses import dataclass, asdict
from loguru import logger
from pathlib import Path
import json


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
        """Initialize flow with name and configuration."""
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


class FlowRegistry:
    """Registry for managing available flows."""
    
    def __init__(self):
        """Initialize empty registry."""
        self._flows: Dict[str, Type[BaseFlow]] = {}
        self._instances: Dict[str, BaseFlow] = {}
    
    def register(self, name: str, flow_class: Type[BaseFlow]):
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
            print(f"Flow instance created: {flow_instance}")
            print(f"Flow instance config: {config}")
            print(f"Flow instance name: {name}")
            print(f"Flow instance flows: {self._flows[name]}")
            if config is None:  # Cache only default instances
                self._instances[name] = flow_instance
            return flow_instance
            
        except Exception as e:
            logger.error(f"Failed to create flow {name}: {e}")
            return None
    
    def get_available_flows(self) -> List[str]:
        """Get list of registered flow names."""
        return list(self._flows.keys())


class FlowEngine:
    """Main engine for executing flow pipelines."""
    
    def __init__(self, registry: FlowRegistry = None):
        """Initialize flow engine."""
        self.registry = registry or FlowRegistry()
        self.execution_log: List[Dict[str, Any]] = []
    
    def execute_pipeline(self, flow_names: List[str], initial_data: Dict[str, Any] = None, 
                        flow_configs: Dict[str, Dict[str, Any]] = None) -> FlowResult:
        """Execute a pipeline of flows sequentially."""
        if not flow_names:
            return FlowResult(success=False, data={}, error="No flows specified")
        
        current_data = initial_data or {}
        flow_configs = flow_configs or {}
        pipeline_results = []
        
        logger.info(f"Starting pipeline with {len(flow_names)} flows")
        
        for flow_name in flow_names:
            # Get flow configuration
            config = flow_configs.get(flow_name)
            
            # Create flow instance
            flow = self.registry.create_flow(flow_name, config)
            if not flow:
                error_msg = f"Failed to create flow: {flow_name}"
                logger.error(error_msg)
                return FlowResult(
                    success=False, 
                    data=current_data, 
                    error=error_msg,
                    metadata={"completed_flows": pipeline_results}
                )
            
            # Execute flow
            try:
                result = flow.execute(current_data)
                pipeline_results.append({
                    "flow": flow_name,
                    "success": result.success,
                    "error": result.error
                })
                
                if not result.success:
                    logger.error(f"Pipeline stopped at flow {flow_name}: {result.error}")
                    return FlowResult(
                        success=False,
                        data=current_data,
                        error=f"Flow {flow_name} failed: {result.error}",
                        metadata={"completed_flows": pipeline_results}
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
                    metadata={"completed_flows": pipeline_results}
                )
        
        logger.info("Pipeline completed successfully")
        return FlowResult(
            success=True,
            data=current_data,
            metadata={"completed_flows": pipeline_results}
        )
    
    def execute_single_flow(self, flow_name: str, input_data: Dict[str, Any] = None,
                           config: Dict[str, Any] = None) -> FlowResult:
        """Execute a single flow."""
        flow = self.registry.create_flow(flow_name, config)
        if not flow:
            return FlowResult(
                success=False,
                data=input_data or {},
                error=f"Flow not found: {flow_name}"
            )
        
        return flow.execute(input_data or {})
    
    def get_execution_log(self) -> List[Dict[str, Any]]:
        """Get execution log."""
        return self.execution_log.copy()
    
    def clear_execution_log(self):
        """Clear execution log."""
        self.execution_log.clear()


# Global registry and engine instances
flow_registry = FlowRegistry()
flow_engine = FlowEngine(flow_registry)


def register_flow(name: str):
    """Decorator for registering flows."""
    def decorator(flow_class: Type[BaseFlow]):
        flow_registry.register(name, flow_class)
        return flow_class
    return decorator