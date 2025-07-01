# urls.py
from django.urls import path
from . import views
from . import dashboard_views

urlpatterns = [
    path('', views.my_home, name="my_home"),
    path('upload/', views.upload_files, name='upload_files'),  # URL for file upload
    path('ontology/', views.uploadOntology, name='uploadOntology'),

    path('get-documents/', views.get_documents, name='get_documents'),

 # New path for document deletion
    path('delete-document/<int:document_id>/', views.delete_document, name='delete_document'),


    path('delete-all-documents/', views.delete_all_documents, name='delete_all_documents'),
    # Add other URLs as needed

    #view document
    path('document/<int:doc_id>/', views.document_viewer, name='document-viewer'),
    path('serve-document/<int:file_id>/file', views.serve_file, name='serve_file'),

    #view template
    path('document/fairscanTemplate/', views.template_document_viewer, name='template_document-viewer'),

    #audit dashboard
    path('dashboard/', dashboard_views.my_dashboard, name="my_dashboard"),
    
    path('processed-document-viewer/<int:doc_id>/', views.processed_document_viewer, name='view_pdf'),
    path('serve-processed-document/<int:doc_id>/', views.serve_processed_file, name='serve_processed_file'),


    # path('generate_pdf_api/', views.generate_pdf_api, name='generate_pdf_api'),
    path('get_documents_api/', views.get_documents_api, name='get_documents_api'),

    #===============================================================================
    path('process-batch/', views.process_resume_batch, name='process_batch'),
    # path('check-progress/<str:task_id>/', views.check_batch_progress, name='check_progress'),



]

