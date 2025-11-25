from typing import Dict, Any, Union, Optional
from .input.adapter import InputAdapter
from .processing.classifier import Classifier
from .processing.structure import StructureParser
from .processing.interpreter import Interpreter
from .processing.risk import RiskEngine
from .output.presenter import Presenter
from .utils.logger import Logger
from .utils.exceptions import SignatureDecoderError, ValidationError, ParsingError

class SemanticPipeline:
    """
    The main orchestration class for the Semantic Signature Decoder.
    Flow: Input -> Adapter -> IR -> Classifier -> Structure -> Interpreter -> Risk -> Output
    """
    
    def __init__(self):
        self.interpreter = Interpreter()
        self.logger = Logger.get_logger("SemanticPipeline")

    def process(self, raw_data: Union[str, Dict[str, Any]], origin: Optional[str] = None) -> Dict[str, Any]:
        """
        Process signature data through the semantic pipeline.
        
        Args:
            raw_data: Raw signature data (string or dict)
            origin: DApp origin URL (optional)
            
        Returns:
            Processed result dictionary
            
        Raises:
            SignatureDecoderError: If processing fails
        """
        try:
            self.logger.debug(f"Processing signature data from origin: {origin}")
            
            # 1. Input Layer
            # Pass origin to adapter for DApp identification
            try:
                ir = InputAdapter.adapt(raw_data, origin=origin)
                self.logger.debug(f"Input adapted: signature_type={ir.signature_type}")
            except Exception as e:
                self.logger.error(f"Input adaptation failed: {e}")
                raise ValidationError(f"Failed to adapt input: {e}") from e
            
            # 2. Processing Layer
            # a. Classify
            try:
                ir = Classifier.classify(ir)
                self.logger.debug(f"Classified: action_type={ir.action_type}")
            except Exception as e:
                self.logger.error(f"Classification failed: {e}")
                raise ParsingError(f"Failed to classify signature: {e}") from e
            
            # b. Structure Extraction
            try:
                structure = StructureParser.parse(ir)
                self.logger.debug(f"Structure parsed: actor={structure.actor.description}")
            except Exception as e:
                self.logger.error(f"Structure parsing failed: {e}")
                raise ParsingError(f"Failed to parse structure: {e}") from e
            
            # c. Semantic Interpretation (Logic + LLM)
            # Pass IR to interpreter so it can enrich structure with semantic information
            try:
                description = self.interpreter.interpret(structure, ir)
                self.logger.debug(f"Interpreted: {description[:100]}...")
            except Exception as e:
                self.logger.warning(f"Interpretation failed, using fallback: {e}")
                description = f"Perform {structure.action.description} on {structure.target_object.description}."
            
            # d. Risk Assessment
            try:
                risk = RiskEngine.assess(ir, structure)
                self.logger.debug(f"Risk assessed: level={risk.level}, reasons={len(risk.reasons)}")
            except Exception as e:
                self.logger.warning(f"Risk assessment failed, using default: {e}")
                from .processing.risk import RiskAssessment
                risk = RiskAssessment(level="medium", reasons=["Risk assessment unavailable"])
            
            # 3. Output Layer
            try:
                result = Presenter.format(ir, structure, risk, description)
                self.logger.info(f"Processing completed successfully: action_type={ir.action_type}, risk={risk.level}")
                return result
            except Exception as e:
                self.logger.error(f"Output formatting failed: {e}")
                raise SignatureDecoderError(f"Failed to format output: {e}") from e
                
        except SignatureDecoderError:
            # Re-raise our custom exceptions
            raise
        except Exception as e:
            # Wrap unexpected exceptions
            self.logger.error(f"Unexpected error in pipeline: {e}", exc_info=True)
            raise SignatureDecoderError(f"Unexpected error: {e}") from e

