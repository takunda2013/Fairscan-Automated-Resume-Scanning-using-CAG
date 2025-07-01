import os
from django.db import models
from django.utils import timezone
from django.contrib.auth.models import User


class UploadedFile(models.Model):
    file = models.FileField(upload_to='uploads/')
    file_type = models.CharField(max_length=100)
    scan_status = models.CharField(max_length=50, default='Pending')
    analysis = models.TextField(blank=True, null=True)
    date_uploaded = models.DateTimeField(default=timezone.now) 
    uploaded_by = models.ForeignKey(User, on_delete=models.CASCADE, null=True)
     # Uses timezone-aware datetime

    print(timezone.now);

    def get_file_extension(self):
        return os.path.splitext(self.file.name)[1].lower()[1:]  # Returns 'docx', 'pdf' etc
    
    def is_supported_type(self):
        return self.get_file_extension() in ['docx', 'pdf']
    
    def save(self, *args, **kwargs):
        # Auto-detect file type before saving
        self.file_type = self.get_file_extension()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.file.name} (Uploaded at: {self.date_uploaded})"

#=============================================================================================================================

#=============================================================================================================================

class PastResumes(models.Model):

    # should save all candidates and their respective category scoring 
    # and reason for scoring in one file
    # would like the used ontology also for audit

    file = models.FileField(upload_to='history/')
    date_generated = models.DateTimeField(default=timezone.now)  # Uses timezone-aware datetime

#==================================================================================================================================


# class ProcessedResume(models.Model):
#     resume_name = models.CharField(max_length=255)
#     processing_score = models.FloatField()
#     file_path = models.CharField(max_length=255)
#     processed_date = models.DateTimeField(auto_now_add=True)
#     created_by = models.ForeignKey(User, on_delete=models.CASCADE, null=True)

    
#     def __str__(self):
#         return f"{self.resume_name} - {self.processing_score}%"
    
class ProcessedResumeText(models.Model):
    resume_name =  models.CharField(max_length=255)
    processing_overall_score =  models.FloatField()
    score_evaluation = models.TextField()
    processed_date = models.DateTimeField(auto_now_add=True)
    processed_by = models.ForeignKey(User, on_delete=models.CASCADE, null=True)

    def __str__(self):
        return f"{self.resume_name} - {self.processing_overall_score}%"


class OntologyDocument(models.Model):
    filename = models.CharField(max_length=255)
    file_path = models.CharField(max_length=500)
    extracted_text = models.TextField()
    uploaded_by = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Ontology: {self.filename}"
    
class ProcessingBatch(models.Model):
    task_id = models.CharField(max_length=255, unique=True)
    total_resumes = models.IntegerField()
    submitted_by = models.ForeignKey(User, on_delete=models.CASCADE)
    submitted_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=[
        ('RUNNING', 'Running'),
        ('COMPLETED', 'Completed'),
        ('FAILED', 'Failed'),
    ], default='RUNNING')
