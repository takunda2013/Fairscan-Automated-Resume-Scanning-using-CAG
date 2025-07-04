# views.py
import base64
import datetime
import glob
from io import BytesIO
import mimetypes
from multiprocessing.pool import AsyncResult
from django.shortcuts import render
from django.http import FileResponse, Http404, HttpResponse, HttpResponseBadRequest, JsonResponse
import os
from django.conf import settings
from django.utils import timezone
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import ensure_csrf_cookie

from .ontology_generator import OntologyGenerator

from .task import long_running_task, process_resume_chain

# from .ai_models.cag import startPipeLine
from .models import  OntologyDocument, ProcessedResumeText, ProcessingBatch, UploadedFile
from .utils import extract_text, create_prompt, generate_pdf, increment_number
from django.shortcuts import render, get_object_or_404
from .models import UploadedFile  # adjust according to your app’s structure
from django.shortcuts import render, get_object_or_404
from .models import UploadedFile  # adjust according to your app’s structure
from django.contrib.auth.decorators import login_required
from django.views.decorators.cache import never_cache
from datetime import datetime
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter

@login_required
@never_cache
def my_home(request):

     # Only create task if not already created
    task_id = request.session.get('current_task_id')
    
    if not task_id:
        result = long_running_task.delay("hello", "world")
        request.session['current_task_id'] = result.id
        task_id = result.id
    
    from celery.result import AsyncResult

    result = AsyncResult(task_id)
    
    print("TASK ID:", task_id)
    print("TASK STATE:", result.state)
    
    if result.ready():
        print("ACTUAL RESULT:", result.result)
        # Clear the session after getting result
        if 'current_task_id' in request.session:
            del request.session['current_task_id']
    else:
        print("Task is still running...")

    # return render(request, 'resume_processor/resume_list.html', {'resumes': resumes})
    return render(request, 'index.html')

# def handle_uploaded_file(file):
#     file_path = os.path.join(settings.MEDIA_ROOT, 'uploads', file.name)
#     with open(file_path, 'wb+') as destination:
#         for chunk in file.chunks():
#             destination.write(chunk)
#     return file_path

#===================================================================================================================================

@login_required
def document_viewer(request, doc_id):
    file = get_object_or_404(UploadedFile, pk=doc_id)
    mime_type = 'application/pdf' if file.file_type == 'pdf' else 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
    return render(request, 'docviewer.html', {'file': file, 'mime_type': mime_type})

@login_required
def template_document_viewer(request):
    """
    View for retrieving a document template from server directory and displaying it.
    Returns the single document found in the template directory.
    """
    # Define the directory where the template is stored
    template_dir = os.path.join(settings.MEDIA_ROOT,  'document_templates')
    
    # Check if directory exists
    if not os.path.exists(template_dir):
        raise Http404("Template directory not found")
    
    # Get the first file in the directory
    try:
        files = [f for f in os.listdir(template_dir) if os.path.isfile(os.path.join(template_dir, f))]
        if not files:
            raise Http404("No template document found in the directory")
        
        # Use the first file (since there should only be one)
        template_name = files[0]
        template_path = os.path.join(template_dir, template_name)
        
    except (FileNotFoundError, IndexError):
        raise Http404("Template document not found")
    
    # Determine the MIME type based on file extension
    file_ext = os.path.splitext(template_name)[1].lower()
    if file_ext == '.pdf':
        mime_type = 'application/pdf'
    elif file_ext in ['.docx', '.doc']:
        mime_type = 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
    else:
        mime_type = 'application/octet-stream'  # Default mime type
    
    # Read the template file
    with open(template_path, 'rb') as f:
        file_data = f.read()
    
    # Create a response with the file content
    response = HttpResponse(file_data, content_type=mime_type)
    response['Content-Disposition'] = f'inline; filename="{template_name}"'
    
    return response

# @login_required
# def serve_file(request, doc_id):
#     file = get_object_or_404(UploadedFile, pk=doc_id)
#     response = FileResponse(file.file.open(), filename=file.file.name)
    
#     print("NORMAL SERVING")
#     # Remove X-Frame-Options header to allow embedding
#     if file.file_type == 'pdf':
#         response['X-Frame-Options'] = 'SAMEORIGIN'  # Or you can use 'ALLOWALL'
    
#     return response

#===================================================================================================================================


@login_required
@require_http_methods(["POST"])
def upload_files(request):
    if request.FILES.getlist('files'):
        files = request.FILES.getlist('files')
        uploaded_files = []
        
        for f in files:
            # Validate file type
            ext = os.path.splitext(f.name)[1].lower()
            if ext not in ['.docx', '.pdf']:
                return JsonResponse({
                    'error': f'Unsupported file type: {ext}',
                    'allowed_types': ['docx', 'pdf']
                }, status=400)
            
            # Create and save model instance
            uploaded_file = UploadedFile(
            file=f,
            uploaded_by = request.user)
            uploaded_file.save()  # This will trigger save() with auto-detected file_type
            
            # ... rest of your processing logic ...
    # Extract text from the uploaded file

            extracted_text, person_identifiers =  create_prompt(handle_resume_file(f))

            print(extracted_text);
      
        
        return JsonResponse({
            'message': 'Files uploaded successfully',
            'files': [
                {
                    'id': file.id,
                    'name': os.path.basename(file.file.name),
                    'file_type': file.file_type,
                    'upload_date': file.date_uploaded.isoformat()
                } for file in uploaded_files
            ]
        })
    return JsonResponse({'error': 'No files received'}, status=400)


@login_required
def serve_file(request, file_id):
    print("NORMAL SERVING")

    uploaded_file = get_object_or_404(UploadedFile, pk=file_id)
    return FileResponse(uploaded_file.file.open(), filename=uploaded_file.file.name)

@login_required
def view_file(request, file_id):
    uploaded_file = get_object_or_404(UploadedFile, pk=file_id)
    
    if not uploaded_file.is_supported_type():
        return HttpResponseBadRequest("Unsupported file format")
    
    return render(request, 'file_viewer.html', {
        'file': uploaded_file,
        'mime_type': 'application/pdf' if uploaded_file.file_type == 'pdf' else 
                     'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
    })

#===================================================================================================================================


def handle_resume_file(file):
    # Remove 'uploads/' prefix if it exists
    file_path = os.path.join(settings.MEDIA_ROOT, 'uploads', file.name)

    print(file_path)
     # Ensure directory exists
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    
    # Write the file and ensure it's properly closed
    with open(file_path, 'wb') as destination:  # Remove the '+' - just write mode
        for chunk in file.chunks():
            destination.write(chunk)
    
    # Verify the file was written correctly
    if os.path.exists(file_path) and os.path.getsize(file_path) > 0:
        print(f"File successfully written: {os.path.getsize(file_path)} bytes")
    else:
        print(f"Warning: File appears empty or doesn't exist")
    
    return file_path


def handle_ontology_file(file):
    ontology_dir = os.path.join(settings.MEDIA_ROOT, 'ontology')
    
    # Create directory if it doesn't exist
    os.makedirs(ontology_dir, exist_ok=True)
    
    # Remove all existing files in the ontology directory
    existing_files = glob.glob(os.path.join(ontology_dir, '*'))
    for existing_file in existing_files:
        try:
            if os.path.isfile(existing_file):
                os.remove(existing_file)
                print(f"Removed existing file: {existing_file}")
        except OSError as e:
            print(f"Error removing file {existing_file}: {e}")
    
    # Save the new file
    file_path = os.path.join(ontology_dir, file.name)
    with open(file_path, 'wb+') as destination:
        for chunk in file.chunks():
            destination.write(chunk)
    
    print(f"Saved new ontology file: {file_path}")
    return file_path

@login_required
def uploadOntology(request):
    if request.method == 'POST' and request.FILES.getlist('files'):
        file = request.FILES.get('files')

        print(file.name)
        file_path = handle_ontology_file(file)

        # Extract text from the uploaded file
        extracted_text = extract_text(file_path)
      
        print(extracted_text)

        # Save to database - get or create single document instance
        try:
            # Try to get existing document (assuming one document per system)
            ontology_doc, created = OntologyDocument.objects.get_or_create(
                defaults={
                    'filename': file.name,
                    'file_path': file_path,
                    'extracted_text': extracted_text,
                    'uploaded_by': request.user
                }
            )
            
            # If document already exists, update it
            if not created:
                ontology_doc.filename = file.name
                ontology_doc.file_path = file_path
                ontology_doc.extracted_text = extracted_text
                ontology_doc.uploaded_by = request.user
                ontology_doc.save()
                
            action = "created" if created else "updated"
            print(f"Ontology document {action} successfully")
            
            #generated the ontology document txt 
            #saved in the media in /generated
            generator = OntologyGenerator()
    
            success, result = generator.generate_ontology(
                pdf_path=file_path,
                output_filename='ontology.txt'
            )

            # print("SUCCESS ", file_path, " DONE ", success)
            
        except Exception as e:
            print(f"Error saving ontology document: {str(e)}")
            return JsonResponse({'message': 'Error saving document to database'}, status=500)

        return JsonResponse({'message': 'Files uploaded and processed successfully'})

    else:
        return JsonResponse({'message': 'No files uploaded'}, status=400)
    


@login_required
def get_documents(request):
    """
    View to retrieve all uploaded documents and return them as JSON
    for the frontend to render
    """
    # startPipeLine()

    if request.method == 'GET':
        try:
            # Get all uploaded files, ordered by upload date (newest first)
            uploaded_files = UploadedFile.objects.all().order_by('-date_uploaded')
            
            # Format the datetime in the Zimbabwe timezone
            files_data = []
            for file in uploaded_files:
                # Get the filename from the path
                filename = file.file.name.split('/')[-1]
                
                # Format the datetime properly for the Zimbabwe timezone
                # Make sure the datetime is aware of the timezone
                upload_datetime = file.date_uploaded
                if timezone.is_naive(upload_datetime):
                    upload_datetime = timezone.make_aware(upload_datetime)
                
                # Format for display in Zimbabwe timezone
                zw_datetime = upload_datetime.astimezone(timezone.get_current_timezone())
                
                files_data.append({
                    'id': file.id,
                    'name': filename,
                    'upload_date': zw_datetime.strftime('%Y-%m-%d'),
                    'upload_time': zw_datetime.strftime('%H:%M:%S'),
                    'upload_datetime': zw_datetime.isoformat(),
                    'file_type': file.file_type,
                    'scan_status': file.scan_status
                })
            
            return JsonResponse({
                'message': 'Documents retrieved successfully',
                'files': files_data,
                'timezone': settings.TIME_ZONE
            })
            
        except Exception as e:
            return JsonResponse({
                'message': f'Error retrieving documents: {str(e)}',
                'files': []
            }, status=500)
    
    # If not a GET request
    return JsonResponse({'message': 'Invalid request method'}, status=400)


@login_required
@require_http_methods(["DELETE"])
def delete_document(request, document_id):
    """
    View to delete a document by its ID
    """
    try:
        # Find the document by ID
        document = UploadedFile.objects.get(id=document_id)
        
        # Get the file path for physical deletion
        file_path = document.file.path
        
        # Delete the file from the filesystem if it exists
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
            except OSError as e:
                # Log the error but continue with database deletion
                print(f"Error deleting file from filesystem: {e}")
        
        # Store the filename for the response
        filename = document.file.name.split('/')[-1]
        
        # Delete the database record
        document.delete()
        
        return JsonResponse({
            'success': True,
            'message': f'Document "{filename}" successfully deleted',
            'document_id': document_id
        })
        
    except UploadedFile.DoesNotExist:
        return JsonResponse({
            'success': False,
            'message': f'Document with ID {document_id} not found'
        }, status=404)
    
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Error deleting document: {str(e)}'
        }, status=500)
    

@login_required   
@require_http_methods(["DELETE"])
def delete_all_documents(request):
    """
    View to delete all documents from the database and filesystem
    """
    try:
        # Get all documents
        documents = UploadedFile.objects.all()
        
        if not documents.exists():
            return JsonResponse({
                'success': True,
                'message': 'No documents found to delete',
                'deleted_count': 0
            })

        deleted_count = 0
        errors = []
        
        for document in documents:
            try:
                # Get the file path for physical deletion
                file_path = document.file.path
                
                # Delete the file from the filesystem if it exists
                if os.path.exists(file_path):
                    try:
                        os.remove(file_path)
                    except OSError as e:
                        errors.append(f"Error deleting file {document.file.name}: {str(e)}")
                
                # Delete the database record
                document.delete()
                deleted_count += 1
                
            except Exception as e:
                errors.append(f"Error deleting document {document.id}: {str(e)}")
                continue

        response_data = {
            'success': True,
            'message': f'Successfully deleted {deleted_count} documents',
            'deleted_count': deleted_count
        }
        
        if errors:
            response_data['errors'] = errors
            response_data['message'] = f'Deleted {deleted_count} documents with some errors'

        return JsonResponse(response_data)
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Error during mass deletion: {str(e)}'
        }, status=500)
    
@login_required
def document_view(request, document_id):
    document = get_object_or_404(UploadedFile, pk=document_id)
    return render(request, 'document_viewer.html', {'document_url': document.file.url})


#=================================================================PROCESSED RESUMES

# @login_required
# def generate_pdf(request):
#     """
#     Generate a PDF file, save it to the specified directory, and store its information in the database.
#     """
#     # Create PDF content using ReportLab
#     buffer = BytesIO()
#     pdf = canvas.Canvas(buffer, pagesize=letter)
    
#     # Add content to the PDF
#     pdf.setFont("Helvetica", 12)
#     pdf.drawString(100, 750, f"Generated PDF Document")
#     pdf.drawString(100, 730, f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
#     pdf.drawString(100, 710, f"Generated by: {request.user.username}")
    
#     # Add more content as needed
#     pdf.drawString(100, 650, "This is a sample PDF document generated by Django.")
    
#     # Save the PDF
#     pdf.save()
    
#     # Create PDF file name
#     timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
#     pdf_filename = f"document_{request.user.id}_{timestamp}.pdf"
    
#     # Define the directory path relative to MEDIA_ROOT
#     pdf_directory = os.path.join(settings.MEDIA_ROOT, 'pdf_documents')
    
#     # Create directory if it doesn't exist
#     if not os.path.exists(pdf_directory):
#         os.makedirs(pdf_directory)
    
#     # Complete file path
#     file_path = os.path.join(pdf_directory, pdf_filename)
    
#     # Write PDF to file
#     with open(file_path, 'wb') as f:
#         f.write(buffer.getvalue())
    
#     # Save document info to the database
#     document = ProcessedResumes(
#         resume_name=f"Document {timestamp}",
#         processing_score=(0.95),
#         file_path=os.path.join('pdf_documents', pdf_filename),
#         processed_date=datetime.now())
#     document.save()
    
#     # Return success response or redirect
#     return render(request, 'pdf_success.html', {'document': document})

# @login_required
# @require_http_methods(["POST"])
# def generate_pdf_api(request):
#     """
#     API endpoint version of the generate_pdf function that returns JSON response
#     """
#     try:
#         # Import the generate_pdf functionality   
        

#         print("DONE IMPORTING")
#         # Create PDF content using ReportLab
#         buffer = BytesIO()
#         pdf = canvas.Canvas(buffer, pagesize=letter)
        
#         # Add content to the PDF
#         pdf.setFont("Helvetica", 12)
#         pdf.drawString(100, 750, f"Generated PDF Document")
#         pdf.drawString(100, 730, f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
#         pdf.drawString(100, 710, f"Generated by: {request.user.username}")
        
#         # Add more content as needed
#         pdf.drawString(100, 650, "This is a sample PDF document generated by Django.")
        
#         # Save the PDF
#         pdf.save()


        
#         print("DONE IMPORTING 2")


#         # Create PDF file name
#         timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
#         pdf_filename = f"document_{request.user.id}_{timestamp}.pdf"
        
#         # Define the directory path relative to MEDIA_ROOT
#         pdf_directory = os.path.join(settings.MEDIA_ROOT, 'pdf_documents')
        

#         # Create directory if it doesn't exist
#         if not os.path.exists(pdf_directory):
#             os.makedirs(pdf_directory)
        
#         # Complete file path
#         file_path = os.path.join(pdf_directory, pdf_filename)
        
#         # Write PDF to file
#         with open(file_path, 'wb') as f:
#             f.write(buffer.getvalue())
        
#         # Save document info to the database
#         document_title = f"Generated Document {timestamp}"

#         # document = ProcessedResume(
#         # resume_name=f"Document {timestamp}",
#         # processing_score=(0.95),
#         # file_path=os.path.join('pdf_documents', pdf_filename),
#         # processed_date=datetime.now(),
#         # created_by = request.user)

       


#         # document.save()
#         print("SAVED AND DONE IMPORTING")

#         # Return JSON response with document info
#         return JsonResponse({
#             'success': True,
#             'document_id': document.id,
#             'document_title': document.resume_name,
#             'timestamp': datetime.now().isoformat()
#         })
        
#     except Exception as e:
#         print(e)
#         return JsonResponse({
#             'success': False,
#             'error': str(e)
#         }, status=500)


@login_required
@ensure_csrf_cookie
@require_http_methods(["GET"])
def get_documents_api(request):
    """
    API endpoint to retrieve all documents for the current user
    """
    try:
        # Get all documents for the current user, ordered by most recent first
        print("GET HISTORY DOCS")
        documents = ProcessedResumeText.objects.all().order_by('-processed_date')
        
        # print(documents)
        # Convert documents to JSON-serializable format
        document_list = []
        for doc in documents:
            # print(doc.id)
            # print(doc.resume_name)
            # print(doc.processed_date.isoformat())

            document_list.append({
                
                'id': doc.id,
                'title': doc.resume_name,
                'created_at': doc.processed_date.isoformat(),
                # 'file_path': doc.file_path
            })
        
        return JsonResponse({
            'success': True,
            'documents': document_list
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)



@login_required
def processed_document_viewer(request, doc_id):
    document = get_object_or_404(ProcessedResumeText, pk=doc_id)
    mime_type = 'application/pdf'
    return render(request, 'viewhistory.html', {
        'file': document,
        'mime_type': mime_type
    })

@login_required
def serve_processed_file(request, doc_id):
    document = generate_pdf(doc_id)
    if document is None:
        return HttpResponse("Document not found", status=404)

    return FileResponse(document, as_attachment=False, content_type='application/pdf')


# 3. Your main view - submits and returns immediately
@login_required
@never_cache
def process_resume_batch(request):
    """Submit list of resumes for sequential processing"""
    
    print("HELLO LETS EXECUTE")
    
    # Only create task if not already created
    task_id = request.session.get('current_batch_task_id')
    
    if not task_id:
        print("No existing task found, creating new batch processing task...")
        
        # Get pending resumes from database
        resumes = UploadedFile.objects.filter(scan_status='pending')
        
        ontolody_doc = OntologyDocument.objects.first()
        file_path = ''
        
        if ontolody_doc:
            file_path = ontolody_doc.file_path  # Absolute filesystem path
        
        print("FILE PATH ONTOLOGY ", file_path)

        # NEED TO CREATE THE ONTOLOGY TXT FILE 

        if not resumes.exists():
            return render(request, 'index.html', {
                'message': 'No pending resumes found to process'
            })
        
        resume_list = []
        
        failed_extractions = []
        
        for resume in resumes:
            # Extract text content from the file
            print("RESUME NAME ", os.path.basename(resume.file.name))

            extracted_path = handle_resume_file(resume.file)
            print(extracted_path)
            extracted_text, person_identifiers = create_prompt(extracted_path)

            print("PERSON IDENTIFIERS ", person_identifiers)
            
            if extracted_text:
                resume_list.append({
                    'id': resume.id,
                    'person_identifiers': person_identifiers,
                    'content': extracted_text,
                    'resume_name':  os.path.basename(resume.file.name)
                })
            else:
                # Track failed extractions
                failed_extractions.append(resume.id)
                print(f"Failed to extract content from: {resume.id}")
        
        if not resume_list:
            return render(request, 'extraction_failed.html', {
                'message': 'Could not extract content from any resume files',
                'failed_files': failed_extractions
            })
        
        print(f"Successfully prepared {len(resume_list)} resumes for processing")
        if failed_extractions:
            print(f"Failed to extract: {failed_extractions}")
        
        print(f"Submitting {len(resume_list)} resumes for sequential processing...")
        
        # Submit the chain - this returns immediately
        chain_result = process_resume_chain.delay(resume_list, request.user.id)
        
        # Store the chain task ID in session
        request.session['current_batch_task_id'] = chain_result.id
        task_id = chain_result.id
        
        # Store the chain task ID for tracking in database
        ProcessingBatch.objects.create(
            task_id=chain_result.id,
            total_resumes=len(resume_list),
            submitted_by=request.user,
            status='RUNNING'
        )
        
        # Update status of uploaded files to 'processing'
        UploadedFile.objects.filter(
            id__in=[resume['id'] for resume in resume_list]
        ).update(scan_status='pending')
        
        # Store additional context in session for later use
        request.session['batch_context'] = {
            'total_resumes': len(resume_list),
            'failed_extractions': failed_extractions,
        }
    
    # Check the current task status
    from celery.result import AsyncResult
    result = AsyncResult(task_id)
    
    print("BATCH TASK ID:", task_id)
    print("BATCH TASK STATE:", result.state)
    
    # Get context from session or set defaults
    batch_context = request.session.get('batch_context', {
        'total_resumes': 0,
        'failed_extractions': []
    })
    
    context = {
        'task_id': task_id,
        'task_state': result.state,
        'total_resumes': batch_context.get('total_resumes', 0),
        'failed_extractions': batch_context.get('failed_extractions', []),
    }
    
    if result.ready():
        print("BATCH PROCESSING COMPLETE!")
        if result.successful():
            print("BATCH RESULT:", result.result)
            context['message'] = f'Successfully completed processing {batch_context.get("total_resumes", 0)} resumes'
            context['result'] = result.result
        else:
            print("BATCH FAILED:", result.result)
            context['message'] = 'Batch processing failed'
            context['error'] = str(result.result)
        
        # Clear the session after getting result
        if 'current_batch_task_id' in request.session:
            del request.session['current_batch_task_id']
        if 'batch_context' in request.session:
            del request.session['batch_context']
            
        # Update database status
        try:
            batch = ProcessingBatch.objects.get(task_id=task_id)
            batch.status = 'COMPLETED' if result.successful() else 'FAILED'
            batch.save()
        except ProcessingBatch.DoesNotExist:
            pass
            
    else:
        print("Batch processing is still running...")
        context['message'] = f'Processing {batch_context.get("total_resumes", 0)} resumes sequentially... (Status: {result.state})'
    
    return render(request, 'index.html', context)




# # 4. Check progress endpoint
# @login_required
# def check_batch_progress(request, task_id):
#     """Check progress of the sequential processing"""
    
#     result = AsyncResult(task_id)
    
#     if result.ready():
#         # Task completed
#         final_result = result.result
        
#         # Update batch status
#         ProcessingBatch.objects.filter(task_id=task_id).update(
#             status='COMPLETED',
#             completed_at=datetime.now()
#         )
        
#         return JsonResponse({
#             'status': 'completed',
#             'result': final_result
#         })
    
#     elif result.state == 'PROGRESS':
#         # Task is running, get progress
#         progress_info = result.info
#         return JsonResponse({
#             'status': 'running',
#             'current': progress_info.get('current', 0),
#             'total': progress_info.get('total', 0),
#             'current_resume': progress_info.get('current_resume', ''),
#             'completed': progress_info.get('completed', [])
#         })
    
#     else:
#         # Task pending or failed
#         return JsonResponse({
#             'status': result.state.lower(),
#             'message': 'Task is pending or failed'
#         })
    
#===========================================
