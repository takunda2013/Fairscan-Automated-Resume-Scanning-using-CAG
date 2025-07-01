# consumers.py
import datetime
import json
import asyncio
import random
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from .models import ProcessedResumeText, UploadedFile
from django.utils import timezone
from asgiref.sync import sync_to_async

class ChatConsumer(AsyncWebsocketConsumer):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.counter = 0
        self.send_task = None

    async def connect(self):
        await self.accept()
        # Start sending incremental values
        self.send_task = asyncio.create_task(self.send_counter_loop())

    async def disconnect(self, close_code):
        # Clean up the task when client disconnects
        if self.send_task:
            self.send_task.cancel()
            try:
                await self.send_task
            except asyncio.CancelledError:
                pass

    async def receive(self, text_data):
        text_data_json = json.loads(text_data)
        message = text_data_json['message']
        
        # Echo back the message
        await self.send(text_data=json.dumps({
            'message': message
        }))

    @database_sync_to_async
    def get_pending_count(self):
        return UploadedFile.objects.filter(scan_status='pending').count()

    @database_sync_to_async
    def get_graded_count(self):
        return UploadedFile.objects.filter(scan_status='Graded').count()

    async def send_counter_loop(self):
        while True:
            try:
                # Use async database calls
                pending_count = await self.get_pending_count()
                graded_count = await self.get_graded_count()
                total_docs = pending_count + graded_count  # You'll need to implement this
            
                # Calculate progress percentage (0-100)
                progress = 0
                if total_docs > 0:
                    progress = min(int((graded_count / total_docs) * 100), 100)
             

                # print("PENDING COUNT ", pending_count)
                
                await self.send(text_data=json.dumps({
                    'counter': progress,
                    'pending': pending_count,
                    'graded': graded_count,
                    'message': f'Processing item {self.counter}'
                }))
                
                self.counter += 1
                await asyncio.sleep(1)
                
                # Reset counter if needed
                if self.counter > 100:
                    self.counter = 0

            except asyncio.CancelledError:
                break

# SAMPLE FOR FILE WEBSOCKETING ===================================================================================

class DashboardConsumer(AsyncWebsocketConsumer):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.counter = 0
        self.send_task = None

    async def connect(self):
        print("✅ DashboardConsumer CONNECTED")

        await self.accept()
        # Start sending incremental values
        self.send_task = asyncio.create_task(self.send_counter_loop())

    async def disconnect(self, close_code):
        # Clean up the task when client disconnects
        if self.send_task:
            self.send_task.cancel()
            try:
                await self.send_task
            except asyncio.CancelledError:
                pass

    async def receive(self, text_data):
        text_data_json = json.loads(text_data)
        message = text_data_json['message']
        
        # Echo back the message
        await self.send(text_data=json.dumps({
            'message': message
        }))

    async def send_counter_loop(self):
        while True:
            try:
                # Calculate progress percentage (example: cap at 100%)
                progress = min(self.counter, 100)
                
                await self.send(text_data=json.dumps({
                    'counter': progress,
                    'message': f'Processing item {self.counter}'
                }))
                
                self.counter += 1
                await asyncio.sleep(1)
                
                # Reset counter if needed
                if self.counter > 100:
                    self.counter = 0

            except asyncio.CancelledError:
                break
            
# -----------------------------------------------------------------------------------------------------------------



class FileTableConsumer(AsyncWebsocketConsumer):
    """
    Debug version of WebSocket consumer with real-time monitoring
    """
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.monitor_task = None
    
    async def connect(self):
        """Handle WebSocket connection"""
        await self.accept()
        print("=== WebSocket connection accepted ===")
        
        # Test database connection first
        await self.test_database_connection()
        
        # Then send initial data
        await self.send_initial_data()
        
        # Start real-time monitoring
        self.monitor_task = asyncio.create_task(self.monitor_new_files())
        print("=== Started real-time monitoring ===")

    async def disconnect(self, close_code):
        """Clean up when connection is closed"""
        print(f"=== WebSocket disconnected with code: {close_code} ===")
        
        # Cancel monitoring task
        if self.monitor_task:
            self.monitor_task.cancel()
            try:
                await self.monitor_task
            except asyncio.CancelledError:
                print("=== Monitoring task cancelled ===")
                pass

    async def test_database_connection(self):
        """Test if we can access the database and model"""
        try:
            print("Testing database connection...")
            
            @sync_to_async
            def test_model_access():
                try:
                    # ⚠️ REPLACE 'your_app' WITH YOUR ACTUAL APP NAME ⚠️
                    from .models import ProcessedResumeText
                    
                    # Test basic query
                    count = ProcessedResumeText.objects.count()
                    print(f"Found {count} records in ProcessedResumeText table")
                    
                    # Get first record if exists
                    if count > 0:
                        first_record = ProcessedResumeText.objects.first()
                        print(f"First record: {first_record.resume_name if hasattr(first_record, 'resume_name') else 'No resume_name field'}")
                        return count, first_record
                    else:
                        print("No records found in the table")
                        return 0, None
                        
                except ImportError as e:
                    print(f"❌ Model import failed: {e}")
                    print("Please update 'your_app' to your actual Django app name")
                    return None, None
                except Exception as e:
                    print(f"❌ Database query failed: {e}")
                    return None, None
            
            result = await test_model_access()
            if result[0] is not None:
                print(f"✅ Database test successful: {result[0]} records found")
            else:
                print("❌ Database test failed")
                
        except Exception as e:
            print(f"❌ Database test error: {e}")
            import traceback
            traceback.print_exc()

    async def send_initial_data(self):
        """Send test data or real data"""
        try:
            print("=== Attempting to send initial data ===")
            
            # Try to get real data first
            real_data = await self.get_all_processed_files()
            
            if real_data:
                print(f"Sending {len(real_data)} real files")
                for file_data in real_data:
                    await self.send(text_data=json.dumps({
                        'action': 'add_file',
                        'file_data': file_data
                    }))
                    print(f"✅ Sent: {file_data['file_name']}")
                    await asyncio.sleep(0.2)
            # else:
            #     print("No real data found, sending test data")
            #     # Send test data to verify WebSocket is working
            #     test_files = [
            #         {
            #             'file_name': 'Test_Resume_1.docx',
            #             'score': '85%',
            #             'id': 'file_test_1',
            #             'processed_date': timezone.now().isoformat(),
            #             'processed_by': 'Test User'
            #         },
            #         {
            #             'file_name': 'Test_Resume_2.docx', 
            #             'score': '92%',
            #             'id': 'file_test_2',
            #             'processed_date': timezone.now().isoformat(),
            #             'processed_by': 'Test User'
            #         }
            #     ]
                
            #     for file_data in test_files:
            #         await self.send(text_data=json.dumps({
            #             'action': 'add_file',
            #             'file_data': file_data
            #         }))
            #         print(f"✅ Sent test file: {file_data['file_name']}")
            #         await asyncio.sleep(0.5)
                    
        except Exception as e:
            print(f"❌ Error in send_initial_data: {e}")
            import traceback
            traceback.print_exc()

    async def get_all_processed_files(self):
        """Get all processed files with detailed error reporting"""
        try:
            print("Fetching all processed files...")
            
            @sync_to_async
            def fetch_all_data():
                try:
                    # ⚠️ REPLACE 'your_app' WITH YOUR ACTUAL APP NAME ⚠️
                    from .models import ProcessedResumeText
                    
                    print("Model imported successfully")
                    
                    # Get all records
                    records = list(ProcessedResumeText.objects.all().order_by('-processed_date'))
                    print(f"Retrieved {len(records)} records from database")
                    
                    if not records:
                        print("No records found in database")
                        return []
                    
                    file_data_list = []
                    for i, record in enumerate(records):
                        try:
                            print(f"Processing record {i+1}/{len(records)}: ID={record.id}")
                            
                            # Safely get processed_by username
                            processed_by = 'Unknown'
                            if hasattr(record, 'processed_by') and record.processed_by:
                                processed_by = record.processed_by.username
                            
                            file_data = {
                                'file_name': str(record.resume_name),
                                'score': f"{record.processing_overall_score}%",
                                'id': f"file_{record.id}",
                                'processed_date': record.processed_date.isoformat(),
                                'processed_by': processed_by
                            }
                            file_data_list.append(file_data)
                            print(f"✅ Processed record: {file_data['file_name']}")
                            
                        except Exception as e:
                            print(f"❌ Error processing individual record {record.id}: {e}")
                            continue
                    
                    print(f"Successfully processed {len(file_data_list)} records")
                    return file_data_list
                    
                except ImportError as e:
                    print(f"❌ Import error: {e}")
                    print("Make sure to replace 'your_app' with your actual app name")
                    return []
                except Exception as e:
                    print(f"❌ Database error: {e}")
                    import traceback
                    traceback.print_exc()
                    return []
            
            result = await fetch_all_data()
            print(f"Final result: {len(result)} files ready to send")
            return result
            
        except Exception as e:
            print(f"❌ Outer error in get_all_processed_files: {e}")
            import traceback
            traceback.print_exc()
            return []

    async def monitor_new_files(self):
        """Monitor for new files and send them as they are added - WITH DETAILED LOGGING"""
        # Get the current time as the baseline
        last_check_time = timezone.now()
        print(f"=== Starting real-time monitoring since: {last_check_time} ===")
        
        while True:
            try:
                print(f"🔍 Checking for new files since {last_check_time}")
                
                # Check for new files since last check
                new_files = await self.get_new_files_since_timestamp(last_check_time)
                
                if new_files:
                    print(f"🆕 Found {len(new_files)} NEW files!")
                    for file_data in new_files:
                        await self.send(text_data=json.dumps({
                            'action': 'add_file',
                            'file_data': file_data
                        }))
                        print(f"📤 Sent new file: {file_data['file_name']}")
                        await asyncio.sleep(0.5)  # Small delay between files
                else:
                    print("📭 No new files found")
                
                # Update last check time
                last_check_time = timezone.now()
                
                # Wait before next check (check every 10 seconds)
                print(f"⏳ Waiting 10 seconds before next check...")
                await asyncio.sleep(10)
                
            except asyncio.CancelledError:
                print("=== Real-time monitoring cancelled ===")
                break
            except Exception as e:
                print(f"❌ Error in monitor_new_files: {e}")
                import traceback
                traceback.print_exc()
                await asyncio.sleep(10)  # Wait before retrying

    async def get_new_files_since_timestamp(self, last_timestamp):
        """Get files added since a specific timestamp - WITH DETAILED LOGGING"""
        try:
            print(f"🔍 Looking for files newer than: {last_timestamp}")
            
            @sync_to_async
            def fetch_new_data():
                try:
                    # ⚠️ REPLACE 'your_app' WITH YOUR ACTUAL APP NAME ⚠️
                    from .models import ProcessedResumeText
                    
                    # Get records newer than the timestamp
                    new_records = list(ProcessedResumeText.objects.filter(
                        processed_date__gt=last_timestamp
                    ).order_by('-processed_date'))
                    
                    print(f"📊 Database query returned {len(new_records)} new records")
                    
                    if not new_records:
                        return []
                    
                    file_data_list = []
                    for record in new_records:
                        try:
                            # Safely get processed_by username
                            processed_by = 'Unknown'
                            if hasattr(record, 'processed_by') and record.processed_by:
                                processed_by = record.processed_by.username
                            
                            file_data = {
                                'file_name': str(record.resume_name),
                                'score': f"{record.processing_overall_score}%",
                                'id': f"file_{record.id}",
                                'processed_date': record.processed_date.isoformat(),
                                'processed_by': processed_by
                            }
                            file_data_list.append(file_data)
                            print(f"✅ New file prepared: {file_data['file_name']} (processed: {record.processed_date})")
                            
                        except Exception as e:
                            print(f"❌ Error processing new record {record.id}: {e}")
                            continue
                    
                    return file_data_list
                    
                except ImportError as e:
                    print(f"❌ Import error: {e}")
                    return []
                except Exception as e:
                    print(f"❌ Database error: {e}")
                    return []
            
            result = await fetch_new_data()
            print(f"📤 Returning {len(result)} new files")
            return result
            
        except Exception as e:
            print(f"❌ Error in get_new_files_since_timestamp: {e}")
            import traceback
            traceback.print_exc()
            return []

    async def receive(self, text_data):
        """Handle messages from client"""
        try:
            text_data_json = json.loads(text_data)
            message = text_data_json.get('message', '')
            print(f"📨 Received message: {message}")
            
            if message == 'reset':
                print("🔄 Resetting table...")
                await self.send(text_data=json.dumps({
                    'action': 'reset_table'
                }))
                await self.send_initial_data()
                print("✅ Table reset complete")
            
        except Exception as e:
            print(f"❌ Error handling message: {e}")