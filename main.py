"""
Interactive OpenAI Assistant with Vector Store Document Processing
------------------------------------------------------------
This script creates an OpenAI Assistant that can answer questions about uploaded documents.
It handles PDF uploads to OpenAI's vector stores and provides an interactive interface
for users to ask questions about the documents.
"""

import os
import sys
import time
import getpass
import hashlib
import json
import concurrent.futures
from concurrent.futures import ThreadPoolExecutor
from typing import Dict, List, Any, Optional

try:
    import PyPDF2
    from tqdm import tqdm
    from openai import OpenAI
    from dotenv import load_dotenv
except ModuleNotFoundError as e:
    print(f"❌ Missing Python dependency: {e.name}")
    print("Use the project virtual environment, or run the helper script:")
    print("  ./run.sh")
    print("or:")
    print("  source venv/bin/activate")
    print("  pip install -r requirements.txt")
    print("  python main.py")
    sys.exit(1)

# Load environment variables from .env file
load_dotenv()

# Configuration
class Config:
    # API key handling using dotenv
    def __init__(self):
        # Get API key from environment variable loaded by dotenv
        self.api_key = os.getenv('OPENAI_API_KEY')
        
        # If not found, prompt the user
        if not self.api_key:
            print("⚠️ OPENAI_API_KEY not found in .env file.")
            self.api_key = getpass.getpass("Please enter your OpenAI API key: ")
            if not self.api_key:
                sys.exit("API key is required to proceed.")
        
        # Set PDF directory with default fallback
        self.pdf_dir = os.environ.get('PDF_DIR', './assets/')
        self.state_file = os.environ.get('APP_STATE_FILE', './.rag_state.json')
        
        # Create directory if it doesn't exist
        if not os.path.exists(self.pdf_dir):
            os.makedirs(self.pdf_dir)
            print(f"Created directory: {self.pdf_dir}")
        
        # Assistant configuration
        self.vector_store_name = "document_store"
        self.assistant_model = "gpt-4o-mini"  # Can be upgraded to more powerful models
        self.assistant_instructions = """
        You are a helpful document assistant that answers questions based on the content of uploaded documents.
        Provide accurate information and cite your sources when possible.
        If you don't know the answer or can't find relevant information, acknowledge this honestly.
        """


class StateManager:
    def __init__(self, state_file: str):
        self.state_file = state_file

    def load(self) -> Dict[str, Any]:
        if not os.path.exists(self.state_file):
            return {}

        try:
            with open(self.state_file, 'r', encoding='utf-8') as state_file:
                return json.load(state_file)
        except Exception as e:
            print(f"⚠️ Could not read state file {self.state_file}: {e}")
            return {}

    def save(self, state: Dict[str, Any]) -> None:
        try:
            with open(self.state_file, 'w', encoding='utf-8') as state_file:
                json.dump(state, state_file, indent=2)
        except Exception as e:
            print(f"⚠️ Could not save state file {self.state_file}: {e}")

# Vector Store Management
class VectorStoreManager:
    def __init__(self, client: OpenAI, config: Config):
        self.client = client
        self.config = config

    def get_pdf_files(self) -> List[str]:
        """Returns the PDF files in the configured directory."""
        return sorted(
            os.path.join(self.config.pdf_dir, file_name)
            for file_name in os.listdir(self.config.pdf_dir)
            if file_name.lower().endswith('.pdf')
        )

    def get_pdf_fingerprint(self, pdf_files: List[str]) -> str:
        """Builds a lightweight fingerprint of the current PDF set."""
        fingerprint = hashlib.sha256()

        for file_path in pdf_files:
            file_stats = os.stat(file_path)
            fingerprint.update(os.path.basename(file_path).encode('utf-8'))
            fingerprint.update(str(file_stats.st_size).encode('utf-8'))
            fingerprint.update(str(file_stats.st_mtime_ns).encode('utf-8'))

        return fingerprint.hexdigest()
    
    def create_vector_store(self) -> Dict[str, Any]:
        """Creates a new vector store and returns its details."""
        try:
            vector_store = self.client.vector_stores.create(name=self.config.vector_store_name)
            details = {
                "id": vector_store.id,
                "name": vector_store.name,
                "created_at": vector_store.created_at,
                "file_count": vector_store.file_counts.completed
            }
            print(f"✅ Vector store '{details['name']}' created successfully (ID: {details['id']})")
            return details
        except Exception as e:
            print(f"❌ Error creating vector store: {e}")
            return {}

    def get_vector_store(self, vector_store_id: str) -> Optional[Any]:
        """Retrieves an existing vector store if it still exists."""
        try:
            return self.client.vector_stores.retrieve(vector_store_id)
        except Exception:
            return None
    
    def upload_single_pdf(self, file_path: str, vector_store_id: str) -> Dict[str, Any]:
        """Uploads a single PDF file to the vector store."""
        file_name = os.path.basename(file_path)
        try:
            # First validate the PDF file
            try:
                with open(file_path, 'rb') as f:
                    PyPDF2.PdfReader(f)
            except Exception as pdf_error:
                return {"file": file_name, "status": "failed", "error": f"Invalid PDF: {str(pdf_error)}"}
            
            # Upload the file
            with open(file_path, 'rb') as pdf_file:
                file_response = self.client.files.create(file=pdf_file, purpose="assistants")
            
            # Attach to vector store
            self.client.vector_stores.files.create(
                vector_store_id=vector_store_id,
                file_id=file_response.id
            )
            return {"file": file_name, "status": "success"}
        except Exception as e:
            return {"file": file_name, "status": "failed", "error": str(e)}
    
    def upload_pdf_files(self, vector_store_id: str, pdf_files: Optional[List[str]] = None) -> Dict[str, Any]:
        """Uploads multiple PDF files to the vector store in parallel."""
        if pdf_files is None:
            pdf_files = self.get_pdf_files()
        
        if not pdf_files:
            print(f"⚠️ No PDF files found in {self.config.pdf_dir}")
            return {"total_files": 0, "successful_uploads": 0, "failed_uploads": 0}
        
        stats = {"total_files": len(pdf_files), "successful_uploads": 0, "failed_uploads": 0, "errors": []}
        print(f"📁 Found {len(pdf_files)} PDF files to process. Uploading in parallel...")
        
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = {executor.submit(self.upload_single_pdf, file_path, vector_store_id): file_path 
                      for file_path in pdf_files}
            
            for future in tqdm(concurrent.futures.as_completed(futures), total=len(pdf_files)):
                result = future.result()
                if result["status"] == "success":
                    stats["successful_uploads"] += 1
                else:
                    stats["failed_uploads"] += 1
                    stats["errors"].append(result)
        
        # Print summary
        print(f"📊 Upload Summary: {stats['successful_uploads']}/{stats['total_files']} files uploaded successfully")
        if stats["errors"]:
            print(f"⚠️ {stats['failed_uploads']} files failed to upload. Check the errors list for details.")
        
        return stats

# Assistant Management
class AssistantManager:
    def __init__(self, client: OpenAI, config: Config):
        self.client = client
        self.config = config
        self.assistant = None
        self.thread = None
    
    def create_assistant(self, vector_store_id: str) -> Dict[str, Any]:
        """Creates a new assistant with the specified configuration."""
        try:
            self.assistant = self.client.beta.assistants.create(
                instructions=self.config.assistant_instructions,
                model=self.config.assistant_model,
                tools=[{"type": "file_search"}],
                tool_resources={
                    "file_search": {
                        "vector_store_ids": [vector_store_id]
                    }
                }
            )
            print(f"🤖 Assistant created successfully (ID: {self.assistant.id})")
            return self.assistant
        except Exception as e:
            print(f"❌ Error creating assistant: {e}")
            return None

    def get_assistant(self, assistant_id: str) -> Optional[Any]:
        """Retrieves an existing assistant if it still exists."""
        try:
            assistant = self.client.beta.assistants.retrieve(assistant_id)
            self.assistant = assistant
            return assistant
        except Exception:
            return None
    
    def create_thread(self) -> Any:
        """Creates a new thread for conversation."""
        try:
            self.thread = self.client.beta.threads.create()
            print(f"💬 Thread created successfully (ID: {self.thread.id})")
            return self.thread
        except Exception as e:
            print(f"❌ Error creating thread: {e}")
            return None
    
    def add_message_to_thread(self, content: str) -> Any:
        """Adds a user message to the thread."""
        if not self.thread:
            print("❌ Thread not initialized. Create a thread first.")
            return None
        
        try:
            message = self.client.beta.threads.messages.create(
                thread_id=self.thread.id,
                role="user",
                content=content
            )
            return message
        except Exception as e:
            print(f"❌ Error adding message to thread: {e}")
            return None
    
    def run_assistant(self, thread_id: str, assistant_id: str) -> Any:
        """Runs the assistant on the specified thread and returns the result."""
        try:
            run = self.client.beta.threads.runs.create(
                thread_id=thread_id,
                assistant_id=assistant_id
            )
            
            # Poll for completion
            print("⏳ Processing your request...", end="", flush=True)
            while True:
                run_status = self.client.beta.threads.runs.retrieve(
                    thread_id=thread_id,
                    run_id=run.id
                )
                
                if run_status.status == 'completed':
                    print("\r✅ Processing complete!       ")
                    break
                elif run_status.status in ['failed', 'cancelled', 'expired']:
                    print(f"\r❌ Run {run_status.status}!       ")
                    return None
                
                print(".", end="", flush=True)
                time.sleep(1)
            
            return run_status
        except Exception as e:
            print(f"\r❌ Error running assistant: {e}")
            return None
    
    def get_messages(self, thread_id: str, limit: int = 10) -> List[Any]:
        """Gets the most recent messages from the thread."""
        try:
            messages = self.client.beta.threads.messages.list(
                thread_id=thread_id,
                limit=limit
            )
            return messages.data
        except Exception as e:
            print(f"❌ Error retrieving messages: {e}")
            return []
    
    def display_assistant_response(self, thread_id: str) -> None:
        """Displays the most recent assistant response from the thread."""
        messages = self.get_messages(thread_id)
        
        # Find the latest assistant message
        for message in messages:
            if message.role == "assistant":
                # Display each content item
                for content in message.content:
                    if content.type == "text":
                        print("\n🤖 Assistant: ", end="")
                        print(content.text.value)
                break

# Main Application Logic
class DocumentAssistant:
    def __init__(self):
        self.config = Config()
        self.client = OpenAI(api_key=self.config.api_key)
        self.state_manager = StateManager(self.config.state_file)
        self.vector_store_manager = VectorStoreManager(self.client, self.config)
        self.assistant_manager = AssistantManager(self.client, self.config)
        self.vector_store_id = None
        self.assistant_id = None
        self.thread_id = None

    def save_state(self, pdf_files: List[str], pdf_fingerprint: str) -> None:
        """Persists reusable OpenAI resource IDs for future runs."""
        self.state_manager.save({
            "vector_store_id": self.vector_store_id,
            "assistant_id": self.assistant_id,
            "pdf_fingerprint": pdf_fingerprint,
            "pdf_files": [os.path.basename(file_path) for file_path in pdf_files],
            "updated_at": int(time.time())
        })

    def create_thread(self) -> bool:
        """Creates a fresh thread for the current interactive session."""
        thread = self.assistant_manager.create_thread()
        if not thread:
            return False

        self.thread_id = thread.id
        return True

    def reuse_cached_resources(self, pdf_files: List[str], pdf_fingerprint: str) -> bool:
        """Reuses the existing vector store and assistant when the PDFs are unchanged."""
        state = self.state_manager.load()
        cached_vector_store_id = state.get("vector_store_id")
        cached_assistant_id = state.get("assistant_id")
        cached_fingerprint = state.get("pdf_fingerprint")

        if not cached_vector_store_id:
            return False

        if cached_fingerprint != pdf_fingerprint:
            print("📄 PDF set changed. Rebuilding the vector store...")
            return False

        vector_store = self.vector_store_manager.get_vector_store(cached_vector_store_id)
        if not vector_store:
            print("♻️ Cached vector store is missing. Rebuilding it...")
            return False

        self.vector_store_id = cached_vector_store_id

        if cached_assistant_id:
            assistant = self.assistant_manager.get_assistant(cached_assistant_id)
            if assistant:
                self.assistant_id = assistant.id
                print("♻️ Reusing cached vector store and assistant.")
                return True

            print("♻️ Cached assistant is missing. Recreating it...")

        assistant = self.assistant_manager.create_assistant(self.vector_store_id)
        if not assistant:
            return False

        self.assistant_id = assistant.id
        self.save_state(pdf_files, pdf_fingerprint)
        print("♻️ Reusing cached vector store and saving a fresh assistant.")
        return True
    
    def setup(self) -> bool:
        """Sets up the assistant and required resources."""
        print("\n" + "="*60)
        print("📚 Setting up Document Assistant")
        print("="*60)

        pdf_files = self.vector_store_manager.get_pdf_files()
        pdf_fingerprint = self.vector_store_manager.get_pdf_fingerprint(pdf_files)

        if self.reuse_cached_resources(pdf_files, pdf_fingerprint):
            if not self.create_thread():
                return False
            print("\n✅ Setup complete! The document assistant is ready to use.")
            return True
        
        # Create vector store
        vector_store = self.vector_store_manager.create_vector_store()
        if not vector_store:
            return False
        self.vector_store_id = vector_store["id"]
        
        # Upload PDF files
        upload_stats = self.vector_store_manager.upload_pdf_files(self.vector_store_id, pdf_files)
        if upload_stats["successful_uploads"] == 0:
            print("⚠️ No files were successfully uploaded. Setup will continue but assistant may not be useful.")
        
        # Create assistant
        assistant = self.assistant_manager.create_assistant(self.vector_store_id)
        if not assistant:
            return False
        self.assistant_id = assistant.id
        
        self.save_state(pdf_files, pdf_fingerprint)

        if not self.create_thread():
            return False
        
        print("\n✅ Setup complete! The document assistant is ready to use.")
        return True
    
    def ask_question(self, question: str) -> None:
        """Sends a question to the assistant and displays the response."""
        # Add message to thread
        message = self.assistant_manager.add_message_to_thread(question)
        if not message:
            return
        
        # Run assistant
        run = self.assistant_manager.run_assistant(self.thread_id, self.assistant_id)
        if not run:
            return
        
        # Display response
        self.assistant_manager.display_assistant_response(self.thread_id)
    
    def interactive_session(self) -> None:
        """Runs an interactive session with the user."""
        print("\n" + "="*60)
        print("🤖 Document Assistant Interactive Mode")
        print("="*60)
        print("Type your questions about the documents. Type 'exit' to quit.")
        
        while True:
            print("\n" + "-"*60)
            try:
                user_input = input("\n🧑 Your question: ")
            except EOFError:
                print("\nInput stream closed. Exiting interactive mode.")
                break
            except KeyboardInterrupt:
                print("\n\nInterrupted. Goodbye!")
                break
            
            if user_input.lower() in ['exit', 'quit', 'q']:
                print("\nThank you for using the Document Assistant. Goodbye!")
                break
            
            if not user_input.strip():
                continue
                
            self.ask_question(user_input)

# Entry point
def main():
    print("\n🔍 Document Assistant - Interactive OpenAI Assistant with Vector Store")
    
    # Confirm dotenv loaded properly
    if os.getenv("OPENAI_API_KEY"):
        print("✅ API key loaded from .env file")
    else:
        print("⚠️ No API key found in .env file")
    
    # Initialize the assistant
    doc_assistant = DocumentAssistant()
    
    # Setup the assistant
    if not doc_assistant.setup():
        print("❌ Setup failed. Exiting.")
        return
    
    # Start interactive session
    doc_assistant.interactive_session()

if __name__ == "__main__":
    main()
