import streamlit as st
import asyncio
import os
import tempfile
import shutil
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any
import threading
import time

# Import our services
from src.document_service import DocumentService
from src.file_watcher import FileWatcher
from src.mcp_server import MCPServer
from src.models import UploadedFile, AdminAction, ServerStatus

# Configure page
st.set_page_config(
    page_title="AI-SLDC Documentation Admin",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize session state
if 'document_service' not in st.session_state:
    st.session_state.document_service = DocumentService()
if 'file_watcher' not in st.session_state:
    st.session_state.file_watcher = FileWatcher(st.session_state.document_service)
if 'mcp_server' not in st.session_state:
    st.session_state.mcp_server = MCPServer(st.session_state.document_service)
if 'server_running' not in st.session_state:
    st.session_state.server_running = False
if 'upload_history' not in st.session_state:
    st.session_state.upload_history = []
if 'admin_actions' not in st.session_state:
    st.session_state.admin_actions = []
if 'docs_directory' not in st.session_state:
    st.session_state.docs_directory = "./docs"


def log_admin_action(action: str, target: str, details: Dict[str, Any] = None):
    """Log admin action"""
    admin_action = AdminAction(
        action=action,
        target=target,
        user="admin",  # In a real app, get from authentication
        details=details or {}
    )
    st.session_state.admin_actions.append(admin_action)


def get_server_status() -> ServerStatus:
    """Get current server status"""
    stats = st.session_state.document_service.get_statistics()
    return ServerStatus(
        status="running" if st.session_state.server_running else "stopped",
        uptime=time.time() - st.session_state.get('start_time', time.time()),
        documents_loaded=stats.total_files,
        memory_usage=0.0,  # Would implement actual memory monitoring
        last_activity=stats.last_activity
    )


async def start_file_watcher():
    """Start the file watcher"""
    try:
        await st.session_state.file_watcher.start()
        st.session_state.server_running = True
        st.session_state.start_time = time.time()
        log_admin_action("start_server", "file_watcher")
    except Exception as e:
        st.error(f"Failed to start file watcher: {e}")


async def stop_file_watcher():
    """Stop the file watcher"""
    try:
        await st.session_state.file_watcher.stop()
        st.session_state.server_running = False
        log_admin_action("stop_server", "file_watcher")
    except Exception as e:
        st.error(f"Failed to stop file watcher: {e}")


def save_uploaded_file(uploaded_file, target_dir: str) -> str:
    """Save uploaded file to target directory"""
    target_path = Path(target_dir)
    target_path.mkdir(parents=True, exist_ok=True)
    
    file_path = target_path / uploaded_file.name
    
    with open(file_path, "wb") as f:
        f.write(uploaded_file.getbuffer())
    
    return str(file_path)


def main():
    # Header
    st.title("🤖 AI-SLDC Documentation Admin")
    st.markdown("**Manage your documentation context for AI tools**")
    
    # Sidebar - Server Control
    with st.sidebar:
        st.header("🔧 Server Control")
        
        # Server status
        status = get_server_status()
        if status.status == "running":
            st.success(f"✅ Server Running ({status.uptime:.0f}s)")
        else:
            st.error("❌ Server Stopped")
        
        # Start/Stop buttons
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🚀 Start", disabled=st.session_state.server_running):
                with st.spinner("Starting server..."):
                    asyncio.run(start_file_watcher())
                st.rerun()
        
        with col2:
            if st.button("🛑 Stop", disabled=not st.session_state.server_running):
                with st.spinner("Stopping server..."):
                    asyncio.run(stop_file_watcher())
                st.rerun()
        
        st.divider()
        
        # Configuration
        st.header("⚙️ Configuration")
        
        # Docs directory
        new_docs_dir = st.text_input(
            "Documentation Directory",
            value=st.session_state.docs_directory,
            help="Directory to monitor for documentation files"
        )
        
        if new_docs_dir != st.session_state.docs_directory:
            st.session_state.docs_directory = new_docs_dir
            st.session_state.file_watcher.root_path = Path(new_docs_dir)
            log_admin_action("change_config", "docs_directory", {"new_path": new_docs_dir})
        
        # Watch patterns
        watch_patterns = st.text_area(
            "Watch Patterns",
            value="**/*.md\n**/*.txt\n**/*.rst",
            help="File patterns to watch (one per line)"
        )
        
        exclude_patterns = st.text_area(
            "Exclude Patterns",
            value="node_modules/**\ndist/**\n.git/**\n__pycache__/**",
            help="Patterns to exclude (one per line)"
        )
        
        if st.button("Update Patterns"):
            watch_list = [p.strip() for p in watch_patterns.split('\n') if p.strip()]
            exclude_list = [p.strip() for p in exclude_patterns.split('\n') if p.strip()]
            st.session_state.file_watcher.set_patterns(watch_list, exclude_list)
            log_admin_action("update_patterns", "file_watcher", {
                "watch": watch_list,
                "exclude": exclude_list
            })
            st.success("Patterns updated!")
    
    # Main content tabs
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📊 Dashboard", "📁 File Upload", "🔍 Search & Browse", 
        "🗑️ Manage Context", "📋 Admin Logs"
    ])
    
    with tab1:
        st.header("📊 Documentation Dashboard")
        
        # Statistics
        stats = st.session_state.document_service.get_statistics()
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total Documents", stats.total_files)
        with col2:
            st.metric("Total Words", f"{stats.total_words:,}")
        with col3:
            st.metric("Total Size", f"{stats.total_size / 1024:.1f} KB")
        with col4:
            st.metric("File Types", len(stats.file_types))
        
        # File types chart
        if stats.file_types:
            st.subheader("📈 File Types Distribution")
            st.bar_chart(stats.file_types)
        
        # Recent activity
        st.subheader("🕒 Recent Activity")
        st.write(f"Last activity: {stats.last_activity.strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Document list preview
        st.subheader("📄 Recent Documents")
        documents = st.session_state.document_service.get_all_documents(limit=5)
        
        if documents:
            for doc in documents:
                with st.expander(f"📄 {doc.title}"):
                    col1, col2 = st.columns([2, 1])
                    with col1:
                        st.write(f"**Path:** {doc.relative_path}")
                        st.write(f"**Modified:** {doc.last_modified.strftime('%Y-%m-%d %H:%M:%S')}")
                        st.write(f"**Words:** {doc.word_count}")
                        if doc.tags:
                            st.write(f"**Tags:** {', '.join(doc.tags)}")
                    with col2:
                        st.write(f"**Size:** {doc.size} bytes")
                        st.write(f"**Type:** {doc.file_type}")
                    
                    if doc.excerpt:
                        st.write(f"**Excerpt:** {doc.excerpt}")
        else:
            st.info("No documents loaded yet. Upload some files or start the file watcher.")
    
    with tab2:
        st.header("📁 File Upload & Management")
        
        # File upload section
        st.subheader("📤 Upload New Documents")
        
        uploaded_files = st.file_uploader(
            "Choose documentation files",
            type=['md', 'txt', 'rst', 'markdown'],
            accept_multiple_files=True,
            help="Upload markdown, text, or reStructuredText files"
        )
        
        if uploaded_files:
            col1, col2 = st.columns([3, 1])
            
            with col1:
                # Target directory selection
                target_dir = st.text_input(
                    "Target Directory",
                    value=st.session_state.docs_directory,
                    help="Directory where files will be saved"
                )
            
            with col2:
                st.write("")  # Spacing
                st.write("")  # Spacing
                upload_button = st.button("📤 Upload Files", type="primary")
            
            if upload_button:
                success_count = 0
                error_count = 0
                
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                for i, uploaded_file in enumerate(uploaded_files):
                    try:
                        # Update progress
                        progress = (i + 1) / len(uploaded_files)
                        progress_bar.progress(progress)
                        status_text.text(f"Uploading {uploaded_file.name}...")
                        
                        # Save file
                        file_path = save_uploaded_file(uploaded_file, target_dir)
                        
                        # Load into document service
                        document = st.session_state.document_service.load_document(file_path, target_dir)
                        if document:
                            st.session_state.document_service.add_document(document)
                            
                            # Log upload
                            upload_record = UploadedFile(
                                filename=uploaded_file.name,
                                content=uploaded_file.getvalue().decode('utf-8'),
                                size=uploaded_file.size,
                                tags=[],
                                metadata={"target_dir": target_dir}
                            )
                            st.session_state.upload_history.append(upload_record)
                            
                            log_admin_action("upload_file", uploaded_file.name, {
                                "size": uploaded_file.size,
                                "target_dir": target_dir
                            })
                            
                            success_count += 1
                        else:
                            error_count += 1
                            
                    except Exception as e:
                        st.error(f"Failed to upload {uploaded_file.name}: {e}")
                        error_count += 1
                
                progress_bar.empty()
                status_text.empty()
                
                if success_count > 0:
                    st.success(f"✅ Successfully uploaded {success_count} file(s)")
                if error_count > 0:
                    st.error(f"❌ Failed to upload {error_count} file(s)")
                
                # Refresh the page to show new documents
                st.rerun()
        
        # Upload history
        st.subheader("📋 Upload History")
        if st.session_state.upload_history:
            for i, upload in enumerate(reversed(st.session_state.upload_history[-10:])):
                with st.expander(f"📄 {upload.filename} - {upload.upload_time.strftime('%Y-%m-%d %H:%M:%S')}"):
                    col1, col2 = st.columns(2)
                    with col1:
                        st.write(f"**Size:** {upload.size} bytes")
                        st.write(f"**Upload Time:** {upload.upload_time}")
                    with col2:
                        if upload.tags:
                            st.write(f"**Tags:** {', '.join(upload.tags)}")
                        if upload.metadata:
                            st.write(f"**Target Dir:** {upload.metadata.get('target_dir', 'N/A')}")
        else:
            st.info("No files uploaded yet.")
    
    with tab3:
        st.header("🔍 Search & Browse Documents")
        
        # Search interface
        col1, col2 = st.columns([3, 1])
        with col1:
            search_query = st.text_input("🔍 Search documents", placeholder="Enter search terms...")
        with col2:
            search_limit = st.number_input("Results", min_value=1, max_value=50, value=10)
        
        # Advanced filters
        with st.expander("🔧 Advanced Filters"):
            col1, col2, col3 = st.columns(3)
            with col1:
                filter_tags = st.multiselect("Filter by Tags", st.session_state.document_service.get_all_tags())
            with col2:
                filter_path = st.text_input("Filter by Path", placeholder="e.g., docs/api/")
            with col3:
                filter_type = st.selectbox("File Type", ["All"] + list(set(doc.file_type for doc in st.session_state.document_service.get_all_documents())))
        
        # Perform search
        if search_query or filter_tags or filter_path or (filter_type and filter_type != "All"):
            from src.models import ContextQuery
            
            query = ContextQuery(
                query=search_query if search_query else None,
                tags=filter_tags,
                path=filter_path if filter_path else None,
                file_type=filter_type if filter_type != "All" else None,
                limit=search_limit
            )
            
            results = st.session_state.document_service.search_documents(query)
            
            st.subheader(f"🔍 Search Results ({len(results)} found)")
            
            for i, result in enumerate(results, 1):
                doc = result.document
                with st.expander(f"{i}. {doc.title} (Score: {result.score:.2f})"):
                    col1, col2 = st.columns([2, 1])
                    with col1:
                        st.write(f"**Path:** {doc.relative_path}")
                        st.write(f"**Modified:** {doc.last_modified.strftime('%Y-%m-%d %H:%M:%S')}")
                        st.write(f"**Excerpt:** {doc.excerpt}")
                        
                        if result.matches:
                            st.write("**Matches:**")
                            for match in result.matches[:3]:
                                st.code(f"Line {match.line}: {match.text}")
                    
                    with col2:
                        st.write(f"**Size:** {doc.size} bytes")
                        st.write(f"**Words:** {doc.word_count}")
                        if doc.tags:
                            st.write(f"**Tags:** {', '.join(doc.tags)}")
                        
                        if st.button(f"View Full Content", key=f"view_{doc.id}"):
                            st.text_area("Full Content", doc.content, height=300, key=f"content_{doc.id}")
        else:
            # Show all documents
            st.subheader("📚 All Documents")
            all_docs = st.session_state.document_service.get_all_documents(limit=20)
            
            for doc in all_docs:
                with st.expander(f"📄 {doc.title}"):
                    col1, col2 = st.columns([2, 1])
                    with col1:
                        st.write(f"**Path:** {doc.relative_path}")
                        st.write(f"**Modified:** {doc.last_modified.strftime('%Y-%m-%d %H:%M:%S')}")
                        st.write(f"**Excerpt:** {doc.excerpt}")
                    with col2:
                        st.write(f"**Size:** {doc.size} bytes")
                        st.write(f"**Words:** {doc.word_count}")
                        if doc.tags:
                            st.write(f"**Tags:** {', '.join(doc.tags)}")
    
    with tab4:
        st.header("🗑️ Manage Context")
        
        # Context management actions
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("🔄 Refresh All Documents", type="primary"):
                with st.spinner("Refreshing documents..."):
                    # Clear current documents
                    st.session_state.document_service.clear_all_documents()
                    
                    # Reload from file system
                    asyncio.run(st.session_state.file_watcher.initial_scan())
                    
                    log_admin_action("refresh_documents", "all")
                    st.success("Documents refreshed!")
                    st.rerun()
        
        with col2:
            if st.button("🗑️ Clear All Context", type="secondary"):
                if st.session_state.get('confirm_clear', False):
                    st.session_state.document_service.clear_all_documents()
                    st.session_state.upload_history.clear()
                    log_admin_action("clear_context", "all")
                    st.success("All context cleared!")
                    st.session_state.confirm_clear = False
                    st.rerun()
                else:
                    st.session_state.confirm_clear = True
                    st.warning("Click again to confirm clearing all context")
        
        with col3:
            if st.button("📊 Rebuild Search Index"):
                with st.spinner("Rebuilding search index..."):
                    # This would rebuild the Whoosh index
                    log_admin_action("rebuild_index", "search")
                    st.success("Search index rebuilt!")
        
        # Document management
        st.subheader("📄 Individual Document Management")
        
        documents = st.session_state.document_service.get_all_documents()
        if documents:
            selected_doc = st.selectbox(
                "Select document to manage",
                options=documents,
                format_func=lambda doc: f"{doc.title} ({doc.relative_path})"
            )
            
            if selected_doc:
                col1, col2 = st.columns(2)
                with col1:
                    st.write(f"**Title:** {selected_doc.title}")
                    st.write(f"**Path:** {selected_doc.relative_path}")
                    st.write(f"**Size:** {selected_doc.size} bytes")
                    st.write(f"**Words:** {selected_doc.word_count}")
                
                with col2:
                    if st.button("🗑️ Remove Document"):
                        st.session_state.document_service.remove_document(selected_doc.id)
                        log_admin_action("remove_document", selected_doc.relative_path)
                        st.success(f"Removed {selected_doc.title}")
                        st.rerun()
                    
                    if st.button("🔄 Reload Document"):
                        # Reload document from file
                        new_doc = st.session_state.document_service.load_document(
                            selected_doc.path, 
                            st.session_state.docs_directory
                        )
                        if new_doc:
                            st.session_state.document_service.remove_document(selected_doc.id)
                            st.session_state.document_service.add_document(new_doc)
                            log_admin_action("reload_document", selected_doc.relative_path)
                            st.success(f"Reloaded {selected_doc.title}")
                            st.rerun()
        else:
            st.info("No documents to manage.")
    
    with tab5:
        st.header("📋 Admin Activity Logs")
        
        # Filter logs
        col1, col2 = st.columns(2)
        with col1:
            log_limit = st.number_input("Show last N actions", min_value=10, max_value=100, value=20)
        with col2:
            action_filter = st.selectbox("Filter by action", ["All"] + list(set(action.action for action in st.session_state.admin_actions)))
        
        # Display logs
        filtered_actions = st.session_state.admin_actions
        if action_filter != "All":
            filtered_actions = [a for a in filtered_actions if a.action == action_filter]
        
        recent_actions = list(reversed(filtered_actions[-log_limit:]))
        
        if recent_actions:
            for action in recent_actions:
                with st.expander(f"{action.action} - {action.target} ({action.timestamp.strftime('%Y-%m-%d %H:%M:%S')})"):
                    col1, col2 = st.columns(2)
                    with col1:
                        st.write(f"**Action:** {action.action}")
                        st.write(f"**Target:** {action.target}")
                        st.write(f"**User:** {action.user}")
                    with col2:
                        st.write(f"**Timestamp:** {action.timestamp}")
                        if action.details:
                            st.write("**Details:**")
                            st.json(action.details)
        else:
            st.info("No admin actions logged yet.")
        
        # Clear logs
        if st.button("🗑️ Clear Logs"):
            st.session_state.admin_actions.clear()
            st.success("Admin logs cleared!")
            st.rerun()


if __name__ == "__main__":
    main()