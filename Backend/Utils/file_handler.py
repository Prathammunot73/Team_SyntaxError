"""
Secure File Upload Handler
Handles PDF file uploads with validation and security checks
"""

import os
import hashlib
import time
from werkzeug.utils import secure_filename
import logging

logger = logging.getLogger(__name__)

# Configuration
ALLOWED_EXTENSIONS = {'pdf'}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
UPLOAD_FOLDER = 'static/uploads/notices'

class FileHandler:
    """Handler for secure file uploads"""
    
    @staticmethod
    def init_upload_folders():
        """Create upload directories if they don't exist"""
        folders = [
            UPLOAD_FOLDER,
            os.path.join(UPLOAD_FOLDER, 'timetables'),
            os.path.join(UPLOAD_FOLDER, 'general'),
            os.path.join(UPLOAD_FOLDER, 'exams'),
            os.path.join(UPLOAD_FOLDER, 'events')
        ]
        
        for folder in folders:
            os.makedirs(folder, exist_ok=True)
            logger.info(f"Upload folder ready: {folder}")
    
    @staticmethod
    def allowed_file(filename):
        """Check if file extension is allowed"""
        return '.' in filename and \
               filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS
    
    @staticmethod
    def validate_file(file):
        """
        Validate uploaded file
        
        Args:
            file: FileStorage object from Flask request
            
        Returns:
            tuple: (is_valid, error_message)
        """
        # Check if file exists
        if not file or file.filename == '':
            return False, 'No file selected'
        
        # Check file extension
        if not FileHandler.allowed_file(file.filename):
            return False, 'Only PDF files are allowed'
        
        # Check file size
        file.seek(0, os.SEEK_END)
        file_size = file.tell()
        file.seek(0)  # Reset file pointer
        
        if file_size > MAX_FILE_SIZE:
            return False, f'File size exceeds {MAX_FILE_SIZE / (1024*1024)}MB limit'
        
        if file_size == 0:
            return False, 'File is empty'
        
        return True, None
    
    @staticmethod
    def generate_unique_filename(original_filename, notice_type='general'):
        """
        Generate a unique filename to prevent collisions
        
        Args:
            original_filename: Original uploaded filename
            notice_type: Type of notice (for subfolder organization)
            
        Returns:
            str: Unique filename
        """
        # Get file extension
        ext = original_filename.rsplit('.', 1)[1].lower()
        
        # Create unique name using timestamp and hash
        timestamp = str(int(time.time() * 1000))
        hash_input = f"{original_filename}{timestamp}".encode()
        file_hash = hashlib.md5(hash_input).hexdigest()[:8]
        
        # Secure the original filename
        safe_name = secure_filename(original_filename.rsplit('.', 1)[0])
        safe_name = safe_name[:50]  # Limit length
        
        # Combine to create unique filename
        unique_name = f"{safe_name}_{timestamp}_{file_hash}.{ext}"
        
        return unique_name
    
    @staticmethod
    def save_file(file, notice_type='general'):
        """
        Save uploaded file securely
        
        Args:
            file: FileStorage object from Flask request
            notice_type: Type of notice (for subfolder organization)
            
        Returns:
            tuple: (success, file_path or error_message, file_size)
        """
        try:
            # Validate file
            is_valid, error = FileHandler.validate_file(file)
            if not is_valid:
                return False, error, 0
            
            # Get file size
            file.seek(0, os.SEEK_END)
            file_size = file.tell()
            file.seek(0)
            
            # Generate unique filename
            unique_filename = FileHandler.generate_unique_filename(
                file.filename, 
                notice_type
            )
            
            # Determine subfolder based on notice type
            subfolder = notice_type if notice_type in ['timetables', 'general', 'exams', 'events'] else 'general'
            upload_path = os.path.join(UPLOAD_FOLDER, subfolder)
            
            # Ensure subfolder exists
            os.makedirs(upload_path, exist_ok=True)
            
            # Full file path
            file_path = os.path.join(upload_path, unique_filename)
            
            # Save file
            file.save(file_path)
            
            logger.info(f"File saved successfully: {file_path} ({file_size} bytes)")
            
            return True, file_path, file_size
            
        except Exception as e:
            logger.error(f"Error saving file: {e}")
            return False, f"Error saving file: {str(e)}", 0
    
    @staticmethod
    def delete_file(file_path):
        """
        Delete a file from the filesystem
        
        Args:
            file_path: Path to file to delete
            
        Returns:
            bool: Success status
        """
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
                logger.info(f"File deleted: {file_path}")
                return True
            else:
                logger.warning(f"File not found for deletion: {file_path}")
                return False
        except Exception as e:
            logger.error(f"Error deleting file: {e}")
            return False
    
    @staticmethod
    def get_file_info(file_path):
        """
        Get information about a file
        
        Args:
            file_path: Path to file
            
        Returns:
            dict: File information
        """
        try:
            if not os.path.exists(file_path):
                return None
            
            stat = os.stat(file_path)
            
            return {
                'path': file_path,
                'size': stat.st_size,
                'created': stat.st_ctime,
                'modified': stat.st_mtime,
                'exists': True
            }
        except Exception as e:
            logger.error(f"Error getting file info: {e}")
            return None
    
    @staticmethod
    def format_file_size(size_bytes):
        """
        Format file size in human-readable format
        
        Args:
            size_bytes: File size in bytes
            
        Returns:
            str: Formatted file size
        """
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.2f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.2f} TB"
    
    @staticmethod
    def validate_pdf_content(file_path):
        """
        Validate that file is actually a PDF (basic check)
        
        Args:
            file_path: Path to file
            
        Returns:
            bool: True if valid PDF
        """
        try:
            with open(file_path, 'rb') as f:
                header = f.read(5)
                # PDF files start with %PDF-
                return header == b'%PDF-'
        except Exception as e:
            logger.error(f"Error validating PDF: {e}")
            return False
    
    @staticmethod
    def get_upload_stats():
        """Get statistics about uploaded files"""
        try:
            total_size = 0
            file_count = 0
            
            for root, dirs, files in os.walk(UPLOAD_FOLDER):
                for file in files:
                    if file.endswith('.pdf'):
                        file_path = os.path.join(root, file)
                        total_size += os.path.getsize(file_path)
                        file_count += 1
            
            return {
                'total_files': file_count,
                'total_size': total_size,
                'total_size_formatted': FileHandler.format_file_size(total_size),
                'upload_folder': UPLOAD_FOLDER
            }
        except Exception as e:
            logger.error(f"Error getting upload stats: {e}")
            return {}

# Initialize upload folders on module import
FileHandler.init_upload_folders()
