from typing import Dict, Any, Union, Optional
from .input.adapter import InputAdapter
from .processing.classifier import Classifier
from .processing.structure import StructureParser
from .processing.interpreter import Interpreter
from .processing.risk import RiskEngine
from .output.presenter import Presenter

class SemanticPipeline:
    """
    The main orchestration class for the Semantic Signature Decoder.
    Flow: Input -> Adapter -> IR -> Classifier -> Structure -> Interpreter -> Risk -> Output
    """
    
    def __init__(self):
        self.interpreter = Interpreter()

    def process(self, raw_data: Union[str, Dict[str, Any]], origin: Optional[str] = None) -> Dict[str, Any]:
        # 1. Input Layer
        # Pass origin to adapter for DApp identification
        ir = InputAdapter.adapt(raw_data, origin=origin)
        
        # 2. Processing Layer
        # a. Classify
        ir = Classifier.classify(ir)
        
        # b. Structure Extraction
        structure = StructureParser.parse(ir)
        
        # c. Semantic Interpretation (Logic + LLM)
        # Pass IR to interpreter so it can enrich structure with semantic information
        description = self.interpreter.interpret(structure, ir)
        
        # d. Risk Assessment
        risk = RiskEngine.assess(ir, structure)
        
        # 3. Output Layer
        result = Presenter.format(ir, structure, risk, description)
        
        return result

