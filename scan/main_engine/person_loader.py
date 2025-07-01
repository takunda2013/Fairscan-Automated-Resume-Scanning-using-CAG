from pathlib import Path

from llama_cpp import Optional

class PersonDataLoader:
    def __init__(self, data_file: Optional[str] = None):
        self.data_file = Path(data_file) if data_file else None
        self.person_data = ""
        self.full_context = ""
        if self.data_file:
            self.load_data()
    
    def load_data(self):
        """Load person data from text file"""
        if not self.data_file or not self.data_file.exists():
            print(f"Info: No additional data file provided or file not found.")
            return
        
        try:
            with open(self.data_file, 'r', encoding='utf-8') as f:
                self.person_data = f.read().strip()
            
            self.full_context = self._create_base_context()
            
            print(f"✓ Loaded {len(self.person_data)} characters of additional data")
            
        except Exception as e:
            print(f"Error loading data file: {e}")
    
    def _create_base_context(self) -> str:
        """Create comprehensive base context for caching"""
        max_context_length = 3000
        
        if len(self.person_data) <= max_context_length:
            return self.person_data
        
        return self.person_data[:max_context_length]
    
    def get_base_context(self) -> str:
        """Get the base context for KV caching"""
        return self.full_context
    # ... (rest of PersonDataLoader implementation from original code)