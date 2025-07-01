from ontology_generator import OntologyGenerator

# Standalone usage (no Django)
generator = OntologyGenerator(
    media_root='C:/Fairscan/takundajori/mysite/media',
    media_url='/media/'  # Only needed if generating URLs
)

success, result = generator.generate_ontology(
    pdf_path='C:/Fairscan/takundajori/mysite/media/document_templates/template.pdf',
    output_filename='ontology.txt'
)

if success:
    print("Ontology generated at:", result['download_url'])
else:
    print("Failed:", result['message'])