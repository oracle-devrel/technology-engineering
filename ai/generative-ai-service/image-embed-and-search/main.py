import gradio as gr
import os
import base64
from PIL import Image
import io
import time

# Disable Gradio analytics to prevent timeout errors
os.environ["GRADIO_ANALYTICS_ENABLED"] = "false"
try:
    from langchain_chroma import Chroma
except ImportError:
    from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import OCIGenAIEmbeddings
from langchain.docstore.document import Document
import config
import oci

# Configuration
endpoint = "https://inference.generativeai.us-chicago-1.oci.oraclecloud.com"  # Same as main.py
embedding_model = config.EMBEDDING_MODEL
embedding_model_choices = config.EMBEDDING_MODEL_CHOICES
compartment_id = config.COMPARTMENT_ID

# Initialize OCI client
oci_config = oci.config.from_file('~/.oci/config', "DEFAULT")
generative_ai_inference_client = oci.generative_ai_inference.GenerativeAiInferenceClient(
    config=oci_config,
    service_endpoint=endpoint,
    retry_strategy=oci.retry.NoneRetryStrategy(),
    timeout=(10, 240)
)

def get_base64_from_images(images):
    """Convert images to base64 with metadata"""
    base64_list = []
    filenames = []
    for image_path in images:
        try:
            with open(image_path, "rb") as f:
                image_data = base64.b64encode(f.read()).decode()
            base64_list.append(image_data)
            filename = image_path.split('/')[-1] if '/' in image_path else image_path.split('\\')[-1]
            filenames.append(filename)
        except Exception as e:
            print(f"Error processing {image_path}: {e}")
    return base64_list, filenames

def create_image_vector_store(base64_list, filenames, embedding_model_name):
    """Create ChromaDB vector store for images"""
    embeddings = OCIGenAIEmbeddings(
        model_id=embedding_model_name,
        service_endpoint=endpoint,
        compartment_id=compartment_id
    )

    # Create documents with metadata
    documents = []
    for base64_data, filename in zip(base64_list, filenames):
        doc = Document(
            page_content=base64_data,
            metadata={"filename": filename, "type": "image"}
        )
        documents.append(doc)

    vectorstore = Chroma.from_documents(
        documents=documents,
        embedding=embeddings
    )

    return vectorstore

def add_images_to_vector_store(vector_store, base64_list, filenames, embedding_model_name):
    """Add new images to existing vector store"""
    if vector_store is None:
        return create_image_vector_store(base64_list, filenames, embedding_model_name)

    embeddings = OCIGenAIEmbeddings(
        model_id=embedding_model_name,
        service_endpoint=endpoint,
        compartment_id=compartment_id
    )

    documents = []
    for base64_data, filename in zip(base64_list, filenames):
        doc = Document(
            page_content=base64_data,
            metadata={"filename": filename, "type": "image"}
        )
        documents.append(doc)

    vector_store.add_documents(documents)
    # Note: Chroma 0.4.x+ automatically persists documents, manual persist() is deprecated
    return vector_store

def search_images_by_text(query, vector_store, embedding_model_name, k=6):
    """Search images using text query"""
    # Load existing vector store if none exists
    if vector_store is None:
        vector_store = load_existing_image_vector_store()
        print(f"DEBUG: Loaded vector store from disk: {vector_store}")

    if vector_store is None:
        return None, [], "Please load and embed images first."

    try:
        # Debug: Check vector store content
        try:
            docs_dict = vector_store.get()
            total_docs = len(docs_dict.get('documents', []))
            print(f"DEBUG: Vector store has {total_docs} total documents")
        except Exception as debug_e:
            print(f"DEBUG: Could not get total document count: {debug_e}")

        # Get text embedding
        embeddings = OCIGenAIEmbeddings(
            model_id=embedding_model,
            service_endpoint=endpoint,
            compartment_id=compartment_id
        )

        # Search for similar images with scores
        docs_with_scores = vector_store.similarity_search_with_score(query, k=k)
        print(f"DEBUG: Search returned {len(docs_with_scores)} documents for query '{query}'")

        if not docs_with_scores:
            return None, [], "No images found for query: '{query}'"

        # Convert base64 back to PIL images and remove duplicates based on content
        # Keep track of all unique results with their scores
        seen_images = set()
        unique_results = []  # List of (image, score, filename) tuples

        for doc, score in docs_with_scores:
            base64_data = doc.page_content
            if base64_data not in seen_images:  # Avoid duplicate images
                seen_images.add(base64_data)
                image_bytes = base64.b64decode(base64_data)
                image = Image.open(io.BytesIO(image_bytes))
                filename = doc.metadata.get("filename", "unknown")
                unique_results.append((image, score, filename))

        # Sort by score in descending order (highest scores first)
        unique_results.sort(key=lambda x: x[1], reverse=True)

        # Take top k results
        top_k_results = unique_results[:k]

        # Extract components
        unique_images = [result[0] for result in top_k_results]
        unique_scores = [result[1] for result in top_k_results]
        unique_filenames = [result[2] for result in top_k_results]

        # Top result (most similar) with confidence score
        top_image = unique_images[0] if unique_images else None
        top_score = unique_scores[0] if unique_scores else 0

        # Similar images (2nd, 3rd, 4th, etc.) with scores
        similar_images = unique_images[1:] if len(unique_images) > 1 else []
        similar_scores = unique_scores[1:] if len(unique_scores) > 1 else []

        # Create status message with confidence scores
        status_parts = [f"Found {len(unique_images)} unique similar images for query: '{query}'"]
        if unique_scores:
            status_parts.append(f"Top match confidence: {top_score:.4f}")
            if len(unique_scores) > 1:
                status_parts.append(f"Other matches: {', '.join([f'{score:.4f}' for score in similar_scores])}")

        # Store the top match filename for deletion
        top_filename = unique_filenames[0] if unique_filenames else None

        return top_image, similar_images, " | ".join(status_parts), top_filename

    except Exception as e:
        print(f"DEBUG: Search error: {e}")
        return None, [], f"Error searching images: {str(e)}"

def search_images_by_image(image_file, vector_store, embedding_model_name, k=6):
    """Search images using image query (image-to-image similarity)"""
    # Load existing vector store if none exists
    if vector_store is None:
        vector_store = load_existing_image_vector_store()

    if vector_store is None:
        return None, [], "Please load and embed images first."

    if image_file is None:
        return None, [], "Please upload an image to search with."

    try:
        # Convert uploaded image to base64
        with open(image_file.name, "rb") as f:
            image_data = base64.b64encode(f.read()).decode()

        # Create data URI for image embedding
        data_uri = f"data:image/jpeg;base64,{image_data}"

        # Get image embedding using OCI
        embed_detail = oci.generative_ai_inference.models.EmbedTextDetails(
            serving_mode=oci.generative_ai_inference.models.OnDemandServingMode(
                model_id=embedding_model
            ),
            input_type="IMAGE",
            inputs=[data_uri],
            truncate="NONE",
            compartment_id=compartment_id
        )

        response = generative_ai_inference_client.embed_text(embed_detail)
        query_embedding = response.data.embeddings[0]

        # Search for similar images using vector search
        docs = vector_store.similarity_search_by_vector(query_embedding, k=k*2)  # Get more results to account for duplicates

        if not docs:
            return None, [], "No similar images found in the database."

        # For image search, we need to calculate similarity scores manually
        # Since we're using in-memory Chroma, we'll use LangChain's similarity search with scores
        try:
            # Use LangChain's similarity_search_by_vector which should work with in-memory store
            docs_with_scores = vector_store.similarity_search_by_vector_with_score(query_embedding, k=k*2)
            # Convert to expected format
            docs_with_scores = [(doc.page_content, score, doc.metadata) for doc, score in docs_with_scores]

        except Exception as e:
            print(f"Error getting scores from Chroma: {e}")
            # Fallback: assign dummy scores
            docs_with_scores = [(doc.page_content, 0.5, doc.metadata) for doc in docs]

        # Convert base64 back to PIL images and remove duplicates based on content
        seen_images = set()
        unique_images = []
        unique_scores = []
        unique_filenames = []

        for doc_content, score, metadata in docs_with_scores:
            base64_data = doc_content
            if base64_data not in seen_images:  # Avoid duplicate images
                seen_images.add(base64_data)
                image_bytes = base64.b64decode(base64_data)
                image = Image.open(io.BytesIO(image_bytes))
                unique_images.append(image)
                unique_scores.append(score)
                unique_filenames.append(metadata.get("filename", "unknown") if metadata else "unknown")

                if len(unique_images) >= k:  # Limit to k results
                    break

        # Top result (most similar) with confidence score
        top_image = unique_images[0] if unique_images else None
        top_score = unique_scores[0] if unique_scores else 0

        # Similar images (2nd, 3rd, 4th, etc.) with scores
        similar_images = unique_images[1:] if len(unique_images) > 1 else []
        similar_scores = unique_scores[1:] if len(unique_scores) > 1 else []

        # Create status message with confidence scores
        status_parts = [f"Found {len(unique_images)} similar images based on your uploaded image"]
        if unique_scores and unique_scores[0] > 0:  # Only show scores if we have real ones
            status_parts.append(f"Top match confidence: {top_score:.4f}")
            if len(unique_scores) > 1:
                status_parts.append(f"Other matches: {', '.join([f'{score:.4f}' for score in similar_scores])}")

        # Store the top match filename for deletion
        top_filename = unique_filenames[0] if unique_filenames else None

        return top_image, similar_images, " | ".join(status_parts), top_filename

    except Exception as e:
        return None, [], f"Error searching images: {str(e)}", None

def load_existing_image_vector_store():
    """Vector store is in-memory only - no persistence"""
    return None

def process_uploaded_images(images, current_vector_store, embedding_model_name):
    """Process uploaded images in batches of 4 and add to vector store"""
    if not images:
        return current_vector_store, "No images selected."

    try:
        # Convert uploaded files to temp files (handle different Gradio formats)
        temp_files = []
        for i, img_file in enumerate(images):
            # Handle different Gradio file input formats
            if hasattr(img_file, 'read') and hasattr(img_file, 'name'):
                # File object format
                filename = os.path.basename(img_file.name) if img_file.name else f"temp_{i}.jpg"
                temp_path = f"temp_{filename}"
                with open(temp_path, "wb") as f:
                    f.write(img_file.read())
            elif isinstance(img_file, str):
                # String path format - copy the file
                filename = os.path.basename(img_file)
                temp_path = f"temp_{filename}"
                with open(img_file, "rb") as src, open(temp_path, "wb") as dst:
                    dst.write(src.read())
            elif hasattr(img_file, 'name') and hasattr(img_file, 'data'):
                # Dictionary format with 'name' and 'data' keys
                filename = os.path.basename(img_file.name) if img_file.name else f"temp_{i}.jpg"
                temp_path = f"temp_{filename}"
                with open(temp_path, "wb") as f:
                    f.write(img_file.data)
            else:
                # Fallback - try to convert to string and handle as path
                img_str = str(img_file)
                filename = f"temp_{i}.jpg"
                temp_path = f"temp_{filename}"
                try:
                    # If it's a path-like string, try to read the file
                    with open(img_str, "rb") as src, open(temp_path, "wb") as dst:
                        dst.write(src.read())
                except:
                    # If that fails, skip this file
                    print(f"Could not process file {i}: {img_file}")
                    continue

            temp_files.append(temp_path)

        # Process images in batches of 10 to avoid API timeouts
        batch_size = 4
        total_processed = 0

        # Load existing vector store if none exists
        if current_vector_store is None:
            current_vector_store = load_existing_image_vector_store()

        for i in range(0, len(temp_files), batch_size):
            batch_files = temp_files[i:i + batch_size]
            print(f"Processing batch {i//batch_size + 1}: {len(batch_files)} images")

            # Convert batch to base64
            base64_list, filenames = get_base64_from_images(batch_files)

            if base64_list:
                # Add batch to vector store
                updated_vector_store = add_images_to_vector_store(current_vector_store, base64_list, filenames, embedding_model_name)
                current_vector_store = updated_vector_store
                total_processed += len(filenames)
                print(f"✓ Batch completed: {len(filenames)} images embedded")
            else:
                print(f"✗ Batch failed: no images could be processed")

            # Small delay between batches to prevent overwhelming the API
            if i + batch_size < len(temp_files):
                time.sleep(0.5)

        # Clean up all temp files
        for temp_file in temp_files:
            try:
                os.remove(temp_file)
            except:
                pass

        return current_vector_store, f"Successfully embedded {total_processed} images in {len(temp_files)//batch_size + 1} batches using {embedding_model_name}."

    except Exception as e:
        # Clean up temp files in case of error
        for temp_file in temp_files:
            try:
                os.remove(temp_file)
            except:
                pass
        return current_vector_store, f"Error processing images: {str(e)}"

def clear_image_embeddings():
    """Clear all image embeddings - in-memory only"""
    return None, "All image embeddings cleared."

def get_all_embedded_images(vector_store, page=1, images_per_page=25):
    """Get all embedded images from vector store with pagination"""
    if vector_store is None:
        vector_store = load_existing_image_vector_store()

    if vector_store is None:
        return [], 0, 0, "No image database found. Please load and embed images first."

    try:
        # Get all documents from vector store
        docs_dict = vector_store.get()
        documents = docs_dict.get('documents', [])
        metadatas = docs_dict.get('metadatas', [])
        total_images = len(documents)

        if total_images == 0:
            return [], 0, 0, "No images found in the database."

        # Calculate pagination
        total_pages = (total_images + images_per_page - 1) // images_per_page  # Ceiling division
        start_idx = (page - 1) * images_per_page
        end_idx = min(start_idx + images_per_page, total_images)

        # Get images for current page
        page_documents = documents[start_idx:end_idx]
        page_metadatas = metadatas[start_idx:end_idx] if start_idx < len(metadatas) else []
        images = []

        for i, doc in enumerate(page_documents):
            try:
                # Convert base64 back to PIL image
                image_bytes = base64.b64decode(doc)
                image = Image.open(io.BytesIO(image_bytes))

                # Apply rotation if specified in metadata
                metadata = page_metadatas[i] if i < len(page_metadatas) and page_metadatas[i] else {}
                rotation = metadata.get('rotation', 0)
                if rotation and rotation != 0:
                    image = image.rotate(-rotation, expand=True)  # Negative for correct orientation

                images.append(image)
            except Exception as e:
                print(f"Error converting image: {e}")
                # Add a placeholder or skip
                continue

        status = f"Showing images {start_idx + 1}-{end_idx} of {total_images} (Page {page}/{total_pages})"

        return images, page, total_pages, status

    except Exception as e:
        return [], 0, 0, f"Error retrieving images: {str(e)}"

def delete_image_from_vector_store(vector_store, image_filename):
    """Delete an image from the vector store by filename - not supported in in-memory mode"""
    return vector_store, "Image deletion is not supported in in-memory mode. Please restart the application to clear all data."

def get_database_stats():
    """Get statistics about the current image database - simplified for in-memory mode"""
    try:
        # For in-memory mode, we can't easily check persistent collections
        # Just return a generic message since we don't have access to the current vector store here
        return "Vector store is running in in-memory mode. Upload images to see database statistics."
    except Exception as e:
        return f"Error retrieving database stats: {str(e)}"



def main():
    """Main Gradio application"""
    # Check for existing vector store (but don't initialize State with it due to deepcopy issues)
    existing_store = load_existing_image_vector_store()
    if existing_store:
        print(f"✓ Found existing image vector store with data - will load when needed")
    else:
        print("No existing image vector store found - will create new one when images are loaded")

    with gr.Blocks(title="Image Embedding & Search", theme=gr.themes.Soft()) as demo:
        vector_store = gr.State(None)  # Keep as None for Gradio compatibility

        # State variables for storing top match filenames
        top_text_filename = gr.State(None)
        top_image_filename = gr.State(None)

        gr.Markdown("# Image Embedding & Search 🖼️🔍")

        with gr.Tabs():
            with gr.TabItem("Load & Embed Images"):
                with gr.Column():
                    gr.Markdown("### Upload Your Own Images")
                    gr.Markdown("Upload your own images to embed them in the database.")
                    images = gr.File(label="Upload Images", file_types=["image/*"], file_count="multiple")
                    embedding_model_upload = gr.Dropdown(
                        label="Embedding Model",
                        choices=embedding_model_choices,
                        value=embedding_model,
                        info="Select the embedding model to use for embedding images"
                    )
                    upload_btn = gr.Button("Upload & Embed Images", variant="primary")

                    gr.Markdown("### Status")
                    status = gr.Textbox(label="Status", interactive=False)

                    gr.Markdown("### Clear All")
                    clear_btn = gr.Button("Clear All Embeddings", variant="secondary")

            with gr.TabItem("Search Images by Text"):
                with gr.Column():
                    gr.Markdown("### Text Search")
                    gr.Markdown("Enter a text description to find similar images.")
                    query = gr.Textbox(
                        label="Search Query",
                        placeholder="e.g., 'red dress', 'blue jeans', 'summer outfit'..."
                    )
                    embedding_model_text = gr.Dropdown(
                        label="Embedding Model",
                        choices=embedding_model_choices,
                        value=embedding_model,
                        info="Select the embedding model to use for search"
                    )
                    search_text_btn = gr.Button("Search by Text", variant="primary")

                    gr.Markdown("### Top Match")
                    with gr.Row():
                        top_image_text = gr.Image(label="Most Similar Image", height=300)
                        with gr.Column():
                            with gr.Row():
                                rotate_left_text_btn = gr.Button("↺ Rotate Left", variant="secondary")
                                rotate_right_text_btn = gr.Button("↻ Rotate Right", variant="secondary")
                            delete_text_btn = gr.Button("🗑️ Delete Top Match", variant="stop")
                            delete_text_status = gr.Textbox(label="Delete Status", interactive=False, lines=2)

            with gr.TabItem("Search Images by Image"):
                with gr.Column():
                    gr.Markdown("### Image Search")
                    gr.Markdown("Upload an image to find visually similar images.")
                    search_image = gr.File(label="Upload Image to Search", file_types=["image/*"])
                    uploaded_image_display = gr.Image(label="Uploaded Image Preview", height=200)

                    embedding_model_image = gr.Dropdown(
                        label="Embedding Model",
                        choices=embedding_model_choices,
                        value="cohere.embed-v4.0",
                        info="Select the embedding model to use for search"
                    )
                    search_image_btn = gr.Button("Search by Image", variant="primary")

                    gr.Markdown("### Top Match")
                    with gr.Row():
                        top_image_image = gr.Image(label="Most Similar Image", height=300)
                        with gr.Column():
                            with gr.Row():
                                rotate_left_image_btn = gr.Button("↺ Rotate Left", variant="secondary")
                                rotate_right_image_btn = gr.Button("↻ Rotate Right", variant="secondary")
                            delete_image_btn = gr.Button("🗑️ Delete Top Match", variant="stop")
                            delete_image_status = gr.Textbox(label="Delete Status", interactive=False, lines=2)

            with gr.TabItem("Browse Vector Store"):
                with gr.Column():
                    gr.Markdown("### Browse All Embedded Images")
                    gr.Markdown("View all images currently embedded in the vector store database.")

                    gr.Markdown("### Navigation")
                    with gr.Row():
                        prev_btn = gr.Button("⬅️ Previous Page", variant="secondary")
                        load_btn = gr.Button("🔄 Load Images", variant="primary")
                        page_input = gr.Number(label="Go to Page", value=40, minimum=1, precision=0)
                        go_to_page_btn = gr.Button("Go", variant="primary")
                        next_btn = gr.Button("Next Page ➡️", variant="secondary")

                    gr.Markdown("### Image Gallery")
                    browse_gallery = gr.Gallery(
                        label="Embedded Images",
                        columns=5,
                        rows=5,
                        height=1500,
                        allow_preview=True
                    )

                    gr.Markdown("### Page Status")
                    page_status = gr.Textbox(
                        label="Current Page",
                        value="Click 'Load Images' to browse your embedded images",
                        interactive=False
                    )

                    # Hidden state for current page
                    current_page = gr.State(1)

        # Event handlers
        upload_btn.click(
            process_uploaded_images,
            inputs=[images, vector_store, embedding_model_upload],
            outputs=[vector_store, status]
        )

        def search_text_handler(query, vector_store, embedding_model):
            top_image, similar_images, status, top_filename = search_images_by_text(query, vector_store, embedding_model)
            return top_image, top_filename

        def search_image_handler(search_image, vector_store, embedding_model):
            top_image, similar_images, status, top_filename = search_images_by_image(search_image, vector_store, embedding_model)
            return top_image, top_filename

        search_text_btn.click(
            search_text_handler,
            inputs=[query, vector_store, embedding_model_text],
            outputs=[top_image_text, top_text_filename]
        )

        search_image_btn.click(
            search_image_handler,
            inputs=[search_image, vector_store, embedding_model_image],
            outputs=[top_image_image, top_image_filename]
        )

        # Rotation handlers for text search
        def rotate_left_text(image):
            if image is not None:
                # Convert numpy array to PIL Image if needed
                if isinstance(image, Image.Image):
                    pil_image = image
                else:
                    # Assume it's a numpy array from Gradio
                    pil_image = Image.fromarray(image.astype('uint8'), 'RGB')
                return pil_image.rotate(90, expand=True)  # Rotate 90 degrees clockwise for "left" visual effect
            return image

        def rotate_right_text(image):
            if image is not None:
                # Convert numpy array to PIL Image if needed
                if isinstance(image, Image.Image):
                    pil_image = image
                else:
                    # Assume it's a numpy array from Gradio
                    pil_image = Image.fromarray(image.astype('uint8'), 'RGB')
                return pil_image.rotate(-90, expand=True)  # Rotate -90 degrees counter-clockwise for "right" visual effect
            return image

        # Rotation handlers for image search
        def rotate_left_image(image):
            if image is not None:
                # Convert numpy array to PIL Image if needed
                if isinstance(image, Image.Image):
                    pil_image = image
                else:
                    # Assume it's a numpy array from Gradio
                    pil_image = Image.fromarray(image.astype('uint8'), 'RGB')
                return pil_image.rotate(90, expand=True)
            return image

        def rotate_right_image(image):
            if image is not None:
                # Convert numpy array to PIL Image if needed
                if isinstance(image, Image.Image):
                    pil_image = image
                else:
                    # Assume it's a numpy array from Gradio
                    pil_image = Image.fromarray(image.astype('uint8'), 'RGB')
                return pil_image.rotate(-90, expand=True)
            return image

        # Apply rotation handlers
        rotate_left_text_btn.click(
            rotate_left_text,
            inputs=[top_image_text],
            outputs=[top_image_text]
        )

        rotate_right_text_btn.click(
            rotate_right_text,
            inputs=[top_image_text],
            outputs=[top_image_text]
        )

        rotate_left_image_btn.click(
            rotate_left_image,
            inputs=[top_image_image],
            outputs=[top_image_image]
        )

        rotate_right_image_btn.click(
            rotate_right_image,
            inputs=[top_image_image],
            outputs=[top_image_image]
        )

        # Delete button handlers
        delete_text_btn.click(
            delete_image_from_vector_store,
            inputs=[vector_store, top_text_filename],
            outputs=[vector_store, delete_text_status]
        )

        delete_image_btn.click(
            delete_image_from_vector_store,
            inputs=[vector_store, top_image_filename],
            outputs=[vector_store, delete_image_status]
        )

        # Update uploaded image display when file is uploaded
        search_image.change(
            lambda img: img,
            inputs=[search_image],
            outputs=[uploaded_image_display]
        )

        clear_btn.click(
            clear_image_embeddings,
            inputs=[],
            outputs=[vector_store, status]
        )

        # Browse Vector Store event handlers
        def load_first_page(vector_store):
            images, page, total_pages, status = get_all_embedded_images(vector_store, page=1)
            return images, status, 1

        def load_prev_page(vector_store, current_page):
            if current_page > 1:
                new_page = current_page - 1
                images, page, total_pages, status = get_all_embedded_images(vector_store, page=new_page)
                return images, status, new_page
            else:
                images, page, total_pages, status = get_all_embedded_images(vector_store, page=current_page)
                return images, f"Already on first page. {status}", current_page

        def load_next_page(vector_store, current_page):
            images, page, total_pages, status = get_all_embedded_images(vector_store, page=current_page + 1)
            if page > current_page:  # Successfully moved to next page
                return images, status, page
            else:  # Couldn't move to next page (probably at end)
                images, page, total_pages, status = get_all_embedded_images(vector_store, page=current_page)
                return images, f"Already on last page. {status}", current_page

        load_btn.click(
            load_first_page,
            inputs=[vector_store],
            outputs=[browse_gallery, page_status, current_page]
        )

        prev_btn.click(
            load_prev_page,
            inputs=[vector_store, current_page],
            outputs=[browse_gallery, page_status, current_page]
        )

        def go_to_specific_page(vector_store, page_number):
            try:
                page_num = int(page_number) if page_number else 1
                images, page, total_pages, status = get_all_embedded_images(vector_store, page=page_num)
                if page_num > total_pages and total_pages > 0:
                    # If requested page is beyond total pages, go to last page
                    images, page, total_pages, status = get_all_embedded_images(vector_store, page=total_pages)
                    status = f"Page {page_num} doesn't exist. Showing last page instead. {status}"
                elif page_num < 1:
                    # If requested page is less than 1, go to first page
                    images, page, total_pages, status = get_all_embedded_images(vector_store, page=1)
                    status = f"Page {page_num} doesn't exist. Showing first page instead. {status}"
                return images, status, page
            except Exception as e:
                return [], f"Error loading page {page_number}: {str(e)}", 1

        next_btn.click(
            load_next_page,
            inputs=[vector_store, current_page],
            outputs=[browse_gallery, page_status, current_page]
        )

        go_to_page_btn.click(
            go_to_specific_page,
            inputs=[vector_store, page_input],
            outputs=[browse_gallery, page_status, current_page]
        )

    demo.launch(show_error=True)

if __name__ == '__main__':
    main()
