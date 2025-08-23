import os
import re
import hashlib
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple
from collections import defaultdict

import frontmatter
from whoosh import fields, index
from whoosh.qparser import QueryParser
from whoosh.scoring import BM25F
from loguru import logger

from .models import (
    DocumentContext, DocumentMetadata, ContextQuery, SearchResult, 
    SearchMatch, ProjectStatistics, SortBy, SortOrder
)


class DocumentService:
    def __init__(self, index_dir: str = "./index"):
        self.documents: Dict[str, DocumentContext] = {}
        self.path_index: Dict[str, str] = {}  # path -> document id
        self.tag_index: Dict[str, Set[str]] = defaultdict(set)  # tag -> document ids
        self.last_updated = datetime.now()
        
        # Whoosh search index
        self.index_dir = Path(index_dir)
        self.index_dir.mkdir(exist_ok=True)
        self._setup_search_index()
        
        # Stop words for better search
        self.stop_words = {
            'the', 'and', 'for', 'are', 'but', 'not', 'you', 'all', 'can', 
            'had', 'her', 'was', 'one', 'our', 'out', 'day', 'get', 'has', 
            'him', 'his', 'how', 'man', 'new', 'now', 'old', 'see', 'two', 
            'way', 'who', 'boy', 'did', 'its', 'let', 'put', 'say', 'she', 
            'too', 'use'
        }
    
    def _setup_search_index(self):
        """Setup Whoosh search index"""
        schema = fields.Schema(
            id=fields.ID(stored=True, unique=True),
            title=fields.TEXT(stored=True, phrase=False),
            content=fields.TEXT(stored=True, phrase=False),
            tags=fields.KEYWORD(stored=True, commas=True),
            path=fields.TEXT(stored=True),
            modified=fields.DATETIME(stored=True)
        )
        
        if index.exists_in(str(self.index_dir)):
            self.search_index = index.open_dir(str(self.index_dir))
        else:
            self.search_index = index.create_in(str(self.index_dir), schema)
    
    def load_document(self, file_path: str, root_path: str) -> Optional[DocumentContext]:
        """Load a document from file system"""
        try:
            file_path = Path(file_path)
            root_path = Path(root_path)
            
            if not file_path.exists():
                logger.warning(f"File not found: {file_path}")
                return None
            
            # Get file stats
            stats = file_path.stat()
            
            # Read and parse content
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Parse frontmatter if it exists
            try:
                post = frontmatter.loads(content)
                metadata_dict = post.metadata
                content_body = post.content
            except:
                metadata_dict = {}
                content_body = content
            
            # Create metadata
            metadata = DocumentMetadata(
                title=metadata_dict.get('title'),
                description=metadata_dict.get('description'),
                tags=metadata_dict.get('tags', []),
                author=metadata_dict.get('author'),
                created=metadata_dict.get('created'),
                modified=datetime.fromtimestamp(stats.st_mtime),
                version=metadata_dict.get('version'),
                custom_fields={k: v for k, v in metadata_dict.items() 
                             if k not in ['title', 'description', 'tags', 'author', 'created', 'version']}
            )
            
            # Extract title
            title = metadata.title or self._extract_title_from_content(content_body) or file_path.stem
            
            # Generate excerpt
            excerpt = self._generate_excerpt(content_body)
            
            # Count words
            word_count = self._count_words(content_body)
            
            # Generate document ID
            relative_path = str(file_path.relative_to(root_path))
            doc_id = self._generate_document_id(relative_path)
            
            document = DocumentContext(
                id=doc_id,
                title=title,
                content=content_body,
                path=str(file_path),
                relative_path=relative_path,
                last_modified=datetime.fromtimestamp(stats.st_mtime),
                size=stats.st_size,
                tags=metadata.tags,
                metadata=metadata,
                excerpt=excerpt,
                word_count=word_count,
                file_type=file_path.suffix.lower()
            )
            
            return document
            
        except Exception as e:
            logger.error(f"Failed to load document {file_path}: {e}")
            return None
    
    def add_document(self, document: DocumentContext) -> None:
        """Add document to index"""
        # Add to in-memory indexes
        self.documents[document.id] = document
        self.path_index[document.relative_path] = document.id
        
        # Update tag index
        for tag in document.tags:
            self.tag_index[tag].add(document.id)
        
        # Add to search index
        writer = self.search_index.writer()
        try:
            writer.update_document(
                id=document.id,
                title=document.title,
                content=document.content,
                tags=','.join(document.tags),
                path=document.relative_path,
                modified=document.last_modified
            )
            writer.commit()
        except Exception as e:
            logger.error(f"Failed to add document to search index: {e}")
            writer.cancel()
        
        self.last_updated = datetime.now()
        logger.debug(f"Added document to index: {document.relative_path}")
    
    def remove_document(self, document_id: str) -> None:
        """Remove document from index"""
        document = self.documents.get(document_id)
        if not document:
            return
        
        # Remove from in-memory indexes
        del self.documents[document_id]
        del self.path_index[document.relative_path]
        
        # Remove from tag index
        for tag in document.tags:
            self.tag_index[tag].discard(document_id)
            if not self.tag_index[tag]:
                del self.tag_index[tag]
        
        # Remove from search index
        writer = self.search_index.writer()
        try:
            writer.delete_by_term('id', document_id)
            writer.commit()
        except Exception as e:
            logger.error(f"Failed to remove document from search index: {e}")
            writer.cancel()
        
        self.last_updated = datetime.now()
        logger.debug(f"Removed document from index: {document.relative_path}")
    
    def search_documents(self, query: ContextQuery) -> List[SearchResult]:
        """Search documents based on query"""
        results = []
        
        if query.query:
            # Use Whoosh for full-text search
            results = self._perform_text_search(query.query)
        else:
            # Return all documents if no query
            results = [
                SearchResult(document=doc, score=1.0, matches=[])
                for doc in self.documents.values()
            ]
        
        # Apply filters
        if query.tags:
            results = [
                r for r in results 
                if any(tag in r.document.tags for tag in query.tags)
            ]
        
        if query.path:
            results = [
                r for r in results 
                if query.path.lower() in r.document.relative_path.lower()
            ]
        
        if query.file_type:
            results = [
                r for r in results 
                if r.document.file_type == query.file_type.lower()
            ]
        
        if query.since:
            results = [
                r for r in results 
                if r.document.last_modified >= query.since
            ]
        
        # Sort results
        self._sort_results(results, query.sort_by, query.sort_order)
        
        # Apply pagination
        start = query.offset
        end = start + query.limit
        
        return results[start:end]
    
    def get_document(self, path: str) -> Optional[DocumentContext]:
        """Get document by path"""
        document_id = self.path_index.get(path)
        if not document_id:
            return None
        return self.documents.get(document_id)
    
    def get_all_documents(self, limit: Optional[int] = None) -> List[DocumentContext]:
        """Get all documents"""
        documents = list(self.documents.values())
        return documents[:limit] if limit else documents
    
    def get_documents_by_tag(self, tag: str) -> List[DocumentContext]:
        """Get documents by tag"""
        document_ids = self.tag_index.get(tag, set())
        return [self.documents[doc_id] for doc_id in document_ids if doc_id in self.documents]
    
    def get_all_tags(self) -> List[str]:
        """Get all tags"""
        return sorted(self.tag_index.keys())
    
    def get_statistics(self) -> ProjectStatistics:
        """Get project statistics"""
        documents = list(self.documents.values())
        file_types = defaultdict(int)
        total_size = 0
        total_words = 0
        last_activity = datetime.min
        
        for doc in documents:
            file_types[doc.file_type] += 1
            total_size += doc.size
            total_words += doc.word_count
            if doc.last_modified > last_activity:
                last_activity = doc.last_modified
        
        return ProjectStatistics(
            total_files=len(documents),
            total_size=total_size,
            total_words=total_words,
            file_types=dict(file_types),
            last_activity=last_activity if last_activity != datetime.min else datetime.now()
        )
    
    def clear_all_documents(self) -> None:
        """Clear all documents from index"""
        self.documents.clear()
        self.path_index.clear()
        self.tag_index.clear()
        
        # Clear search index
        writer = self.search_index.writer()
        try:
            writer.commit(optimize=True)
        except Exception as e:
            logger.error(f"Failed to clear search index: {e}")
            writer.cancel()
        
        self.last_updated = datetime.now()
        logger.info("Cleared all documents from index")
    
    def _extract_title_from_content(self, content: str) -> Optional[str]:
        """Extract title from first heading"""
        heading_match = re.search(r'^#\s+(.+)$', content, re.MULTILINE)
        return heading_match.group(1).strip() if heading_match else None
    
    def _generate_excerpt(self, content: str, max_length: int = 200) -> str:
        """Generate excerpt from content"""
        # Remove markdown syntax
        plain_text = re.sub(r'#{1,6}\s+', '', content)  # Remove headings
        plain_text = re.sub(r'\*\*(.+?)\*\*', r'\1', plain_text)  # Remove bold
        plain_text = re.sub(r'\*(.+?)\*', r'\1', plain_text)  # Remove italic
        plain_text = re.sub(r'`(.+?)`', r'\1', plain_text)  # Remove inline code
        plain_text = re.sub(r'\[(.+?)\]\(.+?\)', r'\1', plain_text)  # Remove links
        plain_text = re.sub(r'\n+', ' ', plain_text)  # Replace newlines
        plain_text = plain_text.strip()
        
        return plain_text[:max_length] + '...' if len(plain_text) > max_length else plain_text
    
    def _count_words(self, content: str) -> int:
        """Count words in content"""
        words = re.findall(r'\b\w+\b', content)
        return len(words)
    
    def _generate_document_id(self, relative_path: str) -> str:
        """Generate unique document ID"""
        return hashlib.md5(relative_path.encode()).hexdigest()
    
    def _perform_text_search(self, query_text: str) -> List[SearchResult]:
        """Perform full-text search using Whoosh"""
        results = []
        
        with self.search_index.searcher(weighting=BM25F()) as searcher:
            # Create query parser for title and content fields
            parser = QueryParser("content", self.search_index.schema)
            query = parser.parse(query_text)
            
            # Perform search
            search_results = searcher.search(query, limit=100)
            
            for hit in search_results:
                document = self.documents.get(hit['id'])
                if document:
                    # Find matches in content
                    matches = self._find_matches(document, query_text)
                    
                    result = SearchResult(
                        document=document,
                        score=hit.score,
                        matches=matches
                    )
                    results.append(result)
        
        return results
    
    def _find_matches(self, document: DocumentContext, query: str) -> List[SearchMatch]:
        """Find query matches in document content"""
        matches = []
        lines = document.content.split('\n')
        query_lower = query.lower()
        
        for line_num, line in enumerate(lines, 1):
            line_lower = line.lower()
            start_index = line_lower.find(query_lower)
            
            if start_index != -1:
                match = SearchMatch(
                    line=line_num,
                    text=line.strip(),
                    start_index=start_index,
                    end_index=start_index + len(query)
                )
                matches.append(match)
                
                # Limit matches per document
                if len(matches) >= 5:
                    break
        
        return matches
    
    def _sort_results(self, results: List[SearchResult], sort_by: SortBy, sort_order: SortOrder) -> None:
        """Sort search results"""
        reverse = sort_order == SortOrder.DESC
        
        if sort_by == SortBy.RELEVANCE:
            results.sort(key=lambda r: r.score, reverse=reverse)
        elif sort_by == SortBy.MODIFIED:
            results.sort(key=lambda r: r.document.last_modified, reverse=reverse)
        elif sort_by == SortBy.CREATED:
            results.sort(key=lambda r: r.document.metadata.created or datetime.min, reverse=reverse)
        elif sort_by == SortBy.TITLE:
            results.sort(key=lambda r: r.document.title.lower(), reverse=reverse)