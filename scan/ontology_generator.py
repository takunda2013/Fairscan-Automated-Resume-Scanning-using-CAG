import os
from django.conf import settings
from .pdf_ontology_text import EnhancedOntologyConverter

class OntologyGenerator:
    def __init__(self, media_root=None, media_url=None):
        """
        Initialize with optional Django media paths.
        If not provided, defaults to Django settings or can be used standalone.
        """
        self.media_root = media_root or getattr(settings, 'MEDIA_ROOT', '')
        self.media_url = media_url or getattr(settings, 'MEDIA_URL', '')

        # Ensure folders exist
        os.makedirs('C:/Fairscan/takundajori/mysite/media/document_templates', exist_ok=True)
        os.makedirs('C:/Fairscan/takundajori/mysite/media/generated', exist_ok=True)

        print("Folders created. Now add 'template.pdf' to document_templates/")

        
        self.converter = EnhancedOntologyConverter()

    def generate_ontology(self, pdf_path=None, output_filename=None):
        """
        Main generation method that can be called from anywhere.
        
        Args:
            pdf_path: Absolute path to PDF (if None, uses default template path)
            company_name: Name to use in ontology
            output_filename: Custom output filename (optional)
        
        Returns:
            Tuple: (success: bool, result: dict)
                  result contains either download_url or error message
        """
        try:
            # Set default paths if not provided
            if pdf_path is None:
                pdf_path = os.path.join(self.media_root, 'document_templates', 'template.pdf')
            
            output_filename = output_filename or 'my_ontology.txt'
            output_path = os.path.join(self.media_root, 'generated', output_filename)
            
            # Ensure directories exist
            os.makedirs(os.path.dirname(pdf_path), exist_ok=True)
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            
            # Perform conversion
            success = self.converter.convert_pdf_to_ontology(
                pdf_path=pdf_path,
                output_path=output_path,
            )

            
            
            if success:
                download_url = os.path.join(self.media_url, 'generated', output_filename)
                return True, {'download_url': download_url}
            return False, {'message': 'Conversion failed'}
            
        except Exception as e:
            return False, {'message': str(e)}