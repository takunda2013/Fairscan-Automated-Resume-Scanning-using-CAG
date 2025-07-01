"""
FairScan Resume Grading System
"""
from .grading_system import FairScanGradingSystem
from .ontology_loader import FairScanOntologyLoader
from .person_loader import PersonDataLoader

__all__ = [
    'FairScanGradingSystem',
    'FairScanOntologyLoader',
    'PersonDataLoader'
]

__version__ = "1.0.0"