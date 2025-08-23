import os
import asyncio
from pathlib import Path
from typing import List, Set, Callable, Optional
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler, FileSystemEvent
from loguru import logger

from .document_service import DocumentService
from .models import FileWatchEvent


class DocumentFileHandler(FileSystemEventHandler):
    """File system event handler for document changes"""
    
    def __init__(self, document_service: DocumentService, root_path: str, 
                 watch_patterns: List[str], exclude_patterns: List[str]):
        self.document_service = document_service
        self.root_path = Path(root_path)
        self.watch_patterns = watch_patterns
        self.exclude_patterns = exclude_patterns
        self.supported_extensions = {'.md', '.txt', '.rst', '.markdown'}
    
    def _should_process_file(self, file_path: str) -> bool:
        """Check if file should be processed"""
        path = Path(file_path)
        
        # Check extension
        if path.suffix.lower() not in self.supported_extensions:
            return False
        
        # Check exclude patterns
        relative_path = str(path.relative_to(self.root_path))
        for pattern in self.exclude_patterns:
            if self._matches_pattern(relative_path, pattern):
                return False
        
        # Check include patterns
        for pattern in self.watch_patterns:
            if self._matches_pattern(relative_path, pattern):
                return True
        
        return False
    
    def _matches_pattern(self, path: str, pattern: str) -> bool:
        """Simple pattern matching (supports * wildcards)"""
        import fnmatch
        return fnmatch.fnmatch(path, pattern)
    
    def on_created(self, event: FileSystemEvent):
        if not event.is_directory and self._should_process_file(event.src_path):
            asyncio.create_task(self._handle_file_created(event.src_path))
    
    def on_modified(self, event: FileSystemEvent):
        if not event.is_directory and self._should_process_file(event.src_path):
            asyncio.create_task(self._handle_file_modified(event.src_path))
    
    def on_deleted(self, event: FileSystemEvent):
        if not event.is_directory and self._should_process_file(event.src_path):
            asyncio.create_task(self._handle_file_deleted(event.src_path))
    
    async def _handle_file_created(self, file_path: str):
        """Handle file creation"""
        try:
            document = self.document_service.load_document(file_path, str(self.root_path))
            if document:
                self.document_service.add_document(document)
                logger.info(f"Document added: {document.relative_path}")
        except Exception as e:
            logger.error(f"Error handling file creation {file_path}: {e}")
    
    async def _handle_file_modified(self, file_path: str):
        """Handle file modification"""
        try:
            # Remove existing document if it exists
            relative_path = str(Path(file_path).relative_to(self.root_path))
            existing_doc = self.document_service.get_document(relative_path)
            if existing_doc:
                self.document_service.remove_document(existing_doc.id)
            
            # Add updated document
            document = self.document_service.load_document(file_path, str(self.root_path))
            if document:
                self.document_service.add_document(document)
                logger.info(f"Document updated: {document.relative_path}")
        except Exception as e:
            logger.error(f"Error handling file modification {file_path}: {e}")
    
    async def _handle_file_deleted(self, file_path: str):
        """Handle file deletion"""
        try:
            relative_path = str(Path(file_path).relative_to(self.root_path))
            document = self.document_service.get_document(relative_path)
            if document:
                self.document_service.remove_document(document.id)
                logger.info(f"Document removed: {relative_path}")
        except Exception as e:
            logger.error(f"Error handling file deletion {file_path}: {e}")


class FileWatcher:
    """File system watcher for document changes"""
    
    def __init__(self, document_service: DocumentService, root_path: str = "."):
        self.document_service = document_service
        self.root_path = Path(root_path).resolve()
        self.observer: Optional[Observer] = None
        self.is_watching = False
        
        # Default patterns
        self.watch_patterns = ['**/*.md', '**/*.txt', '**/*.rst', '**/*.markdown']
        self.exclude_patterns = [
            'node_modules/**', 'dist/**', '.git/**', '__pycache__/**',
            'venv/**', '.venv/**', 'build/**', 'coverage/**'
        ]
    
    def set_patterns(self, watch_patterns: List[str], exclude_patterns: List[str]):
        """Set watch and exclude patterns"""
        self.watch_patterns = watch_patterns
        self.exclude_patterns = exclude_patterns
    
    async def start(self) -> None:
        """Start file watching"""
        if self.is_watching:
            logger.warning("File watcher is already running")
            return
        
        try:
            # Initial scan
            await self.initial_scan()
            
            # Start watching
            self.observer = Observer()
            event_handler = DocumentFileHandler(
                self.document_service, 
                str(self.root_path),
                self.watch_patterns,
                self.exclude_patterns
            )
            
            self.observer.schedule(event_handler, str(self.root_path), recursive=True)
            self.observer.start()
            
            self.is_watching = True
            logger.info(f"File watcher started, monitoring: {self.root_path}")
            logger.info(f"Watch patterns: {', '.join(self.watch_patterns)}")
            logger.info(f"Exclude patterns: {', '.join(self.exclude_patterns)}")
            
        except Exception as e:
            logger.error(f"Failed to start file watcher: {e}")
            raise
    
    async def stop(self) -> None:
        """Stop file watching"""
        if self.observer:
            self.observer.stop()
            self.observer.join()
            self.observer = None
        
        self.is_watching = False
        logger.info("File watcher stopped")
    
    async def initial_scan(self) -> None:
        """Perform initial scan of documents"""
        logger.info("Starting initial document scan...")
        
        total_files = 0
        supported_extensions = {'.md', '.txt', '.rst', '.markdown'}
        
        for pattern in self.watch_patterns:
            try:
                # Convert glob pattern to pathlib pattern
                if pattern.startswith('**/'):
                    # Recursive pattern
                    pattern_suffix = pattern[3:]  # Remove '**/' prefix
                    files = list(self.root_path.rglob(pattern_suffix))
                else:
                    files = list(self.root_path.glob(pattern))
                
                logger.debug(f"Pattern {pattern} found {len(files)} files")
                
                for file_path in files:
                    if not file_path.is_file():
                        continue
                    
                    if file_path.suffix.lower() not in supported_extensions:
                        continue
                    
                    # Check exclude patterns
                    relative_path = str(file_path.relative_to(self.root_path))
                    should_exclude = False
                    for exclude_pattern in self.exclude_patterns:
                        if self._matches_pattern(relative_path, exclude_pattern):
                            should_exclude = True
                            break
                    
                    if should_exclude:
                        continue
                    
                    try:
                        document = self.document_service.load_document(str(file_path), str(self.root_path))
                        if document:
                            self.document_service.add_document(document)
                            total_files += 1
                            logger.debug(f"Loaded document: {document.relative_path}")
                    except Exception as e:
                        logger.warning(f"Failed to load document {file_path}: {e}")
                        
            except Exception as e:
                logger.error(f"Failed to scan pattern {pattern}: {e}")
        
        logger.info(f"Initial scan completed. Loaded {total_files} documents.")
    
    def _matches_pattern(self, path: str, pattern: str) -> bool:
        """Simple pattern matching (supports * wildcards)"""
        import fnmatch
        return fnmatch.fnmatch(path, pattern)
    
    def is_running(self) -> bool:
        """Check if watcher is running"""
        return self.is_watching
    
    def get_watched_path(self) -> str:
        """Get watched path"""
        return str(self.root_path)